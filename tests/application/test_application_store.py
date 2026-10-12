from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

import pytest

from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.contracts import DocumentRole
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.store import RunStore


def _store(tmp_path: Path) -> ApplicationStore:
    return ApplicationStore(tmp_path / "app.sqlite3", backup_directory=tmp_path / "backups")


def test_register_upload_is_deterministic_and_role_scoped(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first = store.register_upload(
        project_id="project-a", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=12,
    )
    repeated = store.register_upload(
        project_id="project-a", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=12,
    )
    reference = store.register_upload(
        project_id="project-a", role=DocumentRole.REFERENCE,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=12,
    )

    assert first == repeated
    assert first.version_id != reference.version_id
    assert first.job_id != reference.job_id
    assert store.get_job(first.job_id).status is ProcessingStatus.ACCEPTED


def test_identical_artifact_is_independently_project_scoped(tmp_path: Path) -> None:
    store = _store(tmp_path)
    values = {
        "role": DocumentRole.REDACTED,
        "artifact_key": "sha256/aa/" + "a" * 64 + ".pdf",
        "sha256": "a" * 64,
        "byte_size": 12,
    }

    first = store.register_upload(project_id="project-a", **values)
    second = store.register_upload(project_id="project-b", **values)

    assert first.document_id != second.document_id
    assert first.version_id != second.version_id


def test_one_processing_job_is_claimed_across_store_instances(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    first = ApplicationStore(path, backup_directory=tmp_path / "backups")
    second = ApplicationStore(path, backup_directory=tmp_path / "backups")
    for digest in ("a" * 64, "b" * 64):
        first.register_upload(
            project_id="project", role=DocumentRole.REDACTED,
            artifact_key=f"sha256/{digest[:2]}/{digest}.pdf", sha256=digest, byte_size=10,
        )

    claimed = first.claim_next(owner="worker-a", now=datetime.now(UTC))

    assert claimed is not None
    assert second.claim_next(owner="worker-b", now=datetime.now(UTC)) is None


def test_completion_reconciles_version_and_survives_reopen(tmp_path: Path) -> None:
    store = _store(tmp_path)
    upload = store.register_upload(
        project_id="project", role=DocumentRole.REFERENCE,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=10,
    )
    claimed = store.claim_next(owner="worker", now=datetime.now(UTC))
    assert claimed and claimed.job_id == upload.job_id
    store.record_runtime(
        claimed.job_id, owner="worker", request_nonce="1" * 32,
        protocol_version="pdf-worker-v1", image_digest="sha256:" + "b" * 64,
        page_count=2,
    )
    store.complete_job(
        claimed.job_id, owner="worker", status=ProcessingStatus.READY,
        page_count=2, source_id=None, reason_code=None,
    )

    reopened = _store(tmp_path)
    assert reopened.get_job(claimed.job_id).status is ProcessingStatus.READY
    version = reopened.get_version(upload.version_id)
    assert version.page_count == 2
    assert version.source_id is None


def test_runtime_evidence_is_single_assignment_and_unknown_page_count_is_null(tmp_path: Path) -> None:
    store = _store(tmp_path)
    upload = store.register_upload(
        project_id="project", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=10,
    )
    job = store.claim_next(owner="worker", now=datetime.now(UTC))
    assert job
    store.record_runtime(
        job.job_id, owner="worker", request_nonce="a" * 32,
        protocol_version="pdf-worker-v1", image_digest="sha256:" + "b" * 64,
        page_count=0,
    )

    assert store.get_job(upload.job_id).page_count is None
    with pytest.raises(sqlite3.IntegrityError, match="transition"):
        store.record_runtime(
            job.job_id, owner="worker", request_nonce="c" * 32,
            protocol_version="pdf-worker-v1", image_digest="sha256:" + "d" * 64,
            page_count=1,
        )


def test_restart_recovery_fails_interrupted_job_without_reprocessing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    upload = store.register_upload(
        project_id="project", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=10,
    )
    old = datetime.now(UTC) - timedelta(minutes=2)
    assert store.claim_next(owner="dead-worker", now=old)

    recovered = store.recover_interrupted(now=datetime.now(UTC))

    assert recovered == (upload.job_id,)
    job = store.get_job(upload.job_id)
    assert job.status is ProcessingStatus.FAILED
    assert job.reason_code == "INTERRUPTED"


def test_restart_reconciles_already_committed_task4_source_without_reparsing(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    store = ApplicationStore(path, backup_directory=tmp_path / "backups")
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    pdf_bytes = redacted.read_bytes()
    digest = __import__("hashlib").sha256(pdf_bytes).hexdigest()
    upload = store.register_upload(
        project_id="project", role=DocumentRole.REDACTED,
        artifact_key=f"sha256/{digest[:2]}/{digest}.pdf", sha256=digest,
        byte_size=len(pdf_bytes),
    )
    job = store.claim_next(owner="dead-worker", now=datetime.now(UTC))
    assert job
    store.record_runtime(
        job.job_id, owner="dead-worker", request_nonce="a" * 32,
        protocol_version="pdf-worker-v1", image_digest="sha256:" + "b" * 64,
        page_count=1,
    )
    source_id = RunStore(path).ingest_redacted_pdf(pdf_bytes, project_id="project")

    assert store.recover_interrupted(now=datetime.now(UTC)) == (upload.job_id,)

    recovered = store.get_job(upload.job_id)
    assert recovered.status is ProcessingStatus.READY
    assert recovered.source_id == source_id


def test_identity_rows_and_terminal_jobs_are_immutable(tmp_path: Path) -> None:
    store = _store(tmp_path)
    upload = store.register_upload(
        project_id="project", role=DocumentRole.REFERENCE,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=10,
    )
    job = store.claim_next(owner="worker", now=datetime.now(UTC))
    assert job
    store.complete_job(job.job_id, owner="worker", status=ProcessingStatus.UNSUPPORTED,
                       page_count=None, source_id=None, reason_code="ENCRYPTED")
    with sqlite3.connect(store.path) as connection:
        for sql in (
            "UPDATE documents SET project_id='other'",
            "DELETE FROM document_versions",
            "UPDATE application_jobs SET status='ACCEPTED'",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql)


def test_database_rejects_ready_redacted_job_without_task4_source(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.register_upload(
        project_id="project", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=10,
    )
    job = store.claim_next(owner="worker", now=datetime.now(UTC))
    assert job

    with store.connect() as connection, pytest.raises(sqlite3.IntegrityError, match="transition"):
        connection.execute(
            "UPDATE application_jobs SET status='READY', updated_at=? WHERE job_id=?",
            (datetime.now(UTC).isoformat(), job.job_id),
        )


def test_store_rejects_fictional_task4_source_binding(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.register_upload(
        project_id="project", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf", sha256="a" * 64, byte_size=10,
    )
    job = store.claim_next(owner="worker", now=datetime.now(UTC))
    assert job

    with pytest.raises(ValueError, match="Task-4 source"):
        store.complete_job(
            job.job_id, owner="worker", status=ProcessingStatus.READY,
            page_count=1, source_id="fictional-source", reason_code=None,
        )
