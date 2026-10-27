"""Fail-closed, application-owned model runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from redaction_lab.adapters.ollama import OllamaAdapter


class InferenceRuntimeUnavailable(RuntimeError):
    """The pinned local model runtime has not been independently qualified."""


@dataclass(frozen=True)
class VerifiedInferenceRuntime:
    adapter: OllamaAdapter
    model_config_id: str
    model_manifest_digest: str


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
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        version = self._json(opener, value["endpoint"] + "/api/version")
        tags = self._json(opener, value["endpoint"] + "/api/tags")
        if not isinstance(version, dict) or version.get("version") != value["ollama_version"]:
            raise InferenceRuntimeUnavailable("Ollama API version mismatch")
        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list) or not any(
            isinstance(model, dict)
            and model.get("name") == value["provider_model_id"]
            and model.get("digest") == digest
            for model in models
        ):
            raise InferenceRuntimeUnavailable("model manifest identity mismatch")
        adapter = OllamaAdapter(
            endpoint=value["endpoint"], model_id=value["model_id"],
            model_config_id=value["model_config_id"], timeout_seconds=60,
        )
        return VerifiedInferenceRuntime(
            adapter=adapter,
            model_config_id=value["model_config_id"],
            model_manifest_digest=digest,
        )

    def verified_adapter(self) -> OllamaAdapter:
        return self.verified().adapter
