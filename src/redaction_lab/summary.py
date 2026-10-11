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
    SummaryExclusion,
    SummaryRequest,
    SummarySnapshot,
)


SUMMARY_SCHEMA_VERSION = "qualitative-summary-evidence-v1"
SUMMARY_VERSION = "qualitative-summary-v1"
AUTHORITATIVE_SUMMARY_SCHEMA_VERSION = "qualitative-summary-evidence-v2"
AUTHORITATIVE_SUMMARY_VERSION = "qualitative-summary-v2"


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


def _eligible_provenance_key(evaluation: EvaluationRecord) -> str:
    values = (
        evaluation.project_id,
        evaluation.redacted_document_version_id,
        evaluation.target_id,
        evaluation.target_version,
        evaluation.reference_target_id,
        evaluation.reference_target_version,
        evaluation.mapping_id,
        evaluation.mapping_version,
        evaluation.mapping_method_version,
        evaluation.reference_document_version_id,
        evaluation.reference_canonical_version_id,
        evaluation.redacted_canonical_hash,
        evaluation.reference_canonical_hash,
        evaluation.reference_trust,
        evaluation.source_fact_record_id,
        evaluation.source_fact_record_version,
    )
    if any(value is None for value in values[:-2]):
        raise SummaryCompatibilityError("eligible reference provenance is incomplete")
    return _digest("eligible-provenance", values)


def _authoritative_profile(
    evaluations: tuple[EvaluationRecord, ...], level: SummaryLevel
) -> dict[str, object]:
    if not evaluations:
        raise SummaryCompatibilityError("at least one included evaluation is required")
    if any(
        item.evidence_schema_version != "qualitative-fact-evidence-v2"
        for item in evaluations
    ):
        raise SummaryCompatibilityError("authoritative v2 evaluations are required")
    if len({item.evaluation_id for item in evaluations}) != len(evaluations):
        raise SummaryCompatibilityError("evaluation_id must be unique")
    if len({_target_key(item) for item in evaluations}) != len(evaluations):
        raise SummaryCompatibilityError("target identity must be unique")
    common_fields = (
        "project_id",
        "model_id",
        "provider_model_id",
        "model_config_id",
        "condition_id",
        "prompt_id",
        "prompt_version",
        "settings_fingerprint",
        "attempt_policy",
        "context_policy",
        "common_context_budget",
        "tool_permissions",
        "prediction_protocol_id",
        "model_provenance_id",
        "rubric_version",
        "evaluator_version",
        "judge_id",
        "judge_version",
        "mapping_version",
        "mapping_method_version",
    )
    profile: dict[str, object] = {}
    for field in common_fields:
        values = {getattr(item, field) for item in evaluations}
        if None in values or len(values) != 1:
            raise SummaryCompatibilityError(f"incompatible {field}")
        profile[field] = next(iter(values))
    eligible_source_versions = {
        item.source_fact_record_version
        for item in evaluations
        if _is_truth_eligible(item) and item.source_fact_record_version is not None
    }
    if len(eligible_source_versions) > 1:
        raise SummaryCompatibilityError("incompatible source_fact_record_version")
    if level is not SummaryLevel.MODEL and len({item.run_id for item in evaluations}) != 1:
        raise SummaryCompatibilityError("incompatible run_id")
    return profile


def _summary_identity_payload(snapshot: SummarySnapshot) -> dict[str, object]:
    return snapshot.model_dump(mode="json", exclude={"summary_id", "generated_at"})


def verify_summary_identity(snapshot: SummarySnapshot) -> None:
    if snapshot.summary_schema_version != AUTHORITATIVE_SUMMARY_SCHEMA_VERSION:
        raise SummaryCompatibilityError("authoritative summary schema is required")
    expected = _digest("summary", _summary_identity_payload(snapshot))
    if snapshot.summary_id != expected:
        raise SummaryCompatibilityError("summary deterministic identity mismatch")


def build_authoritative_summary(
    request: SummaryRequest,
    evaluations: tuple[EvaluationRecord, ...],
    exclusions: tuple[SummaryExclusion, ...],
    *,
    generated_at: datetime,
) -> SummarySnapshot:
    """Build a v2 snapshot from repository-authenticated exact membership."""

    ordered = tuple(sorted(evaluations, key=lambda item: item.evaluation_id))
    profile = _authoritative_profile(ordered, request.summary_level)
    requested_attempt_ids = tuple(sorted(member.attempt_id for member in request.members))
    included_attempt_ids = {item.attempt_id for item in ordered}
    excluded_attempt_ids = {item.attempt_id for item in exclusions}
    if included_attempt_ids & excluded_attempt_ids:
        raise SummaryCompatibilityError("included and excluded attempts overlap")
    if included_attempt_ids | excluded_attempt_ids != set(requested_attempt_ids):
        raise SummaryCompatibilityError("requested attempts must exactly partition membership")
    if any(item.project_id != request.project_id for item in ordered):
        raise SummaryCompatibilityError("incompatible project_id")
    if request.summary_level is SummaryLevel.TARGET:
        if len(ordered) != 1 or any(
            item.target_id != request.scope_id
            or item.target_version != request.scope_version
            for item in ordered
        ):
            raise SummaryCompatibilityError("target scope mismatch")
    elif request.summary_level is SummaryLevel.DOCUMENT:
        if any(
            item.redacted_document_version_id != request.scope_id
            for item in ordered
        ):
            raise SummaryCompatibilityError("document scope mismatch")
    elif any(
        item.model_id != request.scope_id
        or item.model_config_id != request.scope_version
        for item in ordered
    ):
        raise SummaryCompatibilityError("model scope mismatch")

    included_ids = tuple(item.evaluation_id for item in ordered)
    eligible = tuple(item for item in ordered if _is_truth_eligible(item))
    unknown = tuple(item for item in ordered if not _is_truth_eligible(item))

    def attempt_ids(status: AttemptStatus) -> tuple[str, ...]:
        return tuple(item.evaluation_id for item in ordered if item.attempt_status is status)

    completed_ids = attempt_ids(AttemptStatus.SUCCEEDED)
    refused_ids = attempt_ids(AttemptStatus.REFUSED)
    timeout_ids = attempt_ids(AttemptStatus.TIMEOUT)
    malformed_ids = attempt_ids(AttemptStatus.MALFORMED)
    error_ids = attempt_ids(AttemptStatus.ERROR)
    review_ids = tuple(
        item.evaluation_id
        for item in ordered
        if item.attempt_status is AttemptStatus.SUCCEEDED
        and item.process_status is EvaluationProcessStatus.NEEDS_REVIEW
    )
    disagreement_ids = tuple(
        item.evaluation_id
        for item in ordered
        if item.attempt_status is AttemptStatus.SUCCEEDED
        and item.process_status is EvaluationProcessStatus.DISAGREEMENT
    )
    evaluation_error_ids = tuple(
        item.evaluation_id
        for item in ordered
        if item.attempt_status is AttemptStatus.SUCCEEDED
        and item.process_status is EvaluationProcessStatus.ERROR
    )
    eligible_ids = tuple(item.evaluation_id for item in eligible)
    unknown_ids = tuple(item.evaluation_id for item in unknown)
    eligible_target_keys = tuple(sorted(_target_key(item) for item in eligible))
    eligible_provenance_keys = tuple(
        sorted(_eligible_provenance_key(item) for item in eligible)
    )
    encoded = json.dumps(list(eligible_provenance_keys), separators=(",", ":")).encode()
    common_set_id = f"eligible-set-{sha256(encoded).hexdigest()[:24]}"
    contributing_run_ids = tuple(sorted({item.run_id for item in ordered}))
    model_provenance_ids = tuple(
        sorted({item.model_provenance_id for item in ordered if item.model_provenance_id})
    )
    compatibility_payload = {
        key: value
        for key, value in profile.items()
        if key
        not in {
            "model_id",
            "provider_model_id",
            "model_config_id",
            "model_provenance_id",
        }
    }
    compatibility_profile_id = _digest("compatibility-profile", compatibility_payload)
    snapshot = SummarySnapshot(
        summary_id="pending-summary-identity",
        summary_version=AUTHORITATIVE_SUMMARY_VERSION,
        summary_schema_version=AUTHORITATIVE_SUMMARY_SCHEMA_VERSION,
        project_id=request.project_id,
        run_id=(contributing_run_ids[0] if len(contributing_run_ids) == 1 else None),
        summary_level=request.summary_level,
        scope_id=request.scope_id,
        scope_version=request.scope_version,
        requested_attempt_ids=requested_attempt_ids,
        included_evaluation_ids=included_ids,
        excluded_evaluation_ids=tuple(
            sorted(item.evaluation_id for item in exclusions if item.evaluation_id)
        ),
        exclusions=tuple(sorted(exclusions, key=lambda item: item.attempt_id)),
        eligible_evaluation_ids=eligible_ids,
        common_eligible_set_id=common_set_id,
        eligible_target_keys=eligible_target_keys,
        eligible_provenance_keys=eligible_provenance_keys,
        contributing_run_ids=contributing_run_ids,
        redacted_document_version_ids=_version_ids(ordered, "redacted_document_version_id"),
        reference_document_version_ids=_version_ids(ordered, "reference_document_version_id"),
        reference_canonical_version_ids=_version_ids(ordered, "reference_canonical_version_id"),
        reference_mapping_versions=_version_ids(ordered, "mapping_version"),
        source_fact_record_versions=_version_ids(ordered, "source_fact_record_version"),
        model_id=str(profile["model_id"]),
        model_config_id=str(profile["model_config_id"]),
        condition_id=str(profile["condition_id"]),
        prompt_id=str(profile["prompt_id"]),
        prompt_version=str(profile["prompt_version"]),
        settings_fingerprint=str(profile["settings_fingerprint"]),
        attempt_policy=str(profile["attempt_policy"]),
        context_policy=str(profile["context_policy"]),
        common_context_budget=int(profile["common_context_budget"]),
        tool_permissions=tuple(profile["tool_permissions"]),
        prediction_protocol_id=str(profile["prediction_protocol_id"]),
        model_provenance_ids=model_provenance_ids,
        model_identity_limitation=(
            "Requested/reported model names and configuration IDs do not establish "
            "model weights or a provider artifact digest."
        ),
        compatibility_profile_id=compatibility_profile_id,
        rubric_version=str(profile["rubric_version"]),
        evaluator_version=str(profile["evaluator_version"]),
        judge_id=str(profile["judge_id"]),
        judge_version=str(profile["judge_version"]),
        aggregation_version=request.aggregation_version,
        requested_count=len(request.members),
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
        excluded_count=len(exclusions),
        completed_evaluation_ids=completed_ids,
        unknown_evaluation_ids=unknown_ids,
        refused_evaluation_ids=refused_ids,
        timeout_evaluation_ids=timeout_ids,
        malformed_evaluation_ids=malformed_ids,
        error_evaluation_ids=error_ids,
        needs_review_evaluation_ids=review_ids,
        disagreement_evaluation_ids=disagreement_ids,
        evaluation_error_evaluation_ids=evaluation_error_ids,
        score_scale_id=None,
        research_validation_id=None,
        verified_score=None,
        experimental_score=None,
        generated_at=generated_at,
        freshness="immutable-snapshot; compare compatibility_profile_id explicitly",
    )
    final = snapshot.model_copy(
        update={"summary_id": _digest("summary", _summary_identity_payload(snapshot))}
    )
    verify_summary_identity(final)
    return final


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
    if all(
        summary.summary_schema_version == AUTHORITATIVE_SUMMARY_SCHEMA_VERSION
        for summary in summaries
    ):
        for summary in summaries[1:]:
            if (
                summary.common_eligible_set_id != first.common_eligible_set_id
                or summary.eligible_provenance_keys
                != first.eligible_provenance_keys
            ):
                raise SummaryCompatibilityError("eligible reference set mismatch")
            for field in (
                "project_id",
                "compatibility_profile_id",
                "aggregation_version",
            ):
                if getattr(summary, field) != getattr(first, field):
                    raise SummaryCompatibilityError(f"incompatible {field}")
        return
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
