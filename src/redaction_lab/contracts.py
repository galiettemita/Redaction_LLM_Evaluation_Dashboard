"""Versioned, immutable records shared by the Redaction Lab MVP."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
UnitScore = Annotated[float, Field(ge=0.0, le=1.0)]


class FrozenRecord(BaseModel):
    """Base settings for records that must not silently change shape."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class DocumentRole(StrEnum):
    REDACTED = "REDACTED"
    REFERENCE = "REFERENCE"


class ScopeStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


class ReferenceStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    ABSENT = "ABSENT"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"
    UNREADABLE = "UNREADABLE"
    CONFLICTING = "CONFLICTING"


class AttemptStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    REFUSED = "REFUSED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    MALFORMED = "MALFORMED"


class EvaluationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    EXPERIMENTAL = "EXPERIMENTAL"
    UNKNOWN = "UNKNOWN"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DocumentVersion(FrozenRecord):
    document_id: str
    version_id: str
    project_id: str
    sha256: Sha256
    role: DocumentRole
    media_type: str = "application/pdf"
    created_at: datetime
    provenance: str
    access_policy: str
    derivative_ids: tuple[str, ...] = ()


class RedactionTarget(FrozenRecord):
    target_id: str
    target_version: str
    redacted_document_version_id: str
    page_index: Annotated[int, Field(ge=0)]
    normalized_bbox: tuple[float, float, float, float]
    visible_context_locator: str
    scope_status: ScopeStatus
    detection_method: str
    detection_evidence: dict[str, Any] = Field(default_factory=dict)
    detector_version: str

    @model_validator(mode="after")
    def validate_normalized_bbox(self) -> RedactionTarget:
        x0, y0, x1, y1 = self.normalized_bbox
        if not all(0.0 <= coordinate <= 1.0 for coordinate in self.normalized_bbox):
            raise ValueError("normalized_bbox coordinates must be between 0 and 1")
        if x0 >= x1 or y0 >= y1:
            raise ValueError("normalized_bbox must have positive width and height")
        return self


class ReferenceMapping(FrozenRecord):
    mapping_id: str
    mapping_version: str
    target_id: str
    target_version: str
    reference_document_version_id: str | None
    status: ReferenceStatus
    exact_revealed_text: str | None = None
    reference_token_locator: str | None = None
    redacted_canonical_hash: Sha256 | None = None
    reference_canonical_hash: Sha256 | None = None
    global_alignment_version: str | None = None
    left_anchor_evidence: tuple[str, ...] = ()
    right_anchor_evidence: tuple[str, ...] = ()
    mapping_method_version: str
    provenance: str

    @model_validator(mode="after")
    def enforce_truth_availability(self) -> ReferenceMapping:
        if self.status is ReferenceStatus.CONFIRMED:
            if not self.exact_revealed_text:
                raise ValueError("confirmed mappings require exact revealed text")
        elif self.exact_revealed_text is not None:
            raise ValueError("unconfirmed mappings must not expose revealed text")
        return self


class CanonicalRedactedDocument(FrozenRecord):
    canonical_document_version_id: str
    redacted_document_version_id: str
    canonical_hash: Sha256
    canonical_text: str
    target_ids: tuple[str, ...]
    canonicalizer_version: str


class RunDefinition(FrozenRecord):
    run_id: str
    run_version: str
    target_versions: tuple[str, ...]
    model_ids: tuple[str, ...]
    experiment_condition: str
    canonical_document_version_id: str
    canonical_document_hash: Sha256
    common_context_budget: Annotated[int, Field(gt=0)]
    context_policy: str
    prompt_id: str
    prompt_version: str
    settings: dict[str, Any] = Field(default_factory=dict)
    attempt_policy: str
    tool_permissions: tuple[str, ...] = ()
    budget_label: str
    created_by: str
    created_at: datetime


class PredictionManifest(FrozenRecord):
    """The complete redacted-only payload available to a prediction adapter."""

    manifest_id: str
    manifest_version: str
    run_id: str
    target_id: str
    target_version: str
    canonical_document_version_id: str
    canonical_document_hash: Sha256
    canonical_redacted_text: str
    target_marker: str
    other_redaction_markers: tuple[str, ...] = ()
    prompt_id: str
    prompt_version: str
    model_id: str
    settings: dict[str, Any] = Field(default_factory=dict)


class ModelAttempt(FrozenRecord):
    attempt_id: str
    run_id: str
    target_id: str
    target_version: str
    model_id: str
    model_config_id: str
    request_hash: Sha256
    response_hash: Sha256 | None = None
    prediction: str | None = None
    status: AttemptStatus
    usage: dict[str, int | float] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime

    @model_validator(mode="after")
    def enforce_success_payload(self) -> ModelAttempt:
        if self.status is AttemptStatus.SUCCEEDED:
            if not self.prediction or self.response_hash is None:
                raise ValueError("successful attempts require prediction and response hash")
        elif self.prediction is not None:
            raise ValueError("non-success attempts must not contain a prediction")
        return self


class EvaluationRecord(FrozenRecord):
    evaluation_id: str
    evaluation_version: str
    attempt_id: str
    mapping_id: str | None
    mapping_version: str | None
    evaluator_version: str
    rubric_version: str
    status: EvaluationStatus
    verified_score: UnitScore | None = None
    experimental_score: UnitScore | None = None
    fact_comparisons: tuple[dict[str, Any], ...] = ()
    contradictions: tuple[str, ...] = ()
    explanation: str
    created_at: datetime

    @model_validator(mode="after")
    def enforce_score_channel(self) -> EvaluationRecord:
        if self.status is EvaluationStatus.UNKNOWN:
            if self.verified_score is not None or self.experimental_score is not None:
                raise ValueError("unknown evaluations must have null scores")
        elif self.status is EvaluationStatus.VERIFIED:
            if self.verified_score is None or self.experimental_score is not None:
                raise ValueError("verified evaluations use only verified_score")
        elif self.experimental_score is None or self.verified_score is not None:
            raise ValueError("experimental evaluations use only experimental_score")
        return self


class SummarySnapshot(FrozenRecord):
    summary_id: str
    summary_version: str
    included_evaluation_ids: tuple[str, ...]
    model_id: str
    condition_id: str
    rubric_version: str
    eligible_count: Annotated[int, Field(ge=0)]
    unknown_count: Annotated[int, Field(ge=0)]
    refused_count: Annotated[int, Field(ge=0)]
    error_count: Annotated[int, Field(ge=0)]
    verified_score: UnitScore | None = None
    experimental_score: UnitScore | None = None
    generated_at: datetime
    freshness: str


class JobState(FrozenRecord):
    job_id: str
    job_version: str
    run_id: str
    status: JobStatus
    pending_target_ids: tuple[str, ...] = ()
    completed_attempt_ids: tuple[str, ...] = ()
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime

