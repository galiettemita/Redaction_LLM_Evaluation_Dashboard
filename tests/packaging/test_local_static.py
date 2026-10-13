"""Synthetic static hosting: exact assets, confinement and frozen API semantics."""

from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path

import pytest


HTML = b'<!doctype html><html><script type="module" src="/assets/index-test.js"></script></html>'
JS = b'console.log("synthetic");'
CSS = b'body { color: black; }'


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "install"
    dist = root / "web/dist"
    (dist / "assets").mkdir(parents=True)
    assets = {}
    for name, content, mime in [
        ("index.html", HTML, "text/html; charset=utf-8"),
        ("assets/index-test.js", JS, "text/javascript; charset=utf-8"),
        ("assets/index-test.css", CSS, "text/css; charset=utf-8"),
    ]:
        (dist / name).write_bytes(content)
        assets[name] = {"sha256": sha256(content).hexdigest(), "byte_size": len(content), "content_type": mime}
    return root, {"dist_path": "web/dist", "assets": assets}


def call(app, path="/", method="GET", **changes):
    env = {"PATH_INFO": path, "QUERY_STRING": "", "REQUEST_METHOD": method,
           "REMOTE_ADDR": "127.0.0.1", "HTTP_HOST": "127.0.0.1:8765",
           "SERVER_PORT": "8765", "wsgi.url_scheme": "http", "wsgi.input": BytesIO(),
           "CONTENT_LENGTH": "0"}
    env.update(changes)
    response = {}
    def start(status, headers):
        response.update(status=int(status.split()[0]), headers=dict(headers))
    response["body"] = b"".join(app(env, start))
    return response


def composed(bundle):
    from redaction_lab.api.static import create_static_app
    root, config = bundle
    def api(env, start):
        start("418 I'm a Teapot", [("Content-Type", "application/json"), ("Content-Length", "2")])
        return [b"{}"]
    return create_static_app(api, root, config)


@pytest.mark.parametrize("path,body,mime", [
    ("/", HTML, "text/html; charset=utf-8"),
    ("/assets/index-test.js", JS, "text/javascript; charset=utf-8"),
    ("/assets/index-test.css", CSS, "text/css; charset=utf-8"),
])
def test_exact_asset_bytes_mime_length_and_bodyless_head(bundle, path, body, mime):
    app = composed(bundle)
    result = call(app, path)
    assert result["status"] == 200
    assert result["body"] == body
    assert result["headers"]["Content-Type"] == mime
    assert result["headers"]["Content-Length"] == str(len(body))
    head = call(app, path, "HEAD")
    assert head["status"] == 200
    assert head["body"] == b""
    assert head["headers"] == result["headers"]
    assert result["headers"]["X-Content-Type-Options"] == "nosniff"
    assert result["headers"]["X-Frame-Options"] == "DENY"
    assert result["headers"]["Referrer-Policy"] == "no-referrer"
    csp = result["headers"]["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "script-src 'self'" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp


def test_api_subtree_is_delegated_without_response_or_input_changes(bundle):
    app = composed(bundle)
    result = call(app, "/api/v1/health", "POST", QUERY_STRING="opaque", HTTP_HOST="opaque")
    assert result == {"status": 418, "headers": {"Content-Type": "application/json", "Content-Length": "2"}, "body": b"{}"}


@pytest.mark.parametrize("path", ["/index.html", "/assets", "/assets/", "/missing", "/api/v10", "/api",
    "/../index.html", "/assets/../index.html", "/.env", "//", "/assets//index-test.js",
    "/assets/index-test.js/", "/%2e%2e/index.html", "/assets/index-test.js?x", "/assets\\index-test.js"])
def test_only_root_and_exact_produced_assets_have_routes(bundle, path):
    result = call(composed(bundle), path)
    assert result["status"] == 404
    assert HTML not in result["body"]


@pytest.mark.parametrize("changes", [
    {"HTTP_HOST": "localhost:8765"}, {"HTTP_HOST": "127.0.0.1:8766"},
    {"HTTP_ORIGIN": "http://127.0.0.1:8766"}, {"HTTP_ORIGIN": "https://example.com"},
    {"REMOTE_ADDR": "127.0.0.2"}, {"QUERY_STRING": "asset=index.html"},
    {"RAW_URI": "/%61ssets/index-test.js"}, {"RAW_URI": "http://127.0.0.1:8765/"},
    {"HTTP_TRANSFER_ENCODING": "chunked"}, {"CONTENT_LENGTH": "1"},
    {"CONTENT_LENGTH": "0,0"}, {"CONTENT_LENGTH": "-1"},
])
def test_static_requests_reject_host_origin_framing_and_query_confusion(bundle, changes):
    assert call(composed(bundle), **changes)["status"] == 400


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "OPTIONS", "get"])
def test_static_assets_only_allow_get_and_head(bundle, method):
    result = call(composed(bundle), method=method)
    assert result["status"] == 405
    assert result["headers"]["Allow"] == "GET, HEAD"


@pytest.mark.parametrize("mutation", ["missing", "corrupt", "extra", "dotfile", "nested", "symlink-leaf",
    "symlink-dir", "writable", "hardlink", "oversize", "manifest-mime", "manifest-path", "manifest-digest",
    "manifest-length", "manifest-unexpected", "dist-path"])
def test_invalid_tree_or_manifest_fails_closed_without_disclosing_paths(bundle, tmp_path, mutation):
    root, config = bundle
    dist = root / "web/dist"
    js = dist / "assets/index-test.js"
    if mutation == "missing": js.unlink()
    elif mutation == "corrupt": js.write_bytes(b"different")
    elif mutation == "extra": (dist / "secret.txt").write_text("secret")
    elif mutation == "dotfile": (dist / ".secret").write_text("secret")
    elif mutation == "nested": (dist / "extra").mkdir()
    elif mutation == "symlink-leaf":
        js.unlink(); js.symlink_to(tmp_path / "private")
    elif mutation == "symlink-dir":
        (dist / "assets").rename(dist / "old"); (dist / "assets").symlink_to(dist / "old", target_is_directory=True)
    elif mutation == "writable": js.chmod(0o666)
    elif mutation == "hardlink": os.link(js, tmp_path / "alias")
    elif mutation == "oversize": config["assets"]["assets/index-test.js"]["byte_size"] = 4 * 1024 * 1024 + 1
    elif mutation == "manifest-mime": config["assets"]["assets/index-test.js"]["content_type"] = "text/html"
    elif mutation == "manifest-path": config["assets"]["../private"] = config["assets"].pop("assets/index-test.js")
    elif mutation == "manifest-digest": config["assets"]["assets/index-test.js"]["sha256"] = "x" * 64
    elif mutation == "manifest-length": config["assets"]["assets/index-test.js"]["byte_size"] = True
    elif mutation == "manifest-unexpected": config["other"] = True
    elif mutation == "dist-path": config["dist_path"] = str(tmp_path)
    app = composed(bundle)
    result = call(app)
    assert result["status"] == 503
    assert result["body"] == b'{"error":{"code":"FRONTEND_UNAVAILABLE","message":"Verified frontend assets are unavailable"}}'
    assert app.frontend_available is False
    assert str(root).encode() not in result["body"]
    assert call(app, "/api/v1/health")["status"] == 418


def test_symlink_in_install_parent_is_rejected(bundle, tmp_path):
    root, config = bundle
    link = tmp_path / "redirect"
    link.symlink_to(root, target_is_directory=True)
    assert composed((link, config)).frontend_available is False


def test_absent_build_keeps_api_only_diagnostic_and_head_errors_bodyless(bundle):
    root, _ = bundle
    app = composed((root, None))
    assert app.frontend_available is False
    result = call(app, method="HEAD")
    assert result["status"] == 503
    assert result["body"] == b""
    assert int(result["headers"]["Content-Length"]) > 0
    assert call(app, "/api/v1/health")["status"] == 418


def test_verified_immutable_snapshot_never_follows_later_file_redirect(bundle, tmp_path):
    app = composed(bundle)
    root, _ = bundle
    js = root / "web/dist/assets/index-test.js"
    secret = tmp_path / "secret"
    secret.write_bytes(b"not-an-asset")
    js.unlink(); js.symlink_to(secret)
    assert call(app, "/assets/index-test.js")["body"] == JS


@pytest.mark.parametrize("mutation", ["group-writable-install", "group-writable-web", "group-writable-dist", "group-writable-assets", "foreign-owner", "fifo", "real-oversize", "total-oversize", "too-many", "index-only", "asset-map"])
def test_trusted_install_and_bounded_inventory_reject_additional_threats(bundle, monkeypatch, mutation):
    root, config = bundle
    if mutation.startswith("group-writable"):
        selected = {"install": root, "web": root / "web", "dist": root / "web/dist", "assets": root / "web/dist/assets"}
        selected[mutation.rsplit("-", 1)[-1]].chmod(0o775)
    elif mutation == "foreign-owner":
        # Simulate the calling account identity; real no-follow/fstat checks stay real.
        monkeypatch.setattr(os, "geteuid", lambda: 999999)
    elif mutation == "fifo":
        path = root / "web/dist/assets/index-test.js"
        path.unlink(); os.mkfifo(path)
    elif mutation == "real-oversize":
        (root / "web/dist/assets/index-test.js").write_bytes(b"x" * (4 * 1024 * 1024 + 1))
    elif mutation == "total-oversize":
        for entry in config["assets"].values(): entry["byte_size"] = 4 * 1024 * 1024
    elif mutation == "too-many":
        for index in range(33): config["assets"][f"assets/extra-{index}.js"] = config["assets"]["assets/index-test.js"]
    elif mutation == "index-only": config["assets"] = {"index.html": config["assets"]["index.html"]}
    elif mutation == "asset-map": config["assets"]["assets/index-test.js.map"] = config["assets"]["assets/index-test.js"]
    assert composed(bundle).frontend_available is False


def test_empty_path_cannot_alias_root_asset(bundle):
    assert call(composed(bundle), "")["status"] == 404


def test_descriptor_validation_detects_asset_changes_while_reading(bundle, monkeypatch):
    original_read = os.read
    replaced = False
    def changing_read(fd, count):
        nonlocal replaced
        result = original_read(fd, count)
        if result == JS and not replaced:
            replaced = True
            (bundle[0] / "web/dist/assets/index-test.js").write_bytes(JS)
        return result
    monkeypatch.setattr(os, "read", changing_read)
    assert composed(bundle).frontend_available is False
