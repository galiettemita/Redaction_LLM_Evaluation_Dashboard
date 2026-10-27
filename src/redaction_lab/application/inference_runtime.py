"""Fail-closed, application-owned model runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import time
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from redaction_lab.adapters.ollama import OllamaAdapter
from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.contracts import PredictionManifest


class InferenceRuntimeUnavailable(RuntimeError):
    """The pinned local model runtime has not been independently qualified."""


@dataclass(frozen=True)
class VerifiedInferenceRuntime:
    adapter: PredictionAdapter
    model_config_id: str
    model_manifest_digest: str
    process: subprocess.Popen[bytes] | None = None

    def close(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


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

    @staticmethod
    def _json(opener, url: str) -> object:
        try:
            with opener.open(Request(url, method="GET"), timeout=5) as response:
                raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise ValueError("runtime response exceeds limit")
            return json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, HTTPError, URLError, ValueError) as error:
            raise InferenceRuntimeUnavailable("model runtime verification failed") from error

    @classmethod
    def _assert_api_identity(cls, opener, value: dict[str, object]) -> None:
        endpoint = str(value["endpoint"])
        version = cls._json(opener, endpoint + "/api/version")
        tags = cls._json(opener, endpoint + "/api/tags")
        if not isinstance(version, dict) or version.get("version") != value["ollama_version"]:
            raise InferenceRuntimeUnavailable("Ollama API version mismatch")
        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list) or not any(
            isinstance(model, dict)
            and model.get("name") == value["provider_model_id"]
            and model.get("digest") == value["model_manifest_digest"]
            for model in models
        ):
            raise InferenceRuntimeUnavailable("model manifest identity mismatch")

    @staticmethod
    def _start_owned_runtime(
        executable: Path, model_store: Path
    ) -> subprocess.Popen[bytes]:
        try:
            connection = socket.create_connection(("127.0.0.1", 11434), timeout=0.25)
        except (ConnectionRefusedError, TimeoutError, OSError):
            pass
        else:
            connection.close()
            raise InferenceRuntimeUnavailable(
                "refusing an unowned pre-existing model runtime"
            )
        try:
            return subprocess.Popen(
                [str(executable), "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                env={
                    "PATH": "/usr/bin:/bin",
                    "OLLAMA_HOST": "127.0.0.1:11434",
                    "OLLAMA_MODELS": str(model_store),
                },
            )
        except OSError as error:
            raise InferenceRuntimeUnavailable("could not start owned Ollama runtime") from error

    @staticmethod
    def _assert_model_files(model_store: Path, value: dict[str, object]) -> None:
        files = value.get("model_files")
        if not isinstance(files, dict) or not 1 <= len(files) <= 128:
            raise InferenceRuntimeUnavailable("model file inventory is incomplete")
        for relative, expected in files.items():
            if (
                not isinstance(relative, str)
                or re.fullmatch(r"(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+", relative)
                is None
                or not isinstance(expected, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", expected) is None
                or expected.endswith("0" * 64)
            ):
                raise InferenceRuntimeUnavailable("model file inventory is invalid")
            candidate = model_store.joinpath(*relative.split("/"))
            current = model_store
            try:
                for component in relative.split("/")[:-1]:
                    current = current / component
                    if current.is_symlink() or not current.is_dir():
                        raise InferenceRuntimeUnavailable("model file path is untrusted")
                info = candidate.stat()
                if (
                    candidate.is_symlink()
                    or not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.geteuid()
                    or info.st_mode & 0o022
                    or info.st_nlink != 1
                ):
                    raise InferenceRuntimeUnavailable("model file is untrusted")
                observed = sha256()
                with candidate.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        observed.update(chunk)
            except OSError as error:
                raise InferenceRuntimeUnavailable("model file is unavailable") from error
            if "sha256:" + observed.hexdigest() != expected:
                raise InferenceRuntimeUnavailable("model file digest mismatch")

    def verified(self) -> VerifiedInferenceRuntime:
        try:
            value = json.loads(self.LOCK_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise InferenceRuntimeUnavailable("model runtime lock is unavailable") from error
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
        executable = Path(value["ollama_executable"])
        if not executable.is_absolute() or executable.is_symlink() or not os.access(executable, os.X_OK):
            raise InferenceRuntimeUnavailable("locked Ollama executable is unavailable")
        try:
            executable_hash = sha256()
            with executable.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    executable_hash.update(chunk)
        except OSError as error:
            raise InferenceRuntimeUnavailable("Ollama executable verification failed") from error
        if "sha256:" + executable_hash.hexdigest() != executable_digest:
            raise InferenceRuntimeUnavailable("Ollama executable digest mismatch")
        model_store = Path(value["model_store"])
        try:
            model_store_info = model_store.stat()
        except OSError as error:
            raise InferenceRuntimeUnavailable("locked model store is unavailable") from error
        if (
            not model_store.is_absolute()
            or model_store.is_symlink()
            or not stat.S_ISDIR(model_store_info.st_mode)
            or model_store_info.st_uid != os.geteuid()
            or model_store_info.st_mode & 0o022
        ):
            raise InferenceRuntimeUnavailable("locked model store is untrusted")
        self._assert_model_files(model_store, value)
        try:
            completed = subprocess.run(
                [str(executable), "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
                env={"PATH": "/usr/bin:/bin"},
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise InferenceRuntimeUnavailable("Ollama executable verification failed") from error
        if completed.returncode != 0 or completed.stdout.strip() != f"ollama version {value['ollama_version']}":
            raise InferenceRuntimeUnavailable("Ollama version mismatch")
        process = self._start_owned_runtime(executable, model_store)
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        try:
            deadline = time.monotonic() + 5
            while True:
                if process.poll() is not None:
                    raise InferenceRuntimeUnavailable("owned Ollama runtime exited")
                try:
                    self._assert_api_identity(opener, value)
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
                self._assert_model_files(model_store, value)
                self._assert_api_identity(opener, value)

            return VerifiedInferenceRuntime(
                adapter=_RuntimeBoundAdapter(adapter, assert_runtime),
                model_config_id=str(value["model_config_id"]),
                model_manifest_digest=digest,
                process=process,
            )
        except Exception:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            raise
