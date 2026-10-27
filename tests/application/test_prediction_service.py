from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application.prediction_service import PredictionService
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


NOW = datetime(2026, 10, 13, tzinfo=UTC)


class RecordingAdapter(PredictionAdapter):
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
        "redaction_lab.application.prediction_service.InferenceRuntime.verified_adapter",
        lambda self: adapter,
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


def test_service_crash_leaves_in_doubt_and_repeated_call_never_dispatches(
    tmp_path, monkeypatch
) -> None:
    app_store, run_store, version_id, _ = _ready_source(tmp_path)
    adapter = RecordingAdapter(run_store, crash=True)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified_adapter",
        lambda self: adapter,
    )
    service = PredictionService(app_store)

    with pytest.raises(RuntimeError, match="provider crash"):
        asyncio.run(service.run(version_id))
    asyncio.run(service.run(version_id))

    jobs = run_store.jobs_for_source(
        app_store.get_version(version_id).source_id, project_id="project-service"
    )
    assert len(adapter.manifests) == 1
    assert [job.state for job in jobs].count("IN_DOUBT") == 1
    assert [job.state for job in jobs].count("PENDING") == 1


def test_duplicate_repairs_partial_intent_set_without_dispatch(tmp_path, monkeypatch) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    service = PredictionService(app_store)
    source_id, run = service._run_definition(version_id)
    first_job = run_store.enqueue(source_id, source.targets[0].target_id, run)
    adapter = RecordingAdapter(run_store)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified_adapter",
        lambda self: adapter,
    )

    repaired = asyncio.run(service.run(version_id))

    assert repaired[0] == first_job
    assert len(repaired) == len(source.targets) == 2
    assert adapter.manifests == []
    assert [job.manifest.target_id for job in run_store.jobs_for_run(
        run.run_id, project_id=run.project_id
    )] == [target.target_id for target in source.targets]


def test_results_revalidate_project_source_and_attempt_provenance(tmp_path, monkeypatch) -> None:
    app_store, run_store, version_id, source = _ready_source(tmp_path)
    adapter = RecordingAdapter(run_store)
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified_adapter",
        lambda self: adapter,
    )
    service = PredictionService(app_store)
    asyncio.run(service.run(version_id))

    results = service.results(version_id)

    assert [item["target_id"] for item in results] == [target.target_id for target in source.targets]
    assert all(item["attempt_status"] == "SUCCEEDED" for item in results)
    assert all(item["prediction"].startswith("prediction:") for item in results)
    with pytest.raises(ValueError, match="project"):
        run_store.jobs_for_source(source.source_id, project_id="other-project")
