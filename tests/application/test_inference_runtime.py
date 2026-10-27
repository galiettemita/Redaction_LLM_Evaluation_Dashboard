from __future__ import annotations

from io import BytesIO
from hashlib import sha256
import json

import pytest

from redaction_lab.application.inference_runtime import (
    InferenceRuntime,
    InferenceRuntimeUnavailable,
)


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _lock(tmp_path, **overrides):
    executable = tmp_path / "ollama"
    executable.write_text("synthetic executable placeholder")
    executable.chmod(0o700)
    value = {
        "schema": 1,
        "runtime_verified": True,
        "endpoint": "http://127.0.0.1:11434",
        "ollama_executable": str(executable),
        "ollama_executable_sha256": "sha256:" + sha256(executable.read_bytes()).hexdigest(),
        "ollama_version": "0.12.9",
        "model_id": "qwen2.5:1.5b-instruct-q4_K_M",
        "provider_model_id": "qwen2.5:1.5b-instruct-q4_K_M",
        "model_config_id": "ollama-0.12.9-qwen-test",
        "model_manifest_digest": "sha256:" + "a" * 64,
    }
    value.update(overrides)
    path = tmp_path / "runtime.lock"
    path.write_text(json.dumps(value))
    return path, value


def test_shipped_runtime_lock_fails_closed_without_starting_a_process() -> None:
    with pytest.raises(InferenceRuntimeUnavailable, match="unverified"):
        InferenceRuntime().verified_adapter()


def test_runtime_verifies_exact_executable_version_and_full_model_digest(
    tmp_path, monkeypatch
) -> None:
    path, value = _lock(tmp_path)
    monkeypatch.setattr(InferenceRuntime, "LOCK_PATH", path)
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return type("Result", (), {"returncode": 0, "stdout": "ollama version 0.12.9\n", "stderr": ""})()

    class Opener:
        def open(self, request, timeout):
            observed.setdefault("urls", []).append(request.full_url)
            payload = (
                {"version": value["ollama_version"]}
                if request.full_url.endswith("/api/version")
                else {"models": [{"name": value["provider_model_id"], "digest": value["model_manifest_digest"]}]}
            )
            return Response(json.dumps(payload).encode())

    monkeypatch.setattr("redaction_lab.application.inference_runtime.subprocess.run", fake_run)
    monkeypatch.setattr("redaction_lab.application.inference_runtime.build_opener", lambda *handlers: Opener())

    verified = InferenceRuntime().verified()
    adapter = verified.adapter

    assert adapter.model_id == value["model_id"]
    assert verified.model_manifest_digest == value["model_manifest_digest"]
    assert verified.model_config_id == value["model_config_id"]
    assert observed["command"] == [value["ollama_executable"], "--version"]
    assert observed["kwargs"]["env"] == {"PATH": "/usr/bin:/bin"}
    assert observed["urls"] == [
        "http://127.0.0.1:11434/api/version",
        "http://127.0.0.1:11434/api/tags",
    ]


@pytest.mark.parametrize(
    "override",
    [
        {"endpoint": "http://localhost:11434"},
        {"model_manifest_digest": "sha256:" + "a" * 12},
        {"model_id": "substituted-model"},
        {"ollama_executable_sha256": "sha256:" + "b" * 64},
    ],
)
def test_runtime_rejects_endpoint_digest_or_model_substitution_before_dispatch(
    tmp_path, monkeypatch, override
) -> None:
    path, _ = _lock(tmp_path, **override)
    monkeypatch.setattr(InferenceRuntime, "LOCK_PATH", path)
    with pytest.raises(InferenceRuntimeUnavailable):
        InferenceRuntime().verified_adapter()
