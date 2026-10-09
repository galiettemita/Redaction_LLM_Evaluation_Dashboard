"""Versioned, deeply immutable records shared by the Redaction Lab MVP."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, StringConstraints
from pydantic import model_validator


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonNegativeInt = Annotated[int, Field(ge=0)]


class FrozenRecord(BaseModel):
    """Strict base model for records and their nested value objects."""

    model_config = ConfigDict(extra="forbid", frozen=True)


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


class ReferenceScoreability(StrEnum):
    SCOREABLE = "SCOREABLE"
    NOT_SCOREABLE = "NOT_SCOREABLE"


class AttemptStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    REFUSED = "REFUSED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    MALFORMED = "MALFORMED"


class EvaluationProcessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    DISAGREEMENT = "DISAGREEMENT"
    ERROR = "ERROR"


class ScoreStatus(StrEnum):
    NONE = "NONE"
    EXPERIMENTAL = "EXPERIMENTAL"
    VERIFIED = "VERIFIED"


class SummaryLevel(StrEnum):
    TARGET = "TARGET"
    DOCUMENT = "DOCUMENT"
    MODEL = "MODEL"


class FactEvidenceLabel(StrEnum):
    """Qualitative evidence only; labels have no numeric interpretation."""

    SUPPORTED = "SUPPORTED"
    MISSING = "MISSING"
    CONTRADICTED = "CONTRADICTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DetectionEvidence(FrozenRecord):
    """Immutable detector evidence available in the Task 1 contract."""

    rectangle_count: NonNegativeInt
    source_object_ids: tuple[NonEmptyStr, ...] = ()


class PredictionSettings(FrozenRecord):
    """Allow-listed model controls; answer-bearing payloads have no field here."""

    temperature: FiniteFloat | None = None


class TokenUsage(FrozenRecord):
    """Immutable usage metadata; absence remains distinct from a measured zero."""

    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    total_tokens: NonNegativeInt | None = None


class FactComparison(FrozenRecord):
    """Versioned evaluator evidence without imposing a numeric scoring formula."""

    fact_id: NonEmptyStr
    reference_quote: NonEmptyStr
    prediction_excerpt: NonEmptyStr | None = None
    comparison_label: NonEmptyStr
    reference_proposition: NonEmptyStr | None = None
    reference_quote_locator: NonEmptyStr | None = None
    critical_dimensions: tuple[NonEmptyStr, ...] = ()
    evidence_label: FactEvidenceLabel | None = None
    rationale: NonEmptyStr | None = None
    provisional: bool = True

    @model_validator(mode="after")
    def enforce_typed_evidence_consistency(self) -> FactComparison:
        if self.evidence_label is not None:
            if self.comparison_label != self.evidence_label.value:
                raise ValueError("comparison label must match the typed evidence label")
            if (
                self.reference_proposition is None
                or self.reference_quote_locator is None
                or not self.critical_dimensions
                or self.rationale is None
                or not self.provisional
            ):
                raise ValueError(
                    "typed evidence requires complete provisional provenance"
                )
        return self


class DocumentVersion(FrozenRecord):
    document_id: NonEmptyStr
    version_id: NonEmptyStr
    project_id: NonEmptyStr
    sha256: Sha256
    role: DocumentRole
    media_type: NonEmptyStr = "application/pdf"
    created_at: datetime
    provenance: NonEmptyStr
    access_policy: NonEmptyStr
    derivative_ids: tuple[NonEmptyStr, ...] = ()


class RedactionTarget(FrozenRecord):
    target_id: NonEmptyStr
    target_version: NonEmptyStr
    project_id: NonEmptyStr
    redacted_document_version_id: NonEmptyStr
    page_index: NonNegativeInt
    normalized_bbox: tuple[float, float, float, float]
    visible_context_locator: NonEmptyStr
    scope_status: ScopeStatus
    detection_method: NonEmptyStr
    detection_evidence: DetectionEvidence
    detector_version: NonEmptyStr

    @model_validator(mode="after")
    def validate_normalized_bbox(self) -> RedactionTarget:
        x0, y0, x1, y1 = self.normalized_bbox
        if not all(0.0 <= coordinate <= 1.0 for coordinate in self.normalized_bbox):
            raise ValueError("normalized_bbox coordinates must be between 0 and 1")
        if x0 >= x1 or y0 >= y1:
            raise ValueError("normalized_bbox must have positive width and height")
        return self


class ReferenceMapping(FrozenRecord):
    mapping_id: NonEmptyStr
    mapping_version: NonEmptyStr
    project_id: NonEmptyStr
    target_id: NonEmptyStr
    target_version: NonEmptyStr
    redacted_document_version_id: NonEmptyStr
    reference_document_version_id: NonEmptyStr | None
    status: ReferenceStatus
    scoreability: ReferenceScoreability
    exact_revealed_text: str | None = None
    reference_token_locator: NonEmptyStr | None = None
    redacted_canonical_version_id: NonEmptyStr | None = None
    reference_canonical_version_id: NonEmptyStr | None = None
    redacted_canonical_hash: Sha256 | None = None
    reference_canonical_hash: Sha256 | None = None
    global_alignment_version: NonEmptyStr | None = None
    left_anchor_evidence: tuple[NonEmptyStr, ...] = ()
    right_anchor_evidence: tuple[NonEmptyStr, ...] = ()
    left_document_boundary: bool = False
    right_document_boundary: bool = False
    candidate_unique: bool | None = None
    complete_revelation: bool | None = None
    readable: bool | None = None
    reliably_aligned: bool | None = None
    mapping_method_version: NonEmptyStr
    provenance: NonEmptyStr

    @model_validator(mode="after")
    def enforce_truth_availability(self) -> ReferenceMapping:
        if self.status is not ReferenceStatus.CONFIRMED:
            if self.scoreability is not ReferenceScoreability.NOT_SCOREABLE:
                raise ValueError("only confirmed mappings can be scoreable")
            if self.exact_revealed_text is not None:
                raise ValueError("unconfirmed mappings must not expose revealed text")
            return self

        if self.scoreability is not ReferenceScoreability.SCOREABLE:
            raise ValueError("confirmed mappings must be explicitly scoreable")
        if not self.exact_revealed_text or not self.exact_revealed_text.strip():
            raise ValueError("confirmed mappings require exact revealed text")

        required_evidence = {
            "reference_document_version_id": self.reference_document_version_id,
            "reference_token_locator": self.reference_token_locator,
            "redacted_canonical_version_id": self.redacted_canonical_version_id,
            "reference_canonical_version_id": self.reference_canonical_version_id,
            "redacted_canonical_hash": self.redacted_canonical_hash,
            "reference_canonical_hash": self.reference_canonical_hash,
            "global_alignment_version": self.global_alignment_version,
        }
        missing = [name for name, value in required_evidence.items() if value is None]
        if missing:
            raise ValueError(
                "confirmed mappings require evidence fields: " + ", ".join(missing)
            )
        if not self.left_anchor_evidence and not self.left_document_boundary:
            raise ValueError("confirmed mappings require a left anchor or boundary")
        if not self.right_anchor_evidence and not self.right_document_boundary:
            raise ValueError("confirmed mappings require a right anchor or boundary")
        if not all(
            (
                self.candidate_unique,
                self.complete_revelation,
                self.readable,
                self.reliably_aligned,
            )
        ):
            raise ValueError(
                "confirmed mappings require unique, complete, readable, reliable evidence"
            )
        return self


class CanonicalRedactedDocument(FrozenRecord):
    canonical_document_version_id: NonEmptyStr
    project_id: NonEmptyStr
    redacted_document_version_id: NonEmptyStr
    canonical_hash: Sha256
    canonical_text: str
    target_ids: tuple[NonEmptyStr, ...]
    canonicalizer_version: NonEmptyStr


class RunDefinition(FrozenRecord):
    run_id: NonEmptyStr
    run_version: NonEmptyStr
    project_id: NonEmptyStr
    target_versions: tuple[NonEmptyStr, ...]
    model_ids: tuple[NonEmptyStr, ...]
    experiment_condition: NonEmptyStr
    canonical_document_version_id: NonEmptyStr
    canonical_document_hash: Sha256
    common_context_budget: Annotated[int, Field(gt=0)]
    context_policy: NonEmptyStr
    prompt_id: NonEmptyStr
    prompt_version: NonEmptyStr
    settings: PredictionSettings = Field(default_factory=PredictionSettings)
    attempt_policy: NonEmptyStr
    tool_permissions: tuple[NonEmptyStr, ...] = ()
    budget_label: NonEmptyStr
    created_by: NonEmptyStr
    created_at: datetime


class PredictionManifest(FrozenRecord):
    """Complete, allow-listed redacted-only payload for a prediction adapter."""

    manifest_id: NonEmptyStr
    manifest_version: NonEmptyStr
    project_id: NonEmptyStr
    run_id: NonEmptyStr
    target_id: NonEmptyStr
    target_version: NonEmptyStr
    canonical_document_version_id: NonEmptyStr
    canonical_document_hash: Sha256
    canonical_redacted_text: str
    target_marker: NonEmptyStr
    other_redaction_markers: tuple[NonEmptyStr, ...] = ()
    prompt_id: NonEmptyStr
    prompt_version: NonEmptyStr
    model_id: NonEmptyStr
    settings: PredictionSettings = Field(default_factory=PredictionSettings)

    @model_validator(mode="after")
    def enforce_single_target_marker(self) -> PredictionManifest:
        if self.canonical_redacted_text.count(self.target_marker) != 1:
            raise ValueError("canonical text must contain the target marker exactly once")
        if self.target_marker in self.other_redaction_markers:
            raise ValueError("target marker cannot also be an other-redaction marker")
        return self


class ModelAttempt(FrozenRecord):
    attempt_id: NonEmptyStr
    project_id: NonEmptyStr
    run_id: NonEmptyStr
    target_id: NonEmptyStr
    target_version: NonEmptyStr
    model_id: NonEmptyStr
    provider_model_id: NonEmptyStr | None = None
    model_config_id: NonEmptyStr
    request_hash: Sha256
    response_hash: Sha256 | None = None
    prediction: str | None = None
    status: AttemptStatus
    usage: TokenUsage = Field(default_factory=TokenUsage)
    started_at: datetime
    completed_at: datetime

    @model_validator(mode="after")
    def enforce_success_payload(self) -> ModelAttempt:
        if (
            self.status in (AttemptStatus.SUCCEEDED, AttemptStatus.REFUSED)
            and self.provider_model_id is not None
            and self.provider_model_id != self.model_id
        ):
            raise ValueError("successful/refused provider model must match requested model")
        if self.status is AttemptStatus.SUCCEEDED:
            if not self.prediction or self.response_hash is None:
                raise ValueError("successful attempts require prediction and response hash")
        elif self.prediction is not None:
            raise ValueError("non-success attempts must not contain a prediction")
        return self


class EvaluationRecord(FrozenRecord):
    evaluation_id: NonEmptyStr
    evaluation_version: NonEmptyStr
    project_id: NonEmptyStr
    attempt_id: NonEmptyStr
    attempt_status: AttemptStatus
    mapping_id: NonEmptyStr | None
    mapping_version: NonEmptyStr | None
    mapping_status: ReferenceStatus | None
    mapping_scoreability: ReferenceScoreability | None
    evaluator_version: NonEmptyStr
    rubric_version: NonEmptyStr
    process_status: EvaluationProcessStatus
    score_status: ScoreStatus
    score_scale_id: NonEmptyStr | None = None
    research_validation_id: NonEmptyStr | None = None
    verified_score: FiniteFloat | None = None
    experimental_score: FiniteFloat | None = None
    fact_comparisons: tuple[FactComparison, ...] = ()
    contradictions: tuple[NonEmptyStr, ...] = ()
    explanation: NonEmptyStr
    created_at: datetime
    evidence_schema_version: NonEmptyStr | None = None
    run_id: NonEmptyStr | None = None
    target_id: NonEmptyStr | None = None
    target_version: NonEmptyStr | None = None
    redacted_document_version_id: NonEmptyStr | None = None
    reference_document_version_id: NonEmptyStr | None = None
    redacted_canonical_version_id: NonEmptyStr | None = None
    reference_canonical_version_id: NonEmptyStr | None = None
    model_id: NonEmptyStr | None = None
    model_config_id: NonEmptyStr | None = None
    condition_id: NonEmptyStr | None = None
    reference_trust: NonEmptyStr | None = None
    judge_id: NonEmptyStr | None = None
    judge_version: NonEmptyStr | None = None
    source_fact_record_id: NonEmptyStr | None = None
    source_fact_record_version: NonEmptyStr | None = None
    qualitative_status: NonEmptyStr | None = None
    unsupported_assertions: tuple[NonEmptyStr, ...] = ()
    attempt_request_hash: Sha256 | None = None
    attempt_response_hash: Sha256 | None = None

    @model_validator(mode="after")
    def enforce_score_channel_and_prerequisites(self) -> EvaluationRecord:
        mapping_values = (
            self.mapping_id,
            self.mapping_version,
            self.mapping_status,
            self.mapping_scoreability,
        )
        if any(value is not None for value in mapping_values) and not all(
            value is not None for value in mapping_values
        ):
            raise ValueError("mapping identity and status snapshots must be complete")

        if self.evidence_schema_version is not None:
            required = {
                "run_id": self.run_id,
                "target_id": self.target_id,
                "target_version": self.target_version,
                "redacted_document_version_id": self.redacted_document_version_id,
                "redacted_canonical_version_id": self.redacted_canonical_version_id,
                "model_id": self.model_id,
                "model_config_id": self.model_config_id,
                "condition_id": self.condition_id,
                "reference_trust": self.reference_trust,
                "judge_id": self.judge_id,
                "judge_version": self.judge_version,
                "qualitative_status": self.qualitative_status,
                "attempt_request_hash": self.attempt_request_hash,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError(
                    "Task 6 evidence requires complete binding: " + ", ".join(missing)
                )
            if (
                self.score_status is not ScoreStatus.NONE
                or self.verified_score is not None
                or self.experimental_score is not None
                or self.score_scale_id is not None
                or self.research_validation_id is not None
            ):
                raise ValueError("Task 6 evidence requires null numeric score channels")
            if self.attempt_status is not AttemptStatus.SUCCEEDED and (
                self.fact_comparisons or self.unsupported_assertions
            ):
                raise ValueError("non-success attempts cannot carry semantic evidence")
            if self.reference_trust != "APPROVED_SYNTHETIC_PAIR" and (
                self.fact_comparisons or self.unsupported_assertions
            ):
                raise ValueError("untrusted truth cannot carry semantic evidence")
            if self.reference_trust == "APPROVED_SYNTHETIC_PAIR" and (
                self.mapping_status is not ReferenceStatus.CONFIRMED
                or self.mapping_scoreability is not ReferenceScoreability.SCOREABLE
                or self.reference_document_version_id is None
                or self.reference_canonical_version_id is None
            ):
                raise ValueError(
                    "approved synthetic trust requires complete confirmed mapping provenance"
                )
            if self.fact_comparisons and (
                self.source_fact_record_id is None
                or self.source_fact_record_version is None
                or any(
                    comparison.evidence_label is None
                    or comparison.reference_proposition is None
                    or comparison.reference_quote_locator is None
                    or comparison.rationale is None
                    for comparison in self.fact_comparisons
                )
            ):
                raise ValueError(
                    "Task 6 fact comparisons require typed, versioned evidence"
                )

        if self.process_status is not EvaluationProcessStatus.COMPLETE:
            if self.score_status is not ScoreStatus.NONE:
                raise ValueError("incomplete evaluations cannot carry a score channel")

        if self.score_status is ScoreStatus.NONE:
            if self.verified_score is not None or self.experimental_score is not None:
                raise ValueError("score status NONE requires null scores")
            if self.score_scale_id is not None or self.research_validation_id is not None:
                raise ValueError("score status NONE cannot claim score validation")
            return self

        if self.attempt_status is not AttemptStatus.SUCCEEDED:
            raise ValueError("numeric evaluations require a successful frozen attempt")
        if (
            self.mapping_status is not ReferenceStatus.CONFIRMED
            or self.mapping_scoreability is not ReferenceScoreability.SCOREABLE
            or self.mapping_id is None
            or self.mapping_version is None
        ):
            raise ValueError("numeric evaluations require a scoreable confirmed mapping")
        if self.score_scale_id is None:
            raise ValueError("numeric evaluations require a versioned score scale")

        if self.score_status is ScoreStatus.EXPERIMENTAL:
            if self.experimental_score is None or self.verified_score is not None:
                raise ValueError("experimental evaluations use only experimental_score")
            if self.research_validation_id is not None:
                raise ValueError("experimental scores cannot claim research validation")
            return self

        if self.verified_score is None or self.experimental_score is not None:
            raise ValueError("verified evaluations use only verified_score")
        if self.research_validation_id is None:
            raise ValueError("verified scores require a research validation identifier")
        return self


class SummarySnapshot(FrozenRecord):
    summary_id: NonEmptyStr
    summary_version: NonEmptyStr
    project_id: NonEmptyStr
    summary_level: SummaryLevel
    scope_id: NonEmptyStr
    scope_version: NonEmptyStr
    included_evaluation_ids: tuple[NonEmptyStr, ...]
    eligible_evaluation_ids: tuple[NonEmptyStr, ...]
    common_eligible_set_id: NonEmptyStr
    model_id: NonEmptyStr
    condition_id: NonEmptyStr
    rubric_version: NonEmptyStr
    aggregation_version: NonEmptyStr
    requested_count: NonNegativeInt
    eligible_count: NonNegativeInt
    unknown_count: NonNegativeInt
    refused_count: NonNegativeInt
    timeout_count: NonNegativeInt
    malformed_count: NonNegativeInt
    error_count: NonNegativeInt
    needs_review_count: NonNegativeInt
    disagreement_count: NonNegativeInt
    score_scale_id: NonEmptyStr | None = None
    research_validation_id: NonEmptyStr | None = None
    verified_score: FiniteFloat | None = None
    experimental_score: FiniteFloat | None = None
    generated_at: datetime
    freshness: NonEmptyStr
    summary_schema_version: NonEmptyStr | None = None
    run_id: NonEmptyStr | None = None
    model_config_id: NonEmptyStr | None = None
    evaluator_version: NonEmptyStr | None = None
    judge_id: NonEmptyStr | None = None
    judge_version: NonEmptyStr | None = None
    completed_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    unknown_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    refused_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    timeout_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    malformed_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    error_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    needs_review_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    disagreement_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    evaluation_error_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    excluded_evaluation_ids: tuple[NonEmptyStr, ...] = ()
    eligible_target_keys: tuple[NonEmptyStr, ...] = ()
    redacted_document_version_ids: tuple[NonEmptyStr, ...] = ()
    reference_document_version_ids: tuple[NonEmptyStr, ...] = ()
    reference_canonical_version_ids: tuple[NonEmptyStr, ...] = ()
    reference_mapping_versions: tuple[NonEmptyStr, ...] = ()
    source_fact_record_versions: tuple[NonEmptyStr, ...] = ()
    completed_count: NonNegativeInt = 0
    evaluation_error_count: NonNegativeInt = 0
    excluded_count: NonNegativeInt = 0

    @model_validator(mode="after")
    def enforce_scope_denominator_and_scores(self) -> SummarySnapshot:
        included = set(self.included_evaluation_ids)
        eligible = set(self.eligible_evaluation_ids)
        if len(included) != len(self.included_evaluation_ids):
            raise ValueError("included evaluation IDs must be unique")
        if len(eligible) != len(self.eligible_evaluation_ids):
            raise ValueError("eligible evaluation IDs must be unique")
        if not eligible.issubset(included):
            raise ValueError("eligible evaluations must be included evaluations")
        if self.eligible_count != len(self.eligible_evaluation_ids):
            raise ValueError("eligible_count must match exact eligible evaluation IDs")

        if self.summary_schema_version is None:
            partition_count = sum(
                (
                    self.eligible_count,
                    self.unknown_count,
                    self.refused_count,
                    self.timeout_count,
                    self.malformed_count,
                    self.error_count,
                    self.needs_review_count,
                    self.disagreement_count,
                )
            )
            if self.requested_count != partition_count:
                raise ValueError("requested_count must equal the explicit outcome counts")
        else:
            required = {
                "run_id": self.run_id,
                "model_config_id": self.model_config_id,
                "evaluator_version": self.evaluator_version,
                "judge_id": self.judge_id,
                "judge_version": self.judge_version,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError(
                    "Task 6 summaries require complete provenance: "
                    + ", ".join(missing)
                )
            categories = {
                "completed": self.completed_evaluation_ids,
                "refused": self.refused_evaluation_ids,
                "timeout": self.timeout_evaluation_ids,
                "malformed": self.malformed_evaluation_ids,
                "error": self.error_evaluation_ids,
            }
            category_sets = {name: set(ids) for name, ids in categories.items()}
            if any(
                len(ids) != len(categories[name])
                for name, ids in category_sets.items()
            ):
                raise ValueError("Task 6 summary outcome IDs must be unique")
            outcome_ids = set().union(*category_sets.values())
            if sum(len(ids) for ids in category_sets.values()) != len(outcome_ids):
                raise ValueError("Task 6 attempt outcome categories must not overlap")
            if outcome_ids != included:
                raise ValueError("Task 6 attempt outcomes must partition included evaluations")
            unknown = set(self.unknown_evaluation_ids)
            if eligible & unknown or eligible | unknown != included:
                raise ValueError("Task 6 truth categories must partition included evaluations")
            review = set(self.needs_review_evaluation_ids)
            disagreement = set(self.disagreement_evaluation_ids)
            evaluation_errors = set(self.evaluation_error_evaluation_ids)
            completed = category_sets["completed"]
            if not review.issubset(completed) or not disagreement.issubset(completed):
                raise ValueError("review states require completed predictions")
            if not evaluation_errors.issubset(completed):
                raise ValueError("evaluation errors require completed predictions")
            excluded = set(self.excluded_evaluation_ids)
            if included & excluded:
                raise ValueError("excluded evaluations cannot also be included")
            count_pairs = (
                (self.completed_count, self.completed_evaluation_ids),
                (self.unknown_count, self.unknown_evaluation_ids),
                (self.refused_count, self.refused_evaluation_ids),
                (self.timeout_count, self.timeout_evaluation_ids),
                (self.malformed_count, self.malformed_evaluation_ids),
                (self.error_count, self.error_evaluation_ids),
                (self.needs_review_count, self.needs_review_evaluation_ids),
                (self.disagreement_count, self.disagreement_evaluation_ids),
                (self.evaluation_error_count, self.evaluation_error_evaluation_ids),
                (self.excluded_count, self.excluded_evaluation_ids),
            )
            if any(count != len(ids) for count, ids in count_pairs):
                raise ValueError("Task 6 summary counts must match exact ID sets")
            if self.requested_count != len(included) + len(excluded):
                raise ValueError("requested_count must include included and excluded records")
            if len(set(self.eligible_target_keys)) != len(self.eligible_target_keys):
                raise ValueError("eligible target keys must be unique")
            version_sets = (
                self.redacted_document_version_ids,
                self.reference_document_version_ids,
                self.reference_canonical_version_ids,
                self.reference_mapping_versions,
                self.source_fact_record_versions,
            )
            if any(len(set(values)) != len(values) for values in version_sets):
                raise ValueError("Task 6 summary version sets must be unique")
            encoded = json.dumps(
                sorted(self.eligible_target_keys), separators=(",", ":")
            ).encode("utf-8")
            expected_set_id = f"eligible-set-{sha256(encoded).hexdigest()[:24]}"
            if self.common_eligible_set_id != expected_set_id:
                raise ValueError("common eligible set ID must derive from exact targets")
            if (
                self.verified_score is not None
                or self.experimental_score is not None
                or self.score_scale_id is not None
                or self.research_validation_id is not None
            ):
                raise ValueError("Task 6 summaries require null numeric score channels")

        has_verified = self.verified_score is not None
        has_experimental = self.experimental_score is not None
        if has_verified and has_experimental:
            raise ValueError("a summary cannot mix verified and experimental scores")
        if self.eligible_count == 0 and (has_verified or has_experimental):
            raise ValueError("zero eligible denominator requires null scores")
        if has_verified or has_experimental:
            if self.score_scale_id is None:
                raise ValueError("numeric summaries require a versioned score scale")
        elif self.score_scale_id is not None or self.research_validation_id is not None:
            raise ValueError("null-score summaries cannot claim score validation")

        if has_verified and self.research_validation_id is None:
            raise ValueError("verified summaries require research validation")
        if has_experimental and self.research_validation_id is not None:
            raise ValueError("experimental summaries cannot claim research validation")
        return self


class JobState(FrozenRecord):
    job_id: NonEmptyStr
    job_version: NonEmptyStr
    project_id: NonEmptyStr
    run_id: NonEmptyStr
    status: JobStatus
    pending_target_ids: tuple[NonEmptyStr, ...] = ()
    completed_attempt_ids: tuple[NonEmptyStr, ...] = ()
    error_code: NonEmptyStr | None = None
    created_at: datetime
    updated_at: datetime
