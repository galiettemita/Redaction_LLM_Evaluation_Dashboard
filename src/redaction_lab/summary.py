"""Deterministic target, document, and model qualitative summaries."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from redaction_lab.contracts import (
    AttemptStatus,
    EvaluationProcessStatus,
    EvaluationRecord,
    ReferenceScoreability,
    ReferenceStatus,
    SummaryLevel,
    SummarySnapshot,
)


SUMMARY_SCHEMA_VERSION = "qualitative-summary-evidence-v1"
SUMMARY_VERSION = "qualitative-summary-v1"


class SummaryCompatibilityError(ValueError):
    """Raised rather than silently pooling incompatible evaluation records."""


def _digest(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"{prefix}-{sha256(encoded).hexdigest()}"


def _one_value(
    evaluations: tuple[EvaluationRecord, ...], field: str
) -> str:
    values = {getattr(evaluation, field) for evaluation in evaluations}
    if None in values or len(values) != 1:
        raise SummaryCompatibilityError(f"incompatible {field}")
    return next(iter(values))  # type: ignore[return-value]


def _validate_common(evaluations: tuple[EvaluationRecord, ...]) -> None:
    if not evaluations:
        raise SummaryCompatibilityError("at least one evaluation is required")
    ids = tuple(evaluation.evaluation_id for evaluation in evaluations)
    if len(set(ids)) != len(ids):
        raise SummaryCompatibilityError("evaluation_id must be unique")
    target_keys = tuple(_target_key(evaluation) for evaluation in evaluations)
    if len(set(target_keys)) != len(target_keys):
        raise SummaryCompatibilityError("target identity must be unique")
    for field in (
        "project_id",
        "run_id",
        "model_id",
        "model_config_id",
        "condition_id",
        "rubric_version",
        "evaluator_version",
        "judge_id",
        "judge_version",
    ):
        _one_value(evaluations, field)
    mapping_versions = {evaluation.mapping_version for evaluation in evaluations}
    if None in mapping_versions or len(mapping_versions) != 1:
        raise SummaryCompatibilityError("incompatible mapping_version")
    source_versions = {
        evaluation.source_fact_record_version
        for evaluation in evaluations
        if evaluation.source_fact_record_version is not None
    }
    if len(source_versions) > 1:
        raise SummaryCompatibilityError("incompatible source_fact_record_version")
    if any(evaluation.evidence_schema_version is None for evaluation in evaluations):
        raise SummaryCompatibilityError("Task 6 evidence schema is required")


def _is_truth_eligible(evaluation: EvaluationRecord) -> bool:
    return (
        evaluation.reference_trust == "APPROVED_SYNTHETIC_PAIR"
        and evaluation.mapping_status is ReferenceStatus.CONFIRMED
        and evaluation.mapping_scoreability is ReferenceScoreability.SCOREABLE
    )


def _target_key(evaluation: EvaluationRecord) -> str:
    return "|".join(
        (
            evaluation.project_id,
            evaluation.redacted_document_version_id or "",
            evaluation.target_id or "",
            evaluation.target_version or "",
        )
    )


def _version_ids(
    evaluations: tuple[EvaluationRecord, ...], field: str
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for evaluation in evaluations
                if (value := getattr(evaluation, field)) is not None
            }
        )
    )


def _summarize(
    evaluations: tuple[EvaluationRecord, ...],
    *,
    level: SummaryLevel,
    scope_id: str,
    scope_version: str,
    aggregation_version: str,
    generated_at: datetime,
) -> SummarySnapshot:
    _validate_common(evaluations)
    ordered = tuple(sorted(evaluations, key=lambda item: item.evaluation_id))
    included_ids = tuple(item.evaluation_id for item in ordered)
    eligible = tuple(item for item in ordered if _is_truth_eligible(item))
    unknown = tuple(item for item in ordered if not _is_truth_eligible(item))

    def ids_for_attempt(status: AttemptStatus) -> tuple[str, ...]:
        return tuple(
            item.evaluation_id for item in ordered if item.attempt_status is status
        )

    completed_ids = ids_for_attempt(AttemptStatus.SUCCEEDED)
    refused_ids = ids_for_attempt(AttemptStatus.REFUSED)
    timeout_ids = ids_for_attempt(AttemptStatus.TIMEOUT)
    malformed_ids = ids_for_attempt(AttemptStatus.MALFORMED)
    error_ids = ids_for_attempt(AttemptStatus.ERROR)
    review_ids = tuple(
        item.evaluation_id
        for item in ordered
        if item.process_status is EvaluationProcessStatus.NEEDS_REVIEW
        and item.attempt_status is AttemptStatus.SUCCEEDED
    )
    disagreement_ids = tuple(
        item.evaluation_id
        for item in ordered
        if item.process_status is EvaluationProcessStatus.DISAGREEMENT
        and item.attempt_status is AttemptStatus.SUCCEEDED
    )
    evaluation_error_ids = tuple(
        item.evaluation_id
        for item in ordered
        if item.process_status is EvaluationProcessStatus.ERROR
        and item.attempt_status is AttemptStatus.SUCCEEDED
    )
    eligible_ids = tuple(item.evaluation_id for item in eligible)
    unknown_ids = tuple(item.evaluation_id for item in unknown)
    eligible_target_keys = tuple(sorted(_target_key(item) for item in eligible))
    common_set_id = _digest("eligible-set", list(eligible_target_keys))[:37]
    mapping_versions = tuple(
        sorted({item.mapping_version for item in ordered if item.mapping_version})
    )
    source_versions = tuple(
        sorted(
            {
                item.source_fact_record_version
                for item in ordered
                if item.source_fact_record_version
            }
        )
    )
    redacted_document_versions = _version_ids(
        ordered, "redacted_document_version_id"
    )
    reference_document_versions = _version_ids(
        ordered, "reference_document_version_id"
    )
    reference_canonical_versions = _version_ids(
        ordered, "reference_canonical_version_id"
    )
    identity = {
        "summary_version": SUMMARY_VERSION,
        "level": level.value,
        "scope_id": scope_id,
        "scope_version": scope_version,
        "included_evaluation_ids": included_ids,
        "eligible_target_keys": eligible_target_keys,
        "redacted_document_version_ids": redacted_document_versions,
        "reference_document_version_ids": reference_document_versions,
        "reference_canonical_version_ids": reference_canonical_versions,
        "model_id": _one_value(ordered, "model_id"),
        "model_config_id": _one_value(ordered, "model_config_id"),
        "condition_id": _one_value(ordered, "condition_id"),
        "rubric_version": _one_value(ordered, "rubric_version"),
        "evaluator_version": _one_value(ordered, "evaluator_version"),
        "judge_id": _one_value(ordered, "judge_id"),
        "judge_version": _one_value(ordered, "judge_version"),
        "aggregation_version": aggregation_version,
    }
    return SummarySnapshot(
        summary_id=_digest("summary", identity),
        summary_version=SUMMARY_VERSION,
        summary_schema_version=SUMMARY_SCHEMA_VERSION,
        project_id=_one_value(ordered, "project_id"),
        run_id=_one_value(ordered, "run_id"),
        summary_level=level,
        scope_id=scope_id,
        scope_version=scope_version,
        included_evaluation_ids=included_ids,
        eligible_evaluation_ids=eligible_ids,
        common_eligible_set_id=common_set_id,
        eligible_target_keys=eligible_target_keys,
        redacted_document_version_ids=redacted_document_versions,
        reference_document_version_ids=reference_document_versions,
        reference_canonical_version_ids=reference_canonical_versions,
        model_id=_one_value(ordered, "model_id"),
        model_config_id=_one_value(ordered, "model_config_id"),
        condition_id=_one_value(ordered, "condition_id"),
        rubric_version=_one_value(ordered, "rubric_version"),
        evaluator_version=_one_value(ordered, "evaluator_version"),
        judge_id=_one_value(ordered, "judge_id"),
        judge_version=_one_value(ordered, "judge_version"),
        aggregation_version=aggregation_version,
        reference_mapping_versions=mapping_versions,
        source_fact_record_versions=source_versions,
        requested_count=len(ordered),
        eligible_count=len(eligible_ids),
        unknown_count=len(unknown_ids),
        refused_count=len(refused_ids),
        timeout_count=len(timeout_ids),
        malformed_count=len(malformed_ids),
        error_count=len(error_ids),
        needs_review_count=len(review_ids),
        disagreement_count=len(disagreement_ids),
        completed_count=len(completed_ids),
        evaluation_error_count=len(evaluation_error_ids),
        excluded_count=0,
        completed_evaluation_ids=completed_ids,
        unknown_evaluation_ids=unknown_ids,
        refused_evaluation_ids=refused_ids,
        timeout_evaluation_ids=timeout_ids,
        malformed_evaluation_ids=malformed_ids,
        error_evaluation_ids=error_ids,
        needs_review_evaluation_ids=review_ids,
        disagreement_evaluation_ids=disagreement_ids,
        evaluation_error_evaluation_ids=evaluation_error_ids,
        excluded_evaluation_ids=(),
        score_scale_id=None,
        research_validation_id=None,
        verified_score=None,
        experimental_score=None,
        generated_at=generated_at,
        freshness="immutable-snapshot",
    )


def summarize_target(
    evaluation: EvaluationRecord,
    *,
    aggregation_version: str,
    generated_at: datetime,
) -> SummarySnapshot:
    """Create one exact target/model summary."""

    if evaluation.target_id is None or evaluation.target_version is None:
        raise SummaryCompatibilityError("target identity is required")
    return _summarize(
        (evaluation,),
        level=SummaryLevel.TARGET,
        scope_id=evaluation.target_id,
        scope_version=evaluation.target_version,
        aggregation_version=aggregation_version,
        generated_at=generated_at,
    )


def summarize_document(
    evaluations: tuple[EvaluationRecord, ...],
    *,
    aggregation_version: str,
    generated_at: datetime,
) -> SummarySnapshot:
    """Create a per-document-per-model summary; cross-model input is rejected."""

    _validate_common(evaluations)
    document_id = _one_value(evaluations, "redacted_document_version_id")
    for field in (
        "reference_document_version_id",
        "reference_canonical_version_id",
    ):
        if len(_version_ids(evaluations, field)) > 1:
            raise SummaryCompatibilityError(f"incompatible {field}")
    return _summarize(
        evaluations,
        level=SummaryLevel.DOCUMENT,
        scope_id=document_id,
        scope_version=document_id,
        aggregation_version=aggregation_version,
        generated_at=generated_at,
    )


def summarize_model(
    evaluations: tuple[EvaluationRecord, ...],
    *,
    aggregation_version: str,
    generated_at: datetime,
) -> SummarySnapshot:
    """Create one model/configuration summary across compatible documents."""

    _validate_common(evaluations)
    model_id = _one_value(evaluations, "model_id")
    config_id = _one_value(evaluations, "model_config_id")
    return _summarize(
        evaluations,
        level=SummaryLevel.MODEL,
        scope_id=model_id,
        scope_version=config_id,
        aggregation_version=aggregation_version,
        generated_at=generated_at,
    )


def assert_comparable_summaries(*summaries: SummarySnapshot) -> None:
    """Require the same exact eligible targets and non-model configuration."""

    if len(summaries) < 2:
        raise SummaryCompatibilityError("at least two summaries are required")
    first = summaries[0]
    if any(summary.summary_level is not SummaryLevel.MODEL for summary in summaries):
        raise SummaryCompatibilityError("only model summaries are comparable")
    for summary in summaries[1:]:
        if (
            summary.common_eligible_set_id != first.common_eligible_set_id
            or summary.eligible_target_keys != first.eligible_target_keys
        ):
            raise SummaryCompatibilityError("eligible target set mismatch")
        for field in (
            "project_id",
            "run_id",
            "condition_id",
            "rubric_version",
            "aggregation_version",
            "evaluator_version",
            "judge_id",
            "judge_version",
            "redacted_document_version_ids",
            "reference_document_version_ids",
            "reference_canonical_version_ids",
            "reference_mapping_versions",
            "source_fact_record_versions",
        ):
            if getattr(summary, field) != getattr(first, field):
                raise SummaryCompatibilityError(f"incompatible {field}")
