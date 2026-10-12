from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
import uuid

import pytest

from redaction_lab.fixtures import make_synthetic_pair


_API_VERSION = "0.1"
_MAX_PDF_BYTES = 25 * 1024 * 1024
_LOOPBACK_URL = re.compile(r"^http://127\.0\.0\.1:(?:[1-9][0-9]{0,4})$")


def _acceptance_url() -> str:
    value = os.environ.get("REDACTION_LAB_ACCEPTANCE_URL", "")
    if not value:
        pytest.skip("BLOCKED: RL-MVP-007B service is not supplied to 7D prep")
    if not _LOOPBACK_URL.fullmatch(value):
        pytest.fail("REDACTION_LAB_ACCEPTANCE_URL must be explicit 127.0.0.1 HTTP with a port")
    port = int(value.rsplit(":", 1)[1])
    if not 1 <= port <= 65535:
        pytest.fail("REDACTION_LAB_ACCEPTANCE_URL port is out of range")
    return value


def _request(
    method: str,
    path: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object], dict[str, str]]:
    request = urllib.request.Request(
        _acceptance_url() + path,
        data=body,
        method=method,
        headers=headers or {},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = response.read()
            status = response.status
            response_headers = dict(response.headers.items())
    except urllib.error.HTTPError as error:
        payload = error.read()
        status = error.code
        response_headers = dict(error.headers.items())
    parsed = json.loads(payload.decode("utf-8")) if payload else {}
    assert isinstance(parsed, dict)
    return status, parsed, response_headers


def _multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes]]) -> tuple[bytes, str]:
    boundary = f"redactionlab-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )
    for name, (filename, content) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{filename}"\r\n'
                ).encode(),
                b"Content-Type: application/pdf\r\n\r\n",
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _upload_pair(tmp_path: Path) -> tuple[dict[str, object], bytes, bytes]:
    redacted_path, reference_path = make_synthetic_pair("two_boxes", tmp_path / "pair")
    redacted = redacted_path.read_bytes()
    reference = reference_path.read_bytes()
    body, content_type = _multipart(
        {"project_id": "acceptance-project"},
        {
            "redacted_pdf": ("redacted.pdf", redacted),
            "reference_pdf": ("reference.pdf", reference),
        },
    )
    status, payload, headers = _request(
        "POST",
        "/api/v1/documents",
        body=body,
        headers={"Content-Type": content_type, "Origin": _acceptance_url()},
    )
    assert status == 201, payload
    assert headers.get("X-Redaction-Lab-API") == _API_VERSION
    return payload, redacted, reference


def test_health_is_loopback_local_and_runtime_unqualified() -> None:
    status, payload, headers = _request("GET", "/api/v1/health")

    assert status == 200
    assert payload == {
        "api_version": "0.1",
        "state": payload["state"],
        "runtime_qualified": False,
        "mode": "local",
    }
    assert payload["state"] in {"READY", "DEGRADED"}
    assert headers.get("X-Redaction-Lab-API") == _API_VERSION


def test_synthetic_pair_upload_preserves_role_separation_and_unknown_truth(tmp_path: Path) -> None:
    payload, redacted, reference = _upload_pair(tmp_path)

    assert payload["project_id"] == "acceptance-project"
    assert payload["truth_status"] == "UNKNOWN"
    redacted_result = payload["redacted"]
    reference_result = payload["reference"]
    assert isinstance(redacted_result, dict) and isinstance(reference_result, dict)
    assert set(redacted_result) == {"version_id", "job_id", "sha256", "byte_size", "status"}
    assert redacted_result["status"] == "ACCEPTED"
    assert redacted_result["sha256"] == hashlib.sha256(redacted).hexdigest()
    assert redacted_result["byte_size"] == len(redacted)
    assert set(reference_result) == {"version_id", "sha256", "byte_size"}
    assert reference_result["sha256"] == hashlib.sha256(reference).hexdigest()
    assert reference_result["byte_size"] == len(reference)
    assert "job_id" not in reference_result


def test_unverified_runtime_returns_honest_503_without_claiming_job(tmp_path: Path) -> None:
    payload, _, _ = _upload_pair(tmp_path)
    redacted = payload["redacted"]
    assert isinstance(redacted, dict)
    job_id = str(redacted["job_id"])

    status, process_payload, _ = _request("POST", f"/api/v1/jobs/{job_id}/process")

    assert status == 503
    assert process_payload == {
        "error": {
            "code": "RUNTIME_UNVERIFIED",
            "message": "PDF processing runtime is not qualified on this installation",
        },
        "job_id": job_id,
        "status": "ACCEPTED",
    }
    job_status, job_payload, _ = _request("GET", f"/api/v1/jobs/{job_id}")
    assert job_status == 200
    assert job_payload["status"] == "ACCEPTED"
    assert job_payload["source_id"] is None


def test_pending_results_do_not_fabricate_targets_or_scores(tmp_path: Path) -> None:
    payload, _, _ = _upload_pair(tmp_path)
    redacted = payload["redacted"]
    assert isinstance(redacted, dict)
    version_id = str(redacted["version_id"])

    status, result, _ = _request("GET", f"/api/v1/results/{version_id}")

    assert status == 200
    assert result["version_id"] == version_id
    assert result["status"] == "PENDING"
    assert result["targets"] == []
    assert result["summaries"] == {"target": None, "document": None, "model": None}
    assert result["score_status"] == "NONE"
    assert result["verified_score"] is None
    assert result["experimental_score"] is None
    assert result["truth_status"] == "UNKNOWN"


def test_one_over_file_limit_is_rejected() -> None:
    oversized = b"%PDF-" + b"x" * (_MAX_PDF_BYTES + 1 - len(b"%PDF-"))
    body, content_type = _multipart(
        {"project_id": "acceptance-project"},
        {"redacted_pdf": ("oversized.pdf", oversized)},
    )

    status, payload, _ = _request(
        "POST",
        "/api/v1/documents",
        body=body,
        headers={"Content-Type": content_type, "Origin": _acceptance_url()},
    )

    assert status == 413
    assert isinstance(payload.get("error"), dict)


def test_unsafe_origin_is_rejected(tmp_path: Path) -> None:
    redacted_path, _ = make_synthetic_pair("two_boxes", tmp_path / "unsafe-origin")
    body, content_type = _multipart(
        {"project_id": "acceptance-project"},
        {"redacted_pdf": ("redacted.pdf", redacted_path.read_bytes())},
    )

    status, payload, _ = _request(
        "POST",
        "/api/v1/documents",
        body=body,
        headers={"Content-Type": content_type, "Origin": "http://evil.invalid"},
    )

    assert status == 400
    assert isinstance(payload.get("error"), dict)


def test_durable_restart_is_blocked_until_packaging_restart_hook_exists() -> None:
    pytest.skip("BLOCKED: RL-MVP-007P has not yet supplied a frozen restart/launcher acceptance hook")
