"""Provider-neutral, redacted-only prediction adapter primitives."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json

from redaction_lab.contracts import (
    AttemptStatus,
    CanonicalRedactedDocument,
    PredictionManifest,
    RunDefinition,
    TokenUsage,
)


MANIFEST_VERSION = "prediction-manifest-v1"


@dataclass(frozen=True)
class PreparedPrediction:
    """Exact bytes and provenance hash prepared for a provider dispatch."""

    body: bytes
    request_hash: str


@dataclass(frozen=True)
class PredictionResponse:
    """Provider-neutral result; non-success states never contain a prediction."""

    status: AttemptStatus
    request_hash: str
    response_hash: str | None
    prediction: str | None
    usage: TokenUsage
    model_config_id: str
    started_at: datetime
    completed_at: datetime
    provider_model_id: str | None = None


class PredictionAdapter(ABC):
    """Reusable model-provider boundary for one immutable manifest."""

    model_config_id: str

    @abstractmethod
    def request_hash(self, manifest: PredictionManifest) -> str:
        """Return the deterministic hash persisted before dispatch."""

    @abstractmethod
    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        """Make exactly one model attempt for ``manifest``."""


def _manifest_id(values: dict[str, object]) -> str:
    encoded = json.dumps(
        values, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"manifest-{sha256(encoded).hexdigest()}"


def build_prediction_manifest(
    doc: CanonicalRedactedDocument,
    target_id: str,
    run: RunDefinition,
) -> PredictionManifest:
    """Build one frozen, full-context manifest with no reference input channel."""

    if doc.project_id != run.project_id:
        raise ValueError("document and run project mismatch")
    if sha256(doc.canonical_text.encode("utf-8")).hexdigest() != doc.canonical_hash:
        raise ValueError("canonical hash does not match canonical redacted text")
    if (
        doc.canonical_document_version_id != run.canonical_document_version_id
        or doc.canonical_hash != run.canonical_document_hash
    ):
        raise ValueError("run does not identify the frozen canonical document")
    if len(doc.target_ids) != len(set(doc.target_ids)):
        raise ValueError("canonical target IDs must be unique")
    if len(doc.target_ids) != len(run.target_versions):
        raise ValueError("run target versions must cover the canonical targets")
    if target_id not in doc.target_ids:
        raise ValueError("target is not present in the canonical document")
    if len(run.model_ids) != 1:
        raise ValueError("one manifest requires exactly one selected model")
    if run.tool_permissions:
        raise ValueError("baseline prediction manifests cannot grant tools")
    if run.experiment_condition != "redacted-document-only":
        raise ValueError("unsupported prediction experiment condition")
    if run.context_policy != "common-full-document":
        raise ValueError("unsupported prediction context policy")
    if len(doc.canonical_text.encode("utf-8")) > run.common_context_budget:
        raise ValueError("canonical redacted document exceeds common context budget")

    marker_ids: list[str] = []
    rendered = doc.canonical_text
    if doc.canonical_text.count("[[TARGET:") != len(doc.target_ids):
        raise ValueError("canonical target marker invariant failed")
    for other_target_id in doc.target_ids:
        marker = f"[[TARGET:{other_target_id}]]"
        if rendered.count(marker) != 1:
            raise ValueError("canonical target marker invariant failed")
        if other_target_id != target_id:
            rendered = rendered.replace(
                marker, f"[[REDACTED:{other_target_id}]]", 1
            )
            marker_ids.append(f"[[REDACTED:{other_target_id}]]")
    if len(rendered.encode("utf-8")) > run.common_context_budget:
        raise ValueError("rendered redacted document exceeds common context budget")

    target_index = doc.target_ids.index(target_id)
    target_marker = f"[[TARGET:{target_id}]]"
    identity: dict[str, object] = {
        "manifest_version": MANIFEST_VERSION,
        "project_id": run.project_id,
        "run_id": run.run_id,
        "target_id": target_id,
        "target_version": run.target_versions[target_index],
        "canonical_document_version_id": doc.canonical_document_version_id,
        "canonical_document_hash": doc.canonical_hash,
        "canonical_redacted_text": rendered,
        "target_marker": target_marker,
        "other_redaction_markers": marker_ids,
        "prompt_id": run.prompt_id,
        "prompt_version": run.prompt_version,
        "model_id": run.model_ids[0],
        "settings": run.settings.model_dump(mode="json"),
    }
    return PredictionManifest(
        manifest_id=_manifest_id(identity),
        manifest_version=MANIFEST_VERSION,
        project_id=run.project_id,
        run_id=run.run_id,
        target_id=target_id,
        target_version=run.target_versions[target_index],
        canonical_document_version_id=doc.canonical_document_version_id,
        canonical_document_hash=doc.canonical_hash,
        canonical_redacted_text=rendered,
        target_marker=target_marker,
        other_redaction_markers=tuple(marker_ids),
        prompt_id=run.prompt_id,
        prompt_version=run.prompt_version,
        model_id=run.model_ids[0],
        settings=run.settings,
    )
