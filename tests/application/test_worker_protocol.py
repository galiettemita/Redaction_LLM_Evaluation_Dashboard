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


def _reference_payload(**changes):
    text = "fully visible reference"
    payload = _payload(
        role="REFERENCE", detector_version=None, canonicalizer_version=None,
        canonical_text=None, canonical_hash=None, targets=[],
        reference_text=text, reference_hash=sha256(text.encode()).hexdigest(),
        reference_canonicalizer_version="safe-exact-visible-text-v1",
    )
    payload.update(changes)
    return payload


def test_v2_reference_response_requires_isolated_bounded_hashed_text() -> None:
    from redaction_lab.application.config import MAX_CANONICAL_TEXT_BYTES
    assert WORKER_PROTOCOL_VERSION == "pdf-worker-v2"
    parsed = WorkerResponse.model_validate(_reference_payload())
    assert parsed.reference_text == "fully visible reference"
    with pytest.raises(ValueError):
        parsed.to_source_material()
    for changes in (
        {"reference_text": None}, {"reference_hash": "0" * 64},
        {"reference_canonicalizer_version": ""},
        {"reference_text": "é" * (MAX_CANONICAL_TEXT_BYTES // 2 + 1)},
    ):
        with pytest.raises(ValueError):
            WorkerResponse.model_validate(_reference_payload(**changes))


def test_reference_evidence_is_forbidden_for_failures_and_redacted_roles() -> None:
    for status in ("FAILED", "UNSUPPORTED", "NO_REDACTIONS"):
        with pytest.raises(ValueError):
            WorkerResponse.model_validate(_reference_payload(status=status, reason_code="FAILURE"))
    with pytest.raises(ValueError):
        WorkerResponse.model_validate(_payload(reference_text="leak", reference_hash="a" * 64,
                                               reference_canonicalizer_version="v1"))
    with pytest.raises(ValueError):
        WorkerResponse.model_validate(_reference_payload(reference_text=None, reference_hash=None,
                                                         reference_canonicalizer_version=None))


def test_reference_worker_extracts_visible_text_and_suppresses_occluded_text(tmp_path) -> None:
    from redaction_lab.application.worker_protocol import process_request
    from redaction_lab.fixtures import make_synthetic_pair
    redacted, reference = make_synthetic_pair("two_boxes", tmp_path)
    for path, expected in ((reference, True), (redacted, False)):
        pdf = path.read_bytes()
        request = WorkerRequest(protocol_version=WORKER_PROTOCOL_VERSION, request_nonce="a" * 32,
                                project_id="project", role=DocumentRole.REFERENCE,
                                input_sha256=sha256(pdf).hexdigest(), byte_count=len(pdf))
        response = process_request(request, pdf)
        assert response.status is WorkerStatus.PROCESSABLE
        assert ("Agent Cedar" in response.reference_text) is expected
        assert response.reference_hash == sha256(response.reference_text.encode()).hexdigest()
        assert response.reference_canonicalizer_version == "safe-exact-visible-text-v1"
        assert response.canonical_text is None and not response.targets


def test_reference_extraction_excludes_pdf_annotation_contents(tmp_path):
    from io import BytesIO
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import Text
    from redaction_lab.fixtures import make_synthetic_pair
    from redaction_lab.application.worker_protocol import process_request
    _, reference = make_synthetic_pair("two_boxes", tmp_path)
    writer = PdfWriter()
    writer.append_pages_from_reader(PdfReader(reference))
    writer.add_annotation(page_number=0, annotation=Text(rect=(10, 10, 20, 20), text="ANNOTATION_SECRET"))
    output = BytesIO()
    writer.write(output)
    pdf = output.getvalue()
    request = WorkerRequest(protocol_version=WORKER_PROTOCOL_VERSION, request_nonce="a" * 32,
                            project_id="project", role=DocumentRole.REFERENCE,
                            input_sha256=sha256(pdf).hexdigest(), byte_count=len(pdf))
    response = process_request(request, pdf)
    # Existing PDF detection rejects annotation-bearing files conservatively.
    assert response.status is WorkerStatus.UNSUPPORTED
    assert response.reference_text is None
    assert response.canonical_text is None
