"""Synthetic packaging checks; no runtime, model, installer or private data."""

import json
from hashlib import sha256
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
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
GENUINE_ASSETS = {
    "/": ("web/dist/index.html", "1a638c34649d4fc727a446b7f06f0103562af019bfc58b8d554514cbc8d09367"),
    "/assets/index-Dr7D93Wo.css": ("web/dist/assets/index-Dr7D93Wo.css", "5e85c428f8aea611a729cccad5194870a956bb5b794f7d1f8ba6895ae7a867bd"),
    "/assets/index-D4KVD8ty.js": ("web/dist/assets/index-D4KVD8ty.js", "a088437a22f246a85be596cc2d34eddd5c6e4993e83085b2ad2975744aa8d4dc"),
}


def install_synthetic_bundle(root):
    dist = root / "web/dist"
    if dist.exists():
        shutil.rmtree(dist)
    (dist / "assets").mkdir(parents=True)
    files = [("index.html", b'<!doctype html><script type="module" src="/assets/index-smoke.js"></script>', "text/html; charset=utf-8"),
             ("assets/index-smoke.js", b'console.log("synthetic-only")', "text/javascript; charset=utf-8")]
    entries = {}
    for name, body, mime in files:
        (dist / name).write_bytes(body)
        entries[name] = {"byte_size": len(body), "sha256": sha256(body).hexdigest(), "content_type": mime}
    manifest_path = root / "packaging/local/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["frontend"] = {"dist_path": "web/dist", "assets": entries}
    manifest_path.write_text(json.dumps(manifest))
    return dict(("/" if name == "index.html" else "/" + name, body) for name, body, _ in files)


@pytest.fixture
def package(tmp_path):
    # Copy the actual package to prove it does not depend on the owner's checkout.
    root = tmp_path / "recipient package"
    root.mkdir()
    for name in ("src", "packaging"):
        shutil.copytree(ROOT / name, root / name)
    shutil.copytree(ROOT / "web/dist", root / "web/dist")
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


def simulated_python(tmp_path, *, system="Darwin", machine="arm64", version="3.12.14", missing=None, wrong=None, blocked_import=None):
    # Simulate external interpreter/platform/installed metadata, then execute the
    # real shell script's Python payload. All validation and path code stay real.
    wrapper = tmp_path / "test-python"
    wrapper.write_text(
        f"#!{sys.executable}\n"
        "import sys, platform, importlib.metadata, builtins\n"
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
        "original_import = builtins.__import__\n"
        "def guarded_import(name, *args, **kwargs):\n"
        f"    if name == {blocked_import!r}: raise ImportError('missing prerequisite')\n"
        "    return original_import(name, *args, **kwargs)\n"
        "builtins.__import__ = guarded_import\n"
        "sys.argv = [sys.argv[0], *sys.argv[4:]]\n"
        "exec(compile(sys.stdin.read(), '<packaging-payload>', 'exec'))\n"
    )
    wrapper.chmod(0o700)
    return str(wrapper)


def test_preflight_is_read_only_and_reports_verified_frontend_with_unqualified_runtime(package, tmp_path):
    env = environment(tmp_path, REDACTION_LAB_PYTHON=simulated_python(tmp_path))
    result = run(package, "preflight.sh", env)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["state"] == "DEGRADED"
    assert report["runtime_qualified"] is False
    assert report["host"] == "127.0.0.1"
    assert report["frontend_available"] is True
    assert not Path(env["REDACTION_LAB_HOME"]).exists()


def test_preflight_only_reports_frontend_after_exact_bundle_verification(package, tmp_path):
    install_synthetic_bundle(package)
    env = environment(tmp_path, REDACTION_LAB_PYTHON=simulated_python(tmp_path))
    result = run(package, "preflight.sh", env)
    assert result.returncode == 0
    assert json.loads(result.stdout)["frontend_available"] is True
    (package / "web/dist/assets/index-smoke.js").write_bytes(b"tampered")
    result = run(package, "preflight.sh", env)
    assert result.returncode == 0
    assert json.loads(result.stdout)["frontend_available"] is False
    assert not Path(env["REDACTION_LAB_HOME"]).exists()


def test_preflight_verifies_the_genuine_reviewed_frontend_inventory(package, tmp_path):
    env = environment(tmp_path, REDACTION_LAB_PYTHON=simulated_python(tmp_path))
    result = run(package, "preflight.sh", env)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["frontend_available"] is True
    for relative, expected_digest in GENUINE_ASSETS.values():
        body = (package / relative).read_bytes()
        assert sha256(body).hexdigest() == expected_digest
    assert not Path(env["REDACTION_LAB_HOME"]).exists()


@pytest.mark.parametrize("mutation", ["symlink", "duplicate-key", "oversize"])
def test_preflight_rejects_untrusted_package_manifest(package, tmp_path, mutation):
    manifest = package / "packaging/local/manifest.json"
    if mutation == "symlink":
        target = tmp_path / "redirected-manifest"
        manifest.rename(target)
        manifest.symlink_to(target)
    elif mutation == "duplicate-key":
        text = manifest.read_text()
        manifest.write_text(text.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'))
    else:
        manifest.write_bytes(b" " * (64 * 1024 + 1))
    result = run(package, "preflight.sh", environment(tmp_path))
    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]["code"] == "PACKAGE_INVALID"
    assert not (tmp_path / "local state").exists()


@pytest.mark.parametrize("settings,code", [
    ({"system": "Linux", "blocked_import": "pypdf"}, "UNSUPPORTED_PLATFORM"),
    ({"missing": "pypdf", "blocked_import": "pypdf"}, "DEPENDENCY_MISSING"),
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
    assets = {route: (package / relative).read_bytes()
              for route, (relative, _) in GENUINE_ASSETS.items()}
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = environment(tmp_path, REDACTION_LAB_PORT=str(port))
    process, base, health = start(package, env)
    try:
        for path, body in assets.items():
            with HTTP.open(base + path, timeout=2) as response:
                assert response.status == 200
                assert response.read() == body
                assert response.headers["Content-Length"] == str(len(body))
                assert "script-src 'self'" in response.headers["Content-Security-Policy"]
            with HTTP.open(Request(base + path, method="HEAD"), timeout=2) as response:
                assert response.read() == b""
                assert response.headers["Content-Length"] == str(len(body))
        for target in ("/assets/", "/index.html", "/missing", "/.env"):
            status, _ = request(base + target)
            assert status == 404
        status, _ = request(base + "/?asset=secret")
        assert status == 400
        for headers in ({"Host": "localhost"}, {"Origin": "https://example.org"}):
            status, _ = request(base + "/", headers=headers)
            assert status == 400
        for target, headers in [("/%61ssets/index-D4KVD8ty.js", []), ("/", ["Host: 127.0.0.1"]),
                                ("/", ["Content-Length: 0", "Content-Length: 0"]),
                                ("/", ["Transfer-Encoding: chunked"])]:
            raw = ("GET " + target + " HTTP/1.1\r\nHost: 127.0.0.1:" + str(port) + "\r\n" +
                   "\r\n".join(headers) + "\r\n\r\n").encode("ascii")
            with socket.create_connection(("127.0.0.1", port), timeout=2) as connection:
                connection.sendall(raw)
                reply = connection.recv(4096)
                assert reply.split(b"\r\n")[0].split()[1] == b"400"
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
        assert result["experimental_score"] is None
        assert result["truth_status"] == "UNKNOWN"
        assert result["score_status"] == "NONE"
        assert (Path(env["REDACTION_LAB_HOME"]).stat().st_mode & 0o777) == 0o700
    finally:
        process.terminate()
        _, error_log = process.communicate(timeout=5)
    assert "synthetic-package" not in error_log
    process, base, _ = start(package, env)
    try:
        with HTTP.open(base + "/", timeout=2) as response:
            assert response.read() == assets["/"]
        status, job_state = request(base + f"/api/v1/jobs/{job}")
        assert status == 200
        assert job_state["status"] == "ACCEPTED"
        assert job_state["source_id"] is None
    finally:
        process.terminate()
        process.communicate(timeout=5)


def test_existing_chrome_cli_renders_the_genuine_same_origin_application(package, tmp_path):
    if not CHROME.is_file():
        pytest.skip("Existing Google Chrome CLI is unavailable")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = environment(tmp_path, REDACTION_LAB_PORT=str(port))
    process, base, _ = start(package, env)
    try:
        browser = subprocess.run([
            str(CHROME), "--headless=new", "--disable-gpu", "--no-first-run",
            "--disable-background-networking", "--disable-component-update",
            "--user-data-dir=" + str(tmp_path / "chrome-profile"),
            "--virtual-time-budget=3000", "--dump-dom", base + "/",
        ], capture_output=True, text=True, timeout=20)
        assert browser.returncode == 0, browser.stderr
        assert "<title>Redaction Lab — local document workspace</title>" in browser.stdout
        assert "Every passage. Clear uncertainty." in browser.stdout
        assert "Document processing unavailable" in browser.stdout
        assert "No verified or experimental score is available." in browser.stdout
        assert 'id="demo-title">Experimental text-only demo</h2>' in browser.stdout
        assert "Plausible guesses are not proven correct." in browser.stdout
        assert 'id="demo-text"' in browser.stdout
        assert "Manually entered demo text" in browser.stdout
        assert "Generate demo candidates" in browser.stdout
        assert "Clear text and remove results" in browser.stdout
        assert "Uploaded PDFs and references never fill this field." in browser.stdout
        # Initial rendering must not invent candidates before manual submission.
        assert "Unvalidated candidate phrases" not in browser.stdout
        assert 'class="demo-marker"' not in browser.stdout
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
