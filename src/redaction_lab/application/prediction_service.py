"""Deterministic PDF-source to Task-4 prediction orchestration."""

from __future__ import annotations

from hashlib import sha256
import json
import re

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
SERVICE_ID = "application-prediction-service-v0.2"


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

    def _run_definition(
        self,
        version_id: str,
        *,
        model_config_id: str,
        model_manifest_digest: str,
    ) -> tuple[str, RunDefinition]:
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
                model_config_id,
                model_manifest_digest,
            ],
        )
        created_by = json.dumps(
            {
                "model_config_id": model_config_id,
                "model_manifest_digest": model_manifest_digest,
                "service": SERVICE_ID,
            },
            sort_keys=True,
            separators=(",", ":"),
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
            created_by=created_by,
            created_at=version.created_at,
        )

    @staticmethod
    def _runtime_identity(run: RunDefinition) -> tuple[str, str] | None:
        try:
            identity = json.loads(run.created_by)
        except json.JSONDecodeError:
            return None
        if (
            not isinstance(identity, dict)
            or set(identity) != {"model_config_id", "model_manifest_digest", "service"}
            or identity.get("service") != SERVICE_ID
            or not isinstance(identity.get("model_config_id"), str)
            or not isinstance(identity.get("model_manifest_digest"), str)
            or re.fullmatch(r"[A-Za-z0-9._:+-]{1,128}", identity["model_config_id"])
            is None
            or re.fullmatch(
                r"sha256:[0-9a-f]{64}", identity["model_manifest_digest"]
            )
            is None
        ):
            return None
        return identity["model_config_id"], identity["model_manifest_digest"]

    def _stored_run(self, version_id: str) -> tuple[str, RunDefinition | None]:
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
        candidates: list[RunDefinition] = []
        for run in self.runs.runs_for_source(
            version.source_id, project_id=version.project_id
        ):
            identity = self._runtime_identity(run)
            if identity is None:
                continue
            _, expected = self._run_definition(
                version_id,
                model_config_id=identity[0],
                model_manifest_digest=identity[1],
            )
            if run != expected:
                raise ValueError("stored v0.2 run identity is inconsistent")
            candidates.append(run)
        if len(candidates) > 1:
            raise ValueError("document has multiple v0.2 prediction runs")
        return version.source_id, candidates[0] if candidates else None

    async def run(self, version_id: str) -> tuple[str, ...]:
        source_id, run = self._stored_run(version_id)
        existing = (
            self.runs.jobs_for_run(run.run_id, project_id=run.project_id)
            if run is not None
            else ()
        )
        if existing and all(job.state != "PENDING" for job in existing):
            return tuple(job.job_id for job in existing)

        verified = InferenceRuntime().verified()
        try:
            if run is None:
                source_id, run = self._run_definition(
                    version_id,
                    model_config_id=verified.model_config_id,
                    model_manifest_digest=verified.model_manifest_digest,
                )
            elif self._runtime_identity(run) != (
                verified.model_config_id,
                verified.model_manifest_digest,
            ):
                raise ValueError("qualified runtime does not match the frozen run")

            source = self.runs.source(source_id)
            observed = {job.manifest.target_id for job in existing}
            expected = {target.target_id for target in source.targets}
            if not observed <= expected:
                raise ValueError("run contains an unexpected target intent")
            for target in source.targets:
                if target.target_id not in observed:
                    self.runs.enqueue(source_id, target.target_id, run)
            jobs = self.runs.jobs_for_run(run.run_id, project_id=run.project_id)
            for job in jobs:
                if job.state == "PENDING":
                    await run_job_once(self.runs, verified.adapter, job.job_id)
            return tuple(job.job_id for job in jobs)
        finally:
            verified.close()

    def results(self, version_id: str) -> tuple[dict[str, object], ...]:
        version = self.store.get_version(version_id)
        source_id, run = self._stored_run(version_id)
        if run is None:
            return ()
        source = self.runs.source(source_id)
        jobs = self.runs.jobs_for_run(run.run_id, project_id=version.project_id)
        identity = self._runtime_identity(run)
        if identity is None:
            raise ValueError("stored v0.2 run identity is unavailable")
        targets = {target.target_id: target for target in source.targets}
        values: list[dict[str, object]] = []
        for job in jobs:
            if job.attempt_id is None:
                continue
            if job.model_config_id != identity[0] or job.request_hash is None:
                raise ValueError("attempt does not match frozen runtime identity")
            try:
                resolved = self.runs.resolve_attempt(
                    job.attempt_id, project_id=version.project_id
                )
            except KeyError:
                if job.state != "IN_DOUBT":
                    raise
                attempt = None
                target_id = job.manifest.target_id
            else:
                if resolved.run != run or resolved.source.source_id != source_id:
                    raise ValueError("attempt does not belong to the v0.2 run")
                attempt = resolved.attempt
                target_id = attempt.target_id
            target = targets[target_id]
            values.append(
                {
                    "target_id": target.target_id,
                    "target_version": target.target_version,
                    "page_index": target.page_index,
                    "normalized_bbox": list(target.normalized_bbox),
                    "attempt_id": attempt.attempt_id if attempt else job.attempt_id,
                    "attempt_status": attempt.status.value if attempt else "IN_DOUBT",
                    "prediction": attempt.prediction if attempt else None,
                    "model_id": attempt.model_id if attempt else job.manifest.model_id,
                    "provider_model_id": attempt.provider_model_id if attempt else None,
                    "model_config_id": attempt.model_config_id if attempt else job.model_config_id,
                    "request_hash": attempt.request_hash if attempt else job.request_hash,
                    "response_hash": attempt.response_hash if attempt else None,
                }
            )
        return tuple(values)
