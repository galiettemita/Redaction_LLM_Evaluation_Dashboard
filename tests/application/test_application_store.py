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


def test_accepted_reference_does_not_starve_later_redacted_work(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    first_redacted = store.register_upload(
        project_id="project-a", role=DocumentRole.REDACTED,
        artifact_key="sha256/aa/" + "a" * 64 + ".pdf",
        sha256="a" * 64, byte_size=10,
    )
    first_reference = store.register_upload(
        project_id="project-a", role=DocumentRole.REFERENCE,
        artifact_key="sha256/bb/" + "b" * 64 + ".pdf",
        sha256="b" * 64, byte_size=10,
    )
    claimed = store.claim_next(owner="worker-a", now=datetime.now(UTC))
    assert claimed is not None and claimed.job_id == first_redacted.job_id
    store.complete_job(
        claimed.job_id, owner="worker-a", status=ProcessingStatus.UNSUPPORTED,
        page_count=None, source_id=None, reason_code="SYNTHETIC_UNSUPPORTED",
    )
    second_redacted = store.register_upload(
        project_id="project-b", role=DocumentRole.REDACTED,
        artifact_key="sha256/cc/" + "c" * 64 + ".pdf",
        sha256="c" * 64, byte_size=10,
    )
    store.register_upload(
        project_id="project-b", role=DocumentRole.REFERENCE,
        artifact_key="sha256/dd/" + "d" * 64 + ".pdf",
        sha256="d" * 64, byte_size=10,
    )

    next_job = store.claim_next(owner="worker-b", now=datetime.now(UTC))

    assert next_job is not None
    assert next_job.job_id == second_redacted.job_id
    assert next_job.role is DocumentRole.REDACTED
    assert store.get_job(first_reference.job_id).status is ProcessingStatus.ACCEPTED


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


def test_restart_recovery_fails_closed_on_ambiguous_source_profiles(tmp_path: Path) -> None:
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
        protocol_version="pdf-worker-v3", image_digest="sha256:" + "b" * 64,
        page_count=1,
    )
    RunStore(path).ingest_redacted_pdf(pdf_bytes, project_id="project")
    with store.connect() as connection:
        connection.execute(
            """INSERT INTO canonical_sources
               SELECT source_id || '-alternate', source_version, project_id,
                      source_sha256, role, redacted_document_version_id,
                      detector_version || '-alternate', canonicalizer_version || '-alternate',
                      canonical_document_version_id, canonical_hash, canonical_json,
                      targets_json, ingested_at, provenance
               FROM canonical_sources WHERE project_id='project'"""
        )

    store.recover_interrupted(now=datetime.now(UTC))

    recovered = store.get_job(upload.job_id)
    assert recovered.status is ProcessingStatus.FAILED
    assert recovered.reason_code == "INTERRUPTED"


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


def _reference_work(store, *, canonicalizer_version="safe-exact-visible-text-v1"):
    from hashlib import sha256
    from redaction_lab.application.worker_protocol import WorkerResponse, WORKER_PROTOCOL_VERSION
    upload = store.register_upload(project_id="project", role=DocumentRole.REFERENCE,
                                   artifact_key="reference.pdf", sha256="c" * 64, byte_size=12)
    job = store.claim_next(owner="worker", now=datetime.now(UTC))
    response = WorkerResponse(protocol_version=WORKER_PROTOCOL_VERSION, request_nonce="a" * 32,
                              project_id="project", role=DocumentRole.REFERENCE,
                              input_sha256="c" * 64, status="PROCESSABLE", page_count=1,
                              reference_text="isolated reference", reference_hash=sha256(b"isolated reference").hexdigest(),
                              reference_canonicalizer_version=canonicalizer_version)
    store.record_runtime(job.job_id, owner="worker", request_nonce=response.request_nonce,
                         protocol_version=response.protocol_version, image_digest="sha256:" + "d" * 64,
                         page_count=1)
    return upload, job, response


def test_reference_source_is_immutable_bound_and_recoverable_without_task4(tmp_path):
    store = _store(tmp_path)
    upload, job, response = _reference_work(store)
    assert store.reference_source(upload.version_id) is None
    source = store.record_reference_source(job.job_id, owner="worker", response=response)
    assert source.version_id == upload.version_id
    assert source.canonical_text == "isolated reference"
    assert source.provenance == "USER_SUPPLIED_EXPERIMENTAL"
    assert store.record_reference_source(job.job_id, owner="worker", response=response) == source
    assert store.recover_interrupted(now=datetime.now(UTC)) == (job.job_id,)
    reopened = _store(tmp_path)
    assert reopened.reference_source(upload.version_id) == source
    assert reopened.get_job(job.job_id).status is ProcessingStatus.READY
    assert reopened.get_version(upload.version_id).source_id is None
    with store.connect() as connection:
        assert not connection.execute("SELECT 1 FROM sqlite_master WHERE name='canonical_sources'").fetchone()
        for sql in ("UPDATE reference_sources SET canonical_text='tampered'", "DELETE FROM reference_sources"):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(sql)


def test_ocr_reference_source_is_persisted_and_reopens_under_v3(tmp_path):
    store = _store(tmp_path)
    upload, job, response = _reference_work(
        store, canonicalizer_version="ocr-reference-text-v1"
    )

    source = store.record_reference_source(job.job_id, owner="worker", response=response)
    reopened = _store(tmp_path)

    assert source.version_id == upload.version_id
    assert source.canonicalizer_version == "ocr-reference-text-v1"
    assert reopened.reference_source(upload.version_id) == source


def test_reference_source_rejects_wrong_binding_and_missing_ready_evidence(tmp_path):
    store = _store(tmp_path)
    upload, job, response = _reference_work(store)
    for field, value in (("request_nonce", "b" * 32), ("project_id", "other"),
                         ("input_sha256", "e" * 64), ("page_count", 2)):
        with pytest.raises(ValueError, match="binding"):
            store.record_reference_source(job.job_id, owner="worker", response=response.model_copy(update={field: value}))
    with pytest.raises(ValueError, match="reference source"):
        store.complete_job(job.job_id, owner="worker", status=ProcessingStatus.READY,
                           page_count=1, source_id=None, reason_code=None)
    store.recover_interrupted(now=datetime.now(UTC))
    assert store.get_job(job.job_id).status is ProcessingStatus.FAILED
    assert store.reference_source(upload.version_id) is None


def test_reference_source_read_rejects_tampering_even_after_sql_guards_removed(tmp_path):
    store = _store(tmp_path)
    upload, job, response = _reference_work(store)
    store.record_reference_source(job.job_id, owner="worker", response=response)
    with store.connect() as connection:
        connection.execute("DROP TRIGGER reference_sources_no_update")
        connection.execute("UPDATE reference_sources SET canonical_text='tampered'")
    with pytest.raises(ValueError):
        store.reference_source(upload.version_id)
    store.recover_interrupted(now=datetime.now(UTC))
    assert store.get_job(job.job_id).status is ProcessingStatus.FAILED


def test_pair_lookup_preserves_untrusted_reference_binding(tmp_path):
    store = _store(tmp_path)
    redacted = store.register_upload(project_id="project", role=DocumentRole.REDACTED,
                                     artifact_key="redacted.pdf", sha256="a" * 64, byte_size=10)
    reference = store.register_upload(project_id="project", role=DocumentRole.REFERENCE,
                                      artifact_key="reference.pdf", sha256="b" * 64, byte_size=10)
    pair = store.create_pair(project_id="project", redacted_version_id=redacted.version_id,
                              reference_version_id=reference.version_id)
    assert store.get_pair(pair.pair_id) == pair
    assert store.pairs_for_redacted(redacted.version_id) == (pair,)
    assert not pair.truth_trusted
    with pytest.raises(KeyError):
        store.get_pair("missing")


def test_reference_source_sql_replace_cannot_overwrite_committed_evidence(tmp_path):
    store = _store(tmp_path)
    _, job, response = _reference_work(store)
    store.record_reference_source(job.job_id, owner="worker", response=response)
    with store.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("INSERT OR REPLACE INTO reference_sources SELECT * FROM reference_sources")


def _paired_queue(store):
    redacted = store.register_upload(project_id='paired', role=DocumentRole.REDACTED,
        artifact_key='redacted', sha256='a'*64, byte_size=10)
    reference = store.register_upload(project_id='paired', role=DocumentRole.REFERENCE,
        artifact_key='reference', sha256='b'*64, byte_size=10)
    store.create_pair(project_id='paired', redacted_version_id=redacted.version_id, reference_version_id=reference.version_id)
    later = store.register_upload(project_id='paired', role=DocumentRole.REDACTED,
        artifact_key='later', sha256='c'*64, byte_size=10)
    return redacted, reference, later


def test_explicit_paired_reference_can_precede_later_redacted_only_after_terminal_pair(tmp_path):
    store = _store(tmp_path)
    redacted, reference, later = _paired_queue(store)
    now = datetime.now(UTC)
    assert store.claim_next(owner='worker', now=now, expected_job_id=reference.job_id) is None
    job = store.claim_next(owner='worker', now=now, expected_job_id=redacted.job_id)
    assert job.job_id == redacted.job_id
    assert store.claim_next(owner='other', now=now, expected_job_id=reference.job_id) is None
    store.complete_job(job.job_id, owner='worker', status=ProcessingStatus.NO_REDACTIONS,
        page_count=1, source_id=None, reason_code='NO_SUPPORTED_TARGETS')
    claimed = store.claim_next(owner='worker', now=now, expected_job_id=reference.job_id)
    assert claimed is not None and claimed.job_id == reference.job_id
    assert store.get_job(later.job_id).status is ProcessingStatus.ACCEPTED


def test_explicit_reference_and_normal_redacted_claim_race_has_one_winner(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    store = _store(tmp_path)
    redacted, reference, later = _paired_queue(store)
    job = store.claim_next(owner='first', now=datetime.now(UTC))
    store.complete_job(job.job_id, owner='first', status=ProcessingStatus.NO_REDACTIONS,
        page_count=1, source_id=None, reason_code='NO_SUPPORTED_TARGETS')
    barrier = Barrier(2)
    def claim(expected):
        barrier.wait()
        return store.claim_next(owner=str(expected), now=datetime.now(UTC), expected_job_id=expected)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, (reference.job_id, later.job_id)))
    assert sum(value is not None for value in claims) == 1
    assert sum(store.get_job(key).status is ProcessingStatus.PROCESSING for key in (reference.job_id, later.job_id)) == 1
