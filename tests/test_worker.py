from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
import sqlite3

import pytest

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.contracts import AttemptStatus, PredictionManifest, TokenUsage
from redaction_lab.store import RunStore
from redaction_lab.worker import run_pending_once


NOW = datetime(2026, 10, 9, tzinfo=UTC)
HASH_A = "a" * 64


def _manifest(**overrides: object) -> PredictionManifest:
    values: dict[str, object] = {
        "manifest_id": "manifest-001",
        "manifest_version": "prediction-manifest-v1",
        "project_id": "project-001",
        "run_id": "run-001",
        "target_id": "target-001",
        "target_version": "target-v1",
        "canonical_document_version_id": "canonical-v1",
        "canonical_document_hash": HASH_A,
        "canonical_redacted_text": "Visible [[TARGET:target-001]] context.",
        "target_marker": "[[TARGET:target-001]]",
        "other_redaction_markers": (),
        "prompt_id": "prompt-001",
        "prompt_version": "prompt-v1",
        "model_id": "local-model",
        "settings": {"temperature": 0},
    }
    values.update(overrides)
    return PredictionManifest.model_validate(values)


class MockAdapter(PredictionAdapter):
    model_config_id = "mock-config-v1"

    def __init__(
        self,
        status: AttemptStatus = AttemptStatus.SUCCEEDED,
        *,
        delay: float = 0,
    ) -> None:
        self.status = status
        self.delay = delay
        self.calls = 0

    def request_hash(self, manifest: PredictionManifest) -> str:
        return sha256(
            (manifest.model_dump_json() + self.model_config_id).encode()
        ).hexdigest()

    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        request_hash = self.request_hash(manifest)
        prediction = "Agent Cedar" if self.status is AttemptStatus.SUCCEEDED else None
        response_hash = (
            sha256(b"Agent Cedar").hexdigest()
            if self.status is AttemptStatus.SUCCEEDED
            else None
        )
        return PredictionResponse(
            status=self.status,
            request_hash=request_hash,
            response_hash=response_hash,
            prediction=prediction,
            usage=TokenUsage(input_tokens=8, output_tokens=2, total_tokens=10),
            model_config_id=self.model_config_id,
            started_at=NOW,
            completed_at=NOW,
        )


class CrashingAdapter(MockAdapter):
    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        self.calls += 1
        raise RuntimeError("worker died after dispatch began")


def test_duplicate_delivery_creates_one_job_and_one_immutable_attempt(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    first_job = store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")
    duplicate_job = store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")
    adapter = MockAdapter()

    assert first_job == duplicate_job
    assert asyncio.run(run_pending_once(store, adapter)) is True
    assert asyncio.run(run_pending_once(store, adapter)) is False
    assert adapter.calls == 1
    assert len(store.attempts()) == 1
    assert store.attempts()[0].status is AttemptStatus.SUCCEEDED
    assert store.job(first_job).state == "COMPLETE"


def test_same_scope_with_changed_frozen_manifest_is_rejected(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")

    with pytest.raises(ValueError, match="frozen manifest"):
        store.enqueue(
            _manifest(canonical_redacted_text="Changed [[TARGET:target-001]] context."),
            attempt_policy="one-frozen-attempt",
        )


def test_two_concurrent_workers_claim_only_once(tmp_path) -> None:
    store_a = RunStore(tmp_path / "run.sqlite3")
    store_a.enqueue(_manifest(), attempt_policy="one-frozen-attempt")
    store_b = RunStore(tmp_path / "run.sqlite3")
    adapter = MockAdapter(delay=0.02)

    async def run_both() -> list[bool]:
        return await asyncio.gather(
            run_pending_once(store_a, adapter),
            run_pending_once(store_b, adapter),
        )

    outcomes = asyncio.run(run_both())

    assert sorted(outcomes) == [False, True]
    assert adapter.calls == 1
    assert len(store_a.attempts()) == 1


def test_restart_after_dispatch_never_retries_ambiguous_attempt(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    original = RunStore(path)
    job_id = original.enqueue(_manifest(), attempt_policy="one-frozen-attempt")
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


def test_ambiguous_timeout_persists_attempt_but_remains_in_doubt(tmp_path) -> None:
    store = RunStore(tmp_path / "run.sqlite3")
    job_id = store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")
    adapter = MockAdapter(AttemptStatus.TIMEOUT)

    assert asyncio.run(run_pending_once(store, adapter)) is True

    attempts = store.attempts()
    assert len(attempts) == 1
    assert attempts[0].status is AttemptStatus.TIMEOUT
    assert attempts[0].prediction is None
    assert store.job(job_id).state == "IN_DOUBT"
    assert asyncio.run(run_pending_once(store, adapter)) is False
    assert adapter.calls == 1


@pytest.mark.parametrize(
    "status",
    [AttemptStatus.REFUSED, AttemptStatus.MALFORMED, AttemptStatus.ERROR],
)
def test_non_prediction_outcomes_remain_distinct_and_terminal(
    tmp_path, status: AttemptStatus
) -> None:
    store = RunStore(tmp_path / f"{status.value}.sqlite3")
    job_id = store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")

    asyncio.run(run_pending_once(store, MockAdapter(status)))

    attempt = store.attempts()[0]
    assert attempt.status is status
    assert attempt.prediction is None
    assert store.job(job_id).state == "COMPLETE"


def test_request_and_attempt_ids_are_deterministic(tmp_path) -> None:
    manifest = _manifest()
    adapter_a = MockAdapter()
    adapter_b = MockAdapter()
    store_a = RunStore(tmp_path / "a.sqlite3")
    store_b = RunStore(tmp_path / "b.sqlite3")

    job_a = store_a.enqueue(manifest, attempt_policy="one-frozen-attempt")
    job_b = store_b.enqueue(manifest, attempt_policy="one-frozen-attempt")
    asyncio.run(run_pending_once(store_a, adapter_a))
    asyncio.run(run_pending_once(store_b, adapter_b))

    assert job_a == job_b
    assert adapter_a.request_hash(manifest) == adapter_b.request_hash(manifest)
    assert store_a.attempts()[0].attempt_id == store_b.attempts()[0].attempt_id


def test_attempt_rows_reject_update_and_delete(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")
    asyncio.run(run_pending_once(store, MockAdapter()))

    connection = sqlite3.connect(path)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE attempts SET attempt_json = '{}' ")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM attempts")
    connection.close()


def test_durable_job_intent_rejects_database_rewrite(tmp_path) -> None:
    path = tmp_path / "run.sqlite3"
    store = RunStore(path)
    store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")

    connection = sqlite3.connect(path)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute(
            "UPDATE jobs SET manifest_json = ?", ("{}",)
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM jobs")
    connection.close()


def test_completion_rejects_forged_adapter_provenance(tmp_path) -> None:
    class ForgedAdapter(MockAdapter):
        async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
            response = await super().predict(manifest)
            return PredictionResponse(
                **{
                    **response.__dict__,
                    "request_hash": "f" * 64,
                }
            )

    store = RunStore(tmp_path / "run.sqlite3")
    job_id = store.enqueue(_manifest(), attempt_policy="one-frozen-attempt")

    with pytest.raises(ValueError, match="provenance"):
        asyncio.run(run_pending_once(store, ForgedAdapter()))

    assert store.job(job_id).state == "IN_DOUBT"
    assert store.attempts() == ()
