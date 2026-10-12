"""One-at-a-time durable document validation worker."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.isolation import VerifiedWorkerResult
from redaction_lab.application.worker_protocol import WorkerStatus
from redaction_lab.contracts import DocumentRole
from redaction_lab.prediction_source import build_prediction_source_from_material
from redaction_lab.store import RunStore


class PdfWorker(Protocol):
    def process(
        self,
        pdf_bytes: bytes,
        *,
        project_id: str,
        role: DocumentRole,
    ) -> VerifiedWorkerResult: ...


class DocumentWorker:
    def __init__(
        self,
        store: ApplicationStore,
        artifacts: ArtifactStore,
        isolated_worker: PdfWorker,
    ) -> None:
        self.store = store
        self.artifacts = artifacts
        self.isolated_worker = isolated_worker

    def run_once(self, *, owner: str) -> bool:
        job = self.store.claim_next(owner=owner, now=datetime.now(UTC))
        if job is None:
            return False
        version = self.store.get_version(job.version_id)
        try:
            pdf_bytes = self.artifacts.read(
                version.artifact_key, expected_sha256=version.sha256
            )
            verified = self.isolated_worker.process(
                pdf_bytes, project_id=job.project_id, role=job.role
            )
            response = verified.response
            self.store.record_runtime(
                job.job_id,
                owner=owner,
                request_nonce=response.request_nonce,
                protocol_version=response.protocol_version,
                image_digest=verified.image_digest,
                page_count=response.page_count,
            )
            if response.status is WorkerStatus.PROCESSABLE:
                source_id: str | None = None
                if job.role is DocumentRole.REDACTED:
                    material = response.to_source_material()

                    def source_deriver(value: bytes, *, project_id: str):
                        return build_prediction_source_from_material(
                            value, project_id=project_id, material=material
                        )

                    source_id = RunStore(
                        self.store.path, source_deriver=source_deriver
                    ).ingest_redacted_pdf(pdf_bytes, project_id=job.project_id)
                self.store.complete_job(
                    job.job_id,
                    owner=owner,
                    status=ProcessingStatus.READY,
                    page_count=response.page_count,
                    source_id=source_id,
                    reason_code=None,
                )
            else:
                status = {
                    WorkerStatus.NO_REDACTIONS: ProcessingStatus.NO_REDACTIONS,
                    WorkerStatus.UNSUPPORTED: ProcessingStatus.UNSUPPORTED,
                    WorkerStatus.FAILED: ProcessingStatus.FAILED,
                }[response.status]
                self.store.complete_job(
                    job.job_id,
                    owner=owner,
                    status=status,
                    page_count=response.page_count or None,
                    source_id=None,
                    reason_code=response.reason_code,
                )
        except Exception:
            current = self.store.get_job(job.job_id)
            if current.status is ProcessingStatus.PROCESSING:
                self.store.complete_job(
                    job.job_id,
                    owner=owner,
                    status=ProcessingStatus.FAILED,
                    page_count=None,
                    source_id=None,
                    reason_code="RUNTIME_OR_PROTOCOL_FAILURE",
                )
        return True
