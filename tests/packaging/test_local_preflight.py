"""Synthetic packaging checks; no runtime, model, installer or private data."""

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

import pytest


ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "packaging" / "local"
HTTP = build_opener(ProxyHandler({}))


@pytest.fixture
def package(tmp_path):
    # Copy the actual package to prove it does not depend on the owner's checkout.
    root = tmp_path / "recipient package"
    root.mkdir()
    for name in ("src", "packaging"):
        shutil.copytree(ROOT / name, root / name)
    return root


def environment(tmp_path, **updates):
    env = os.environ.copy()
    for key in ("REDACTION_LAB_HOST", "REDACTION_LAB_PORT", "PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    env.update(REDACTION_LAB_PYTHON=sys.executable,
               REDACTION_LAB_HOME=str(tmp_path / "local state"))
    env.update(updates)
    return env


def run(root, script, env, *args):
    return subprocess.run(["/bin/sh", str(root / "packaging/local" / script), *args],
                          env=env, cwd="/", capture_output=True, text=True, timeout=15)


def simulated_python(tmp_path, *, system="Darwin", machine="arm64", version="3.12.14", missing=None, wrong=None):
    # Simulate external interpreter/platform/installed metadata, then execute the
    # real shell script's Python payload. All validation and path code stay real.
    wrapper = tmp_path / "test-python"
    wrapper.write_text(
        f"#!{sys.executable}\n"
        "import sys, platform, importlib.metadata\n"
        "sys.dont_write_bytecode = True\n"
        f"platform.system = lambda: {system!r}\n"
        f"platform.machine = lambda: {machine!r}\n"
        f"platform.python_version = lambda: {version!r}\n"
        "original = importlib.metadata.version\n"
        "def version(name):\n"
        f"    if name == {missing!r}: raise importlib.metadata.PackageNotFoundError(name)\n"
        f"    if name == {wrong!r}: return '0.0.0'\n"
        "    return original(name)\n"
        "importlib.metadata.version = version\n"
        "sys.argv = [sys.argv[0], *sys.argv[4:]]\n"
        "exec(compile(sys.stdin.read(), '<packaging-payload>', 'exec'))\n"
    )
    wrapper.chmod(0o700)
    return str(wrapper)


def test_preflight_is_read_only_and_reports_unqualified_runtime(package, tmp_path):
    env = environment(tmp_path, REDACTION_LAB_PYTHON=simulated_python(tmp_path))
    result = run(package, "preflight.sh", env)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["state"] == "DEGRADED"
    assert report["runtime_qualified"] is False
    assert report["host"] == "127.0.0.1"
    assert report["frontend_available"] is False
    assert not Path(env["REDACTION_LAB_HOME"]).exists()


@pytest.mark.parametrize("settings,code", [
    ({"system": "Linux"}, "UNSUPPORTED_PLATFORM"),
    ({"machine": "x86_64"}, "UNSUPPORTED_PLATFORM"),
    ({"version": "3.11.9"}, "PYTHON_PIN_MISMATCH"),
    ({"missing": "pydantic"}, "DEPENDENCY_MISSING"),
    ({"wrong": "pdfplumber"}, "DEPENDENCY_PIN_MISMATCH"),
])
def test_preflight_rejects_incompatible_prerequisites(package, tmp_path, settings, code):
    env = environment(tmp_path, REDACTION_LAB_PYTHON=simulated_python(tmp_path, **settings))
    result = run(package, "preflight.sh", env)
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]["code"] == code
    assert not Path(env["REDACTION_LAB_HOME"]).exists()


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "127.0.0.2", ""])
def test_launcher_check_rejects_every_nonliteral_loopback_host(package, tmp_path, host):
    env = environment(tmp_path, REDACTION_LAB_HOST=host)
    result = run(package, "launch.sh", env, "--check")
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_HOST"
    assert not Path(env["REDACTION_LAB_HOME"]).exists()


@pytest.mark.parametrize("port", ["0", "65536", "-1", "8765;touch nope", "", "1.5"])
def test_preflight_rejects_invalid_port_without_state_changes(package, tmp_path, port):
    result = run(package, "preflight.sh", environment(tmp_path, REDACTION_LAB_PORT=port))
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_PORT"
    assert not (tmp_path / "local state").exists()


def test_preflight_rejects_state_inside_checkout_and_symlinks(package, tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    link = tmp_path / "state-link"
    link.symlink_to(target, target_is_directory=True)
    for location in (package / "private-data", link, Path.home()):
        result = run(package, "preflight.sh", environment(tmp_path, REDACTION_LAB_HOME=str(location)))
        assert result.returncode != 0
        assert json.loads(result.stdout)["error"]["code"] == "UNSAFE_DATA_HOME"


def test_preflight_rejects_changed_runtime_lock_before_launch(package, tmp_path):
    lock = package / "packaging/pdf-worker/runtime.lock"
    content = json.loads(lock.read_text())
    content["runtime_verified"] = True
    lock.write_text(json.dumps(content))
    result = run(package, "launch.sh", environment(tmp_path), "--check")
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]["code"] == "RUNTIME_LOCK_MISMATCH"
    assert not (tmp_path / "local state").exists()


def request(url, *, method="GET", body=None, headers=None):
    try:
        response = HTTP.open(Request(url, method=method, data=body, headers=headers or {}), timeout=2)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.loads(response.read())


def start(root, env):
    process = subprocess.Popen(["/bin/sh", str(root / "packaging/local/launch.sh")],
                               env=env, cwd="/", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    base = f"http://127.0.0.1:{env['REDACTION_LAB_PORT']}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(f"Launcher exited: {process.communicate()}")
        try:
            status, health = request(base + "/api/v1/health")
            assert status == 200
            return process, base, health
        except OSError:
            time.sleep(0.05)
    process.terminate()
    process.communicate(timeout=5)
    pytest.fail("Launcher did not become available")


def test_synthetic_loopback_api_upload_fail_closed_and_restart(package, tmp_path):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = environment(tmp_path, REDACTION_LAB_PORT=str(port))
    process, base, health = start(package, env)
    try:
        assert health == {"api_version": "0.1", "state": "DEGRADED", "runtime_qualified": False, "mode": "local"}
        status, _ = request(base + "/api/v1/health", headers={"Host": "localhost"})
        assert status == 400
        status, _ = request(base + "/api/v1/health", headers={"Origin": "https://example.org"})
        assert status == 400
        body = (b"--synthetic\r\nContent-Disposition: form-data; name=\"project_id\"\r\n\r\nsynthetic-package\r\n"
                b"--synthetic\r\nContent-Disposition: form-data; name=\"redacted_pdf\"; filename=\"synthetic.pdf\"\r\n"
                b"Content-Type: application/pdf\r\n\r\n%PDF-1.4\nsynthetic-package-only\r\n--synthetic--\r\n")
        status, uploaded = request(base + "/api/v1/documents", method="POST", body=body,
                                  headers={"Content-Type": "multipart/form-data; boundary=synthetic"})
        assert status == 201
        job = uploaded["redacted"]["job_id"]
        version = uploaded["redacted"]["version_id"]
        status, result = request(base + f"/api/v1/jobs/{job}/process", method="POST", body=b"")
        assert status == 503
        assert result["error"]["code"] == "RUNTIME_UNVERIFIED"
        assert result["status"] == "ACCEPTED"
        status, result = request(base + f"/api/v1/results/{version}")
        assert status == 200
        assert result["targets"] == []
        assert result["verified_score"] is None
        assert result["truth_status"] == "UNKNOWN"
        assert (Path(env["REDACTION_LAB_HOME"]).stat().st_mode & 0o777) == 0o700
    finally:
        process.terminate()
        _, error_log = process.communicate(timeout=5)
    assert "synthetic-package" not in error_log
    process, base, _ = start(package, env)
    try:
        status, job_state = request(base + f"/api/v1/jobs/{job}")
        assert status == 200
        assert job_state["status"] == "ACCEPTED"
        assert job_state["source_id"] is None
    finally:
        process.terminate()
        process.communicate(timeout=5)


def test_occupied_port_rejects_launch_before_creating_state(package, tmp_path):
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        env = environment(tmp_path, REDACTION_LAB_PORT=str(occupied.getsockname()[1]))
        result = run(package, "launch.sh", env)
    assert result.returncode != 0
    assert "STARTUP_FAILED" in result.stderr
    assert not Path(env["REDACTION_LAB_HOME"]).exists()
