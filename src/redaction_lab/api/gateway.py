"""Owner-only HTTP boundary for an HTTPS tunnel to the fixed local application.

TLS terminates at the configured tunnel. This server listens only on loopback;
its only destination is the literal application socket, never a supplied URL.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from email.errors import MultipartInvariantViolationDefect, StartBoundaryNotFoundDefect
from hashlib import sha256
import hmac
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import signal
import socket
from tempfile import SpooledTemporaryFile
from threading import BoundedSemaphore
from typing import Mapping

from redaction_lab.api.http import API_VERSION, MAX_UPLOAD_BODY_BYTES


_HOST = re.compile(r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\Z")
_TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_READ_ROUTE = re.compile(r"/(?:api/v1/(?:health|(?:documents|jobs|results)/[A-Za-z0-9_-]{1,256})|assets/[A-Za-z0-9_-]+\.(?:js|css))\Z")
_PROCESS_ROUTE = re.compile(r"/api/v1/jobs/[A-Za-z0-9_-]{1,256}/process\Z")
_SINGLETONS = (
    "Host", "Origin", "Authorization", "Content-Length", "Content-Type",
    "Transfer-Encoding", "Expect",
)
_RESPONSE_HEADERS = frozenset({
    "content-type", "content-length", "cache-control", "content-security-policy",
    "x-content-type-options", "x-frame-options", "referrer-policy", "x-redaction-lab-api",
})
_CHUNK = 64 * 1024
_MAX_RESPONSE = 16 * 1024 * 1024
_MAX_CHUNK_SIZE_DIGITS = 16


class _RequestBodyError(ValueError):
    def __init__(self, status: int) -> None:
        self.status = status


def _gateway_error_body(code: str) -> bytes:
    return json.dumps(
        {"error": {"code": code, "message": "Request could not be completed"}},
        separators=(",", ":"),
    ).encode()


def _gateway_error_response(status: int, code: str) -> bytes:
    body = _gateway_error_body(code)
    reason = "Service Unavailable" if status == 503 else "Bad Request"
    return (
        f"HTTP/1.1 {status} {reason}\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n"
        f"X-Redaction-Lab-API: {API_VERSION}\r\n"
        "X-Content-Type-Options: nosniff\r\n"
        "Referrer-Policy: no-referrer\r\n"
        "Strict-Transport-Security: max-age=31536000\r\n\r\n"
    ).encode() + body


@dataclass(frozen=True)
class GatewayConfig:
    public_host: str
    authorization_digest: bytes = field(repr=False)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "GatewayConfig":
        env = os.environ if environment is None else environment
        host = env.get("REDACTION_LAB_PUBLIC_HOST", "")
        username = env.get("REDACTION_LAB_GATEWAY_USERNAME", "")
        password = env.get("REDACTION_LAB_GATEWAY_PASSWORD", "")
        if (_HOST.fullmatch(host) is None
                or re.fullmatch(r"[A-Za-z0-9._-]{1,64}", username) is None
                or not 24 <= len(password) <= 256
                or any(not 33 <= ord(character) <= 126 for character in password)):
            raise ValueError("gateway requires an exact public DNS host and private credentials")
        token = b"Basic " + base64.b64encode((username + ":" + password).encode("ascii"))
        return cls(host, sha256(token).digest())


class GatewayServer(ThreadingHTTPServer):
    """At most eight active connections; fixed binding and destination."""

    daemon_threads = True
    block_on_close = False

    def __init__(self, config: GatewayConfig):
        self.config = config
        self._slots = BoundedSemaphore(8)
        super().__init__(("127.0.0.1", 8766), GatewayHandler)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            try:
                request.sendall(_gateway_error_response(503, "GATEWAY_BUSY"))
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()

    def handle_error(self, request, client_address):
        # No request URLs, document IDs, credentials or response payload logs.
        pass


class GatewayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def send_error(self, code, message=None, explain=None):
        self._reject(code)

    def _reject(self, code):
        body = _gateway_error_body("GATEWAY_REJECTED")
        self.close_connection = True
        self.send_response_only(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Redaction-Lab-API", API_VERSION)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        if code == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="Redaction Lab", charset="UTF-8"')
        self.end_headers()
        if getattr(self, "command", None) != "HEAD":
            self.wfile.write(body)
        return False

    def handle_expect_100(self):
        return self._reject(400)

    def parse_request(self):
        if not super().parse_request():
            return False
        self.close_connection = True
        # The base parser normalizes leading //; inspect the original target too.
        target = self.raw_requestline.split()[1]
        # HTTPMessage is parsed with email's MIME parser, without the HTTP body.
        # Multipart body warnings therefore occur on every valid browser upload.
        # Only these two body-only defects are irrelevant at the header boundary;
        # malformed header defects, framing and the API's multipart parser remain.
        body_defects = (MultipartInvariantViolationDefect, StartBoundaryNotFoundDefect)
        malformed_headers = any(
            not (self.headers.get_content_type() == "multipart/form-data" and type(defect) in body_defects)
            for defect in self.headers.defects
        )
        if (self.request_version != "HTTP/1.1" or target != self.path.encode("iso-8859-1")
                or malformed_headers or len(self.headers) > 40
                or sum(len(key) + len(value) for key, value in self.headers.raw_items()) > 16384
                or any(_TOKEN.fullmatch(key) is None or any(ord(c) < 32 or ord(c) > 126 for c in value)
                       for key, value in self.headers.raw_items())
                or any(len(self.headers.get_all(name, [])) > 1 for name in _SINGLETONS)
                or any(self.headers.get(name) is not None for name in ("Expect", "Upgrade"))):
            return self._reject(400)
        if self.headers.get("Host") != self.server.config.public_host:
            return self._reject(400)
        authorization = self.headers.get("Authorization", "").encode("ascii")
        if not hmac.compare_digest(sha256(authorization).digest(), self.server.config.authorization_digest):
            return self._reject(401)
        if self.command not in {"GET", "HEAD", "POST"}:
            return self._reject(405)
        if self.command == "POST":
            route_ok = self.path == "/api/v1/documents" or _PROCESS_ROUTE.fullmatch(self.path)
        else:
            route_ok = self.path == "/" or _READ_ROUTE.fullmatch(self.path)
        if not route_ok:
            return self._reject(404)
        origin = self.headers.get("Origin")
        if (origin is not None or self.command == "POST") and origin != "https://" + self.server.config.public_host:
            return self._reject(403)
        limit = MAX_UPLOAD_BODY_BYTES if self.path == "/api/v1/documents" and self.command == "POST" else 0
        transfer_encoding = self.headers.get("Transfer-Encoding")
        raw_length = self.headers.get("Content-Length")
        if transfer_encoding is not None:
            if (
                raw_length is not None
                or transfer_encoding != transfer_encoding.strip()
                or transfer_encoding.casefold() != "chunked"
                or limit == 0
                or self.headers.get_content_type() != "multipart/form-data"
            ):
                return self._reject(400)
            self.body_mode = "chunked"
            self.body_length = None
        else:
            raw_length = raw_length if raw_length is not None else ("0" if self.command != "POST" else "")
            if re.fullmatch(r"[0-9]{1,10}", raw_length) is None:
                return self._reject(400)
            self.body_mode = "fixed"
            self.body_length = int(raw_length)
            if self.body_length > limit:
                return self._reject(413 if limit else 400)
        return True

    def _read_exact(self, size: int) -> bytes:
        value = bytearray()
        try:
            while len(value) < size:
                chunk = self.rfile.read1(size - len(value))
                if not chunk:
                    raise _RequestBodyError(400)
                value.extend(chunk)
        except (OSError, ValueError) as error:
            raise _RequestBodyError(400) from error
        return bytes(value)

    def _decode_chunked_upload(self, output) -> int:
        total = 0
        while True:
            try:
                line = self.rfile.readline(_MAX_CHUNK_SIZE_DIGITS + 3)
            except (OSError, ValueError) as error:
                raise _RequestBodyError(400) from error
            if (
                not line.endswith(b"\r\n")
                or len(line) > _MAX_CHUNK_SIZE_DIGITS + 2
                or re.fullmatch(rb"[0-9A-Fa-f]{1,16}\r\n", line) is None
            ):
                raise _RequestBodyError(400)
            size = int(line[:-2], 16)
            if size == 0:
                if self._read_exact(2) != b"\r\n":
                    raise _RequestBodyError(400)
                return total
            if size > MAX_UPLOAD_BODY_BYTES - total:
                raise _RequestBodyError(413)
            remaining = size
            while remaining:
                block = self._read_exact(min(_CHUNK, remaining))
                output.write(block)
                total += len(block)
                remaining -= len(block)
            if self._read_exact(2) != b"\r\n":
                raise _RequestBodyError(400)

    @staticmethod
    def _send_body(upstream, source, length: int, *, read1: bool) -> None:
        remaining = length
        while remaining:
            size = min(_CHUNK, remaining)
            chunk = source.read1(size) if read1 else source.read(size)
            if not chunk:
                raise _RequestBodyError(400)
            upstream.send(chunk)
            remaining -= len(chunk)

    def _forward(self):
        decoded = None
        body_length = self.body_length
        if self.body_mode == "chunked":
            decoded = SpooledTemporaryFile(max_size=_CHUNK)
            try:
                body_length = self._decode_chunked_upload(decoded)
                decoded.seek(0)
            except _RequestBodyError as error:
                decoded.close()
                return self._reject(error.status)
        upstream = HTTPConnection("127.0.0.1", 8765, timeout=300)
        try:
            upstream.putrequest(self.command, self.path, skip_host=True, skip_accept_encoding=True)
            upstream.putheader("Host", "127.0.0.1:8765")
            upstream.putheader("Connection", "close")
            upstream.putheader("Content-Length", str(body_length))
            if self.headers.get("Origin") is not None:
                upstream.putheader("Origin", "http://127.0.0.1:8765")
            if self.headers.get("Content-Type") is not None:
                upstream.putheader("Content-Type", self.headers["Content-Type"])
            upstream.endheaders()
            self._send_body(
                upstream,
                decoded if decoded is not None else self.rfile,
                body_length,
                read1=decoded is None,
            )
            response = upstream.getresponse()
            headers = response.getheaders()
            names = [key.lower() for key, _ in headers]
            length = response.getheader("Content-Length", "")
            if (not 200 <= response.status < 600 or 300 <= response.status < 400
                    or response.headers.defects or len(headers) > 40 or len(names) != len(set(names))
                    or "transfer-encoding" in names or "location" in names
                    or any(_TOKEN.fullmatch(key) is None or any(ord(c) < 32 or ord(c) > 126 for c in value)
                           for key, value in headers)
                    or re.fullmatch(r"[0-9]{1,10}", length) is None or int(length) > _MAX_RESPONSE):
                return self._reject(502)
            # Validate complete bounded response before committing status/headers.
            # Large results spill to a private temporary file, not unbounded RAM.
            with SpooledTemporaryFile(max_size=_CHUNK) as output:
                remaining = int(length) if self.command != "HEAD" else 0
                while remaining:
                    chunk = response.read(min(_CHUNK, remaining))
                    if not chunk:
                        return self._reject(502)
                    output.write(chunk)
                    remaining -= len(chunk)
                self.send_response_only(response.status)
                for key, value in headers:
                    if key.lower() in _RESPONSE_HEADERS:
                        self.send_header(key, value)
                self.send_header("Strict-Transport-Security", "max-age=31536000")
                self.send_header("Connection", "close")
                self.end_headers()
                output.seek(0)
                while chunk := output.read(_CHUNK):
                    self.wfile.write(chunk)
        except _RequestBodyError as error:
            self._reject(error.status)
        except (OSError, HTTPException, ValueError):
            self._reject(502)
        finally:
            if decoded is not None:
                decoded.close()
            upstream.close()

    do_GET = _forward
    do_HEAD = _forward
    do_POST = _forward


def main():
    def stop(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        with GatewayServer(GatewayConfig.from_environment()) as server:
            print("Authenticated gateway listening on 127.0.0.1:8766", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError):
        print("GATEWAY_STARTUP_FAILED: check private configuration and port availability")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
