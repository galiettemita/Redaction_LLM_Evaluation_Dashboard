"""Strict framed protocol shared by the host and isolated PDF worker image."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import re
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
from redaction_lab.contracts import DocumentRole
from redaction_lab.canonical import CANONICALIZER_VERSION
from redaction_lab.document_analysis import (
    AnalysisMethod,
    DocumentAnalysisStatus,
    analyze_redacted_document,
    analyze_reference_document,
)
from redaction_lab.pdf_detector import DETECTOR_VERSION, _suppress_parser_debug_logs
from redaction_lab.prediction_source import (
    PredictionSourceMaterial,
    PredictionTargetObservation,
)
from redaction_lab.raster_analysis import (
    RASTER_CANONICALIZER_VERSION,
    RASTER_DETECTOR_VERSION,
    RASTER_REFERENCE_VERSION,
)


WORKER_PROTOCOL_VERSION = "pdf-worker-v3"
REFERENCE_CANONICALIZER_VERSION = "safe-exact-visible-text-v1"
REFERENCE_CANONICALIZER_VERSIONS = frozenset(
    {REFERENCE_CANONICALIZER_VERSION, RASTER_REFERENCE_VERSION}
)
MAX_HEADER_BYTES = 4096
MAX_RESPONSE_BYTES = MAX_WORKER_RESPONSE_BYTES
_TARGET_MARKER = re.compile(r"\[\[TARGET:([^\]]+)\]\]")
_ANALYSIS_METHOD_BY_VERSION = {
    (DETECTOR_VERSION, CANONICALIZER_VERSION): AnalysisMethod.VECTOR,
    (RASTER_DETECTOR_VERSION, RASTER_CANONICALIZER_VERSION): AnalysisMethod.RASTER,
}


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
    target_id: Annotated[str, Field(pattern=r"^target-[A-Za-z0-9_-]{1,128}$")]
    analysis_method: AnalysisMethod
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
    reference_text: str | None = None
    reference_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    reference_canonicalizer_version: Annotated[str, Field(min_length=1)] | None = None
    targets: tuple[WorkerTargetObservation, ...] = ()
    reason_code: Annotated[str, Field(pattern=r"^[A-Z0-9_]{1,64}$")] | None = None

    @model_validator(mode="after")
    def validate_disposition(self):
        if self.protocol_version != WORKER_PROTOCOL_VERSION:
            raise ValueError("unsupported worker protocol version")
        if len(self.targets) > MAX_TARGETS:
            raise ValueError("worker target count exceeds limit")
        reference_fields = (self.reference_text, self.reference_hash, self.reference_canonicalizer_version)
        if self.status != WorkerStatus.PROCESSABLE or self.role is not DocumentRole.REFERENCE:
            if any(value is not None for value in reference_fields):
                raise ValueError("reference evidence is only valid for processable reference responses")
        elif any(value is None for value in reference_fields):
            raise ValueError("processable reference response requires complete reference material")
        else:
            assert self.reference_text is not None
            if len(self.reference_text.encode("utf-8")) > MAX_CANONICAL_TEXT_BYTES:
                raise ValueError("reference text exceeds limit")
            if sha256(self.reference_text.encode("utf-8")).hexdigest() != self.reference_hash:
                raise ValueError("reference canonical hash mismatch")
            if self.reference_canonicalizer_version not in REFERENCE_CANONICALIZER_VERSIONS:
                raise ValueError("unsupported reference canonicalizer")
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
                expected_method = _ANALYSIS_METHOD_BY_VERSION.get(
                    (self.detector_version, self.canonicalizer_version)
                )
                if (
                    expected_method is None
                    or any(target.analysis_method is not expected_method for target in self.targets)
                    or sha256(self.canonical_text.encode("utf-8")).hexdigest()
                    != self.canonical_hash
                    or tuple(_TARGET_MARKER.findall(self.canonical_text))
                    != tuple(target.target_id for target in self.targets)
                ):
                    raise ValueError("redacted analysis provenance mismatch")
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
        with _suppress_parser_debug_logs():
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
        analysis = analyze_reference_document(pdf_bytes, project_id=request.project_id)
        if analysis.status is not DocumentAnalysisStatus.PROCESSABLE:
            return WorkerResponse(
                **_base(
                    request,
                    status=WorkerStatus(analysis.status.value),
                    page_count=analysis.page_count,
                    reason_code=analysis.reason_code or "REFERENCE_EXTRACTION_FAILED",
                )
            )
        assert analysis.reference_text is not None
        assert analysis.reference_hash is not None
        assert analysis.reference_canonicalizer_version is not None
        if len(analysis.reference_text.encode("utf-8")) > MAX_CANONICAL_TEXT_BYTES:
            return WorkerResponse(**_base(request, status=WorkerStatus.UNSUPPORTED,
                                          page_count=page_count, reason_code="REFERENCE_TEXT_LIMIT"))
        return WorkerResponse(
            **_base(request, status=WorkerStatus.PROCESSABLE, page_count=analysis.page_count),
            reference_text=analysis.reference_text,
            reference_hash=analysis.reference_hash,
            reference_canonicalizer_version=analysis.reference_canonicalizer_version,
        )

    analysis = analyze_redacted_document(pdf_bytes, project_id=request.project_id)
    if analysis.status is not DocumentAnalysisStatus.PROCESSABLE:
        return WorkerResponse(
            **_base(
                request,
                status=WorkerStatus(analysis.status.value),
                page_count=analysis.page_count,
                reason_code=analysis.reason_code or "UNSUPPORTED_PDF",
            )
        )
    assert analysis.detector_version is not None
    assert analysis.canonicalizer_version is not None
    assert analysis.canonical_text is not None
    assert analysis.canonical_hash is not None
    return WorkerResponse(
        **_base(request, status=WorkerStatus.PROCESSABLE, page_count=analysis.page_count),
        detector_version=analysis.detector_version,
        canonicalizer_version=analysis.canonicalizer_version,
        canonical_text=analysis.canonical_text,
        canonical_hash=analysis.canonical_hash,
        targets=tuple(
            WorkerTargetObservation(
                target_id=target.target_id,
                analysis_method=target.analysis_method,
                page_index=target.page_index,
                normalized_bbox=target.normalized_bbox,
                rectangle_index=target.rectangle_index,
            )
            for target in analysis.targets
        ),
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
