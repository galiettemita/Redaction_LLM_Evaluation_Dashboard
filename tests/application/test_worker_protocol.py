from __future__ import annotations

from hashlib import sha256
import json

import pytest

from redaction_lab.application.worker_protocol import (
    MAX_RESPONSE_BYTES,
    WORKER_PROTOCOL_VERSION,
    WorkerResponse,
    WorkerStatus,
    decode_response,
    decode_request,
    encode_request,
    WorkerRequest,
)
from redaction_lab.contracts import DocumentRole


def _payload(**changes: object) -> dict[str, object]:
    text = "visible [[TARGET:target-placeholder]] text"
    payload: dict[str, object] = {
        "protocol_version": WORKER_PROTOCOL_VERSION,
        "request_nonce": "a" * 32,
        "project_id": "project",
        "role": "REDACTED",
        "input_sha256": "b" * 64,
        "status": "PROCESSABLE",
        "page_count": 1,
        "detector_version": "vector-text-rect-v6",
        "canonicalizer_version": "safe-visible-text-v1",
        "canonical_text": text,
        "canonical_hash": sha256(text.encode()).hexdigest(),
        "targets": [{"page_index": 0, "normalized_bbox": [0.1, 0.2, 0.3, 0.4], "rectangle_index": 0}],
        "reason_code": None,
    }
    payload.update(changes)
    return payload


def test_strict_response_rejects_unknown_fields_and_invalid_status_payloads() -> None:
    with pytest.raises(ValueError):
        WorkerResponse.model_validate(_payload(fabricated_authority=True))
    with pytest.raises(ValueError):
        WorkerResponse.model_validate(_payload(status="UNSUPPORTED", reason_code=None))
    with pytest.raises(ValueError):
        WorkerResponse.model_validate(_payload(status="PROCESSABLE", targets=[]))


def test_response_decoder_enforces_byte_bound_before_json_parsing() -> None:
    with pytest.raises(ValueError, match="response size"):
        decode_response(b"{" + b"x" * MAX_RESPONSE_BYTES)


def test_unsupported_response_cannot_carry_canonical_or_target_evidence() -> None:
    payload = _payload(status="UNSUPPORTED", reason_code="ENCRYPTED")
    for key in ("canonical_text", "canonical_hash", "targets", "detector_version", "canonicalizer_version"):
        payload[key] = None if key != "targets" else []

    parsed = WorkerResponse.model_validate(payload)

    assert parsed.status is WorkerStatus.UNSUPPORTED
    assert parsed.targets == ()


def test_malformed_json_fails_closed() -> None:
    with pytest.raises(ValueError, match="worker response"):
        decode_response(json.dumps(_payload()).encode()[:-2])


def test_request_frame_binds_exact_bytes_and_rejects_trailing_content() -> None:
    pdf = b"%PDF-synthetic"
    request = WorkerRequest(
        protocol_version=WORKER_PROTOCOL_VERSION,
        request_nonce="a" * 32,
        project_id="project",
        role=DocumentRole.REDACTED,
        input_sha256=sha256(pdf).hexdigest(),
        byte_count=len(pdf),
    )

    assert decode_request(encode_request(request, pdf)) == (request, pdf)
    with pytest.raises(ValueError, match="body binding"):
        decode_request(encode_request(request, pdf) + b"trailing")
