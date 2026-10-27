"""Deterministic PDF-source to Task-4 prediction orchestration."""

from __future__ import annotations

from hashlib import sha256
import json

from redaction_lab.application.application_store import (
    ApplicationStore,
    ProcessingStatus,
)
from redaction_lab.application.inference_runtime import InferenceRuntime
from redaction_lab.contracts import AttemptStatus, DocumentRole, RunDefinition
from redaction_lab.store import RunStore, StoredJob
from redaction_lab.worker import run_job_once


MODEL_ID = "qwen2.5:1.5b-instruct-q4_K_M"
PROMPT_ID = "redaction-reconstruction-json"
PROMPT_VERSION = "prompt-v1"
RUN_VERSION = "run-v0.2"
COMMON_CONTEXT_BUDGET = 131_072


def _identity(prefix: str, values: object) -> str:
    encoded = json.dumps(
        values, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return f"{prefix}-{sha256(encoded).hexdigest()}"


class PredictionService:
    """Application-owned orchestration; public callers provide only a version ID."""

    def __init__(self, store: ApplicationStore) -> None:
        self.store = store
        self.runs = RunStore(store.path)

    def _run_definition(self, version_id: str) -> tuple[str, RunDefinition]:
        version = self.store.get_version(version_id)
        if (
            version.role is not DocumentRole.REDACTED
            or version.processing_state is not ProcessingStatus.READY
            or version.source_id is None
        ):
            raise ValueError("prediction requires an authentic ready redacted source")
        source = self.runs.source(version.source_id)
        if source.project_id != version.project_id or source.source_sha256 != version.sha256:
            raise ValueError("document and prediction source provenance mismatch")
        run_id = _identity(
            "run",
            [
                source.source_id,
                source.canonical_document.canonical_hash,
                source.target_versions,
                MODEL_ID,
                PROMPT_ID,
                PROMPT_VERSION,
                {"temperature": 0},
            ],
        )
        return source.source_id, RunDefinition(
            run_id=run_id,
            run_version=RUN_VERSION,
            project_id=version.project_id,
            target_versions=source.target_versions,
            model_ids=(MODEL_ID,),
            experiment_condition="redacted-document-only",
            canonical_document_version_id=source.canonical_document.canonical_document_version_id,
            canonical_document_hash=source.canonical_document.canonical_hash,
            common_context_budget=COMMON_CONTEXT_BUDGET,
            context_policy="common-full-document",
            prompt_id=PROMPT_ID,
            prompt_version=PROMPT_VERSION,
            settings={"temperature": 0},
            attempt_policy="one-frozen-attempt",
            tool_permissions=(),
            budget_label="zero-cost-local-experimental",
            created_by="application-prediction-service-v0.2",
            created_at=version.created_at,
        )

    async def run(self, version_id: str) -> tuple[str, ...]:
        source_id, run = self._run_definition(version_id)
        existing = self.runs.jobs_for_run(run.run_id, project_id=run.project_id)
        if existing:
            return tuple(job.job_id for job in existing)
        adapter = InferenceRuntime().verified_adapter()
        source = self.runs.source(source_id)
        job_ids = tuple(
            self.runs.enqueue(source_id, target.target_id, run)
            for target in source.targets
        )
        for job_id in job_ids:
            await run_job_once(self.runs, adapter, job_id)
        return job_ids

    def results(self, version_id: str) -> tuple[dict[str, object], ...]:
        version = self.store.get_version(version_id)
        jobs = self.runs.jobs_for_source(version.source_id, project_id=version.project_id)
        source = self.runs.source(version.source_id) if version.source_id else None
        if source is None:
            return ()
        targets = {target.target_id: target for target in source.targets}
        values: list[dict[str, object]] = []
        for job in jobs:
            if job.attempt_id is None:
                continue
            resolved = self.runs.resolve_attempt(job.attempt_id, project_id=version.project_id)
            attempt = resolved.attempt
            target = targets[attempt.target_id]
            status = "IN_DOUBT" if job.state == "IN_DOUBT" else attempt.status.value
            values.append(
                {
                    "target_id": target.target_id,
                    "target_version": target.target_version,
                    "page_index": target.page_index,
                    "normalized_bbox": list(target.normalized_bbox),
                    "attempt_id": attempt.attempt_id,
                    "attempt_status": status,
                    "prediction": attempt.prediction,
                    "model_id": attempt.model_id,
                    "provider_model_id": attempt.provider_model_id,
                    "model_config_id": attempt.model_config_id,
                    "request_hash": attempt.request_hash,
                    "response_hash": attempt.response_hash,
                }
            )
        return tuple(values)
