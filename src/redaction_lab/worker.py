"""One-shot durable prediction worker."""

from __future__ import annotations

from redaction_lab.adapters.base import PredictionAdapter
from redaction_lab.contracts import ModelAttempt
from redaction_lab.store import RunStore


async def run_pending_once(store: RunStore, adapter: PredictionAdapter) -> bool:
    """Claim and dispatch at most one job, with no automatic retry path."""

    pending = store.next_pending()
    if pending is None:
        return False

    request_hash = adapter.request_hash(pending.manifest)
    attempt_id = store.claim(
        pending.job_id,
        request_hash=request_hash,
        model_config_id=adapter.model_config_id,
    )
    if attempt_id is None:
        return False

    response = await adapter.predict(pending.manifest)
    if (
        response.request_hash != request_hash
        or response.model_config_id != adapter.model_config_id
    ):
        raise ValueError("adapter response provenance mismatch")

    attempt = ModelAttempt(
        attempt_id=attempt_id,
        project_id=pending.manifest.project_id,
        run_id=pending.manifest.run_id,
        target_id=pending.manifest.target_id,
        target_version=pending.manifest.target_version,
        model_id=pending.manifest.model_id,
        model_config_id=response.model_config_id,
        request_hash=response.request_hash,
        response_hash=response.response_hash,
        prediction=response.prediction,
        status=response.status,
        usage=response.usage,
        started_at=response.started_at,
        completed_at=response.completed_at,
    )
    store.complete(pending.job_id, attempt)
    return True
