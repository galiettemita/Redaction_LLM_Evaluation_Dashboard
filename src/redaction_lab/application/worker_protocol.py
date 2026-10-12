"""Strict framed protocol shared by the host and isolated PDF worker image."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import sys
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from pypdf import PdfReader

from redaction_lab.application.config import (
    MAX_CANONICAL_TEXT_BYTES,
    MAX_PDF_BYTES,
    MAX_PDF_PAGES,
    MAX_TARGETS,
    MAX_WORKER_RESPONSE_BYTES,
)
from redaction_lab.canonical import CANONICALIZER_VERSION
from redaction_lab.contracts import DocumentRole
from redaction_lab.pdf_detector import DETECTOR_VERSION, DetectionStatus, detect_targets
from redaction_lab.prediction_source import (
    PredictionSourceMaterial,
    PredictionTargetObservation,
    derive_prediction_source,
)


WORKER_PROTOCOL_VERSION = "pdf-worker-v1"
MAX_HEADER_BYTES = 4096
MAX_RESPONSE_BYTES = MAX_WORKER_RESPONSE_BYTES


class WorkerStatus(StrEnum):
    PROCESSABLE = "PROCESSABLE"
    NO_REDACTIONS = "NO_REDACTIONS"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkerRequest(_StrictModel):
    protocol_version: str
    request_nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    project_id: Annotated[str, Field(min_length=1)]
    role: DocumentRole
    input_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    byte_count: Annotated[int, Field(gt=0, le=MAX_PDF_BYTES)]
    max_pages: Annotated[int, Field(gt=0, le=MAX_PDF_PAGES)] = MAX_PDF_PAGES


class WorkerTargetObservation(_StrictModel):
    page_index: Annotated[int, Field(ge=0)]
    normalized_bbox: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]
    rectangle_index: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_bbox(self):
        x0, y0, x1, y1 = self.normalized_bbox
        if not all(0.0 <= value <= 1.0 for value in self.normalized_bbox) or x0 >= x1 or y0 >= y1:
            raise ValueError("invalid normalized target geometry")
        return self


class WorkerResponse(_StrictModel):
    protocol_version: str
    request_nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    project_id: Annotated[str, Field(min_length=1)]
    role: DocumentRole
    input_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    status: WorkerStatus
    page_count: Annotated[int, Field(ge=0, le=MAX_PDF_PAGES)]
    detector_version: str | None = None
    canonicalizer_version: str | None = None
    canonical_text: str | None = None
    canonical_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    targets: tuple[WorkerTargetObservation, ...] = ()
    reason_code: Annotated[str, Field(pattern=r"^[A-Z0-9_]{1,64}$")] | None = None

    @model_validator(mode="after")
    def validate_disposition(self):
        if self.protocol_version != WORKER_PROTOCOL_VERSION:
            raise ValueError("unsupported worker protocol version")
        if len(self.targets) > MAX_TARGETS:
            raise ValueError("worker target count exceeds limit")
        if self.status == WorkerStatus.PROCESSABLE:
            if self.page_count < 1 or self.reason_code is not None:
                raise ValueError("processable response has invalid disposition fields")
            if self.role is DocumentRole.REDACTED:
                if (
                    self.detector_version is None
                    or self.canonicalizer_version is None
                    or self.canonical_text is None
                    or self.canonical_hash is None
                    or not self.targets
                ):
                    raise ValueError("processable redacted response requires complete material")
                if len(self.canonical_text.encode("utf-8")) > MAX_CANONICAL_TEXT_BYTES:
                    raise ValueError("canonical text exceeds limit")
            elif any(
                value is not None
                for value in (
                    self.detector_version,
                    self.canonicalizer_version,
                    self.canonical_text,
                    self.canonical_hash,
                )
            ) or self.targets:
                raise ValueError("reference validation must not return prediction material")
        else:
            if self.reason_code is None:
                raise ValueError("non-processable response requires a reason code")
            if any(
                value is not None
                for value in (
                    self.detector_version,
                    self.canonicalizer_version,
                    self.canonical_text,
                    self.canonical_hash,
                )
            ) or self.targets:
                raise ValueError("non-processable response cannot carry derived evidence")
        return self

    def to_source_material(self) -> PredictionSourceMaterial:
        if self.status != WorkerStatus.PROCESSABLE or self.role is not DocumentRole.REDACTED:
            raise ValueError("worker response has no redacted prediction material")
        assert self.detector_version is not None
        assert self.canonicalizer_version is not None
        assert self.canonical_text is not None
        assert self.canonical_hash is not None
        return PredictionSourceMaterial(
            source_sha256=self.input_sha256,
            page_count=self.page_count,
            detector_version=self.detector_version,
            canonicalizer_version=self.canonicalizer_version,
            canonical_text=self.canonical_text,
            canonical_hash=self.canonical_hash,
            targets=tuple(
                PredictionTargetObservation(
                    page_index=target.page_index,
                    normalized_bbox=target.normalized_bbox,
                    rectangle_index=target.rectangle_index,
                )
                for target in self.targets
            ),
        )


def encode_request(request: WorkerRequest, pdf_bytes: bytes) -> bytes:
    if len(pdf_bytes) != request.byte_count or sha256(pdf_bytes).hexdigest() != request.input_sha256:
        raise ValueError("worker request does not match input bytes")
    header = request.model_dump_json().encode("utf-8")
    if len(header) > MAX_HEADER_BYTES:
        raise ValueError("worker request header exceeds limit")
    return len(header).to_bytes(4, "big") + header + pdf_bytes


def decode_request(payload: bytes) -> tuple[WorkerRequest, bytes]:
    if len(payload) < 4:
        raise ValueError("worker request frame is truncated")
    header_size = int.from_bytes(payload[:4], "big")
    if not 1 <= header_size <= MAX_HEADER_BYTES:
        raise ValueError("worker request header size is invalid")
    try:
        request = WorkerRequest.model_validate_json(payload[4 : 4 + header_size])
    except Exception as error:
        raise ValueError("invalid worker request header") from error
    pdf_bytes = payload[4 + header_size :]
    if len(pdf_bytes) != request.byte_count or sha256(pdf_bytes).hexdigest() != request.input_sha256:
        raise ValueError("worker request body binding mismatch")
    return request, pdf_bytes


def decode_response(payload: bytes) -> WorkerResponse:
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("worker response size exceeds limit")
    try:
        return WorkerResponse.model_validate_json(payload)
    except Exception as error:
        raise ValueError("invalid worker response") from error


def _base(request: WorkerRequest, *, status: str, page_count: int, reason_code: str | None = None) -> dict[str, object]:
    return {
        "protocol_version": WORKER_PROTOCOL_VERSION,
        "request_nonce": request.request_nonce,
        "project_id": request.project_id,
        "role": request.role,
        "input_sha256": request.input_sha256,
        "status": status,
        "page_count": page_count,
        "reason_code": reason_code,
    }


def process_request(request: WorkerRequest, pdf_bytes: bytes) -> WorkerResponse:
    """Execute only inside the isolated worker runtime."""

    if request.protocol_version != WORKER_PROTOCOL_VERSION:
        raise ValueError("unsupported worker protocol")
    if len(pdf_bytes) != request.byte_count or sha256(pdf_bytes).hexdigest() != request.input_sha256:
        raise ValueError("worker request binding mismatch")
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=True)
        if reader.is_encrypted:
            return WorkerResponse(**_base(request, status=WorkerStatus.UNSUPPORTED, page_count=0, reason_code="ENCRYPTED"))
        page_count = len(reader.pages)
    except Exception:
        return WorkerResponse(**_base(request, status=WorkerStatus.FAILED, page_count=0, reason_code="MALFORMED_PDF"))
    if page_count == 0:
        return WorkerResponse(**_base(request, status=WorkerStatus.FAILED, page_count=0, reason_code="EMPTY_PDF"))
    if page_count > request.max_pages:
        return WorkerResponse(**_base(request, status=WorkerStatus.UNSUPPORTED, page_count=0, reason_code="PAGE_LIMIT"))
    if request.role is DocumentRole.REFERENCE:
        return WorkerResponse(**_base(request, status=WorkerStatus.PROCESSABLE, page_count=page_count))

    detection = detect_targets(
        pdf_bytes,
        project_id=request.project_id,
        redacted_document_version_id="worker-preflight",
    )
    if detection.status is DetectionStatus.NO_REDACTIONS:
        return WorkerResponse(**_base(request, status=WorkerStatus.NO_REDACTIONS, page_count=page_count, reason_code="NO_SUPPORTED_REDACTIONS"))
    if detection.status is DetectionStatus.UNSUPPORTED:
        status = WorkerStatus.FAILED if detection.reason_code == "MALFORMED_PDF" else WorkerStatus.UNSUPPORTED
        return WorkerResponse(**_base(request, status=status, page_count=page_count, reason_code=detection.reason_code or "UNSUPPORTED_PDF"))
    try:
        source = derive_prediction_source(pdf_bytes, project_id=request.project_id)
    except Exception:
        return WorkerResponse(**_base(request, status=WorkerStatus.FAILED, page_count=page_count, reason_code="DERIVATION_FAILED"))
    observations = []
    for target in source.targets:
        identifier = target.detection_evidence.source_object_ids[0]
        observations.append(
            WorkerTargetObservation(
                page_index=target.page_index,
                normalized_bbox=target.normalized_bbox,
                rectangle_index=int(identifier.rsplit("-", 1)[1]),
            )
        )
    return WorkerResponse(
        **_base(request, status=WorkerStatus.PROCESSABLE, page_count=page_count),
        detector_version=DETECTOR_VERSION,
        canonicalizer_version=CANONICALIZER_VERSION,
        canonical_text=source.canonical_document.canonical_text,
        canonical_hash=source.canonical_document.canonical_hash,
        targets=tuple(observations),
    )


def main() -> int:
    try:
        request, pdf_bytes = decode_request(sys.stdin.buffer.read(MAX_PDF_BYTES + MAX_HEADER_BYTES + 5))
        response = process_request(request, pdf_bytes)
        output = response.model_dump_json().encode("utf-8")
        if len(output) > MAX_RESPONSE_BYTES:
            raise ValueError("worker response exceeds limit")
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
