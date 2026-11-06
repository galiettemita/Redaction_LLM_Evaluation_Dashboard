"""Versioned vector/raster document analysis routing inside the PDF worker."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from redaction_lab.analysis_identity import (
    RASTER_ANALYSIS_METHOD,
    VECTOR_ANALYSIS_METHOD,
    source_ids,
    target_id,
)
from redaction_lab.canonical import CANONICALIZER_VERSION
from redaction_lab.ocr import OcrEngine, TesseractOcrEngine
from redaction_lab.pdf_detector import DETECTOR_VERSION, DetectionStatus, detect_targets
from redaction_lab.prediction_source import derive_prediction_source
from redaction_lab.raster_analysis import (
    RASTER_CANONICALIZER_VERSION,
    RASTER_DETECTOR_VERSION,
    RasterRenderer,
    RasterStatus,
    analyze_redacted_scan,
    analyze_reference_scan,
)
from redaction_lab.reference import _safe_exact_reference_text


VECTOR_REFERENCE_CANONICALIZER_VERSION = "safe-exact-visible-text-v1"
_RASTER_ELIGIBLE_REASONS = frozenset(
    {"IMAGE_OR_ANNOTATION_CONTENT", "NONDEFAULT_PAGE_BOUNDARY", "NO_VISIBLE_TEXT"}
)


class AnalysisMethod(StrEnum):
    VECTOR = VECTOR_ANALYSIS_METHOD
    RASTER = RASTER_ANALYSIS_METHOD


class DocumentAnalysisStatus(StrEnum):
    PROCESSABLE = "PROCESSABLE"
    NO_REDACTIONS = "NO_REDACTIONS"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DocumentTargetObservation:
    target_id: str
    analysis_method: AnalysisMethod
    page_index: int
    normalized_bbox: tuple[float, float, float, float]
    rectangle_index: int


@dataclass(frozen=True)
class RedactedDocumentAnalysis:
    status: DocumentAnalysisStatus
    page_count: int
    detector_version: str | None = None
    canonicalizer_version: str | None = None
    canonical_text: str | None = None
    canonical_hash: str | None = None
    targets: tuple[DocumentTargetObservation, ...] = ()
    reason_code: str | None = None


@dataclass(frozen=True)
class ReferenceDocumentAnalysis:
    status: DocumentAnalysisStatus
    page_count: int
    reference_text: str | None = None
    reference_hash: str | None = None
    reference_canonicalizer_version: str | None = None
    reason_code: str | None = None


def _disposition(reason_code: str | None) -> DocumentAnalysisStatus:
    return (
        DocumentAnalysisStatus.FAILED
        if reason_code == "MALFORMED_PDF"
        else DocumentAnalysisStatus.UNSUPPORTED
    )


def analyze_redacted_document(
    pdf_bytes: bytes,
    *,
    project_id: str,
    ocr_engine: OcrEngine | None = None,
    raster_renderer: RasterRenderer | None = None,
) -> RedactedDocumentAnalysis:
    detection = detect_targets(
        pdf_bytes,
        project_id=project_id,
        redacted_document_version_id="worker-preflight",
    )
    if detection.status is DetectionStatus.SUPPORTED:
        try:
            source = derive_prediction_source(pdf_bytes, project_id=project_id)
        except Exception:
            return RedactedDocumentAnalysis(
                status=DocumentAnalysisStatus.FAILED,
                page_count=detection.page_count,
                reason_code="DERIVATION_FAILED",
            )
        targets = []
        for target in source.targets:
            identifier = target.detection_evidence.source_object_ids[0]
            targets.append(
                DocumentTargetObservation(
                    target_id=target.target_id,
                    analysis_method=AnalysisMethod.VECTOR,
                    page_index=target.page_index,
                    normalized_bbox=target.normalized_bbox,
                    rectangle_index=int(identifier.rsplit("-", 1)[1]),
                )
            )
        return RedactedDocumentAnalysis(
            status=DocumentAnalysisStatus.PROCESSABLE,
            page_count=detection.page_count,
            detector_version=source.detector_version,
            canonicalizer_version=source.canonicalizer_version,
            canonical_text=source.canonical_document.canonical_text,
            canonical_hash=source.canonical_document.canonical_hash,
            targets=tuple(targets),
        )
    if detection.status is DetectionStatus.NO_REDACTIONS:
        return RedactedDocumentAnalysis(
            status=DocumentAnalysisStatus.NO_REDACTIONS,
            page_count=detection.page_count,
            reason_code="NO_SUPPORTED_REDACTIONS",
        )
    if detection.reason_code not in _RASTER_ELIGIBLE_REASONS:
        return RedactedDocumentAnalysis(
            status=_disposition(detection.reason_code),
            page_count=detection.page_count,
            reason_code=detection.reason_code or "UNSUPPORTED_PDF",
        )

    source_hash = sha256(pdf_bytes).hexdigest()
    _, redacted_version, _ = source_ids(
        project_id,
        source_hash,
        RASTER_DETECTOR_VERSION,
        RASTER_CANONICALIZER_VERSION,
    )

    def marker(observation) -> str:
        return target_id(
            project_id=project_id,
            redacted_document_version_id=redacted_version,
            page_index=observation.page_index,
            normalized_bbox=observation.normalized_bbox,
            detector_version=RASTER_DETECTOR_VERSION,
            analysis_method=RASTER_ANALYSIS_METHOD,
        )

    raster = analyze_redacted_scan(
        pdf_bytes,
        ocr_engine=ocr_engine or TesseractOcrEngine(),
        renderer=raster_renderer,
        marker_id=marker,
    )
    if raster.status is RasterStatus.SUPPORTED:
        return RedactedDocumentAnalysis(
            status=DocumentAnalysisStatus.PROCESSABLE,
            page_count=raster.page_count,
            detector_version=raster.detector_version,
            canonicalizer_version=raster.canonicalizer_version,
            canonical_text=raster.canonical_text,
            canonical_hash=raster.canonical_hash,
            targets=tuple(
                DocumentTargetObservation(
                    target_id=marker(observation),
                    analysis_method=AnalysisMethod.RASTER,
                    page_index=observation.page_index,
                    normalized_bbox=observation.normalized_bbox,
                    rectangle_index=observation.rectangle_index,
                )
                for observation in raster.targets
            ),
        )
    status = (
        DocumentAnalysisStatus.NO_REDACTIONS
        if raster.status is RasterStatus.NO_REDACTIONS
        else DocumentAnalysisStatus.UNSUPPORTED
    )
    return RedactedDocumentAnalysis(
        status=status,
        page_count=raster.page_count,
        reason_code=raster.reason_code,
    )


def analyze_reference_document(
    pdf_bytes: bytes,
    *,
    project_id: str,
    ocr_engine: OcrEngine | None = None,
    raster_renderer: RasterRenderer | None = None,
) -> ReferenceDocumentAnalysis:
    detection = detect_targets(
        pdf_bytes,
        project_id=project_id,
        redacted_document_version_id="worker-reference",
    )
    if detection.status is not DetectionStatus.UNSUPPORTED:
        text = _safe_exact_reference_text(pdf_bytes, detection)
        if text is None:
            return ReferenceDocumentAnalysis(
                status=DocumentAnalysisStatus.UNSUPPORTED,
                page_count=detection.page_count,
                reason_code="REFERENCE_EXTRACTION_FAILED",
            )
        return ReferenceDocumentAnalysis(
            status=DocumentAnalysisStatus.PROCESSABLE,
            page_count=detection.page_count,
            reference_text=text,
            reference_hash=sha256(text.encode()).hexdigest(),
            reference_canonicalizer_version=VECTOR_REFERENCE_CANONICALIZER_VERSION,
        )
    if detection.reason_code not in _RASTER_ELIGIBLE_REASONS:
        return ReferenceDocumentAnalysis(
            status=_disposition(detection.reason_code),
            page_count=detection.page_count,
            reason_code=detection.reason_code or "REFERENCE_EXTRACTION_FAILED",
        )
    raster = analyze_reference_scan(
        pdf_bytes,
        ocr_engine=ocr_engine or TesseractOcrEngine(),
        renderer=raster_renderer,
    )
    if raster.status is not RasterStatus.SUPPORTED:
        return ReferenceDocumentAnalysis(
            status=DocumentAnalysisStatus.UNSUPPORTED,
            page_count=raster.page_count,
            reason_code=raster.reason_code,
        )
    return ReferenceDocumentAnalysis(
        status=DocumentAnalysisStatus.PROCESSABLE,
        page_count=raster.page_count,
        reference_text=raster.reference_text,
        reference_hash=raster.reference_hash,
        reference_canonicalizer_version=raster.canonicalizer_version,
    )
