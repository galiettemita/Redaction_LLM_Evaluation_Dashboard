from __future__ import annotations

from pathlib import Path

import pytest

from redaction_lab.application.application_store import ApplicationStore
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.config import MAX_PDF_BYTES
from redaction_lab.application.upload_service import UploadService
from redaction_lab.contracts import DocumentRole


def _service(tmp_path: Path, *, limit: int = MAX_PDF_BYTES) -> UploadService:
    return UploadService(
        ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary", max_bytes=limit),
        ApplicationStore(tmp_path / "app.sqlite3", backup_directory=tmp_path / "backups"),
    )


def test_upload_accepts_bounded_pdf_without_parsing_or_retaining_filename(tmp_path: Path) -> None:
    service = _service(tmp_path)

    accepted = service.accept(
        project_id="project", role=DocumentRole.REDACTED,
        chunks=[b"%PDF-1.7\n", b"synthetic"], original_filename="private-name.pdf",
    )

    assert accepted.byte_size == len(b"%PDF-1.7\nsynthetic")
    assert "private-name" not in repr(accepted)
    assert service.store.get_job(accepted.job_id).status.value == "ACCEPTED"


def test_exact_limit_is_accepted_and_one_over_is_rejected(tmp_path: Path) -> None:
    service = _service(tmp_path, limit=16)
    service.accept(project_id="p", role=DocumentRole.REFERENCE,
                   chunks=[b"%PDF-", b"x" * 11])

    with pytest.raises(ValueError, match="size limit"):
        service.accept(project_id="p", role=DocumentRole.REFERENCE,
                       chunks=[b"%PDF-", b"x" * 12])


def test_pair_keeps_reference_separate_and_pairing_does_not_grant_truth(tmp_path: Path) -> None:
    service = _service(tmp_path)
    pair = service.accept_pair(
        project_id="project",
        redacted_chunks=[b"%PDF-redacted"],
        reference_chunks=[b"%PDF-reference"],
    )

    redacted = service.store.get_version(pair.redacted_version_id)
    reference = service.store.get_version(pair.reference_version_id)
    assert redacted.role is DocumentRole.REDACTED
    assert reference.role is DocumentRole.REFERENCE
    assert pair.truth_trusted is False
