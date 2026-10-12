from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.document_worker import DocumentWorker
from redaction_lab.application.isolation import VerifiedWorkerResult
from redaction_lab.application.upload_service import UploadService
from redaction_lab.application.worker_protocol import WorkerResponse
from redaction_lab.canonical import CANONICALIZER_VERSION
from redaction_lab.contracts import DocumentRole
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.pdf_detector import DETECTOR_VERSION
from redaction_lab.prediction_source import derive_prediction_source


class SyntheticWorker:
    image_digest = "sha256:" + "1" * 64

    def process(self, pdf_bytes: bytes, *, project_id: str, role: DocumentRole) -> VerifiedWorkerResult:
        if role is DocumentRole.REFERENCE:
            response = WorkerResponse(
                protocol_version="pdf-worker-v1", request_nonce="a" * 32,
                project_id=project_id, role=role, input_sha256=__import__("hashlib").sha256(pdf_bytes).hexdigest(),
                status="PROCESSABLE", page_count=1, targets=(),
            )
        else:
            source = derive_prediction_source(pdf_bytes, project_id=project_id)
            observations = tuple(
                {"page_index": target.page_index, "normalized_bbox": target.normalized_bbox,
                 "rectangle_index": int(target.detection_evidence.source_object_ids[0].rsplit("-", 1)[1])}
                for target in source.targets
            )
            response = WorkerResponse(
                protocol_version="pdf-worker-v1", request_nonce="a" * 32,
                project_id=project_id, role=role, input_sha256=source.source_sha256,
                status="PROCESSABLE", page_count=1,
                detector_version=DETECTOR_VERSION, canonicalizer_version=CANONICALIZER_VERSION,
                canonical_text=source.canonical_document.canonical_text,
                canonical_hash=source.canonical_document.canonical_hash,
                targets=observations,
            )
        return VerifiedWorkerResult(response=response, image_digest=self.image_digest)


def test_redacted_job_persists_worker_derived_task4_source_without_enqueue(tmp_path: Path) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    artifacts = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    app_store = ApplicationStore(tmp_path / "app.sqlite3", backup_directory=tmp_path / "backups")
    accepted = UploadService(artifacts, app_store).accept(
        project_id="project", role=DocumentRole.REDACTED, chunks=[redacted.read_bytes()]
    )

    assert DocumentWorker(app_store, artifacts, SyntheticWorker()).run_once(owner="worker") is True

    job = app_store.get_job(accepted.job_id)
    assert job.status is ProcessingStatus.READY
    assert job.source_id is not None
    with app_store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0


def test_reference_job_never_creates_task4_source(tmp_path: Path) -> None:
    _, reference = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    artifacts = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    app_store = ApplicationStore(tmp_path / "app.sqlite3", backup_directory=tmp_path / "backups")
    accepted = UploadService(artifacts, app_store).accept(
        project_id="project", role=DocumentRole.REFERENCE, chunks=[reference.read_bytes()]
    )

    DocumentWorker(app_store, artifacts, SyntheticWorker()).run_once(owner="worker")

    job = app_store.get_job(accepted.job_id)
    assert job.status is ProcessingStatus.READY
    assert job.source_id is None
    with app_store.connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='canonical_sources'"
        ).fetchone()[0] == 0
