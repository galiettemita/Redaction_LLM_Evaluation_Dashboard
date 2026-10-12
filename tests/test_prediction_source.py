from __future__ import annotations

from pathlib import Path

import pytest

from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.prediction_source import (
    PredictionSourceMaterial,
    PredictionTargetObservation,
    build_prediction_source_from_material,
    derive_prediction_source,
)


def _redacted(case: str, tmp_path: Path) -> bytes:
    redacted, _ = make_synthetic_pair(case, tmp_path)
    return redacted.read_bytes()


def test_source_identity_is_pdf_derived_deterministic_and_project_scoped(
    tmp_path: Path,
) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)

    first = derive_prediction_source(pdf_bytes, project_id="project-a")
    repeated = derive_prediction_source(pdf_bytes, project_id="project-a")
    other_project = derive_prediction_source(pdf_bytes, project_id="project-b")

    assert first == repeated
    assert first.source_id != other_project.source_id
    assert first.redacted_document_version_id != other_project.redacted_document_version_id
    assert first.canonical_document.project_id == "project-a"
    assert first.canonical_document.redacted_document_version_id == (
        first.redacted_document_version_id
    )
    assert first.canonical_document.target_ids == tuple(
        target.target_id for target in first.targets
    )
    assert tuple(target.target_version for target in first.targets)


def test_changed_pdf_bytes_cannot_reuse_the_registered_source_identity(
    tmp_path: Path,
) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)
    original = derive_prediction_source(pdf_bytes, project_id="project-a")
    changed = derive_prediction_source(pdf_bytes + b"X", project_id="project-a")

    assert changed.source_sha256 != original.source_sha256
    assert changed.source_id != original.source_id
    assert changed.redacted_document_version_id != original.redacted_document_version_id


def test_hidden_selectable_text_never_enters_prediction_source(tmp_path: Path) -> None:
    source = derive_prediction_source(
        _redacted("hidden_text_layer", tmp_path), project_id="project-a"
    )

    serialized = repr(source)
    assert "SYNTHETIC_TRAP_TOKEN" not in source.canonical_document.canonical_text
    assert "SYNTHETIC_TRAP_TOKEN" not in serialized
    assert "reference" not in source.provenance.lower()
    assert ".pdf" not in serialized.lower()


@pytest.mark.parametrize("pdf_bytes", [b"", b"not-a-pdf"])
def test_malformed_or_unsupported_source_fails_closed(pdf_bytes: bytes) -> None:
    with pytest.raises(ValueError, match="supported redacted PDF"):
        derive_prediction_source(pdf_bytes, project_id="project-a")


def test_blank_project_context_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="project"):
        derive_prediction_source(_redacted("two_boxes", tmp_path), project_id=" ")


def test_caller_cannot_self_assert_a_trusted_flag(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="trusted"):
        derive_prediction_source(
            _redacted("two_boxes", tmp_path),
            project_id="project-a",
            trusted=True,  # type: ignore[call-arg]
        )


def test_worker_material_reconstructs_identical_source_without_pdf_parsing(tmp_path: Path) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)
    expected = derive_prediction_source(pdf_bytes, project_id="project-a")
    material = PredictionSourceMaterial(
        source_sha256=expected.source_sha256,
        page_count=1,
        detector_version=expected.detector_version,
        canonicalizer_version=expected.canonicalizer_version,
        canonical_text=expected.canonical_document.canonical_text,
        canonical_hash=expected.canonical_document.canonical_hash,
        targets=tuple(
            PredictionTargetObservation(
                page_index=target.page_index,
                normalized_bbox=target.normalized_bbox,
                rectangle_index=int(target.detection_evidence.source_object_ids[0].rsplit("-", 1)[1]),
            )
            for target in expected.targets
        ),
    )

    rebuilt = build_prediction_source_from_material(
        pdf_bytes, project_id="project-a", material=material
    )

    assert rebuilt == expected


def test_worker_material_has_no_authority_to_persist_itself(tmp_path: Path) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)
    source = derive_prediction_source(pdf_bytes, project_id="project-a")
    material = PredictionSourceMaterial(
        source_sha256=source.source_sha256,
        page_count=1,
        detector_version=source.detector_version,
        canonicalizer_version=source.canonicalizer_version,
        canonical_text=source.canonical_document.canonical_text,
        canonical_hash=source.canonical_document.canonical_hash,
        targets=tuple(
            PredictionTargetObservation(
                page_index=target.page_index,
                normalized_bbox=target.normalized_bbox,
                rectangle_index=int(
                    target.detection_evidence.source_object_ids[0].rsplit("-", 1)[1]
                ),
            )
            for target in source.targets
        ),
    )

    assert not hasattr(material, "persist")
    assert not hasattr(material, "trusted")


@pytest.mark.parametrize(
    "change",
    [
        {"source_sha256": "f" * 64},
        {"page_count": 0},
        {"detector_version": "forged"},
        {"canonicalizer_version": "forged"},
        {"canonical_hash": "f" * 64},
        {"targets": ()},
    ],
)
def test_worker_material_spoofing_fails_closed(tmp_path: Path, change: dict[str, object]) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)
    source = derive_prediction_source(pdf_bytes, project_id="project-a")
    values = {
        "source_sha256": source.source_sha256,
        "page_count": 1,
        "detector_version": source.detector_version,
        "canonicalizer_version": source.canonicalizer_version,
        "canonical_text": source.canonical_document.canonical_text,
        "canonical_hash": source.canonical_document.canonical_hash,
        "targets": tuple(
            PredictionTargetObservation(
                page_index=t.page_index, normalized_bbox=t.normalized_bbox,
                rectangle_index=int(t.detection_evidence.source_object_ids[0].rsplit("-", 1)[1]),
            ) for t in source.targets
        ),
    }
    values.update(change)

    with pytest.raises(ValueError):
        build_prediction_source_from_material(
            pdf_bytes, project_id="project-a", material=PredictionSourceMaterial(**values)
        )


def test_worker_material_bridge_never_invokes_host_pdf_parsers(tmp_path: Path, monkeypatch) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)
    source = derive_prediction_source(pdf_bytes, project_id="project-a")
    material = PredictionSourceMaterial(
        source_sha256=source.source_sha256,
        page_count=1,
        detector_version=source.detector_version,
        canonicalizer_version=source.canonicalizer_version,
        canonical_text=source.canonical_document.canonical_text,
        canonical_hash=source.canonical_document.canonical_hash,
        targets=tuple(
            PredictionTargetObservation(
                page_index=t.page_index, normalized_bbox=t.normalized_bbox,
                rectangle_index=int(t.detection_evidence.source_object_ids[0].rsplit("-", 1)[1]),
            ) for t in source.targets
        ),
    )
    monkeypatch.setattr("redaction_lab.prediction_source.detect_targets", lambda *a, **k: (_ for _ in ()).throw(AssertionError("host parse")))
    monkeypatch.setattr("redaction_lab.prediction_source.canonicalize_redacted", lambda *a, **k: (_ for _ in ()).throw(AssertionError("host parse")))

    rebuilt = build_prediction_source_from_material(
        pdf_bytes, project_id="project-a", material=material
    )

    assert rebuilt == source


def test_worker_material_rejects_reused_detector_evidence_identifier(tmp_path: Path) -> None:
    pdf_bytes = _redacted("two_boxes", tmp_path)
    source = derive_prediction_source(pdf_bytes, project_id="project-a")
    observations = tuple(
        PredictionTargetObservation(
            page_index=target.page_index,
            normalized_bbox=target.normalized_bbox,
            rectangle_index=0,
        )
        for target in source.targets
    )
    material = PredictionSourceMaterial(
        source_sha256=source.source_sha256,
        page_count=1,
        detector_version=source.detector_version,
        canonicalizer_version=source.canonicalizer_version,
        canonical_text=source.canonical_document.canonical_text,
        canonical_hash=source.canonical_document.canonical_hash,
        targets=observations,
    )

    with pytest.raises(ValueError, match="evidence"):
        build_prediction_source_from_material(
            pdf_bytes, project_id="project-a", material=material
        )
