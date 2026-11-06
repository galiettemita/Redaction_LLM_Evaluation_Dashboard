from __future__ import annotations

from hashlib import sha256

import pytest

import redaction_lab.document_analysis as analysis_module
from redaction_lab.document_analysis import (
    AnalysisMethod,
    DocumentAnalysisStatus,
    analyze_redacted_document,
    analyze_reference_document,
)
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.pdf_detector import DetectionResult, DetectionStatus
from redaction_lab.raster_analysis import (
    RASTER_CANONICALIZER_VERSION,
    RASTER_DETECTOR_VERSION,
    RASTER_REFERENCE_VERSION,
    RasterRedactedAnalysis,
    RasterReferenceAnalysis,
    RasterStatus,
    RasterTargetObservation,
)


class BombOcr:
    def recognize(self, image):
        raise AssertionError("OCR must not run")


def test_supported_vector_redacted_document_never_invokes_ocr(tmp_path) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path)

    result = analyze_redacted_document(
        redacted.read_bytes(),
        project_id="vector-project",
        ocr_engine=BombOcr(),
    )

    assert result.status is DocumentAnalysisStatus.PROCESSABLE
    assert result.detector_version == "vector-text-rect-v6"
    assert result.canonicalizer_version == "safe-visible-text-v1"
    assert {target.analysis_method for target in result.targets} == {
        AnalysisMethod.VECTOR
    }


def test_supported_vector_reference_never_invokes_ocr(tmp_path) -> None:
    _, reference = make_synthetic_pair("two_boxes", tmp_path)

    result = analyze_reference_document(
        reference.read_bytes(),
        project_id="vector-project",
        ocr_engine=BombOcr(),
    )

    assert result.status is DocumentAnalysisStatus.PROCESSABLE
    assert result.reference_canonicalizer_version == "safe-exact-visible-text-v1"
    assert result.reference_text is not None


@pytest.mark.parametrize(
    "reason_code",
    ("IMAGE_OR_ANNOTATION_CONTENT", "NONDEFAULT_PAGE_BOUNDARY", "NO_VISIBLE_TEXT"),
)
def test_only_explicit_scan_dispositions_route_to_raster(
    monkeypatch: pytest.MonkeyPatch, reason_code: str
) -> None:
    source = b"synthetic-raster-pdf"
    detection = DetectionResult(
        status=DetectionStatus.UNSUPPORTED,
        targets=(),
        source_sha256=sha256(source).hexdigest(),
        page_count=1,
        project_id="raster-project",
        redacted_document_version_id="worker-preflight",
        reason_code=reason_code,
    )
    monkeypatch.setattr(analysis_module, "detect_targets", lambda *args, **kwargs: detection)

    def raster(pdf_bytes, *, ocr_engine, marker_id, renderer=None):
        observation = RasterTargetObservation(0, (0.1, 0.2, 0.3, 0.4), 0)
        target_id = marker_id(observation)
        text = f"Visible [[TARGET:{target_id}]] context"
        return RasterRedactedAnalysis(
            status=RasterStatus.SUPPORTED,
            page_count=1,
            targets=(observation,),
            canonical_text=text,
            canonical_hash=sha256(text.encode()).hexdigest(),
        )

    monkeypatch.setattr(analysis_module, "analyze_redacted_scan", raster)

    result = analyze_redacted_document(
        source,
        project_id="raster-project",
        ocr_engine=BombOcr(),
    )

    assert result.status is DocumentAnalysisStatus.PROCESSABLE
    assert result.detector_version == RASTER_DETECTOR_VERSION
    assert result.canonicalizer_version == RASTER_CANONICALIZER_VERSION
    assert result.targets[0].analysis_method is AnalysisMethod.RASTER
    assert result.canonical_text is not None
    assert result.canonical_text.count(f"[[TARGET:{result.targets[0].target_id}]]") == 1


def test_security_disposition_never_falls_through_to_raster(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = b"synthetic-unsafe-pdf"
    detection = DetectionResult(
        status=DetectionStatus.UNSUPPORTED,
        targets=(),
        source_sha256=sha256(source).hexdigest(),
        page_count=1,
        project_id="project",
        redacted_document_version_id="worker-preflight",
        reason_code="COMPLEX_PAGE_GRAPHICS",
    )
    monkeypatch.setattr(analysis_module, "detect_targets", lambda *args, **kwargs: detection)
    monkeypatch.setattr(
        analysis_module,
        "analyze_redacted_scan",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("raster fallback")),
    )

    result = analyze_redacted_document(
        source,
        project_id="project",
        ocr_engine=BombOcr(),
    )

    assert result.status is DocumentAnalysisStatus.UNSUPPORTED
    assert result.reason_code == "COMPLEX_PAGE_GRAPHICS"


def test_reference_raster_failure_maps_without_prediction_material(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = b"synthetic-reference-scan"
    detection = DetectionResult(
        status=DetectionStatus.UNSUPPORTED,
        targets=(),
        source_sha256=sha256(source).hexdigest(),
        page_count=1,
        project_id="project",
        redacted_document_version_id="worker-reference",
        reason_code="IMAGE_OR_ANNOTATION_CONTENT",
    )
    monkeypatch.setattr(analysis_module, "detect_targets", lambda *args, **kwargs: detection)
    monkeypatch.setattr(
        analysis_module,
        "analyze_reference_scan",
        lambda *args, **kwargs: RasterReferenceAnalysis(
            status=RasterStatus.UNSUPPORTED,
            page_count=1,
            reason_code="REFERENCE_PARTIALLY_HIDDEN",
        ),
    )

    result = analyze_reference_document(
        source,
        project_id="project",
        ocr_engine=BombOcr(),
    )

    assert result.status is DocumentAnalysisStatus.UNSUPPORTED
    assert result.reason_code == "REFERENCE_PARTIALLY_HIDDEN"
    assert result.reference_text is None
    assert result.reference_canonicalizer_version is None
