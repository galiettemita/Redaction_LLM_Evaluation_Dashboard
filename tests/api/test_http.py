from __future__ import annotations

from io import BytesIO
import json

import pytest

import redaction_lab.api.http as http_module
from redaction_lab.api.http import (
    HttpProblem,
    json_response,
    parse_document_upload,
    read_bounded_body,
    validate_local_request,
)


def _environment(
    body: bytes = b"",
    *,
    host: str = "127.0.0.1:8765",
    origin: str | None = "http://127.0.0.1:8765",
    remote: str = "127.0.0.1",
    content_type: str = "application/octet-stream",
) -> dict[str, object]:
    environment: dict[str, object] = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/v1/documents",
        "HTTP_HOST": host,
        "REMOTE_ADDR": remote,
        "wsgi.url_scheme": "http",
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    if origin is not None:
        environment["HTTP_ORIGIN"] = origin
    return environment


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"REMOTE_ADDR": "192.0.2.1"}, "loopback"),
        ({"HTTP_HOST": "localhost:8765"}, "Host"),
        ({"HTTP_HOST": "127.0.0.1.evil.test"}, "Host"),
        ({"HTTP_ORIGIN": "https://evil.test"}, "Origin"),
        ({"HTTP_ORIGIN": "http://127.0.0.1:9999"}, "Origin"),
        ({"REMOTE_ADDR": "::1"}, "loopback"),
        ({"HTTP_ORIGIN": "http://user@127.0.0.1:8765"}, "Origin"),
        ({"HTTP_ORIGIN": "http://127.0.0.1:8765/?query"}, "Origin"),
    ],
)
def test_local_request_guard_rejects_non_loopback_or_cross_origin(
    changes: dict[str, str], message: str
) -> None:
    environment = _environment()
    environment.update(changes)

    with pytest.raises(HttpProblem, match=message) as raised:
        validate_local_request(environment)

    assert raised.value.status == 400
    assert raised.value.code == "INVALID_REQUEST"


def test_local_request_guard_accepts_absent_origin_for_local_client() -> None:
    validate_local_request(_environment(origin=None, host="127.0.0.1"))


def test_bounded_body_rejects_declared_overflow() -> None:
    declared = _environment(b"abcdef")
    with pytest.raises(HttpProblem) as declared_error:
        read_bounded_body(declared, max_bytes=5)
    assert (declared_error.value.status, declared_error.value.code) == (
        413,
        "PAYLOAD_TOO_LARGE",
    )

def test_bounded_body_collects_short_reads_until_declared_length() -> None:
    class ShortReadStream:
        def __init__(self) -> None:
            self.chunks = [b"ab", b"cd", b"ef", b""]

        def read(self, size: int) -> bytes:
            chunk = self.chunks.pop(0)
            assert len(chunk) <= size
            return chunk

    environment = _environment()
    environment["CONTENT_LENGTH"] = "6"
    environment["wsgi.input"] = ShortReadStream()

    assert read_bounded_body(environment, max_bytes=6) == b"abcdef"


@pytest.mark.parametrize("content_length", ["", "+3", " 3", "3 "])
def test_bounded_body_requires_strict_decimal_content_length(
    content_length: str,
) -> None:
    environment = _environment(b"abc")
    environment["CONTENT_LENGTH"] = content_length

    with pytest.raises(HttpProblem) as raised:
        read_bounded_body(environment, max_bytes=3)

    assert (raised.value.status, raised.value.code) == (400, "INVALID_REQUEST")


def _multipart(
    *,
    redacted: bytes = b"%PDF-redacted",
    reference: bytes | None = b"%PDF-reference",
    project_id: str = "project-1",
    redacted_type: str = "application/pdf",
) -> tuple[bytes, str]:
    boundary = "redaction-lab-test-boundary"
    parts = [
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="project_id"\r\n\r\n'
            f"{project_id}\r\n"
        ).encode(),
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="redacted_pdf"; filename="redacted.pdf"\r\n'
            f"Content-Type: {redacted_type}\r\n\r\n"
        ).encode()
        + redacted
        + b"\r\n",
    ]
    if reference is not None:
        parts.append(
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="reference_pdf"; filename="reference.pdf"\r\n'
                "Content-Type: application/pdf\r\n\r\n"
            ).encode()
            + reference
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def test_multipart_parser_returns_only_frozen_upload_fields() -> None:
    body, content_type = _multipart()

    upload = parse_document_upload(content_type, body)

    assert upload.project_id == "project-1"
    assert upload.redacted_pdf == b"%PDF-redacted"
    assert upload.reference_pdf == b"%PDF-reference"


def test_multipart_parser_preserves_binary_pdf_bytes_exactly() -> None:
    pdf = b"%PDF-\x00\xff\r\nbinary\nbytes"
    body, content_type = _multipart(redacted=pdf, reference=None)

    upload = parse_document_upload(content_type, body)

    assert upload.redacted_pdf == pdf


def test_multipart_parser_rejects_missing_closing_boundary() -> None:
    body, content_type = _multipart()
    closing = b"--redaction-lab-test-boundary--\r\n"

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, body.removesuffix(closing))

    assert raised.value.status == 422


def test_multipart_parser_rejects_epilogue_bytes() -> None:
    body, content_type = _multipart()

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, body + b"smuggled")

    assert raised.value.status == 422


def test_multipart_parser_rejects_nonempty_preamble() -> None:
    body, content_type = _multipart()

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, b"smuggled\r\n" + body)

    assert (raised.value.status, raised.value.code) == (422, "MALFORMED_REQUEST")


@pytest.mark.parametrize(
    "content_type",
    [
        (
            "multipart/form-data; boundary=redaction-lab-test-boundary; "
            "boundary=evil"
        ),
        (
            "multipart/form-data; boundary=redaction-lab-test-boundary, "
            "application/json"
        ),
        (
            "multipart/form-data; boundary=redaction-lab-test-boundary; "
            "charset=utf-8"
        ),
    ],
)
def test_multipart_parser_rejects_ambiguous_content_type_parameters(
    content_type: str,
) -> None:
    body, _ = _multipart(reference=None)

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, body)

    assert raised.value.status in {415, 422}


def test_multipart_parser_accepts_one_quoted_boundary_parameter() -> None:
    body, _ = _multipart(reference=None)

    upload = parse_document_upload(
        'multipart/form-data; boundary="redaction-lab-test-boundary"', body
    )

    assert upload.redacted_pdf == b"%PDF-redacted"


@pytest.mark.parametrize(
    "duplicate_header",
    [
        'Content-Disposition: form-data; name="redacted_pdf"',
        "Content-Type: application/pdf",
        (
            "Content-Transfer-Encoding: binary\r\n"
            "Content-Transfer-Encoding: 8bit"
        ),
    ],
)
def test_multipart_parser_rejects_duplicate_singleton_part_headers(
    duplicate_header: str,
) -> None:
    body, content_type = _multipart(reference=None)
    marker = b"Content-Type: application/pdf\r\n\r\n"
    replacement = (
        b"Content-Type: application/pdf\r\n"
        + duplicate_header.encode("ascii")
        + b"\r\n\r\n"
    )
    tampered = body.replace(marker, replacement, 1)

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, tampered)

    assert (raised.value.status, raised.value.code) == (422, "MALFORMED_REQUEST")


def test_multipart_parser_enforces_each_pdf_byte_limit(monkeypatch) -> None:
    monkeypatch.setattr(http_module, "MAX_PDF_BYTES", 8)
    monkeypatch.setattr(http_module, "MAX_PAIR_BYTES", 32)
    body, content_type = _multipart(redacted=b"%PDF-1234", reference=None)

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, body)

    assert (raised.value.status, raised.value.code) == (413, "PAYLOAD_TOO_LARGE")


def test_multipart_parser_enforces_combined_pair_byte_limit(monkeypatch) -> None:
    monkeypatch.setattr(http_module, "MAX_PDF_BYTES", 16)
    monkeypatch.setattr(http_module, "MAX_PAIR_BYTES", 16)
    body, content_type = _multipart(
        redacted=b"%PDF-1234", reference=b"%PDF-5678"
    )

    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, body)

    assert (raised.value.status, raised.value.code) == (413, "PAYLOAD_TOO_LARGE")


@pytest.mark.parametrize(
    ("body", "content_type", "status"),
    [
        (b"{}", "application/json", 415),
        (_multipart(redacted_type="text/plain")[0], _multipart()[1], 415),
        (_multipart(redacted=b"not-a-pdf")[0], _multipart()[1], 422),
        (_multipart(project_id=" ")[0], _multipart()[1], 422),
    ],
)
def test_multipart_parser_rejects_wrong_type_or_malformed_fields(
    body: bytes, content_type: str, status: int
) -> None:
    with pytest.raises(HttpProblem) as raised:
        parse_document_upload(content_type, body)
    assert raised.value.status == status


def test_json_response_adds_version_and_no_cache_headers() -> None:
    captured: dict[str, object] = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(json_response(start_response, 201, {"ok": True}))

    assert captured["status"] == "201 Created"
    assert captured["headers"] == {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": str(len(body)),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "X-Redaction-Lab-API": "0.1",
    }
    assert json.loads(body) == {"ok": True}
