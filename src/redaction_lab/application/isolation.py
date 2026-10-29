"""Fail-closed launcher abstraction for the dedicated PDF worker runtime."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
from threading import Event, Thread
import tomllib
from typing import Protocol

from redaction_lab.application.config import WORKER_TIMEOUT_SECONDS
from redaction_lab.application.config import MAX_WORKER_RESPONSE_BYTES
from redaction_lab.application.paths import resolve_paths
from redaction_lab.application.worker_protocol import (
    WORKER_PROTOCOL_VERSION,
    WorkerRequest,
    WorkerResponse,
    decode_response,
    encode_request,
)
from redaction_lab.contracts import DocumentRole


class RuntimeUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimePolicy:
    executable: str
    executable_sha256: str
    executable_version: str
    machine_name: str
    image_digest: str
    runtime_root: str
    containers_conf: str
    timeout_seconds: int = WORKER_TIMEOUT_SECONDS

    @classmethod
    def from_lock(
        cls, lock_path: Path, *, application_root: Path | None = None
    ) -> "RuntimePolicy":
        try:
            payload = json.loads(Path(lock_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeUnavailable("PDF worker runtime lock is unavailable") from error
        if not isinstance(payload, dict):
            raise RuntimeUnavailable("PDF worker runtime lock is invalid")
        digests = (
            payload.get("machine_image_digest"),
            payload.get("base_image_digest"),
            payload.get("image_digest"),
        )
        if (
            payload.get("runtime_verified") is not True
            or payload.get("protocol_version") != WORKER_PROTOCOL_VERSION
            or any(
                not isinstance(value, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
                or value.endswith("0" * 64)
                for value in digests
            )
        ):
            raise RuntimeUnavailable("PDF worker runtime lock is unverified")
        expected_paths = {
            "podman_executable": "runtime/pdf-worker/podman/bin/podman",
            "runtime_state": "runtime/pdf-worker/state",
            "containers_conf": "runtime/pdf-worker/containers.conf",
        }
        if any(payload.get(key) != value for key, value in expected_paths.items()):
            raise RuntimeUnavailable("PDF worker runtime lock paths are invalid")
        executable_sha256 = payload.get("podman_executable_sha256")
        executable_version = payload.get("podman_version")
        timeout_seconds = payload.get("timeout_seconds")
        if (
            not isinstance(executable_sha256, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", executable_sha256) is None
            or executable_sha256.endswith("0" * 64)
            or not isinstance(executable_version, str)
            or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", executable_version) is None
            or payload.get("machine_name") != "redaction-lab-pdf-v1"
            or not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or not 1 <= timeout_seconds <= 300
        ):
            raise RuntimeUnavailable("PDF worker runtime executable identity is invalid")
        root = Path(application_root) if application_root is not None else resolve_paths().root
        if not root.is_absolute():
            raise RuntimeUnavailable("application runtime root is invalid")
        runtime_root = root / "runtime" / "pdf-worker"
        return cls(
            executable=str(root / expected_paths["podman_executable"]),
            executable_sha256=executable_sha256,
            executable_version=executable_version,
            machine_name=payload["machine_name"],
            image_digest=payload["image_digest"],
            runtime_root=str(runtime_root),
            containers_conf=str(root / expected_paths["containers_conf"]),
            timeout_seconds=timeout_seconds,
        )


@dataclass(frozen=True)
class RuntimeInspection:
    executable_available: bool
    machine_name: str
    rootless: bool
    machine_volumes: tuple[str, ...]
    image_digest: str
    executable_sha256: str
    executable_version: str


@dataclass(frozen=True)
class WorkerObservation:
    """Bound protocol output, not proof of production runtime authority."""

    response: WorkerResponse
    image_digest: str


class RuntimeRunner(Protocol):
    def inspect(self, policy: RuntimePolicy) -> RuntimeInspection: ...

    def run(
        self,
        command: tuple[str, ...],
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> tuple[int, bytes, bytes]: ...


class SubprocessPodmanRunner:
    """Production runner. Tests inject a fake and never operate Podman."""

    def __init__(self, *, max_stdout_bytes: int = MAX_WORKER_RESPONSE_BYTES) -> None:
        self.max_stdout_bytes = max_stdout_bytes
        self._executable_fd: int | None = None
        self._executable_identity: tuple[int, ...] | None = None
        self._environment: dict[str, str] | None = None

    @staticmethod
    def _file_identity(info: os.stat_result) -> tuple[int, ...]:
        return (
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            info.st_mode,
            info.st_uid,
            info.st_nlink,
        )

    def _release_executable(self) -> None:
        descriptor, self._executable_fd = self._executable_fd, None
        self._executable_identity = None
        self._environment = None
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def close(self) -> None:
        self._release_executable()

    @classmethod
    def _audit_runtime_path(cls, runtime_root: Path, target: Path) -> None:
        try:
            relative = target.relative_to(runtime_root)
        except ValueError as error:
            raise RuntimeUnavailable("PDF worker runtime path escapes its root") from error
        paths = [runtime_root]
        current = runtime_root
        for component in relative.parts:
            current /= component
            paths.append(current)
        for path in paths:
            try:
                info = path.lstat()
            except OSError as error:
                raise RuntimeUnavailable("PDF worker runtime path is unavailable") from error
            if (
                path.is_symlink()
                or not stat.S_ISDIR(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o022
            ):
                raise RuntimeUnavailable("PDF worker runtime path is untrusted")

    @classmethod
    def _hash_descriptor(cls, descriptor: int) -> tuple[str, tuple[int, ...]]:
        before = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if cls._file_identity(before) != cls._file_identity(after):
            raise RuntimeUnavailable("Podman executable changed during hashing")
        return "sha256:" + digest.hexdigest(), cls._file_identity(after)

    def _open_executable(self, policy: RuntimePolicy) -> None:
        self._release_executable()
        executable = Path(policy.executable)
        runtime_root = Path(policy.runtime_root)
        self._audit_runtime_path(runtime_root, executable.parent)
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
                raise RuntimeUnavailable("Podman executable is untrusted")
            digest, identity = self._hash_descriptor(descriptor)
            if digest != policy.executable_sha256:
                raise RuntimeUnavailable("Podman executable digest mismatch")
        except Exception:
            if "descriptor" in locals():
                os.close(descriptor)
            raise
        self._executable_fd = descriptor
        self._executable_identity = identity

    def _assert_executable_identity(self, policy: RuntimePolicy, phase: str) -> None:
        if self._executable_fd is None or self._executable_identity is None:
            raise RuntimeUnavailable("Podman executable is not retained")
        try:
            descriptor_info = os.fstat(self._executable_fd)
            path_info = Path(policy.executable).lstat()
        except OSError as error:
            raise RuntimeUnavailable(f"Podman executable changed {phase}") from error
        if (
            stat.S_ISLNK(path_info.st_mode)
            or self._file_identity(descriptor_info) != self._executable_identity
            or self._file_identity(path_info) != self._executable_identity
        ):
            raise RuntimeUnavailable(f"Podman executable changed {phase}")

    @staticmethod
    def _runtime_environment(policy: RuntimePolicy) -> dict[str, str]:
        state = Path(policy.runtime_root) / "state"
        return {
            "PATH": "/usr/bin:/bin",
            "HOME": str(Path(policy.runtime_root)),
            "XDG_CONFIG_HOME": str(state / "config"),
            "XDG_DATA_HOME": str(state / "data"),
            "XDG_RUNTIME_DIR": str(state / "tmp"),
            "CONTAINERS_CONF": policy.containers_conf,
        }

    def _run_verified(
        self, policy: RuntimePolicy, command: tuple[str, ...], *, timeout: int = 10
    ) -> subprocess.CompletedProcess[bytes]:
        self._assert_executable_identity(policy, "before execution")
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                timeout=timeout,
                env=self._environment,
            )
        finally:
            self._assert_executable_identity(policy, "during execution")
        return completed

    def _assert_runtime_configuration(self, policy: RuntimePolicy) -> None:
        runtime_root = Path(policy.runtime_root)
        state = runtime_root / "state"
        for directory in (state, state / "config", state / "data", state / "tmp"):
            self._audit_runtime_path(runtime_root, directory)
        path = Path(policy.containers_conf)
        self._audit_runtime_path(runtime_root, path.parent)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.geteuid()
                or before.st_mode & 0o022
                or before.st_nlink != 1
                or not 0 < before.st_size <= 64 * 1024
            ):
                raise RuntimeUnavailable("Podman runtime configuration is untrusted")
            raw = os.read(descriptor, 64 * 1024 + 1)
            after = os.fstat(descriptor)
        except OSError as error:
            raise RuntimeUnavailable("Podman runtime configuration is unavailable") from error
        finally:
            if "descriptor" in locals():
                os.close(descriptor)
        if (
            len(raw) != before.st_size
            or self._file_identity(before) != self._file_identity(after)
        ):
            raise RuntimeUnavailable("Podman runtime configuration changed")
        try:
            value = tomllib.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise RuntimeUnavailable("Podman runtime configuration is invalid") from error
        expected_helpers = [str(runtime_root / "podman/bin")]
        if (
            value.get("engine", {}).get("helper_binaries_dir") != expected_helpers
            or value.get("machine", {}).get("volumes") != []
            or value.get("containers", {}).get("netns") != "none"
            or value.get("containers", {}).get("read_only") is not True
            or value.get("containers", {}).get("no_hosts") is not True
        ):
            raise RuntimeUnavailable("Podman runtime configuration is unsafe")

    def _read_machine_configuration(self, policy: RuntimePolicy) -> dict[str, object]:
        path = (
            Path(policy.runtime_root)
            / "state/config/containers/podman/machine/applehv"
            / f"{policy.machine_name}.json"
        )
        self._audit_runtime_path(Path(policy.runtime_root), path.parent)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.geteuid()
                or before.st_mode & 0o022
                or before.st_nlink != 1
                or not 0 < before.st_size <= 64 * 1024
            ):
                raise RuntimeUnavailable("Podman machine configuration is untrusted")
            raw = os.read(descriptor, 64 * 1024 + 1)
            after = os.fstat(descriptor)
        except OSError as error:
            raise RuntimeUnavailable("Podman machine configuration is unavailable") from error
        finally:
            if "descriptor" in locals():
                os.close(descriptor)
        if (
            len(raw) != before.st_size
            or self._file_identity(before) != self._file_identity(after)
        ):
            raise RuntimeUnavailable("Podman machine configuration changed")
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeUnavailable("Podman machine configuration is invalid") from error
        if not isinstance(value, dict):
            raise RuntimeUnavailable("Podman machine configuration is invalid")
        return value

    def _terminate_container(self, command: tuple[str, ...]) -> None:
        try:
            name = command[command.index("--name") + 1]
            prefix = command[:3]
            subprocess.run(
                (*prefix, "kill", "--signal=KILL", name),
                capture_output=True,
                timeout=5,
                check=False,
                env=self._environment,
            )
            subprocess.run(
                (*prefix, "rm", "--force", name),
                capture_output=True,
                timeout=5,
                check=False,
                env=self._environment,
            )
        except Exception:
            pass

    def inspect(self, policy: RuntimePolicy) -> RuntimeInspection:
        try:
            self._open_executable(policy)
            self._assert_runtime_configuration(policy)
            self._environment = self._runtime_environment(policy)
            version = self._run_verified(
                policy, (policy.executable, "--version")
            )
            expected_version = f"podman version {policy.executable_version}"
            if version.stdout.decode("utf-8").strip() != expected_version:
                raise RuntimeUnavailable("Podman executable version mismatch")
            machine = self._run_verified(
                policy,
                (policy.executable, "machine", "inspect", policy.machine_name),
            )
            image = self._run_verified(
                policy,
                (
                    policy.executable,
                    "--connection",
                    policy.machine_name,
                    "image",
                    "inspect",
                    policy.image_digest,
                ),
            )
            machine_data = json.loads(machine.stdout)[0]
            image_data = json.loads(image.stdout)[0]
            machine_configuration = self._read_machine_configuration(policy)
            configured_mounts = machine_configuration.get("Mounts")
            configured_host_user = machine_configuration.get("HostUser")
            if not isinstance(configured_mounts, list) or not isinstance(
                configured_host_user, dict
            ):
                raise RuntimeUnavailable("Podman machine policy is incomplete")
            volumes = tuple(str(value) for value in configured_mounts)
            configured_rootful = configured_host_user.get("Rootful") is not False
            live_rootful = machine_data.get("Rootful") is not False
            running = machine_data.get("State") == "running"
            digests = tuple(image_data.get("RepoDigests", ()))
            identities = {
                str(image_data.get("Id", "")),
                str(image_data.get("Digest", "")),
                *(value.rsplit("@", 1)[-1] for value in digests),
            }
            identities.update(
                f"sha256:{value}" for value in tuple(identities)
                if re.fullmatch(r"[0-9a-f]{64}", value) is not None
            )
            observed_digest = policy.image_digest if policy.image_digest in identities else ""
            return RuntimeInspection(
                True,
                str(machine_data.get("Name", "")),
                running and not configured_rootful and not live_rootful,
                volumes,
                observed_digest,
                policy.executable_sha256,
                policy.executable_version,
            )
        except RuntimeUnavailable:
            self._release_executable()
            raise
        except Exception:
            self._release_executable()
            return RuntimeInspection(False, policy.machine_name, False, (), "", "", "")

    def run(
        self,
        command: tuple[str, ...],
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> tuple[int, bytes, bytes]:
        if self._executable_fd is None or self._environment is None:
            raise RuntimeUnavailable("Podman executable was not verified")
        policy = RuntimePolicy(
            executable=command[0],
            executable_sha256="",
            executable_version="",
            machine_name=command[2],
            image_digest=command[-1],
            runtime_root=str(Path(self._environment["XDG_CONFIG_HOME"]).parents[1]),
            containers_conf=self._environment["CONTAINERS_CONF"],
        )
        self._assert_executable_identity(policy, "before worker launch")
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self._environment,
            )
        except Exception:
            self._release_executable()
            raise
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None
        stdout = bytearray()
        stderr = bytearray()
        overflow = Event()

        def write_input() -> None:
            try:
                process.stdin.write(input_bytes)
                process.stdin.flush()
            except BrokenPipeError:
                pass
            finally:
                process.stdin.close()

        def read_bounded(stream, destination: bytearray, limit: int) -> None:
            while True:
                chunk = stream.read(65_536)
                if not chunk:
                    return
                remaining = limit + 1 - len(destination)
                if remaining > 0:
                    destination.extend(chunk[:remaining])
                if len(destination) > limit:
                    overflow.set()
                    process.kill()
                    return

        threads = (
            Thread(target=write_input, daemon=True),
            Thread(target=read_bounded, args=(process.stdout, stdout, self.max_stdout_bytes), daemon=True),
            Thread(target=read_bounded, args=(process.stderr, stderr, 4096), daemon=True),
        )
        for thread in threads:
            thread.start()
        try:
            try:
                returncode = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired as error:
                process.kill()
                process.wait()
                self._terminate_container(command)
                raise TimeoutError("isolated PDF worker deadline exceeded") from error
            finally:
                for thread in threads:
                    thread.join(timeout=5)
            if overflow.is_set():
                self._terminate_container(command)
                raise RuntimeUnavailable("isolated PDF worker output limit exceeded")
            return returncode, bytes(stdout), bytes(stderr)
        finally:
            try:
                self._assert_executable_identity(policy, "during worker execution")
            finally:
                self._release_executable()


class _IsolatedPdfWorkerClient:
    def __init__(self, policy: RuntimePolicy, runner: RuntimeRunner | None = None) -> None:
        self.policy = policy
        self.runner = runner or SubprocessPodmanRunner()

    def _verify_runtime(self) -> RuntimeInspection:
        inspection = self.runner.inspect(self.policy)
        if (
            not inspection.executable_available
            or inspection.machine_name != self.policy.machine_name
            or not inspection.rootless
            or inspection.machine_volumes
            or inspection.image_digest != self.policy.image_digest
            or inspection.executable_sha256 != self.policy.executable_sha256
            or inspection.executable_version != self.policy.executable_version
        ):
            close = getattr(self.runner, "close", None)
            if callable(close):
                close()
            raise RuntimeUnavailable("approved isolated PDF runtime is unavailable")
        return inspection

    def ensure_available(self) -> None:
        """Verify runtime readiness without retaining an executable descriptor."""

        try:
            self._verify_runtime()
        finally:
            close = getattr(self.runner, "close", None)
            if callable(close):
                close()

    def _command(self, nonce: str) -> tuple[str, ...]:
        return (
            self.policy.executable,
            "--connection",
            self.policy.machine_name,
            "run",
            "--interactive",
            "--rm",
            "--name",
            f"redaction-lab-pdf-{nonce}",
            "--pull=never",
            "--network=none",
            "--read-only",
            "--read-only-tmpfs=false",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=256m",
            "--cap-drop=all",
            "--security-opt=no-new-privileges",
            "--user=65532:65532",
            "--pids-limit=32",
            "--memory=1536m",
            "--memory-swap=1536m",
            "--cpus=1",
            "--shm-size=32m",
            "--ulimit=nofile=64:64",
            "--log-driver=none",
            self.policy.image_digest,
        )

    def process(
        self,
        pdf_bytes: bytes,
        *,
        project_id: str,
        role: DocumentRole,
    ) -> WorkerObservation:
        inspection = self._verify_runtime()
        nonce = secrets.token_hex(16)
        request = WorkerRequest(
            protocol_version=WORKER_PROTOCOL_VERSION,
            request_nonce=nonce,
            project_id=project_id,
            role=role,
            input_sha256=sha256(pdf_bytes).hexdigest(),
            byte_count=len(pdf_bytes),
        )
        try:
            returncode, stdout, _stderr = self.runner.run(
                self._command(nonce),
                input_bytes=encode_request(request, pdf_bytes),
                timeout_seconds=self.policy.timeout_seconds,
            )
        except TimeoutError as error:
            raise RuntimeUnavailable("isolated PDF worker timeout") from error
        if returncode != 0:
            raise RuntimeUnavailable("isolated PDF worker failed")
        response = decode_response(stdout)
        if (
            response.protocol_version != request.protocol_version
            or response.request_nonce != request.request_nonce
            or response.project_id != request.project_id
            or response.role is not request.role
            or response.input_sha256 != request.input_sha256
        ):
            raise ValueError("isolated worker response binding mismatch")
        return WorkerObservation(response=response, image_digest=inspection.image_digest)


class NonAuthoritativePdfWorkerProbe(_IsolatedPdfWorkerClient):
    """Injectable protocol/command probe with no persistence authority.

    This seam exists only for deterministic tests. Application processing never
    accepts an instance of this class or any caller-provided runner or policy.
    """


_INSTALL_RUNTIME_LOCK = (
    Path(__file__).resolve().parents[3] / "packaging" / "pdf-worker" / "runtime.lock"
)


class ApplicationPdfWorker(_IsolatedPdfWorkerClient):
    """Application-owned production worker composed from install-owned state."""

    def __init__(self) -> None:
        policy = RuntimePolicy.from_lock(
            _INSTALL_RUNTIME_LOCK, application_root=resolve_paths().root
        )
        super().__init__(policy, SubprocessPodmanRunner())
