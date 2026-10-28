from __future__ import annotations

import asyncio
from io import BytesIO
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

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
    def fake_start(self, executable_fd, executable, model_store):
        observed["serve_fd"] = executable_fd
        observed["serve_path"] = executable
        return process

    monkeypatch.setattr(InferenceRuntime, "_start_owned_runtime", fake_start)

    verified = InferenceRuntime().verified()
    adapter = verified.adapter

    assert adapter.model_id == value["model_id"]
    assert verified.model_manifest_digest == value["model_manifest_digest"]
    assert verified.model_config_id == value["model_config_id"]
    assert observed["command"][0].startswith("/dev/fd/")
    assert observed["command"][1] == "--version"
    assert observed["command"][0] == f"/dev/fd/{observed['serve_fd']}"
    assert observed["serve_path"] == Path(value["ollama_executable"])
    assert observed["kwargs"]["env"] == {"PATH": "/usr/bin:/bin"}
    assert observed["kwargs"]["pass_fds"]
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
        InferenceRuntime._start_owned_runtime(123, executable, model_store)


def test_owned_runtime_launches_only_pinned_binary_and_confined_model_store(
    tmp_path, monkeypatch
) -> None:
    executable = tmp_path / "ollama"
    executable.write_text("synthetic")
    model_store = tmp_path / "models"
    model_store.mkdir()
    observed = {}
    lifetime_read, lifetime_write = os.pipe()
    status_read, status_write = os.pipe()

    class Process:
        pid = 123
        returncode = 0

        def poll(self):
            return 0

        def wait(self, timeout):
            return 0

    process = Process()

    def refused(*args, **kwargs):
        raise ConnectionRefusedError

    def popen(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return process

    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.socket.create_connection", refused
    )
    descriptor = os.open(executable, os.O_RDONLY)
    try:
        monkeypatch.setattr(
            "redaction_lab.application.inference_runtime.subprocess.Popen", popen
        )
        InferenceRuntime._supervisor_main(
            lifetime_read, status_write, descriptor, executable, model_store
        )
    finally:
        os.close(lifetime_write)
        os.close(status_read)
        os.close(descriptor)
    assert observed["command"] == [str(executable), "serve"]
    assert observed["kwargs"]["env"] == {
        "PATH": "/usr/bin:/bin",
        "OLLAMA_HOST": "127.0.0.1:11434",
        "OLLAMA_MODELS": str(model_store),
    }
    assert observed["kwargs"]["close_fds"] is True
    assert observed["kwargs"]["pass_fds"] == (descriptor,)


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_for(predicate, timeout: float = 5) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    assert predicate()


def _harmless_runtime(tmp_path: Path) -> tuple[Path, Path, Path]:
    owned_pids = tmp_path / "owned.pids"
    executable = tmp_path / "harmless-runtime"
    shutil.copyfile("/usr/bin/yes", executable)
    executable.chmod(0o700)
    model_store = tmp_path / "models"
    model_store.mkdir()
    return executable, owned_pids, model_store


def test_supervisor_reaps_owned_child_after_abrupt_application_exit(tmp_path) -> None:
    executable, owned_pids_path, model_store = _harmless_runtime(tmp_path)
    parent = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import os,sys; from pathlib import Path; "
                "from redaction_lab.application.inference_runtime import InferenceRuntime; "
                "fd=os.open(sys.argv[1],os.O_RDONLY); "
                "owned=InferenceRuntime._launch_supervisor(fd,Path(sys.argv[1]),Path(sys.argv[2])); "
                "Path(sys.argv[3]).write_text(f'{owned.pid},{owned.child_pid}'); "
                "os._exit(0)"
            ),
            str(executable),
            str(model_store),
            str(owned_pids_path),
        ],
        env={"PATH": os.environ["PATH"], "PYTHONPATH": str(Path.cwd() / "src")},
    )
    assert parent.wait(timeout=5) == 0
    _wait_for(owned_pids_path.exists)
    supervisor_pid, child_pid = map(int, owned_pids_path.read_text().split(","))

    _wait_for(lambda: not _process_exists(child_pid))
    _wait_for(lambda: not _process_exists(supervisor_pid))


def test_supervisor_start_failure_is_reaped_and_reported(tmp_path) -> None:
    executable = tmp_path / "invalid-runtime"
    executable.write_text("not an executable format")
    executable.chmod(0o700)
    model_store = tmp_path / "models"
    model_store.mkdir()
    descriptor = os.open(executable, os.O_RDONLY)
    try:
        with pytest.raises(InferenceRuntimeUnavailable, match="could not start"):
            InferenceRuntime._launch_supervisor(descriptor, executable, model_store)
    finally:
        os.close(descriptor)


def test_supervisor_popen_failure_closes_every_pipe_descriptor(
    tmp_path, monkeypatch
) -> None:
    executable = tmp_path / "runtime"
    executable.write_bytes(b"synthetic")
    executable.chmod(0o700)
    model_store = tmp_path / "models"
    model_store.mkdir()
    descriptor = os.open(executable, os.O_RDONLY)
    created_pipes: list[int] = []
    real_pipe = os.pipe

    def tracked_pipe():
        pair = real_pipe()
        created_pipes.extend(pair)
        return pair

    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.os.pipe", tracked_pipe
    )
    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.subprocess.Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("synthetic failure")),
    )
    try:
        with pytest.raises(InferenceRuntimeUnavailable, match="supervisor"):
            InferenceRuntime._launch_supervisor(
                descriptor, executable, model_store
            )
    finally:
        os.close(descriptor)

    for pipe_descriptor in created_pipes:
        with pytest.raises(OSError):
            os.fstat(pipe_descriptor)


def test_supervisor_handshake_exception_closes_pipe_and_reaps_process(
    tmp_path, monkeypatch
) -> None:
    executable = tmp_path / "runtime"
    executable.write_bytes(b"synthetic")
    executable.chmod(0o700)
    model_store = tmp_path / "models"
    model_store.mkdir()
    descriptor = os.open(executable, os.O_RDONLY)

    class Supervisor:
        pid = 321
        terminated = False

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout):
            self.terminated = True
            return 0

        def kill(self):
            self.terminated = True

    supervisor = Supervisor()
    created_pipes: list[int] = []
    real_pipe = os.pipe

    def tracked_pipe():
        pair = real_pipe()
        created_pipes.extend(pair)
        return pair

    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.os.pipe", tracked_pipe
    )
    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.subprocess.Popen",
        lambda *args, **kwargs: supervisor,
    )
    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.select.select",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("handshake failed")),
    )
    try:
        with pytest.raises(InferenceRuntimeUnavailable, match="handshake"):
            InferenceRuntime._launch_supervisor(
                descriptor, executable, model_store
            )
    finally:
        os.close(descriptor)

    assert supervisor.terminated is True
    for pipe_descriptor in created_pipes:
        with pytest.raises(OSError):
            os.fstat(pipe_descriptor)


def test_post_launch_identity_failure_kills_sigterm_resistant_child(
    tmp_path, monkeypatch
) -> None:
    executable = tmp_path / "runtime"
    executable.write_bytes(b"synthetic")
    executable.chmod(0o700)
    model_store = tmp_path / "models"
    model_store.mkdir()
    descriptor = os.open(executable, os.O_RDONLY)
    lifetime_read, lifetime_write = os.pipe()
    status_read, status_write = os.pipe()

    class Child:
        pid = 456
        returncode = None
        killed = False

        def poll(self):
            return -9 if self.killed else None

        def terminate(self):
            pass

        def wait(self, timeout):
            if not self.killed:
                raise subprocess.TimeoutExpired("synthetic", timeout)
            self.returncode = -9
            return self.returncode

        def kill(self):
            self.killed = True

    child = Child()
    identities = iter(((1,), (1,), (2,)))
    monkeypatch.setattr(
        InferenceRuntime, "_file_identity", lambda info: next(identities)
    )
    monkeypatch.setattr(
        "redaction_lab.application.inference_runtime.subprocess.Popen",
        lambda *args, **kwargs: child,
    )
    try:
        assert (
            InferenceRuntime._supervisor_main(
                lifetime_read,
                status_write,
                descriptor,
                executable,
                model_store,
            )
            == 1
        )
        assert child.killed is True
        assert os.read(status_read, 16) == b"ERROR\n"
    finally:
        os.close(lifetime_write)
        os.close(status_read)
        os.close(descriptor)


def test_model_file_inventory_detects_blob_substitution(tmp_path) -> None:
    _, value = _lock(tmp_path)
    model_store = Path(value["model_store"])
    InferenceRuntime._assert_model_files(model_store, value)
    next(model_store.iterdir()).write_bytes(b"substituted")
    with pytest.raises(InferenceRuntimeUnavailable, match="digest mismatch"):
        InferenceRuntime._assert_model_files(model_store, value)


def test_model_file_inventory_rejects_unlisted_payload(tmp_path) -> None:
    _, value = _lock(tmp_path)
    model_store = Path(value["model_store"])
    (model_store / "unlisted-actual-model-blob").write_bytes(b"unlisted")
    with pytest.raises(InferenceRuntimeUnavailable, match="inventory is incomplete"):
        InferenceRuntime._assert_model_files(model_store, value)


@pytest.mark.parametrize("mutation", ["writable", "hardlink"])
def test_executable_descriptor_rejects_mutable_or_aliased_binary(tmp_path, mutation) -> None:
    executable = tmp_path / "ollama"
    executable.write_bytes(b"synthetic")
    executable.chmod(0o700)
    digest = "sha256:" + sha256(executable.read_bytes()).hexdigest()
    if mutation == "writable":
        executable.chmod(0o720)
    else:
        os.link(executable, tmp_path / "ollama-alias")
    with pytest.raises(InferenceRuntimeUnavailable, match="untrusted"):
        InferenceRuntime._open_verified_executable(executable, digest)


@pytest.mark.parametrize("mutation", ["writable", "symlink"])
def test_runtime_lock_rejects_mutable_or_redirected_file(tmp_path, mutation) -> None:
    path, _ = _lock(tmp_path)
    if mutation == "writable":
        path.chmod(0o666)
        target = path
    else:
        target = tmp_path / "redirected.lock"
        path.rename(target)
        path.symlink_to(target)
        target = path
    with pytest.raises(InferenceRuntimeUnavailable):
        InferenceRuntime._read_lock(target)
