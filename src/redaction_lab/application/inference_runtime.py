"""Fail-closed, application-owned model runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import time
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.adapters.ollama import OllamaAdapter
from redaction_lab.application.paths import resolve_paths
from redaction_lab.contracts import PredictionManifest


class InferenceRuntimeUnavailable(RuntimeError):
    """The pinned local model runtime has not been independently qualified."""


def _terminate_process(process) -> None:  # type: ignore[no-untyped-def]
    if isinstance(process, _SupervisedProcess):
        process.terminate()
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _terminate_process_group(process) -> None:  # type: ignore[no-untyped-def]
    """Terminate the runtime's isolated group even if its leader already exited."""

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        _terminate_process(process)
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.02)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


class _SupervisedProcess:
    """Process-like handle whose pipe owns the supervisor and runtime lifetime."""

    def __init__(
        self,
        supervisor: subprocess.Popen[bytes],
        lifetime_fd: int,
        child_pid: int,
    ) -> None:
        self._supervisor = supervisor
        self._lifetime_fd = lifetime_fd
        self.child_pid = child_pid

    @property
    def pid(self) -> int:
        return self._supervisor.pid

    def poll(self) -> int | None:
        return self._supervisor.poll()

    def terminate(self) -> None:
        descriptor, self._lifetime_fd = self._lifetime_fd, -1
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def wait(self, timeout: float) -> int:
        return self._supervisor.wait(timeout=timeout)

    def kill(self) -> None:
        self.terminate()
        if self.child_pid > 0:
            try:
                os.killpg(self.child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self._supervisor.poll() is not None:
            return
        try:
            if os.getpgid(self.pid) == self.pid:
                os.killpg(self.pid, signal.SIGKILL)
            else:
                self._supervisor.kill()
        except ProcessLookupError:
            pass


@dataclass
class VerifiedInferenceRuntime:
    adapter: PredictionAdapter
    model_id: str
    model_config_id: str
    model_manifest_digest: str
    process: subprocess.Popen[bytes] | _SupervisedProcess | None = None
    executable_fd: int | None = None

    def close(self) -> None:
        process, self.process = self.process, None
        descriptor, self.executable_fd = self.executable_fd, None
        if process is not None:
            _terminate_process(process)
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


class _RuntimeBoundAdapter(PredictionAdapter):
    """Check the owned process and exact model digest around every request."""

    def __init__(self, adapter: OllamaAdapter, assert_runtime: Callable[[], None]) -> None:
        self._adapter = adapter
        self._assert_runtime = assert_runtime
        self.model_id = adapter.model_id
        self.model_config_id = adapter.model_config_id

    def request_hash(self, manifest: PredictionManifest) -> str:
        return self._adapter.request_hash(manifest)

    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        self._assert_runtime()
        response = await self._adapter.predict(manifest)
        self._assert_runtime()
        return response


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise HTTPError(req.full_url, code, "redirect rejected", headers, fp)


class InferenceRuntime:
    """Load only the install-owned lock; callers cannot supply trusted transports."""

    LOCK_PATH = Path(__file__).resolve().parents[3] / "packaging/model-runtime/runtime.lock"
    APPLICATION_ROOT: Path | None = None

    @classmethod
    def _resolve_locked_path(cls, raw: object) -> Path:
        if (
            not isinstance(raw, str)
            or re.fullmatch(r"(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+", raw) is None
            or any(part in {".", ".."} for part in raw.split("/"))
        ):
            raise InferenceRuntimeUnavailable("runtime path is not application-relative")
        root = cls.APPLICATION_ROOT or resolve_paths().root
        if not root.is_absolute():
            raise InferenceRuntimeUnavailable("application root is unavailable")
        return root / raw

    @staticmethod
    def _version_output_matches(stdout: str, expected: str) -> bool:
        return stdout.strip().splitlines() in (
            [f"ollama version {expected}"],
            [
                "Warning: could not connect to a running Ollama instance",
                f"Warning: client version is {expected}",
            ],
        )

    @staticmethod
    def _json(opener, url: str, *, timeout: float = 5) -> object:
        try:
            with opener.open(Request(url, method="GET"), timeout=timeout) as response:
                raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise ValueError("runtime response exceeds limit")
            return json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, HTTPError, URLError, ValueError) as error:
            raise InferenceRuntimeUnavailable("model runtime verification failed") from error

    @classmethod
    def _assert_api_identity(
        cls, opener, value: dict[str, object], *, timeout: float = 5
    ) -> None:
        endpoint = str(value["endpoint"])
        version = cls._json(opener, endpoint + "/api/version", timeout=timeout)
        tags = cls._json(opener, endpoint + "/api/tags", timeout=timeout)
        cls._validate_api_identity(version, tags, value)

    @staticmethod
    def _validate_api_identity(
        version: object, tags: object, value: dict[str, object]
    ) -> None:
        if not isinstance(version, dict) or version.get("version") != value["ollama_version"]:
            raise InferenceRuntimeUnavailable("Ollama API version mismatch")
        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list) or not any(
            isinstance(model, dict)
            and model.get("name") == value["provider_model_id"]
            and isinstance(model.get("digest"), str)
            and re.fullmatch(r"[0-9a-f]{64}", model["digest"]) is not None
            and "sha256:" + model["digest"] == value["model_manifest_digest"]
            for model in models
        ):
            raise InferenceRuntimeUnavailable("model manifest identity mismatch")

    @classmethod
    def _probe_api_identity(
        cls, value: dict[str, object], *, timeout: float
    ) -> None:
        endpoint = str(value["endpoint"])
        if endpoint != "http://127.0.0.1:11434" or timeout <= 0:
            raise InferenceRuntimeUnavailable("model runtime probe is invalid")
        command = [
            sys.executable,
            "-m",
            "redaction_lab.application.inference_runtime",
            "--probe",
            endpoint,
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                timeout=timeout,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
        except subprocess.TimeoutExpired as error:
            raise InferenceRuntimeUnavailable("model runtime probe timed out") from error
        except OSError as error:
            raise InferenceRuntimeUnavailable("model runtime probe failed") from error
        if completed.returncode != 0 or len(completed.stdout) > 2_097_152:
            raise InferenceRuntimeUnavailable("model runtime probe failed")
        try:
            payload = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InferenceRuntimeUnavailable("model runtime probe failed") from error
        if not isinstance(payload, dict) or set(payload) != {"tags", "version"}:
            raise InferenceRuntimeUnavailable("model runtime probe failed")
        cls._validate_api_identity(payload["version"], payload["tags"], value)

    @staticmethod
    def _supervisor_main(
        lifetime_fd: int,
        status_fd: int,
        executable_fd: int,
        executable: Path,
        model_store: Path,
    ) -> int:
        stopping = False
        child: subprocess.Popen[bytes] | None = None

        def stop(_signum, _frame) -> None:  # type: ignore[no-untyped-def]
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            descriptor_identity = InferenceRuntime._file_identity(
                os.fstat(executable_fd)
            )
            if (
                executable.is_symlink()
                or InferenceRuntime._file_identity(executable.lstat())
                != descriptor_identity
            ):
                raise OSError("verified executable path changed")
            child = subprocess.Popen(
                [str(executable), "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                pass_fds=(executable_fd,),
                cwd=str(executable.parent),
                start_new_session=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "HOME": str(model_store.parent),
                    "OLLAMA_HOST": "127.0.0.1:11434",
                    "OLLAMA_MODELS": str(model_store),
                    "OLLAMA_NO_CLOUD": "true",
                },
            )
            if InferenceRuntime._file_identity(executable.lstat()) != descriptor_identity:
                raise OSError("verified executable path changed during launch")
        except OSError:
            if child is not None:
                _terminate_process_group(child)
            try:
                os.write(status_fd, b"ERROR\n")
            except OSError:
                pass
            os.close(status_fd)
            os.close(lifetime_fd)
            return 1

        try:
            try:
                os.write(status_fd, f"READY:{child.pid}\n".encode("ascii"))
            except OSError:
                stopping = True
            os.close(status_fd)
            while child.poll() is None and not stopping:
                readable, _, _ = select.select([lifetime_fd], [], [], 0.1)
                if readable and not os.read(lifetime_fd, 1):
                    break
        finally:
            _terminate_process_group(child)
            os.close(lifetime_fd)
        return child.returncode or 0

    @staticmethod
    def _launch_supervisor(
        executable_fd: int, executable: Path, model_store: Path
    ) -> _SupervisedProcess:
        lifetime_read, lifetime_write = os.pipe()
        status_read, status_write = os.pipe()
        supervisor: subprocess.Popen[bytes] | None = None
        try:
            supervisor = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "redaction_lab.application.inference_runtime",
                    "--supervise",
                    str(lifetime_read),
                    str(status_write),
                    str(executable_fd),
                    str(executable),
                    str(model_store),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                pass_fds=(lifetime_read, status_write, executable_fd),
                start_new_session=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
        except OSError as error:
            os.close(lifetime_write)
            os.close(status_read)
            raise InferenceRuntimeUnavailable(
                "could not start owned Ollama supervisor"
            ) from error
        finally:
            os.close(lifetime_read)
            os.close(status_write)

        owned = _SupervisedProcess(supervisor, lifetime_write, 0)
        try:
            try:
                readable, _, _ = select.select([status_read], [], [], 5)
                status = os.read(status_read, 64) if readable else b""
            except (OSError, ValueError) as error:
                _terminate_process(owned)
                raise InferenceRuntimeUnavailable(
                    "owned Ollama supervisor handshake failed"
                ) from error
        finally:
            os.close(status_read)
        try:
            marker, child_value = status.rstrip(b"\n").split(b":", 1)
            child_pid = int(child_value) if marker == b"READY" else 0
        except (TypeError, ValueError):
            child_pid = 0
        owned.child_pid = child_pid
        if child_pid <= 0:
            _terminate_process(owned)
            raise InferenceRuntimeUnavailable("could not start owned Ollama runtime")
        return owned

    @staticmethod
    def _start_owned_runtime(
        executable_fd: int, executable: Path, model_store: Path
    ) -> _SupervisedProcess:
        try:
            connection = socket.create_connection(("127.0.0.1", 11434), timeout=0.25)
        except (ConnectionRefusedError, TimeoutError, OSError):
            pass
        else:
            connection.close()
            raise InferenceRuntimeUnavailable(
                "refusing an unowned pre-existing model runtime"
            )
        return InferenceRuntime._launch_supervisor(
            executable_fd, executable, model_store
        )

    @staticmethod
    def _file_identity(info: os.stat_result) -> tuple[int, ...]:
        return (
            info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode, info.st_uid, info.st_nlink,
        )

    @staticmethod
    def _audit_parent_directories(path: Path) -> None:
        for parent in path.parents:
            try:
                info = parent.lstat()
            except OSError as error:
                raise InferenceRuntimeUnavailable("runtime path is unavailable") from error
            if (
                parent.is_symlink()
                or not stat.S_ISDIR(info.st_mode)
                or info.st_uid not in {0, os.geteuid()}
                or info.st_mode & 0o022
            ):
                raise InferenceRuntimeUnavailable("runtime path is untrusted")

    @classmethod
    def _read_lock(cls, path: Path) -> dict[str, object]:
        if not path.is_absolute():
            raise InferenceRuntimeUnavailable("model runtime lock is unavailable")
        cls._audit_parent_directories(path)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                before = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_uid != os.geteuid()
                    or before.st_mode & 0o022
                    or before.st_nlink != 1
                    or not 0 < before.st_size <= 64 * 1024
                ):
                    raise InferenceRuntimeUnavailable("model runtime lock is untrusted")
                raw = os.read(descriptor, 64 * 1024 + 1)
                after = os.fstat(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise InferenceRuntimeUnavailable("model runtime lock is unavailable") from error
        if len(raw) != before.st_size or cls._file_identity(before) != cls._file_identity(after):
            raise InferenceRuntimeUnavailable("model runtime lock changed during verification")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InferenceRuntimeUnavailable("model runtime lock is unavailable") from error
        if not isinstance(value, dict):
            raise InferenceRuntimeUnavailable("model runtime lock is invalid")
        return value

    @classmethod
    def _hash_descriptor(cls, descriptor: int) -> tuple[str, tuple[int, ...]]:
        before = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if cls._file_identity(before) != cls._file_identity(after):
            raise InferenceRuntimeUnavailable("executable changed during verification")
        return "sha256:" + digest.hexdigest(), cls._file_identity(after)

    @classmethod
    def _open_verified_executable(
        cls, executable: Path, expected: str
    ) -> tuple[int, tuple[int, ...]]:
        if not executable.is_absolute():
            raise InferenceRuntimeUnavailable("locked Ollama executable is unavailable")
        cls._audit_parent_directories(executable)
        try:
            descriptor = os.open(executable, os.O_RDONLY | os.O_NOFOLLOW)
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o022
                or info.st_nlink != 1
                or not info.st_mode & stat.S_IXUSR
            ):
                raise InferenceRuntimeUnavailable("locked Ollama executable is untrusted")
            observed, identity = cls._hash_descriptor(descriptor)
            if observed != expected:
                raise InferenceRuntimeUnavailable("Ollama executable digest mismatch")
            return descriptor, identity
        except Exception:
            if "descriptor" in locals():
                os.close(descriptor)
            raise

    @classmethod
    def _assert_executable_path_identity(
        cls, executable: Path, expected: tuple[int, ...], phase: str
    ) -> None:
        try:
            observed = executable.lstat()
        except OSError as error:
            raise InferenceRuntimeUnavailable(
                f"Ollama executable changed {phase}"
            ) from error
        if (
            stat.S_ISLNK(observed.st_mode)
            or cls._file_identity(observed) != expected
        ):
            raise InferenceRuntimeUnavailable(f"Ollama executable changed {phase}")

    @staticmethod
    def _inventory_map(
        value: dict[str, object], key: str, *, required: bool, limit: int
    ) -> dict[str, str]:
        raw = value.get(key)
        if not isinstance(raw, dict) or (required and not raw) or len(raw) > limit:
            raise InferenceRuntimeUnavailable("runtime file inventory is incomplete")
        result: dict[str, str] = {}
        for relative, expected in raw.items():
            if (
                not isinstance(relative, str)
                or re.fullmatch(r"(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+", relative)
                is None
                or any(part in {".", ".."} for part in relative.split("/"))
                or not isinstance(expected, str)
            ):
                raise InferenceRuntimeUnavailable("runtime file inventory is invalid")
            result[relative] = expected
        return result

    @classmethod
    def _assert_file_inventory(
        cls,
        root: Path,
        expected_files: dict[str, str],
        expected_symlinks: dict[str, str],
        *,
        label: str,
    ) -> None:
        for expected in expected_files.values():
            if (
                re.fullmatch(r"sha256:[0-9a-f]{64}", expected) is None
                or expected.endswith("0" * 64)
            ):
                raise InferenceRuntimeUnavailable(f"{label} inventory is invalid")
        for target in expected_symlinks.values():
            if (
                re.fullmatch(r"(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+", target)
                is None
                or any(part in {".", ".."} for part in target.split("/"))
            ):
                raise InferenceRuntimeUnavailable(f"{label} inventory is invalid")

        cls._audit_parent_directories(root)
        directory_flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        root_descriptor = -1
        open_directories: list[tuple[int, str]] = []
        try:
            root_path_before = root.lstat()
            root_descriptor = os.open(root, directory_flags)
            root_before = os.fstat(root_descriptor)
            if (
                stat.S_ISLNK(root_path_before.st_mode)
                or not stat.S_ISDIR(root_before.st_mode)
                or cls._file_identity(root_path_before) != cls._file_identity(root_before)
                or root_before.st_uid != os.geteuid()
                or root_before.st_mode & 0o022
            ):
                raise InferenceRuntimeUnavailable(f"{label} is untrusted")
            open_directories.append((os.dup(root_descriptor), ""))
            observed_files: dict[str, str] = {}
            observed_symlinks: dict[str, str] = {}
            visited = 0
            while open_directories:
                directory_fd, prefix = open_directories.pop()
                try:
                    visited += 1
                    if visited > 256:
                        raise InferenceRuntimeUnavailable(
                            f"{label} inventory is too large"
                        )
                    with os.scandir(directory_fd) as entries:
                        for entry in entries:
                            relative = prefix + entry.name
                            info = entry.stat(follow_symlinks=False)
                            if info.st_uid != os.geteuid():
                                raise InferenceRuntimeUnavailable(
                                    f"{label} entry is untrusted"
                                )
                            if stat.S_ISLNK(info.st_mode):
                                target = os.readlink(entry.name, dir_fd=directory_fd)
                                observed_symlinks[relative] = target
                                continue
                            if info.st_mode & 0o022:
                                raise InferenceRuntimeUnavailable(
                                    f"{label} entry is untrusted"
                                )
                            if stat.S_ISDIR(info.st_mode):
                                child_fd = os.open(
                                    entry.name, directory_flags, dir_fd=directory_fd
                                )
                                child_info = os.fstat(child_fd)
                                if cls._file_identity(info) != cls._file_identity(child_info):
                                    os.close(child_fd)
                                    raise InferenceRuntimeUnavailable(
                                        f"{label} changed during verification"
                                    )
                                open_directories.append(
                                    (child_fd, relative + "/")
                                )
                                continue
                            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                                raise InferenceRuntimeUnavailable(
                                    f"{label} entry is untrusted"
                                )
                            file_fd = os.open(
                                entry.name,
                                os.O_RDONLY | os.O_NOFOLLOW,
                                dir_fd=directory_fd,
                            )
                            try:
                                before = os.fstat(file_fd)
                                if (
                                    not stat.S_ISREG(before.st_mode)
                                    or before.st_uid != os.geteuid()
                                    or before.st_mode & 0o022
                                    or before.st_nlink != 1
                                    or cls._file_identity(before)
                                    != cls._file_identity(info)
                                ):
                                    raise InferenceRuntimeUnavailable(
                                        f"{label} entry is untrusted"
                                    )
                                digest = sha256()
                                while chunk := os.read(file_fd, 1024 * 1024):
                                    digest.update(chunk)
                                after = os.fstat(file_fd)
                            finally:
                                os.close(file_fd)
                            if cls._file_identity(before) != cls._file_identity(after):
                                raise InferenceRuntimeUnavailable(
                                    f"{label} changed during verification"
                                )
                            observed_files[relative] = "sha256:" + digest.hexdigest()
                finally:
                    os.close(directory_fd)

            if (
                set(observed_files) != set(expected_files)
                or set(observed_symlinks) != set(expected_symlinks)
            ):
                raise InferenceRuntimeUnavailable(f"{label} inventory is incomplete")
            if observed_files != expected_files or observed_symlinks != expected_symlinks:
                raise InferenceRuntimeUnavailable(f"{label} digest mismatch")
            root_after = os.fstat(root_descriptor)
            root_path_after = root.lstat()
            cls._audit_parent_directories(root)
            if (
                cls._file_identity(root_before) != cls._file_identity(root_after)
                or cls._file_identity(root_before) != cls._file_identity(root_path_after)
            ):
                raise InferenceRuntimeUnavailable(f"{label} changed during verification")
        except InferenceRuntimeUnavailable:
            raise
        except OSError as error:
            raise InferenceRuntimeUnavailable(f"{label} is untrusted") from error
        finally:
            for descriptor, _ in open_directories:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if root_descriptor >= 0:
                os.close(root_descriptor)

    @classmethod
    def _assert_model_files(cls, model_store: Path, value: dict[str, object]) -> None:
        files = cls._inventory_map(value, "model_files", required=True, limit=128)
        cls._assert_file_inventory(
            model_store, files, {}, label="model store"
        )

    @classmethod
    def _assert_runtime_files(
        cls, runtime_payload: Path, value: dict[str, object]
    ) -> None:
        files = cls._inventory_map(value, "runtime_files", required=True, limit=128)
        symlinks = cls._inventory_map(
            value, "runtime_symlinks", required=False, limit=32
        )
        cls._assert_file_inventory(
            runtime_payload, files, symlinks, label="runtime payload"
        )

    def verified(self) -> VerifiedInferenceRuntime:
        value = self._read_lock(self.LOCK_PATH)
        required = {
            "schema": 1,
            "runtime_verified": True,
            "endpoint": "http://127.0.0.1:11434",
        }
        if any(value.get(key) != expected for key, expected in required.items()):
            raise InferenceRuntimeUnavailable("model runtime is unverified")
        strings = (
            "ollama_executable",
            "ollama_executable_sha256",
            "runtime_payload",
            "model_store",
            "model_id",
            "provider_model_id",
            "model_config_id",
            "ollama_version",
            "model_manifest_digest",
        )
        if any(not isinstance(value.get(key), str) or not value[key].strip() for key in strings):
            raise InferenceRuntimeUnavailable("model runtime identity is incomplete")
        if re.fullmatch(r"[A-Za-z0-9._:+-]{1,128}", value["model_config_id"]) is None:
            raise InferenceRuntimeUnavailable("model configuration identity is invalid")
        digest = value["model_manifest_digest"]
        executable_digest = value["ollama_executable_sha256"]
        if any(
            re.fullmatch(r"sha256:[0-9a-f]{64}", candidate) is None
            or candidate.endswith("0" * 64)
            for candidate in (digest, executable_digest)
        ):
            raise InferenceRuntimeUnavailable("model manifest digest is not full SHA-256")
        if value["model_id"] != value["provider_model_id"]:
            raise InferenceRuntimeUnavailable("provider model identity mismatch")
        runtime_payload = self._resolve_locked_path(value["runtime_payload"])
        executable_relative = str(value["ollama_executable"])
        if "/" in executable_relative:
            raise InferenceRuntimeUnavailable("Ollama executable path is invalid")
        executable = runtime_payload / executable_relative
        model_store = self._resolve_locked_path(value["model_store"])
        self._audit_parent_directories(model_store)
        try:
            model_store_info = model_store.stat()
        except OSError as error:
            raise InferenceRuntimeUnavailable("locked model store is unavailable") from error
        if (
            model_store.is_symlink()
            or not stat.S_ISDIR(model_store_info.st_mode)
            or model_store_info.st_uid != os.geteuid()
            or model_store_info.st_mode & 0o022
        ):
            raise InferenceRuntimeUnavailable("locked model store is untrusted")
        self._assert_runtime_files(runtime_payload, value)
        self._assert_model_files(model_store, value)
        executable_fd, executable_identity = self._open_verified_executable(
            executable, executable_digest
        )
        try:
            self._assert_executable_path_identity(
                executable, executable_identity, "before version execution"
            )
            try:
                completed = subprocess.run(
                    [str(executable), "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=str(runtime_payload),
                    env={
                        "PATH": "/usr/bin:/bin",
                        "HOME": str(model_store.parent),
                        "OLLAMA_MODELS": str(model_store),
                        "OLLAMA_NO_CLOUD": "true",
                    },
                    pass_fds=(executable_fd,),
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise InferenceRuntimeUnavailable(
                    "Ollama executable verification failed"
                ) from error
            self._assert_executable_path_identity(
                executable, executable_identity, "after version execution"
            )
            if (
                completed.returncode != 0
                or not self._version_output_matches(
                    completed.stdout, str(value["ollama_version"])
                )
            ):
                raise InferenceRuntimeUnavailable("Ollama version mismatch")
            observed_digest, observed_identity = self._hash_descriptor(executable_fd)
            if (
                observed_digest != executable_digest
                or observed_identity != executable_identity
            ):
                raise InferenceRuntimeUnavailable(
                    "Ollama executable changed before launch"
                )
            self._assert_runtime_files(runtime_payload, value)
        except Exception:
            os.close(executable_fd)
            raise
        try:
            process = self._start_owned_runtime(executable_fd, executable, model_store)
        except Exception:
            os.close(executable_fd)
            raise
        try:
            self._assert_runtime_files(runtime_payload, value)
            observed_digest, observed_identity = self._hash_descriptor(executable_fd)
            if observed_digest != executable_digest or observed_identity != executable_identity:
                raise InferenceRuntimeUnavailable("Ollama executable changed during launch")
        except Exception:
            VerifiedInferenceRuntime(
                adapter=OllamaAdapter(
                    endpoint=str(value["endpoint"]), model_id=str(value["model_id"]),
                    model_config_id=str(value["model_config_id"]), timeout_seconds=60,
                ),
                model_id=str(value["model_id"]),
                model_config_id=str(value["model_config_id"]),
                model_manifest_digest=digest,
                process=process,
                executable_fd=executable_fd,
            ).close()
            raise
        try:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise InferenceRuntimeUnavailable("owned Ollama runtime exited")
                try:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise InferenceRuntimeUnavailable(
                            "model runtime readiness timed out"
                        )
                    self._probe_api_identity(value, timeout=min(1, remaining))
                    if time.monotonic() > deadline:
                        raise InferenceRuntimeUnavailable(
                            "model runtime readiness timed out"
                        )
                    break
                except InferenceRuntimeUnavailable:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.05)
            adapter = OllamaAdapter(
                endpoint=str(value["endpoint"]), model_id=str(value["model_id"]),
                model_config_id=str(value["model_config_id"]), timeout_seconds=60,
            )

            def assert_runtime() -> None:
                if process.poll() is not None:
                    raise InferenceRuntimeUnavailable("owned Ollama runtime exited")
                self._assert_runtime_files(runtime_payload, value)
                self._assert_model_files(model_store, value)
                self._probe_api_identity(value, timeout=5)

            return VerifiedInferenceRuntime(
                adapter=_RuntimeBoundAdapter(adapter, assert_runtime),
                model_id=str(value["model_id"]),
                model_config_id=str(value["model_config_id"]),
                model_manifest_digest=digest,
                process=process,
                executable_fd=executable_fd,
            )
        except Exception:
            _terminate_process(process)
            os.close(executable_fd)
            raise


def _main(arguments: list[str]) -> int:
    if len(arguments) == 2 and arguments[0] == "--probe":
        endpoint = arguments[1]
        if endpoint != "http://127.0.0.1:11434":
            return 2
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        try:
            payload = {
                "version": InferenceRuntime._json(
                    opener, endpoint + "/api/version", timeout=5
                ),
                "tags": InferenceRuntime._json(
                    opener, endpoint + "/api/tags", timeout=5
                ),
            }
        except InferenceRuntimeUnavailable:
            return 1
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        if len(encoded) > 2_097_152:
            return 1
        os.write(sys.stdout.fileno(), encoded)
        return 0
    if len(arguments) != 6 or arguments[0] != "--supervise":
        return 2
    try:
        lifetime_fd, status_fd, executable_fd = map(int, arguments[1:4])
    except ValueError:
        return 2
    return InferenceRuntime._supervisor_main(
        lifetime_fd,
        status_fd,
        executable_fd,
        Path(arguments[4]),
        Path(arguments[5]),
    )


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
