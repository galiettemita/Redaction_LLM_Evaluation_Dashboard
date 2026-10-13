"""Bounded, install-owned static snapshot alongside the unchanged local API.

Only a reviewed manifest can name assets. Filesystem reads happen once through
no-follow directory descriptors; requests never open paths or use a SPA fallback.
"""

from __future__ import annotations

from hashlib import sha256
from http import HTTPStatus
import json
import os
from pathlib import Path
import re
import stat
from types import MappingProxyType
from typing import Callable, Iterable, Mapping


MAX_ASSET_BYTES = 4 * 1024 * 1024
MAX_BUNDLE_BYTES = 8 * 1024 * 1024
MAX_ASSETS = 32
_ASSET_NAME = re.compile(r"assets/[A-Za-z0-9][A-Za-z0-9_-]{0,119}\.(js|css)\Z")
_DIGEST = re.compile(r"[a-f0-9]{64}\Z")
_MIMES = {"html": "text/html; charset=utf-8", "js": "text/javascript; charset=utf-8", "css": "text/css; charset=utf-8"}
_SECURITY_HEADERS = (
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
    ("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"),
)
StartResponse = Callable[[str, list[tuple[str, str]]], object]
WsgiApp = Callable[[Mapping[str, object], StartResponse], Iterable[bytes]]


def _trusted(info: os.stat_result, *, directory: bool) -> None:
    if (not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            or info.st_uid != os.geteuid() or info.st_mode & 0o022
            or (not directory and info.st_nlink != 1)):
        raise ValueError("Untrusted package entry")


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_mode, info.st_uid, info.st_nlink)


def _directory(parent: int, name: str) -> int:
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    try:
        _trusted(os.fstat(fd), directory=True)
        return fd
    except Exception:
        os.close(fd)
        raise


def _install_root(root: Path) -> int:
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Install root must be absolute")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        # Ancestors may be system-owned; none may redirect through a symlink.
        for part in root.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        _trusted(os.fstat(fd), directory=True)
        return fd
    except Exception:
        os.close(fd)
        raise


def _read_regular(parent: int, name: str, limit: int, expected_size: int | None = None) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        before = os.fstat(fd)
        _trusted(before, directory=False)
        if before.st_size <= 0 or before.st_size > limit or (expected_size is not None and before.st_size != expected_size):
            raise ValueError("Invalid asset size")
        chunks = bytearray()
        while len(chunks) <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
        if len(chunks) != before.st_size or _identity(before) != _identity(os.fstat(fd)):
            raise ValueError("Package entry changed during verification")
        return bytes(chunks)
    finally:
        os.close(fd)


def _check_inventory(directory: int, expected: set[str]) -> None:
    observed = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name not in expected or entry.name in observed:
                raise ValueError("Unexpected frontend entry")
            observed.add(entry.name)
    if observed != expected:
        raise ValueError("Missing frontend entry")


def read_local_manifest(root: Path) -> dict[str, object]:
    """Read the bounded install-owned manifest without following redirected files."""
    descriptors = [_install_root(root)]
    try:
        descriptors.append(_directory(descriptors[-1], "packaging"))
        descriptors.append(_directory(descriptors[-1], "local"))
        raw = _read_regular(descriptors[-1], "manifest.json", 64 * 1024)
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicated manifest key")
                result[key] = value
            return result
        manifest = json.loads(raw, object_pairs_hook=unique)
        if not isinstance(manifest, dict):
            raise ValueError("Invalid manifest")
        return manifest
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def _load_assets(root: Path, config: object) -> Mapping[str, tuple[bytes, str]]:
    if not isinstance(config, dict) or set(config) != {"dist_path", "assets"} or config["dist_path"] != "web/dist":
        raise ValueError("Invalid frontend manifest")
    entries = config["assets"]
    if not isinstance(entries, dict) or not 2 <= len(entries) <= MAX_ASSETS or "index.html" not in entries:
        raise ValueError("Invalid frontend inventory")
    total = 0
    for name, entry in entries.items():
        match = _ASSET_NAME.fullmatch(name) if isinstance(name, str) else None
        extension = "html" if name == "index.html" else match.group(1) if match else None
        if (extension is None or not isinstance(entry, dict) or set(entry) != {"sha256", "byte_size", "content_type"}
                or not isinstance(entry["sha256"], str) or _DIGEST.fullmatch(entry["sha256"]) is None
                or type(entry["byte_size"]) is not int or not 0 < entry["byte_size"] <= MAX_ASSET_BYTES
                or entry["content_type"] != _MIMES[extension]):
            raise ValueError("Invalid frontend inventory entry")
        total += entry["byte_size"]
    if total > MAX_BUNDLE_BYTES or not any(name.endswith(".js") for name in entries):
        raise ValueError("Invalid frontend bundle")
    descriptors = [_install_root(root)]
    try:
        descriptors.append(_directory(descriptors[-1], "web"))
        descriptors.append(_directory(descriptors[-1], "dist"))
        dist_fd = descriptors[-1]
        dist_before = os.fstat(dist_fd)
        _check_inventory(dist_fd, {"index.html", "assets"})
        descriptors.append(_directory(dist_fd, "assets"))
        assets_fd = descriptors[-1]
        assets_before = os.fstat(assets_fd)
        expected_names = {name.split("/", 1)[1] for name in entries if name != "index.html"}
        _check_inventory(assets_fd, expected_names)
        loaded = {}
        for name, entry in entries.items():
            parent = dist_fd if name == "index.html" else assets_fd
            body = _read_regular(parent, name.rsplit("/", 1)[-1], MAX_ASSET_BYTES, entry["byte_size"])
            if sha256(body).hexdigest() != entry["sha256"]:
                raise ValueError("Frontend digest mismatch")
            loaded["/" if name == "index.html" else "/" + name] = (body, entry["content_type"])
        if (_identity(dist_before) != _identity(os.fstat(dist_fd))
                or _identity(assets_before) != _identity(os.fstat(assets_fd))):
            raise ValueError("Frontend directory changed during verification")
        return MappingProxyType(loaded)
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


class LocalStatic:
    """Serve a verified immutable asset snapshot; keep API-only diagnostics usable."""

    def __init__(self, api: WsgiApp, root: Path, config: object):
        self.api = api
        try:
            self._assets = _load_assets(root, config)
        except (OSError, ValueError, TypeError, KeyError):
            self._assets = MappingProxyType({})
        self.frontend_available = bool(self._assets)

    @staticmethod
    def _respond(start: StartResponse, method: str, status: int, body: bytes, mime: str, extra=()):
        start(f"{status} {HTTPStatus(status).phrase}", [("Content-Type", mime), ("Content-Length", str(len(body))), *_SECURITY_HEADERS, *extra])
        return (b"" if method == "HEAD" else body,)

    def __call__(self, environment: Mapping[str, object], start_response: StartResponse):
        from redaction_lab.api.http import HttpProblem, validate_local_request

        path = str(environment.get("PATH_INFO", ""))
        if path == "/api/v1" or path.startswith("/api/v1/"):
            return self.api(environment, start_response)
        method = str(environment.get("REQUEST_METHOD", ""))
        status, code, message, extra = 404, "NOT_FOUND", "Resource was not found", ()
        try:
            validate_local_request(environment)
            expected_host = "127.0.0.1:" + str(environment.get("SERVER_PORT", ""))
            if environment.get("HTTP_HOST") != expected_host:
                raise HttpProblem(400, "INVALID_REQUEST", "Host must match the local listening port")
            raw = str(environment.get("RAW_URI", path))
            if (environment.get("QUERY_STRING") or raw != path or environment.get("HTTP_TRANSFER_ENCODING") is not None
                    or str(environment.get("CONTENT_LENGTH", "")) not in {"", "0"}):
                raise HttpProblem(400, "INVALID_REQUEST", "Static request framing is invalid")
            if method not in {"GET", "HEAD"}:
                status, code, message, extra = 405, "METHOD_NOT_ALLOWED", "Static assets require GET or HEAD", (("Allow", "GET, HEAD"),)
            elif path == "/" or _ASSET_NAME.fullmatch(path[1:]) is not None:
                if not self.frontend_available:
                    status, code, message = 503, "FRONTEND_UNAVAILABLE", "Verified frontend assets are unavailable"
                elif path in self._assets:
                    body, mime = self._assets[path]
                    return self._respond(start_response, method, 200, body, mime)
        except HttpProblem as problem:
            status, code, message = problem.status, problem.code, problem.message
        body = json.dumps({"error": {"code": code, "message": message}}, separators=(",", ":")).encode("utf-8")
        return self._respond(start_response, method, status, body, "application/json; charset=utf-8", extra)


def create_static_app(api: WsgiApp, root: Path, frontend: object) -> LocalStatic:
    return LocalStatic(api, root, frontend)
