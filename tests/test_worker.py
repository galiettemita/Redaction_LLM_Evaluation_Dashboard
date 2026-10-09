from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
import json
import sqlite3
import socket
from urllib.error import URLError

import pytest

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.adapters.ollama import OllamaAdapter
from redaction_lab.contracts import (
    AttemptStatus,
    PredictionManifest,
    RunDefinition,
    TokenUsage,
)
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.store import RunStore
from redaction_lab.worker import run_pending_once


NOW = datetime(2026, 10, 9, tzinfo=UTC)


def _run(source, **overrides: object) -> RunDefinition:
    values: dict[str, object] = {
        "run_id": "run-001",
        "run_version": "run-v1",
        "project_id": source.project_id,
        "target_versions": source.target_versions,
        "model_ids": ("local-model",),
        "experiment_condition": "redacted-document-only",
        "canonical_document_version_id": (
            source.canonical_document.canonical_document_version_id
        ),
        "canonical_document_hash": source.canonical_document.canonical_hash,
        "common_context_budget": 4096,
        "context_policy": "common-full-document",
        "prompt_id": "prompt-001",
        "prompt_version": "prompt-v1",
        "settings": {"temperature": 0},
        "attempt_policy": "one-frozen-attempt",
        "tool_permissions": (),
        "budget_label": "synthetic-no-spend",
        "created_by": "trusted-test-harness",
        "created_at": NOW,
    }
    values.update(overrides)
    return RunDefinition.model_validate(values)


def _ingest(store: RunStore, tmp_path, *, project_id: str = "project-001"):
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path / project_id)
    source_id = store.ingest_redacted_pdf(
        redacted.read_bytes(), project_id=project_id
    )
    return store.source(source_id)


def _enqueue(store: RunStore, tmp_path, *, target_index: int = 0, **run_overrides):
    source = _ingest(store, tmp_path)
    run = _run(source, **run_overrides)
    job_id = store.enqueue(
        source.source_id, source.targets[target_index].target_id, run
    )
    return job_id, source, run


def _forged_manifest() -> PredictionManifest:
    text = "REFERENCE SECRET [[TARGET:forged-target]]"
    return PredictionManifest(
        manifest_id="manifest-forged",
        manifest_version="prediction-manifest-v1",
        project_id="project-001",
        run_id="run-001",
        target_id="forged-target",
        target_version="forged-version",
        canonical_document_version_id="forged-canonical",
        canonical_document_hash=sha256(text.encode()).hexdigest(),
        canonical_redacted_text=text,
        target_marker="[[TARGET:forged-target]]",
        prompt_id="prompt-001",
        prompt_version="prompt-v1",
        model_id="local-model",
        settings={"temperature": 0},
    )


class MockAdapter(PredictionAdapter):
    model_config_id = "mock-config-v1"

    def __init__(
        self,
        status: AttemptStatus = AttemptStatus.SUCCEEDED,
        *,
        delay: float = 0,
        provider_model_id: str | None = None,
    ) -> None:
        self.status = status
        self.delay = delay
        self.calls = 0
        self.provider_model_id = provider_model_id

    def request_hash(self, manifest: PredictionManifest) -> str:
        return sha256(
            (manifest.model_dump_json() + self.model_config_id).encode()
        ).hexdigest()

    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        prediction = "Agent Cedar" if self.status is AttemptStatus.SUCCEEDED else None
        response_hash = (
            sha256(b"Agent Cedar").hexdigest()
            if self.status in (AttemptStatus.SUCCEEDED, AttemptStatus.ERROR)
            else None
        )
        provider_model_id = self.provider_model_id
        if provider_model_id is None and self.status in (
            AttemptStatus.SUCCEEDED,
            AttemptStatus.REFUSED,
        ):
            provider_model_id = manifest.model_id
        return PredictionResponse(
            status=self.status,
            request_hash=self.request_hash(manifest),
            response_hash=response_hash,
            prediction=prediction,
            usage=TokenUsage(input_tokens=8, output_tokens=2, total_tokens=10),
            model_config_id=self.model_config_id,
            started_at=NOW,
            completed_at=NOW,
            provider_model_id=provider_model_id,
        )


class CrashingAdapter(MockAdapter):
    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        self.calls += 1
        raise RuntimeError("worker died after dispatch began")


def test_only_stored_pdf_source_can_enqueue_not_direct_or_forged_manifest(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    forged = _forged_manifest()

    with pytest.raises(TypeError):
        store.enqueue(forged, attempt_policy="one-frozen-attempt")  # type: ignore[call-arg]
    with pytest.raises(KeyError):
        store.enqueue("unregistered-source", "forged-target", _run(_ingest(store, tmp_path)))

    job_id, source, _ = _enqueue(store, tmp_path)
    manifest = store.job(job_id).manifest
    assert manifest.canonical_document_hash == source.canonical_document.canonical_hash
    assert "REFERENCE SECRET" not in manifest.canonical_redacted_text


def test_source_and_run_project_target_and_order_mismatches_fail_closed(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    source = _ingest(store, tmp_path, project_id="project-a")
    other = _ingest(store, tmp_path, project_id="project-b")
    assert source.source_id != other.source_id

    with pytest.raises(ValueError, match="trusted prediction source"):
        store.enqueue(source.source_id, source.targets[0].target_id, _run(source, project_id="project-b"))
    with pytest.raises(ValueError, match="trusted prediction source"):
        store.enqueue(
            source.source_id,
            source.targets[0].target_id,
            _run(source, target_versions=tuple(reversed(source.target_versions))),
        )
    with pytest.raises(ValueError, match="trusted prediction source"):
        store.enqueue(
            source.source_id,
            source.targets[0].target_id,
            _run(source, canonical_document_hash="f" * 64),
        )
    with pytest.raises(ValueError, match="trusted prediction source"):
        store.enqueue(
            source.source_id,
            source.targets[0].target_id,
            _run(source, canonical_document_version_id="forged-canonical"),
        )
    with pytest.raises(ValueError, match="trusted prediction source"):
        store.enqueue(
            source.source_id,
            source.targets[0].target_id,
            _run(source, attempt_policy="retry-on-reconnect"),
        )
    with pytest.raises(ValueError, match="registered"):
        store.enqueue(source.source_id, other.targets[0].target_id, _run(source))


def test_generated_manifest_masks_other_targets_and_has_no_hidden_channels(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    job_id, source, _ = _enqueue(store, tmp_path)
    manifest = store.job(job_id).manifest

    assert manifest.canonical_redacted_text.count(manifest.target_marker) == 1
    assert f"[[REDACTED:{source.targets[1].target_id}]]" in manifest.canonical_redacted_text
    serialized = manifest.model_dump_json().lower()
    for forbidden in ("agent cedar", "12 paper stars", "reference", "filename", "evaluation"):
        assert forbidden not in serialized


def test_duplicate_delivery_creates_one_job_and_one_immutable_attempt(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    job_id, source, run = _enqueue(store, tmp_path)
    duplicate = store.enqueue(source.source_id, source.targets[0].target_id, run)
    adapter = MockAdapter()

    assert job_id == duplicate
    assert asyncio.run(run_pending_once(store, adapter)) is True
    assert asyncio.run(run_pending_once(store, adapter)) is False
    assert adapter.calls == 1
    assert len(store.attempts()) == 1
    assert store.attempts()[0].provider_model_id == "local-model"
    assert store.job(job_id).state == "COMPLETE"


def test_same_run_with_changed_frozen_intent_is_rejected(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    _, source, run = _enqueue(store, tmp_path)

    with pytest.raises(ValueError, match="run identity"):
        store.enqueue(
            source.source_id,
            source.targets[1].target_id,
            _run(source, prompt_version="changed-prompt"),
        )


def test_two_concurrent_workers_claim_only_once(tmp_path) -> None:
    store_a = RunStore(tmp_path / "run.sqlite3")
    _enqueue(store_a, tmp_path)
    store_b = RunStore(tmp_path / "run.sqlite3")
    adapter = MockAdapter(delay=0.02)

    async def run_both() -> list[bool]:
        return await asyncio.gather(
            run_pending_once(store_a, adapter), run_pending_once(store_b, adapter)
        )

    assert sorted(asyncio.run(run_both())) == [False, True]
    assert adapter.calls == 1
    assert len(store_a.attempts()) == 1


def test_restart_after_dispatch_never_retries_ambiguous_attempt(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    original = RunStore(path)
    job_id, _, _ = _enqueue(original, tmp_path)
    crashing = CrashingAdapter()

    with pytest.raises(RuntimeError, match="died"):
        asyncio.run(run_pending_once(original, crashing))

    restarted = RunStore(path)
    replacement = MockAdapter()
    assert restarted.job(job_id).state == "IN_DOUBT"
    assert asyncio.run(run_pending_once(restarted, replacement)) is False
    assert crashing.calls == 1
    assert replacement.calls == 0
    assert restarted.attempts() == ()


def test_ambiguous_timeout_persists_attempt_but_never_retries(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    job_id, _, _ = _enqueue(store, tmp_path)
    adapter = MockAdapter(AttemptStatus.TIMEOUT)

    assert asyncio.run(run_pending_once(store, adapter)) is True
    assert store.attempts()[0].status is AttemptStatus.TIMEOUT
    assert store.job(job_id).state == "IN_DOUBT"
    assert asyncio.run(run_pending_once(RunStore(path), adapter)) is False
    assert adapter.calls == 1


def test_urllib_wrapped_timeout_stays_in_doubt_without_redispatch(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    job_id, _, _ = _enqueue(store, tmp_path)
    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="mock-config-v1",
    )
    calls = 0

    async def transport(*_: object) -> bytes:
        nonlocal calls
        calls += 1
        raise URLError(socket.timeout("wrapped provider timeout"))

    monkeypatch.setattr(adapter, "_stdlib_transport", transport)
    assert asyncio.run(run_pending_once(store, adapter)) is True
    assert store.attempts()[0].status is AttemptStatus.TIMEOUT
    assert store.job(job_id).state == "IN_DOUBT"
    assert asyncio.run(run_pending_once(RunStore(path), adapter)) is False
    assert calls == 1


@pytest.mark.parametrize(
    "status", [AttemptStatus.REFUSED, AttemptStatus.MALFORMED, AttemptStatus.ERROR]
)
def test_non_prediction_outcomes_remain_distinct_and_terminal(tmp_path, status) -> None:
    store = RunStore(tmp_path / f"{status.value}.sqlite3")
    job_id, _, _ = _enqueue(store, tmp_path / status.value)
    asyncio.run(run_pending_once(store, MockAdapter(status)))

    attempt = store.attempts()[0]
    assert attempt.status is status
    assert attempt.prediction is None
    assert store.job(job_id).state == "COMPLETE"


def test_request_job_and_attempt_ids_are_deterministic(tmp_path) -> None:
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    stores = [RunStore(tmp_path / name) for name in ("a.sqlite3", "b.sqlite3")]
    jobs = []
    manifests = []
    for store in stores:
        source_id = store.ingest_redacted_pdf(redacted.read_bytes(), project_id="project-001")
        source = store.source(source_id)
        jobs.append(store.enqueue(source_id, source.targets[0].target_id, _run(source)))
        manifests.append(store.job(jobs[-1]).manifest)
        asyncio.run(run_pending_once(store, MockAdapter()))

    assert jobs[0] == jobs[1]
    assert MockAdapter().request_hash(manifests[0]) == MockAdapter().request_hash(manifests[1])
    assert stores[0].attempts()[0].attempt_id == stores[1].attempts()[0].attempt_id


def test_source_run_manifest_attempt_and_state_are_immutable(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    job_id, _, _ = _enqueue(store, tmp_path)
    asyncio.run(run_pending_once(store, MockAdapter()))

    connection = sqlite3.connect(path)
    for sql in (
        "UPDATE canonical_sources SET canonical_json = '{}'",
        "UPDATE canonical_sources SET role = 'REFERENCE'",
        "DELETE FROM canonical_sources",
        "UPDATE jobs SET manifest_json = '{}'",
        "UPDATE jobs SET run_json = '{}'",
        "DELETE FROM jobs",
        "UPDATE attempts SET attempt_json = '{}'",
        "DELETE FROM attempts",
        "UPDATE jobs SET state='PENDING', attempt_id=NULL, request_hash=NULL, model_config_id=NULL",
    ):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(sql)
    connection.close()
    assert store.job(job_id).state == "COMPLETE"


def test_database_rejects_new_untrusted_direct_manifest_rows(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    RunStore(path)
    manifest = _forged_manifest()
    connection = sqlite3.connect(path)

    with pytest.raises(sqlite3.IntegrityError, match="trusted source binding"):
        connection.execute(
            """INSERT INTO jobs (
                job_id, scope_key, project_id, run_id, target_id,
                target_version, model_id, attempt_policy, manifest_json,
                state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)""",
            (
                "direct-forged-job", "direct-forged-scope", manifest.project_id,
                manifest.run_id, manifest.target_id, manifest.target_version,
                manifest.model_id, "one-frozen-attempt", manifest.model_dump_json(),
                NOW.isoformat(), NOW.isoformat(),
            ),
        )
    connection.close()


def test_trusted_looking_but_forged_database_job_never_reaches_adapter(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    source = _ingest(store, tmp_path)
    run = _run(source)
    forged = _forged_manifest()
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO jobs (
            job_id, scope_key, project_id, run_id, target_id, target_version,
            model_id, attempt_policy, manifest_json, source_id, run_json,
            trust_version, state, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)""",
        (
            "forged-bound-job", "forged-bound-scope", source.project_id,
            run.run_id, forged.target_id, forged.target_version, forged.model_id,
            run.attempt_policy, forged.model_dump_json(), source.source_id,
            run.model_dump_json(), "canonical-source-binding-v1", NOW.isoformat(),
            NOW.isoformat(),
        ),
    )
    connection.commit()
    connection.close()
    adapter = MockAdapter()

    with pytest.raises(ValueError, match="target"):
        asyncio.run(run_pending_once(store, adapter))
    assert adapter.calls == 0


def test_corrupted_source_is_revalidated_before_claim_and_never_dispatched(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    _enqueue(store, tmp_path)
    connection = sqlite3.connect(path)
    connection.execute("DROP TRIGGER canonical_sources_no_update")
    connection.execute("UPDATE canonical_sources SET canonical_hash = ?", ("f" * 64,))
    connection.commit()
    connection.close()
    adapter = MockAdapter()

    with pytest.raises(ValueError, match="canonical identity"):
        asyncio.run(run_pending_once(store, adapter))
    assert adapter.calls == 0


def test_legacy_pending_manifest_is_quarantined_after_migration(tmp_path) -> None:
    path = tmp_path / "legacy.sqlite3"
    manifest = _forged_manifest()
    connection = sqlite3.connect(path)
    connection.execute(
        """CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY, scope_key TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL, run_id TEXT NOT NULL, target_id TEXT NOT NULL,
            target_version TEXT NOT NULL, model_id TEXT NOT NULL,
            attempt_policy TEXT NOT NULL, manifest_json TEXT NOT NULL,
            state TEXT NOT NULL, attempt_id TEXT, request_hash TEXT,
            model_config_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )"""
    )
    connection.execute(
        """CREATE TABLE attempts (
            attempt_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL UNIQUE REFERENCES jobs(job_id),
            attempt_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    connection.execute(
        "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', NULL, NULL, NULL, ?, ?)",
        (
            "legacy-job", "legacy-scope", manifest.project_id, manifest.run_id,
            manifest.target_id, manifest.target_version, manifest.model_id,
            "one-frozen-attempt", manifest.model_dump_json(), NOW.isoformat(), NOW.isoformat(),
        ),
    )
    connection.execute(
        "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETE', ?, ?, ?, ?, ?)",
        (
            "legacy-complete", "legacy-complete-scope", manifest.project_id,
            "legacy-complete-run", manifest.target_id, manifest.target_version,
            manifest.model_id, "one-frozen-attempt", manifest.model_dump_json(),
            "legacy-attempt", "a" * 64, "legacy-config", NOW.isoformat(),
            NOW.isoformat(),
        ),
    )
    legacy_attempt = {
        "attempt_id": "legacy-attempt",
        "project_id": manifest.project_id,
        "run_id": "legacy-complete-run",
        "target_id": manifest.target_id,
        "target_version": manifest.target_version,
        "model_id": manifest.model_id,
        "model_config_id": "legacy-config",
        "request_hash": "a" * 64,
        "response_hash": "b" * 64,
        "prediction": "legacy prediction",
        "status": "SUCCEEDED",
        "usage": {},
        "started_at": NOW.isoformat(),
        "completed_at": NOW.isoformat(),
    }
    connection.execute(
        "INSERT INTO attempts VALUES (?, ?, ?, ?)",
        (
            "legacy-attempt", "legacy-complete", json.dumps(legacy_attempt),
            NOW.isoformat(),
        ),
    )
    connection.commit()
    connection.close()

    migrated = RunStore(path)
    adapter = MockAdapter()
    assert migrated.next_pending() is None
    assert asyncio.run(run_pending_once(migrated, adapter)) is False
    assert migrated.job("legacy-job").state == "PENDING"
    assert adapter.calls == 0
    assert migrated.attempts()[0].provider_model_id is None
    connection = sqlite3.connect(path)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE attempts SET attempt_json = '{}' ")
    connection.close()


def test_run_rejects_mixed_model_configuration_across_targets(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    _, source, run = _enqueue(store, tmp_path)
    second_job = store.enqueue(source.source_id, source.targets[1].target_id, run)
    assert asyncio.run(run_pending_once(store, MockAdapter())) is True

    other = MockAdapter()
    other.model_config_id = "different-config-v2"
    with pytest.raises(ValueError, match="different model configuration"):
        asyncio.run(run_pending_once(store, other))
    assert store.job(second_job).state == "PENDING"
    assert other.calls == 0


def test_provider_model_mismatch_is_persisted_as_error_with_both_ids(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    _enqueue(store, tmp_path)
    adapter = MockAdapter(
        AttemptStatus.ERROR, provider_model_id="different-provider-model"
    )

    assert asyncio.run(run_pending_once(store, adapter)) is True
    attempt = store.attempts()[0]
    assert attempt.status is AttemptStatus.ERROR
    assert attempt.model_id == "local-model"
    assert attempt.provider_model_id == "different-provider-model"
    assert attempt.prediction is None
    assert attempt.response_hash is not None


def test_completion_rejects_forged_adapter_provenance(tmp_path) -> None:
    class ForgedAdapter(MockAdapter):
        async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
            response = await super().predict(manifest)
            return PredictionResponse(**{**response.__dict__, "request_hash": "f" * 64})

    store = RunStore(tmp_path / "run.sqlite3")
    job_id, _, _ = _enqueue(store, tmp_path)
    with pytest.raises(ValueError, match="provenance"):
        asyncio.run(run_pending_once(store, ForgedAdapter()))
    assert store.job(job_id).state == "IN_DOUBT"
    assert store.attempts() == ()
