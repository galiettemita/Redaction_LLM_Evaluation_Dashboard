from __future__ import annotations

from pathlib import Path

import pytest

from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.prediction_source import derive_prediction_source


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
