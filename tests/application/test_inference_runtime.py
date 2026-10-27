from __future__ import annotations

import asyncio
from io import BytesIO
from hashlib import sha256
import json
from pathlib import Path

import pytest

from redaction_lab.application.inference_runtime import (
    InferenceRuntime,
    InferenceRuntimeUnavailable,
    _RuntimeBoundAdapter,
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
    model_store = tmp_path / "models"
    model_store.mkdir()
    model_store.chmod(0o700)
    model_file = model_store / "sha256-model-blob"
    model_file.write_bytes(b"synthetic model bytes")
    model_file.chmod(0o600)
    value = {
        "schema": 1,
        "runtime_verified": True,
        "endpoint": "http://127.0.0.1:11434",
        "ollama_executable": str(executable),
        "ollama_executable_sha256": "sha256:" + sha256(executable.read_bytes()).hexdigest(),
        "model_store": str(model_store),
        "model_files": {
            model_file.name: "sha256:" + sha256(model_file.read_bytes()).hexdigest()
        },
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
        InferenceRuntime().verified()


def test_runtime_verifies_exact_executable_version_and_full_model_digest(
    tmp_path, monkeypatch
) -> None:
    path, value = _lock(tmp_path)
    monkeypatch.setattr(InferenceRuntime, "LOCK_PATH", path)
    observed = {}

    class Process:
        def __init__(self):
            self.closed = False

        def poll(self):
            return 0 if self.closed else None

        def terminate(self):
            self.closed = True

        def wait(self, timeout):
            return 0

    process = Process()

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
    monkeypatch.setattr(InferenceRuntime, "_start_owned_runtime", lambda self, executable, model_store: process)

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
    verified.close()
    assert process.closed is True


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
        InferenceRuntime().verified()


def test_runtime_bound_adapter_checks_identity_before_and_after_generation() -> None:
    calls = []

    class Delegate:
        model_id = "model-test"
        model_config_id = "config-test"

        def request_hash(self, manifest):
            return "a" * 64

        async def predict(self, manifest):
            return "synthetic-response"

    def changed_after_generation():
        calls.append("check")
        if len(calls) == 2:
            raise InferenceRuntimeUnavailable("model digest changed")

    adapter = _RuntimeBoundAdapter(Delegate(), changed_after_generation)
    with pytest.raises(InferenceRuntimeUnavailable, match="digest changed"):
        asyncio.run(adapter.predict(object()))
    assert calls == ["check", "check"]


def test_owned_runtime_refuses_preexisting_loopback_listener(tmp_path, monkeypatch) -> None:
    executable = tmp_path / "ollama"
    executable.write_text("synthetic")
    model_store = tmp_path / "models"
    model_store.mkdir()

    class Connection:
        def close(self):
            pass

    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.socket.create_connection",
        lambda *args, **kwargs: Connection(),
    )
    with pytest.raises(InferenceRuntimeUnavailable, match="unowned"):
        InferenceRuntime._start_owned_runtime(executable, model_store)


def test_owned_runtime_launches_only_pinned_binary_and_confined_model_store(
    tmp_path, monkeypatch
) -> None:
    executable = tmp_path / "ollama"
    executable.write_text("synthetic")
    model_store = tmp_path / "models"
    model_store.mkdir()
    observed = {}
    process = object()

    def refused(*args, **kwargs):
        raise ConnectionRefusedError

    def popen(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return process

    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.socket.create_connection", refused
    )
    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.subprocess.Popen", popen
    )

    assert InferenceRuntime._start_owned_runtime(executable, model_store) is process
    assert observed["command"] == [str(executable), "serve"]
    assert observed["kwargs"]["env"] == {
        "PATH": "/usr/bin:/bin",
        "OLLAMA_HOST": "127.0.0.1:11434",
        "OLLAMA_MODELS": str(model_store),
    }
    assert observed["kwargs"]["close_fds"] is True


def test_model_file_inventory_detects_blob_substitution(tmp_path) -> None:
    _, value = _lock(tmp_path)
    model_store = Path(value["model_store"])
    InferenceRuntime._assert_model_files(model_store, value)
    next(model_store.iterdir()).write_bytes(b"substituted")
    with pytest.raises(InferenceRuntimeUnavailable, match="digest mismatch"):
        InferenceRuntime._assert_model_files(model_store, value)
