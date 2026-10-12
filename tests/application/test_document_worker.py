from __future__ import annotations

from pathlib import Path

import pytest

from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.document_worker import DocumentWorker
from redaction_lab.application.isolation import (
    NonAuthoritativePdfWorkerProbe,
    RuntimeInspection,
    RuntimePolicy,
    RuntimeUnavailable,
)
from redaction_lab.application.upload_service import UploadService
from redaction_lab.contracts import DocumentRole
from redaction_lab.fixtures import make_synthetic_pair
def test_unverified_runtime_leaves_redacted_job_accepted_and_task4_unchanged(tmp_path: Path) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    artifacts = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    app_store = ApplicationStore(tmp_path / "app.sqlite3", backup_directory=tmp_path / "backups")
    accepted = UploadService(artifacts, app_store).accept(
        project_id="project", role=DocumentRole.REDACTED, chunks=[redacted.read_bytes()]
    )

    with pytest.raises(RuntimeUnavailable, match="unverified"):
        DocumentWorker(app_store, artifacts).run_once(owner="worker")

    job = app_store.get_job(accepted.job_id)
    assert job.status is ProcessingStatus.ACCEPTED
    assert job.source_id is None
    with app_store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='canonical_sources'"
        ).fetchone()[0] == 0
        evidence = connection.execute(
            "SELECT owner, request_nonce, protocol_version, image_digest "
            "FROM application_jobs WHERE job_id = ?",
            (accepted.job_id,),
        ).fetchone()
        assert tuple(evidence) == (None, None, None, None)


def test_caller_worker_injection_is_rejected_and_cannot_mark_reference_ready(tmp_path: Path) -> None:
    _, reference = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    artifacts = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    app_store = ApplicationStore(tmp_path / "app.sqlite3", backup_directory=tmp_path / "backups")
    accepted = UploadService(artifacts, app_store).accept(
        project_id="project", role=DocumentRole.REFERENCE, chunks=[reference.read_bytes()]
    )

    policy = RuntimePolicy(
        executable="/not/podman", machine_name="probe",
        image_digest="sha256:" + "1" * 64,
    )

    class ForgedRunner:
        def inspect(self, policy):
            return RuntimeInspection(True, "probe", True, (), policy.image_digest)

        def run(self, command, *, input_bytes, timeout_seconds):
            return 0, b"{}", b""

    probe = NonAuthoritativePdfWorkerProbe(policy, ForgedRunner())
    with pytest.raises(TypeError):
        DocumentWorker(app_store, artifacts, probe)  # type: ignore[call-arg]

    job = app_store.get_job(accepted.job_id)
    assert job.status is ProcessingStatus.ACCEPTED
    assert job.source_id is None
    with app_store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='canonical_sources'"
        ).fetchone()[0] == 0
