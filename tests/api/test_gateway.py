"""Raw HTTP tests of the fixed loopback owner-only gateway (synthetic credentials)."""

import base64
from contextlib import contextmanager
import importlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
from threading import Event, Thread

import pytest


ENV = {
    "REDACTION_LAB_PUBLIC_HOST": "demo.example.invalid",
    "REDACTION_LAB_GATEWAY_USERNAME": "synthetic-owner",
    "REDACTION_LAB_GATEWAY_PASSWORD": "synthetic-test-password-0123456789",
}
AUTH = "Basic " + base64.b64encode(
    (ENV["REDACTION_LAB_GATEWAY_USERNAME"] + ":" + ENV["REDACTION_LAB_GATEWAY_PASSWORD"]).encode()
).decode()


def test_gateway_exists_as_an_explicit_authenticated_boundary():
    assert importlib.util.find_spec("redaction_lab.api.gateway") is not None


@pytest.fixture
def gateway():
    return importlib.import_module("redaction_lab.api.gateway")


@pytest.fixture
def upstream():
    observations = []
    first_chunk = Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.reply()

        def do_HEAD(self):
            self.reply()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(min(length, 65536))
            first_chunk.set()
            body += self.rfile.read(length - len(body))
            observations.append((self.path, dict(self.headers), body))
            self.reply()

        def reply(self):
            if self.command != "POST":
                observations.append((self.path, dict(self.headers), b""))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "2")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; frame-src blob:")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(b"{}")

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield observations, first_chunk
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def running(gateway):
    server = gateway.GatewayServer(gateway.GatewayConfig.from_environment(ENV))
    assert server.server_address == ("127.0.0.1", 8766)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def request(method="GET", path="/", *, headers=(), body=b"", auth=AUTH, host="demo.example.invalid"):
    fields = [f"{method} {path} HTTP/1.1", f"Host: {host}"]
    if auth is not None:
        fields.append("Authorization: " + auth)
    fields.extend(headers)
    with socket.create_connection(("127.0.0.1", 8766), timeout=3) as connection:
        connection.sendall(("\r\n".join(fields) + "\r\n\r\n").encode() + body)
        connection.shutdown(socket.SHUT_WR)
        reply = b""
        while chunk := connection.recv(65536):
            reply += chunk
    head, payload = reply.split(b"\r\n\r\n", 1)
    return int(head.split()[1]), head.decode(), payload


def chunks(*values: bytes, terminal: bytes = b"0\r\n\r\n") -> bytes:
    return b"".join(f"{len(value):x}\r\n".encode() + value + b"\r\n" for value in values) + terminal


@pytest.mark.parametrize("key,value", [
    ("REDACTION_LAB_PUBLIC_HOST", ""), ("REDACTION_LAB_PUBLIC_HOST", "https://demo.example.invalid"),
    ("REDACTION_LAB_PUBLIC_HOST", "127.0.0.1"), ("REDACTION_LAB_PUBLIC_HOST", "demo.example.invalid:443"),
    ("REDACTION_LAB_PUBLIC_HOST", "a.example/evil"), ("REDACTION_LAB_PUBLIC_HOST", "a..invalid"),
    ("REDACTION_LAB_GATEWAY_USERNAME", "bad:user"), ("REDACTION_LAB_GATEWAY_PASSWORD", "short"),
    ("REDACTION_LAB_GATEWAY_PASSWORD", "a" * 30 + "\n"),
])
def test_private_configuration_fails_closed(gateway, key, value):
    with pytest.raises(ValueError):
        gateway.GatewayConfig.from_environment({**ENV, key: value})
    assert ENV["REDACTION_LAB_GATEWAY_PASSWORD"] not in repr(gateway.GatewayConfig.from_environment(ENV))


@pytest.mark.parametrize("auth", [None, "", "Bearer fake", "Basic invalid", AUTH[:-2] + "xx"])
def test_authentication_precedes_forwarding_and_body_reads(running, upstream, auth):
    status, head, _ = request("POST", "/api/v1/documents", auth=auth,
                              headers=["Content-Length: 1024", "Origin: https://demo.example.invalid"])
    assert status == 401
    assert 'WWW-Authenticate: Basic realm="Redaction Lab"' in head
    assert upstream[0] == []


def test_chunked_upload_authentication_precedes_body_reads(running, upstream):
    status, head, _ = request("POST", "/api/v1/documents", auth="Basic invalid", headers=[
        "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
        "Content-Type: multipart/form-data; boundary=synthetic",
    ])
    assert status == 401
    assert 'WWW-Authenticate: Basic realm="Redaction Lab"' in head
    assert upstream[0] == []


@pytest.mark.parametrize("host", ["other.invalid", "127.0.0.1:8766", "demo.example.invalid:443", "DEMO.example.invalid", "demo.example.invalid."])
def test_exact_host_only(running, upstream, host):
    assert request(host=host)[0] == 400
    assert upstream[0] == []


@pytest.mark.parametrize("headers", [[], ["Origin: http://demo.example.invalid"],
    ["Origin: https://other.invalid"], ["Origin: null"], ["Origin: https://demo.example.invalid/"]])
def test_mutations_require_exact_https_origin(running, upstream, headers):
    assert request("POST", "/api/v1/documents", headers=[*headers, "Content-Length: 0"])[0] == 403
    assert upstream[0] == []


@pytest.mark.parametrize("headers", [
    ["Host: demo.example.invalid"], ["Authorization: " + AUTH],
    ["Origin: https://demo.example.invalid", "Origin: https://demo.example.invalid"],
    ["Content-Length: 0", "Content-Length: 0"], ["Content-Length: 0, 0"],
    ["Content-Length: +0"], ["Content-Length: -1"], ["Transfer-Encoding: chunked"],
    ["Content-Length: 0", "Transfer-Encoding: chunked"], ["Expect: 100-continue"],
    ["Content-Type: application/pdf", "Content-Type: text/plain"],
    ["X-Fold: first\r\n second"], ["Bad Header: value"],
])
def test_ambiguous_framing_is_rejected_without_forwarding(running, upstream, headers):
    assert request(headers=headers)[0] == 400
    assert upstream[0] == []


@pytest.mark.parametrize("method,path", [
    ("CONNECT", "127.0.0.1:11434"), ("GET", "http://127.0.0.1:11434/api/tags"),
    ("GET", "//127.0.0.1:11434/api/tags"), ("GET", "/api/generate"),
    ("GET", "/api/tags"), ("GET", "/runtime/models"), ("GET", "/api/v1/health?url=http://other.invalid"),
    ("GET", "/api/v1/../generate"), ("GET", "/%61pi/v1/health"),
    ("DELETE", "/api/v1/documents/anything"), ("POST", "/"),
])
def test_gateway_cannot_be_an_arbitrary_proxy_or_ollama_route(running, upstream, method, path):
    assert request(method, path)[0] in {400, 404, 405}
    assert upstream[0] == []


def test_bounded_upload_streams_with_only_translated_loopback_headers(running, upstream, gateway):
    prefix = b"%PDF-1.7\n" + b"x" * 65527
    suffix = b"y" * 65536
    with socket.create_connection(("127.0.0.1", 8766), timeout=3) as connection:
        raw = ("POST /api/v1/documents HTTP/1.1\r\nHost: demo.example.invalid\r\n"
               f"Authorization: {AUTH}\r\nOrigin: https://demo.example.invalid\r\n"
               f"Content-Length: {len(prefix + suffix)}\r\nContent-Type: application/pdf\r\n"
               "X-Forwarded-Host: attacker.invalid\r\nCookie: private\r\n\r\n").encode()
        connection.sendall(raw + prefix)
        assert upstream[1].wait(2), "gateway buffered upload instead of bounded streaming"
        connection.sendall(suffix)
        reply = connection.recv(4096)
        assert reply.split()[1] == b"200"
    path, headers, body = upstream[0][0]
    assert path == "/api/v1/documents" and body == prefix + suffix
    assert headers["Host"] == "127.0.0.1:8765"
    assert headers["Origin"] == "http://127.0.0.1:8765"
    assert "Authorization" not in headers and "Cookie" not in headers and "X-Forwarded-Host" not in headers


def test_browser_multipart_headers_are_http_headers_not_a_mime_body(running, upstream):
    body = b'--synthetic\r\nContent-Disposition: form-data; name="project_id"\r\n\r\ntest\r\n--synthetic--\r\n'
    status, _, _ = request("POST", "/api/v1/documents", body=body, headers=[
        "Origin: https://demo.example.invalid", "Content-Type: multipart/form-data; boundary=synthetic",
        f"Content-Length: {len(body)}"])
    assert status == 200
    assert upstream[0][0][2] == body


def test_browser_chunked_upload_is_decoded_once_before_fixed_length_forwarding(running, upstream):
    parts = (
        b"--synthetic\r\nContent-Disposition: form-data; name=\"project_id\"\r\n\r\nproject-1\r\n",
        b"--synthetic\r\nContent-Disposition: form-data; name=\"redacted_pdf\"; filename=\"redacted.pdf\"\r\n"
        b"Content-Type: application/pdf\r\n\r\n%PDF-1.7\nsynthetic\r\n--synthetic--\r\n",
    )
    status, _, _ = request("POST", "/api/v1/documents", body=chunks(*parts), headers=[
        "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
        "Content-Type: multipart/form-data; boundary=synthetic",
        "Cookie: private", "X-Forwarded-Host: attacker.invalid",
    ])
    assert status == 200
    path, headers, body = upstream[0][0]
    assert path == "/api/v1/documents" and body == b"".join(parts)
    assert headers["Content-Length"] == str(len(body))
    assert "Transfer-Encoding" not in headers
    assert "Authorization" not in headers and "Cookie" not in headers
    assert "X-Forwarded-Host" not in headers


def test_bytes_after_terminal_chunk_are_discarded_by_connection_close(running, upstream):
    status, head, _ = request(
        "POST", "/api/v1/documents", body=chunks(b"synthetic") + b"smuggled", headers=[
            "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
            "Content-Type: multipart/form-data; boundary=synthetic",
        ]
    )
    assert status == 200
    assert "Connection: close" in head
    assert upstream[0][0][2] == b"synthetic"


@pytest.mark.parametrize("transfer", [
    "gzip", "compress", "chunked, gzip", "gzip, chunked", "chunked, chunked", "Chunked ",
])
def test_unsupported_or_ambiguous_transfer_codings_never_reach_upstream(running, upstream, transfer):
    status, _, _ = request("POST", "/api/v1/documents", body=b"0\r\n\r\n", headers=[
        "Origin: https://demo.example.invalid", f"Transfer-Encoding: {transfer}",
        "Content-Type: multipart/form-data; boundary=synthetic",
    ])
    assert status == 400
    assert upstream[0] == []


@pytest.mark.parametrize("method,path", [
    ("GET", "/"), ("POST", "/api/v1/jobs/job-1/process"),
])
def test_chunked_bodies_are_limited_to_document_uploads(running, upstream, method, path):
    status, _, _ = request(method, path, body=b"0\r\n\r\n", headers=[
        "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
        "Content-Type: multipart/form-data; boundary=synthetic",
    ])
    assert status == 400
    assert upstream[0] == []


@pytest.mark.parametrize("body", [
    b"1;extension=value\r\nx\r\n0\r\n\r\n",
    b"1\r\nx\r\n0\r\nX-Trailer: value\r\n\r\n",
    b"z\r\nx\r\n0\r\n\r\n",
    b"00000000000000000\r\n0\r\n\r\n",
    b"5\r\nabc",
    b"1\r\nxXX0\r\n\r\n",
    b"1\r\nx\r\n",
])
def test_malformed_chunked_uploads_fail_before_upstream(running, upstream, body):
    status, _, _ = request("POST", "/api/v1/documents", body=body, headers=[
        "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
        "Content-Type: multipart/form-data; boundary=synthetic",
    ])
    assert status == 400
    assert upstream[0] == []


def test_decoded_chunked_upload_overflow_returns_413_without_upstream(running, upstream, gateway, monkeypatch):
    monkeypatch.setattr(gateway, "MAX_UPLOAD_BODY_BYTES", 5)
    status, _, _ = request("POST", "/api/v1/documents", body=chunks(b"abc", b"def"), headers=[
        "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
        "Content-Type: multipart/form-data; boundary=synthetic",
    ])
    assert status == 413
    assert upstream[0] == []


@pytest.mark.parametrize("failure", ["write", "seek"])
def test_chunked_spool_io_failure_is_closed_and_returns_api_error(
    running, upstream, gateway, monkeypatch, failure
):
    spools = []

    class BrokenSpool:
        def __init__(self, *, max_size):
            assert max_size == gateway._CHUNK
            self.closed = False
            spools.append(self)

        def write(self, _value):
            if failure == "write":
                raise OSError("synthetic spool write failure")

        def seek(self, _offset):
            if failure == "seek":
                raise OSError("synthetic spool seek failure")

        def close(self):
            self.closed = True

    monkeypatch.setattr(gateway, "SpooledTemporaryFile", BrokenSpool)
    status, head, payload = request(
        "POST", "/api/v1/documents", body=chunks(b"synthetic"), headers=[
            "Origin: https://demo.example.invalid", "Transfer-Encoding: chunked",
            "Content-Type: multipart/form-data; boundary=synthetic",
        ]
    )
    assert status == 500
    assert "X-Redaction-Lab-API: 0.3" in head
    assert json.loads(payload)["error"]["code"] == "GATEWAY_REJECTED"
    assert len(spools) == 1 and spools[0].closed
    assert upstream[0] == []


def test_gateway_rejections_are_bounded_api_v03_errors(running, upstream):
    status, head, payload = request(host="wrong.invalid")
    assert status == 400
    assert "X-Redaction-Lab-API: 0.3" in head
    assert json.loads(payload) == {
        "error": {"code": "GATEWAY_REJECTED", "message": "Request could not be completed"}
    }
    assert upstream[0] == []


def test_connection_limit_rejection_is_a_bounded_api_v03_error(running):
    for _ in range(8):
        assert running._slots.acquire(blocking=False)
    try:
        status, head, payload = request()
        assert status == 503
        assert "X-Redaction-Lab-API: 0.3" in head
        assert json.loads(payload) == {
            "error": {"code": "GATEWAY_BUSY", "message": "Request could not be completed"}
        }
    finally:
        for _ in range(8):
            running._slots.release()


def test_oversize_or_static_body_rejected_before_upstream(running, upstream, gateway):
    assert request("POST", "/api/v1/documents", headers=["Origin: https://demo.example.invalid",
        f"Content-Length: {gateway.MAX_UPLOAD_BODY_BYTES + 1}"])[0] == 413
    assert request(headers=["Content-Length: 1"], body=b"x")[0] == 400
    assert upstream[0] == []


def test_security_headers_and_bodyless_head_preserved(running, upstream):
    status, headers, body = request()
    assert status == 200 and body == b"{}"
    assert "Content-Security-Policy: default-src 'self'; frame-src blob:" in headers
    assert "Cache-Control: no-store" in headers and "X-Content-Type-Options: nosniff" in headers
    assert "Strict-Transport-Security: max-age=31536000" in headers
    status, headers, body = request("HEAD")
    assert status == 200 and body == b"" and "Content-Length: 2" in headers


def test_upstream_absence_returns_bounded_sanitized_error(running):
    status, headers, body = request()
    assert status == 502 and b"upstream" not in body.lower()
    assert b"127.0.0.1" not in body and "Cache-Control: no-store" in headers


@pytest.mark.parametrize("response", [
    b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Length: 2\r\n\r\n{}",
    b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n",
    b"HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1:11434\r\nContent-Length: 0\r\n\r\n",
    b"HTTP/1.1 200 OK\r\nContent-Length: 50000000\r\n\r\n",
    b"HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\nshort",
])
def test_invalid_upstream_responses_fail_closed(running, response):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 8765))
        listener.listen()
        def serve():
            connection, _ = listener.accept()
            with connection:
                connection.recv(65536)
                connection.sendall(response)
        thread = Thread(target=serve)
        thread.start()
        assert request()[0] == 502
        thread.join()
