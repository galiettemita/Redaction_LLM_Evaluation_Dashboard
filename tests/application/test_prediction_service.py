from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
import json

import pytest

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application import prediction_service
from redaction_lab.application.prediction_service import MODEL_ID, PredictionService
from redaction_lab.application.inference_runtime import (
    InferenceRuntimeUnavailable,
    VerifiedInferenceRuntime,
)
from redaction_lab.contracts import AttemptStatus, DocumentRole, PredictionManifest, TokenUsage
from redaction_lab.pdf_detector import DETECTOR_VERSION
from redaction_lab.canonical import CANONICALIZER_VERSION
from redaction_lab.prediction_source import (
    PredictionSourceMaterial,
    PredictionTargetObservation,
    _source_ids,
    _target_from_observation,
    build_prediction_source_from_material,
)
from redaction_lab.store import RunStore
from redaction_lab.worker import run_job_once


NOW = datetime(2026, 10, 13, tzinfo=UTC)


class RecordingAdapter(PredictionAdapter):
    model_id = MODEL_ID
    model_config_id = "ollama-qwen-test-config"

    def __init__(self, store: RunStore, *, crash: bool = False) -> None:
        self.store = store
        self.crash = crash
        self.manifests: list[PredictionManifest] = []

    def request_hash(self, manifest: PredictionManifest) -> str:
        return sha256((manifest.manifest_id + self.model_config_id).encode()).hexdigest()

    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        assert len(self.store.jobs_for_run(manifest.run_id, project_id=manifest.project_id)) == 2
        self.manifests.append(manifest)
        if self.crash:
            raise RuntimeError("simulated provider crash")
        raw = ("prediction:" + manifest.target_id).encode()
        return PredictionResponse(
            status=AttemptStatus.SUCCEEDED,
            request_hash=self.request_hash(manifest),
            response_hash=sha256(raw).hexdigest(),
            prediction=raw.decode(),
            usage=TokenUsage(input_tokens=10, output_tokens=2, total_tokens=12),
            model_config_id=self.model_config_id,
            started_at=NOW,
            completed_at=NOW,
            provider_model_id=manifest.model_id,
        )


def _verified(adapter: RecordingAdapter, digest: str = "a") -> VerifiedInferenceRuntime:
    return VerifiedInferenceRuntime(
        adapter=adapter,
        model_id=adapter.model_id,
        model_config_id=adapter.model_config_id,
        model_manifest_digest="sha256:" + digest * 64,
    )


def _ready_source(tmp_path):
    path = tmp_path / "application.sqlite3"
    app_store = ApplicationStore(path, backup_directory=tmp_path / "backups")
    pdf_bytes = b"%PDF-synthetic-worker-output-only"
    digest = sha256(pdf_bytes).hexdigest()
    upload = app_store.register_upload(
        project_id="project-service",
        role=DocumentRole.REDACTED,
        artifact_key=f"sha256/{digest[:2]}/{digest}.pdf",
        sha256=digest,
        byte_size=len(pdf_bytes),
    )
    _, redacted_version, _ = _source_ids("project-service", digest)
    observations = (
        PredictionTargetObservation(0, (0.1, 0.2, 0.3, 0.25), 0),
        PredictionTargetObservation(1, (0.2, 0.3, 0.5, 0.35), 1),
    )
    target_ids = tuple(
        _target_from_observation(
            observation,
            project_id="project-service",
            redacted_document_version_id=redacted_version,
        ).target_id
        for observation in observations
    )
    canonical_text = f"Before [[TARGET:{target_ids[0]}]] between [[TARGET:{target_ids[1]}]] after"
    material = PredictionSourceMaterial(
        source_sha256=digest,
        page_count=2,
        detector_version=DETECTOR_VERSION,
        canonicalizer_version=CANONICALIZER_VERSION,
        canonical_text=canonical_text,
        canonical_hash=sha256(canonical_text.encode()).hexdigest(),
        targets=observations,
    )
    source = build_prediction_source_from_material(
        pdf_bytes, project_id="project-service", material=material
    )
    run_store = RunStore(path)
    run_store._persist_prediction_source(
        source, pdf_bytes=pdf_bytes, project_id="project-service"
    )
    claimed = app_store.claim_next(owner="synthetic-worker", now=NOW)
    assert claimed is not None
    app_store.record_runtime(
        claimed.job_id,
        owner="synthetic-worker",
        request_nonce="a" * 32,
        protocol_version="pdf-worker-v1",
        image_digest="sha256:" + "b" * 64,
        page_count=2,
    )
    app_store.complete_job(
        claimed.job_id,
        owner="synthetic-worker",
        status=ProcessingStatus.READY,
        page_count=2,
        source_id=source.source_id,
        reason_code=None,
    )
    return app_store, run_store, upload.version_id, source


def test_service_persists_all_intents_before_target_scoped_dispatch_and_is_idempotent(
    tmp_path, monkeypatch
) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    adapter = RecordingAdapter(run_store)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda self: _verified(adapter),
    )

    service = PredictionService(app_store)
    first = asyncio.run(service.run(version_id))
    second = asyncio.run(service.run(version_id))

    assert first == second
    assert len(first) == len(source.targets) == len(adapter.manifests) == 2
    for manifest in adapter.manifests:
        assert manifest.canonical_redacted_text.count(manifest.target_marker) == 1
        assert "REFERENCE" not in manifest.canonical_redacted_text
        assert all(marker in manifest.canonical_redacted_text for marker in manifest.other_redaction_markers)
    assert len(run_store.attempts()) == 2


def test_service_crash_leaves_in_doubt_and_resume_never_retries_claimed_attempt(
    tmp_path, monkeypatch
) -> None:
    app_store, run_store, version_id, _ = _ready_source(tmp_path)
    adapter = RecordingAdapter(run_store, crash=True)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda self: _verified(adapter),
    )
    service = PredictionService(app_store)

    with pytest.raises(RuntimeError, match="provider crash"):
        asyncio.run(service.run(version_id))
    in_doubt = service.results(version_id)
    adapter.crash = False
    asyncio.run(service.run(version_id))

    _, run = service._stored_run(version_id)
    assert run is not None
    jobs = run_store.jobs_for_run(run.run_id, project_id="project-service")
    assert in_doubt[0]["attempt_status"] == "IN_DOUBT"
    assert in_doubt[0]["prediction"] is None
    assert len(adapter.manifests) == 2
    assert [job.state for job in jobs].count("IN_DOUBT") == 1
    assert [job.state for job in jobs].count("COMPLETE") == 1


def test_explicit_resume_repairs_partial_intent_set_and_dispatches_only_pending(tmp_path, monkeypatch) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    service = PredictionService(app_store)
    source_id, run = service._run_definition(
        version_id,
        model_config_id="ollama-qwen-test-config",
        model_manifest_digest="sha256:" + "a" * 64,
    )
    first_job = run_store.enqueue(source_id, source.targets[0].target_id, run)
    adapter = RecordingAdapter(run_store)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda self: _verified(adapter),
    )

    repaired = asyncio.run(service.run(version_id))

    assert repaired[0] == first_job
    assert len(repaired) == len(source.targets) == 2
    assert len(adapter.manifests) == 2
    assert [job.manifest.target_id for job in run_store.jobs_for_run(
        run.run_id, project_id=run.project_id
    )] == [target.target_id for target in source.targets]


def test_results_revalidate_project_source_and_attempt_provenance(tmp_path, monkeypatch) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    adapter = RecordingAdapter(run_store)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda self: _verified(adapter),
    )
    service = PredictionService(app_store)
    asyncio.run(service.run(version_id))

    results = service.results(version_id)

    assert [item["target_id"] for item in results] == [target.target_id for target in source.targets]
    assert all(item["attempt_status"] == "SUCCEEDED" for item in results)
    assert all(item["prediction"].startswith("prediction:") for item in results)
    with pytest.raises(ValueError, match="project"):
        run_store.jobs_for_source(source.source_id, project_id="other-project")


def test_results_ignore_other_authentic_task4_run_for_same_source(tmp_path, monkeypatch) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    adapter = RecordingAdapter(run_store)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda self: _verified(adapter),
    )
    service = PredictionService(app_store)
    asyncio.run(service.run(version_id))
    _, service_run = service._stored_run(version_id)
    assert service_run is not None
    legacy = service_run.model_copy(
        update={"run_id": "run-legacy-task4", "created_by": "legacy-task4-worker"}
    )
    legacy_jobs = tuple(
        run_store.enqueue(source.source_id, target.target_id, legacy)
        for target in source.targets
    )
    for legacy_job in legacy_jobs:
        asyncio.run(run_job_once(run_store, adapter, legacy_job))

    results = service.results(version_id)

    assert len(results) == len(source.targets) == 2
    legacy_attempts = {run_store.job(job_id).attempt_id for job_id in legacy_jobs}
    assert all(item["attempt_id"] not in legacy_attempts for item in results)


def test_run_identity_changes_with_model_digest_or_configuration(tmp_path) -> None:
    app_store, _, version_id, _ = _ready_source(tmp_path)
    service = PredictionService(app_store)
    _, first = service._run_definition(
        version_id,
        model_config_id="config-a",
        model_manifest_digest="sha256:" + "a" * 64,
    )
    _, changed_digest = service._run_definition(
        version_id,
        model_config_id="config-a",
        model_manifest_digest="sha256:" + "b" * 64,
    )
    _, changed_config = service._run_definition(
        version_id,
        model_config_id="config-b",
        model_manifest_digest="sha256:" + "a" * 64,
    )

    assert len({first.run_id, changed_digest.run_id, changed_config.run_id}) == 3
    assert "model_manifest_digest" in first.created_by
    assert "model_config_id" in first.created_by


def test_consistently_substituted_runtime_fails_before_any_intent_mutation(
    tmp_path, monkeypatch
) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    rejected_adapter = RecordingAdapter(run_store)
    rejected_adapter.model_id = "substituted-model"

    class RejectedRuntime:
        adapter = rejected_adapter
        model_id = "substituted-model"
        model_config_id = "substituted-config"
        model_manifest_digest = "sha256:" + "c" * 64
        closed = False

        def close(self):
            self.closed = True

    rejected = RejectedRuntime()
    approved = _verified(RecordingAdapter(run_store))
    runtimes = iter((rejected, approved))
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda self: next(runtimes),
    )
    service = PredictionService(app_store)

    with pytest.raises(InferenceRuntimeUnavailable, match="approved model"):
        asyncio.run(service.run(version_id))

    assert rejected.closed is True
    assert run_store.runs_for_source(
        source.source_id, project_id=source.project_id
    ) == ()
    assert asyncio.run(service.run(version_id))


@pytest.mark.parametrize(
    ("name", "changed"),
    [
        ("RUN_VERSION", "run-v-next"),
        ("MODEL_ID", "changed-model"),
        ("EXPERIMENT_CONDITION", "changed-condition"),
        ("COMMON_CONTEXT_BUDGET", 65_536),
        ("CONTEXT_POLICY", "changed-policy"),
        ("PROMPT_ID", "changed-prompt"),
        ("PROMPT_VERSION", "prompt-v-next"),
        ("SETTINGS", {"temperature": 0.1}),
        ("ATTEMPT_POLICY", "changed-attempt-policy"),
        ("TOOL_PERMISSIONS", ("changed-tool",)),
        ("BUDGET_LABEL", "changed-budget"),
        ("SERVICE_ID", "application-prediction-service-next"),
    ],
)
def test_run_identity_changes_with_every_frozen_semantic(
    tmp_path, monkeypatch, name, changed
) -> None:
    app_store, _, version_id, _ = _ready_source(tmp_path)
    service = PredictionService(app_store)
    _, first = service._run_definition(
        version_id,
        model_config_id="config-a",
        model_manifest_digest="sha256:" + "a" * 64,
    )

    monkeypatch.setattr(prediction_service, name, changed, raising=False)
    _, second = PredictionService(app_store)._run_definition(
        version_id,
        model_config_id="config-a",
        model_manifest_digest="sha256:" + "a" * 64,
    )

    assert second.run_id != first.run_id


def test_identical_run_intent_is_stable_across_service_restart(tmp_path) -> None:
    app_store, _, version_id, _ = _ready_source(tmp_path)
    arguments = {
        "model_config_id": "config-a",
        "model_manifest_digest": "sha256:" + "a" * 64,
    }

    _, first = PredictionService(app_store)._run_definition(version_id, **arguments)
    _, restarted = PredictionService(app_store)._run_definition(version_id, **arguments)

    assert restarted.run_id == first.run_id
    assert restarted == first


@pytest.mark.parametrize(
    ("run_version", "service_id"),
    [
        ("run-v0.2", "application-prediction-service-v0.2"),
        ("run-v0.3", "application-prediction-service-v0.3"),
    ],
)
def test_legacy_branch_only_run_identity_is_rejected_without_rewrite(
    tmp_path, run_version, service_id
) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    service = PredictionService(app_store)
    _, current = service._run_definition(
        version_id,
        model_config_id="config-a",
        model_manifest_digest="sha256:" + "a" * 64,
    )
    old_values = [
        source.source_id,
        source.canonical_document.canonical_hash,
        source.target_versions,
        MODEL_ID,
        "redaction-reconstruction-json",
        "prompt-v1",
        {"temperature": 0},
        "config-a",
        "sha256:" + "a" * 64,
    ]
    encoded = json.dumps(
        old_values, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    legacy = current.model_copy(
        update={
            "run_id": "run-" + sha256(encoded).hexdigest(),
            "run_version": run_version,
            "created_by": json.dumps(
                {
                    "model_config_id": "config-a",
                    "model_manifest_digest": "sha256:" + "a" * 64,
                    "service": service_id,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
    )
    run_store.enqueue(source.source_id, source.targets[0].target_id, legacy)

    with pytest.raises(ValueError, match="legacy prediction"):
        service._stored_run(version_id)

    stored = run_store.runs_for_source(
        source.source_id, project_id=source.project_id
    )
    assert stored == (legacy,)


def test_run_identity_binds_canonical_and_ordered_target_provenance(
    tmp_path, monkeypatch
) -> None:
    app_store, _, version_id, source = _ready_source(tmp_path)
    service = PredictionService(app_store)
    arguments = {
        "model_config_id": "config-a",
        "model_manifest_digest": "sha256:" + "a" * 64,
    }
    _, baseline = service._run_definition(version_id, **arguments)
    canonical = source.canonical_document
    changed_target = source.targets[0].model_copy(
        update={"target_version": source.targets[0].target_version + "-next"}
    )
    variants = (
        replace(
            source,
            canonical_document=canonical.model_copy(
                update={"canonical_document_version_id": "canonical-changed"}
            ),
        ),
        replace(
            source,
            canonical_document=canonical.model_copy(
                update={"canonical_hash": "b" * 64}
            ),
        ),
        replace(source, targets=tuple(reversed(source.targets))),
        replace(source, targets=(changed_target, source.targets[1])),
    )

    observed = []
    for variant in variants:
        monkeypatch.setattr(service.runs, "source", lambda _source_id, value=variant: value)
        _, changed = service._run_definition(version_id, **arguments)
        observed.append(changed.run_id)

    assert len(set(observed + [baseline.run_id])) == len(variants) + 1
