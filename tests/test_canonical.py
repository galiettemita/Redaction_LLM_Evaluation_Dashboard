from __future__ import annotations

import inspect
from io import BytesIO
import logging
from dataclasses import replace
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

import redaction_lab.canonical as canonical_module
from redaction_lab.canonical import canonicalize_redacted
from redaction_lab.contracts import PredictionManifest, PredictionSettings
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.pdf_detector import DetectionStatus, detect_targets


PROJECT_ID = "project-rl-mvp-002"
DOCUMENT_VERSION_ID = "redacted-document-v1"
CANONICAL_VERSION_ID = "canonical-redacted-v1"


def _detect(pdf_bytes: bytes):
    return detect_targets(
        pdf_bytes,
        project_id=PROJECT_ID,
        redacted_document_version_id=DOCUMENT_VERSION_ID,
    )


def _canonicalize(pdf_bytes: bytes, detection):
    return canonicalize_redacted(
        pdf_bytes,
        detection,
        project_id=PROJECT_ID,
        redacted_document_version_id=DOCUMENT_VERSION_ID,
        canonical_document_version_id=CANONICAL_VERSION_ID,
    )


def _pdf_bytes(draw) -> bytes:
    output = BytesIO()
    canvas = Canvas(output, pagesize=letter, invariant=1, pageCompression=0)
    draw(canvas)
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def test_hidden_overlay_text_never_in_canonical_or_manifest(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    redacted, _ = make_synthetic_pair("hidden_text_layer", tmp_path)
    pdf_bytes = redacted.read_bytes()

    with caplog.at_level(logging.DEBUG):
        detection = _detect(pdf_bytes)
        canonical = _canonicalize(pdf_bytes, detection)

    target = detection.targets[0]
    marker = f"[[TARGET:{target.target_id}]]"
    manifest = PredictionManifest(
        manifest_id="manifest-001",
        manifest_version="manifest-v1",
        project_id=PROJECT_ID,
        run_id="run-001",
        target_id=target.target_id,
        target_version=target.target_version,
        canonical_document_version_id=canonical.canonical_document_version_id,
        canonical_document_hash=canonical.canonical_hash,
        canonical_redacted_text=canonical.canonical_text,
        target_marker=marker,
        prompt_id="prompt-001",
        prompt_version="prompt-v1",
        model_id="synthetic-model",
        settings=PredictionSettings(temperature=0.0),
    )
    serialized = manifest.model_dump_json()

    assert detection.status is DetectionStatus.SUPPORTED
    assert "SYNTHETIC_TRAP_TOKEN" not in canonical.canonical_text
    assert "SYNTHETIC_TRAP_TOKEN" not in serialized
    assert "SYNTHETIC_TRAP_TOKEN" not in caplog.text
    assert canonical.canonical_text.count(marker) == 1


def test_one_marker_per_target_and_visible_reading_order_preserved(
    tmp_path: Path,
) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path)
    pdf_bytes = redacted.read_bytes()
    detection = _detect(pdf_bytes)

    canonical = _canonicalize(pdf_bytes, detection)

    assert canonical.target_ids == tuple(
        target.target_id for target in detection.targets
    )
    markers = [f"[[TARGET:{target_id}]]" for target_id in canonical.target_ids]
    assert all(canonical.canonical_text.count(marker) == 1 for marker in markers)
    assert canonical.canonical_text.index(
        "The synthetic courier was"
    ) < canonical.canonical_text.index(markers[0])
    assert canonical.canonical_text.index(markers[0]) < canonical.canonical_text.index(
        "at 09:00."
    )
    assert canonical.canonical_text.index("at 09:00.") < canonical.canonical_text.index(
        "The synthetic package contained"
    )
    assert canonical.canonical_text.index(
        "The synthetic package contained"
    ) < canonical.canonical_text.index(markers[1])
    assert f"was {markers[0]} at 09:00." in canonical.canonical_text
    assert f"contained {markers[1]}" in canonical.canonical_text
    assert "Agent Cedar" not in canonical.canonical_text
    assert "12 paper stars" not in canonical.canonical_text


def test_tall_supported_rectangle_keeps_marker_in_sentence_order() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(108, 680, 112, 45, stroke=0, fill=1)

    pdf_bytes = _pdf_bytes(draw)
    detection = _detect(pdf_bytes)
    canonical = _canonicalize(pdf_bytes, detection)
    marker = f"[[TARGET:{detection.targets[0].target_id}]]"

    assert detection.status is DetectionStatus.SUPPORTED
    assert f"Visible {marker} after" in canonical.canonical_text


def test_positioned_words_preserve_a_visible_word_boundary() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible")
        canvas.drawString(115, 700, "context")

    pdf_bytes = _pdf_bytes(draw)
    detection = _detect(pdf_bytes)
    canonical = _canonicalize(pdf_bytes, detection)

    assert detection.status is DetectionStatus.NO_REDACTIONS
    assert canonical.canonical_text == "Visible context"


def test_adjacent_targets_receive_distinct_markers(tmp_path: Path) -> None:
    redacted, _ = make_synthetic_pair("adjacent_boxes", tmp_path)
    pdf_bytes = redacted.read_bytes()
    detection = _detect(pdf_bytes)

    canonical = _canonicalize(pdf_bytes, detection)

    assert len(detection.targets) == 2
    assert len(canonical.target_ids) == 2
    first_marker = f"[[TARGET:{canonical.target_ids[0]}]]"
    second_marker = f"[[TARGET:{canonical.target_ids[1]}]]"
    assert first_marker != second_marker
    assert canonical.canonical_text.index(
        first_marker
    ) < canonical.canonical_text.index(second_marker)
    assert "ALPHA" not in canonical.canonical_text
    assert "BRAVO" not in canonical.canonical_text


def test_canonicalization_rejects_unsupported_detection() -> None:
    detection = _detect(b"malformed synthetic bytes")

    with pytest.raises(ValueError, match="unsupported detection") as error:
        _canonicalize(b"malformed synthetic bytes", detection)

    assert "malformed synthetic bytes" not in str(error.value)


def test_canonicalization_rejects_detection_for_other_source(tmp_path: Path) -> None:
    first, _ = make_synthetic_pair("two_boxes", tmp_path / "first")
    second, _ = make_synthetic_pair("adjacent_boxes", tmp_path / "second")
    detection = _detect(first.read_bytes())

    with pytest.raises(ValueError, match="source hash mismatch"):
        _canonicalize(second.read_bytes(), detection)


def test_canonicalization_rejects_detection_from_other_project(tmp_path: Path) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path)
    pdf_bytes = redacted.read_bytes()
    detection = _detect(pdf_bytes)

    with pytest.raises(ValueError, match="detection identity mismatch"):
        _canonicalize(pdf_bytes, replace(detection, project_id="other-project"))


def test_canonicalization_rejects_forged_target_geometry(tmp_path: Path) -> None:
    redacted, _ = make_synthetic_pair("hidden_text_layer", tmp_path)
    pdf_bytes = redacted.read_bytes()
    detection = _detect(pdf_bytes)
    target = detection.targets[0]
    forged_target = target.model_copy(
        update={"normalized_bbox": (0.01, 0.01, 0.02, 0.02)}
    )
    forged_detection = replace(detection, targets=(forged_target,))

    with pytest.raises(ValueError, match="detection verification mismatch"):
        _canonicalize(pdf_bytes, forged_detection)


def test_canonicalization_sanitizes_extraction_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path)
    pdf_bytes = redacted.read_bytes()
    detection = _detect(pdf_bytes)

    def unsafe_extractor(*_args, **_kwargs):
        raise ValueError("SYNTHETIC_TRAP_TOKEN")

    monkeypatch.setattr(canonical_module, "_page_text", unsafe_extractor)

    with pytest.raises(ValueError, match="canonical PDF parse failed") as error:
        _canonicalize(pdf_bytes, detection)

    assert "SYNTHETIC_TRAP_TOKEN" not in str(error.value)


def test_canonicalizer_has_no_reference_input() -> None:
    parameter_names = set(inspect.signature(canonicalize_redacted).parameters)

    assert parameter_names == {
        "pdf_bytes",
        "detection",
        "project_id",
        "redacted_document_version_id",
        "canonical_document_version_id",
    }
    assert all("reference" not in name for name in parameter_names)
