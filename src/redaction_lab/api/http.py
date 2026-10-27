"""Small standard-library HTTP boundary for the frozen local API contract."""

from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser
from http import HTTPStatus
import json
import re
from typing import Callable, Iterable, Mapping
from urllib.parse import urlsplit

from redaction_lab.application.config import MAX_PAIR_BYTES, MAX_PDF_BYTES


API_VERSION = "0.2"
MAX_MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_UPLOAD_BODY_BYTES = MAX_PAIR_BYTES + MAX_MULTIPART_OVERHEAD_BYTES
_HOST_PATTERN = re.compile(r"^127\.0\.0\.1(?::([0-9]{1,5}))?$")
_MULTIPART_CONTENT_TYPE_PATTERN = re.compile(
    r"^multipart/form-data[ \t]*;[ \t]*boundary[ \t]*=[ \t]*"
    r'(?:"(?P<quoted>[A-Za-z0-9\'()+_,./:=? \-]{1,70})"|'
    r"(?P<token>[A-Za-z0-9'._+\-]{1,70}))[ \t]*$",
    re.IGNORECASE,
)


class HttpProblem(ValueError):
    """A public, path-free error safe to serialize to a local client."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DocumentUpload:
    project_id: str
    redacted_pdf: bytes
    reference_pdf: bytes | None


StartResponse = Callable[[str, list[tuple[str, str]]], object]


def _host_port(host: str, scheme: str) -> int:
    match = _HOST_PATTERN.fullmatch(host)
    if match is None:
        raise HttpProblem(400, "INVALID_REQUEST", "Host must use 127.0.0.1")
    if match.group(1) is None:
        return 443 if scheme == "https" else 80
    port = int(match.group(1))
    if not 1 <= port <= 65_535:
        raise HttpProblem(400, "INVALID_REQUEST", "Host port is invalid")
    return port


def validate_local_request(environment: Mapping[str, object]) -> None:
    """Reject requests that are not loopback and same-origin."""

    if environment.get("REMOTE_ADDR") != "127.0.0.1":
        raise HttpProblem(400, "INVALID_REQUEST", "Request must use loopback")
    scheme = str(environment.get("wsgi.url_scheme", "http")).lower()
    if scheme not in {"http", "https"}:
        raise HttpProblem(400, "INVALID_REQUEST", "Request scheme is invalid")
    host = str(environment.get("HTTP_HOST", ""))
    host_port = _host_port(host, scheme)
    origin_value = environment.get("HTTP_ORIGIN")
    if origin_value is None:
        return
    origin = urlsplit(str(origin_value))
    try:
        origin_port = origin.port or (443 if origin.scheme == "https" else 80)
    except ValueError as error:
        raise HttpProblem(400, "INVALID_REQUEST", "Origin is invalid") from error
    if (
        origin.scheme != scheme
        or origin.hostname != "127.0.0.1"
        or origin.username is not None
        or origin.password is not None
        or origin_port != host_port
        or origin.path not in {"", "/"}
        or origin.query
        or origin.fragment
    ):
        raise HttpProblem(400, "INVALID_REQUEST", "Origin must match Host")


def read_bounded_body(
    environment: Mapping[str, object], *, max_bytes: int
) -> bytes:
    """Read at most ``max_bytes`` from a WSGI input stream."""

    raw_length = str(environment.get("CONTENT_LENGTH", ""))
    stream = environment.get("wsgi.input")
    if stream is None or not hasattr(stream, "read"):
        raise HttpProblem(400, "INVALID_REQUEST", "Request body is unavailable")
    if not raw_length.isascii() or not raw_length.isdecimal():
        raise HttpProblem(400, "INVALID_REQUEST", "Content-Length is invalid")
    declared = int(raw_length)
    if declared > max_bytes:
        raise HttpProblem(413, "PAYLOAD_TOO_LARGE", "Request body is too large")
    limit = declared
    collected = bytearray()
    while len(collected) < limit:
        chunk = stream.read(limit - len(collected))  # type: ignore[union-attr]
        if not isinstance(chunk, bytes):
            raise HttpProblem(400, "INVALID_REQUEST", "Request body must be bytes")
        if not chunk:
            break
        collected.extend(chunk)
    body = bytes(collected)
    if len(body) > max_bytes:
        raise HttpProblem(413, "PAYLOAD_TOO_LARGE", "Request body is too large")
    if len(body) != declared:
        raise HttpProblem(422, "MALFORMED_REQUEST", "Request body is incomplete")
    return body


def _content_type_message(content_type: str) -> Message:
    if "\r" in content_type or "\n" in content_type:
        raise HttpProblem(415, "UNSUPPORTED_MEDIA_TYPE", "Content-Type is invalid")
    try:
        content_type.encode("ascii")
    except UnicodeEncodeError as error:
        raise HttpProblem(
            415, "UNSUPPORTED_MEDIA_TYPE", "Content-Type is invalid"
        ) from error
    message = Message(policy=policy.default)
    message["Content-Type"] = content_type
    return message


def parse_document_upload(content_type: str, body: bytes) -> DocumentUpload:
    """Parse the exact multipart fields permitted by API v0.1."""

    header = _content_type_message(content_type)
    if header.get_content_type() != "multipart/form-data":
        raise HttpProblem(
            415,
            "UNSUPPORTED_MEDIA_TYPE",
            "Content-Type must be multipart/form-data",
        )
    content_type_match = _MULTIPART_CONTENT_TYPE_PATTERN.fullmatch(content_type)
    if content_type_match is None:
        raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart boundary is invalid")
    boundary = content_type_match.group("quoted") or content_type_match.group("token")
    if boundary.endswith(" "):
        raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart boundary is invalid")
    encoded_type = content_type.encode("ascii")
    message = BytesParser(policy=policy.default).parsebytes(
        b"Content-Type: " + encoded_type + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    )
    if (
        not message.is_multipart()
        or any(part.defects for part in message.walk())
        or message.preamble not in {None, ""}
        or message.epilogue not in {None, ""}
    ):
        raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart body is malformed")

    fields: dict[str, bytes] = {}
    for part in message.iter_parts():
        if part.is_multipart() or part.get_content_disposition() != "form-data":
            raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart part is invalid")
        for singleton_header in (
            "Content-Disposition",
            "Content-Type",
            "Content-Transfer-Encoding",
        ):
            if len(part.get_all(singleton_header, [])) > 1:
                raise HttpProblem(
                    422,
                    "MALFORMED_REQUEST",
                    "Multipart part contains a duplicated header",
                )
        name = part.get_param("name", header="content-disposition")
        if name not in {"project_id", "redacted_pdf", "reference_pdf"}:
            raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart field is not allowed")
        if name in fields:
            raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart field is duplicated")
        transfer_encoding = part.get("Content-Transfer-Encoding")
        if transfer_encoding not in {None, "binary", "8bit"}:
            raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart encoding is not allowed")
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            raise HttpProblem(422, "MALFORMED_REQUEST", "Multipart field is malformed")
        filename = part.get_filename()
        if name == "project_id":
            if filename is not None:
                raise HttpProblem(422, "MALFORMED_REQUEST", "Project field is malformed")
        elif filename is None or part.get_content_type() != "application/pdf":
            raise HttpProblem(
                415,
                "UNSUPPORTED_MEDIA_TYPE",
                "PDF fields must use application/pdf",
            )
        fields[name] = payload

    if "project_id" not in fields or "redacted_pdf" not in fields:
        raise HttpProblem(422, "MALFORMED_REQUEST", "Required upload field is missing")
    try:
        project_id = fields["project_id"].decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise HttpProblem(422, "MALFORMED_REQUEST", "Project ID is invalid") from error
    if (
        not project_id
        or len(project_id) > 256
        or any(ord(character) < 32 for character in project_id)
    ):
        raise HttpProblem(422, "MALFORMED_REQUEST", "Project ID is invalid")
    redacted_pdf = fields["redacted_pdf"]
    reference_pdf = fields.get("reference_pdf")
    for value in (redacted_pdf, reference_pdf):
        if value is None:
            continue
        if not value.startswith(b"%PDF-"):
            raise HttpProblem(422, "MALFORMED_REQUEST", "PDF signature is invalid")
        if len(value) > MAX_PDF_BYTES:
            raise HttpProblem(413, "PAYLOAD_TOO_LARGE", "PDF exceeds 25 MiB")
    if len(redacted_pdf) + (len(reference_pdf) if reference_pdf else 0) > MAX_PAIR_BYTES:
        raise HttpProblem(413, "PAYLOAD_TOO_LARGE", "PDF pair exceeds 50 MiB")
    return DocumentUpload(project_id, redacted_pdf, reference_pdf)


def json_response(
    start_response: StartResponse,
    status: int,
    payload: Mapping[str, object],
) -> Iterable[bytes]:
    body = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Redaction-Lab-API", API_VERSION),
    ]
    start_response(f"{status} {HTTPStatus(status).phrase}", headers)
    return (body,)
