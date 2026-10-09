from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from redaction_lab.contracts import EvaluationRecord, SummaryLevel
from redaction_lab.summary import (
    SummaryCompatibilityError,
    assert_comparable_summaries,
    summarize_document,
    summarize_model,
    summarize_target,
)


NOW = datetime(2026, 10, 9, 23, 0, tzinfo=UTC)


def _evaluation(
    evaluation_id: str,
    *,
    target_id: str,
    document_id: str = "redacted-document-v1",
    attempt_status: str = "SUCCEEDED",
    truth_eligible: bool = True,
    process_status: str = "COMPLETE",
    model_id: str = "model-a",
    model_config_id: str = "config-a",
    condition_id: str = "condition-a",
    rubric_version: str = "rubric-v1",
    judge_version: str = "judge-v1",
) -> EvaluationRecord:
    return EvaluationRecord(
        evaluation_id=evaluation_id,
        evaluation_version="qualitative-evaluation-v1",
        evidence_schema_version="qualitative-fact-evidence-v1",
        project_id="project-rl-mvp-003",
        run_id="run-v1",
        target_id=target_id,
        target_version=f"{target_id}-v1",
        redacted_document_version_id=document_id,
        reference_document_version_id=("reference-v1" if truth_eligible else None),
        redacted_canonical_version_id="redacted-canonical-v1",
        reference_canonical_version_id=(
            "reference-canonical-v1" if truth_eligible else None
        ),
        attempt_id=f"attempt-{evaluation_id}",
        attempt_status=attempt_status,
        model_id=model_id,
        model_config_id=model_config_id,
        condition_id=condition_id,
        mapping_id=f"mapping-{evaluation_id}",
        mapping_version="mapping-v1",
        mapping_status="CONFIRMED" if truth_eligible else "CONFLICTING",
        mapping_scoreability="SCOREABLE" if truth_eligible else "NOT_SCOREABLE",
        reference_trust=(
            "APPROVED_SYNTHETIC_PAIR"
            if truth_eligible
            else "UNTRUSTED_OR_UNAVAILABLE"
        ),
        evaluator_version="evaluator-v1",
        judge_id="judge",
        judge_version=judge_version,
        rubric_version=rubric_version,
        source_fact_record_id=(f"facts-{evaluation_id}" if truth_eligible else None),
        source_fact_record_version=("source-facts-v1" if truth_eligible else None),
        process_status=process_status,
        qualitative_status=(
            "ACCURACY_UNKNOWN"
            if not truth_eligible
            else "PROVISIONAL_ALL_FACTS_SUPPORTED"
        ),
        attempt_request_hash="a" * 64,
        attempt_response_hash=("b" * 64 if attempt_status == "SUCCEEDED" else None),
        score_status="NONE",
        verified_score=None,
        experimental_score=None,
        explanation="Synthetic qualitative evidence only.",
        created_at=NOW,
    )


def test_target_summary_has_exact_counts_and_null_scores() -> None:
    evaluation = _evaluation("eval-1", target_id="target-1")

    summary = summarize_target(
        evaluation,
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )

    assert summary.summary_level is SummaryLevel.TARGET
    assert summary.included_evaluation_ids == ("eval-1",)
    assert summary.completed_evaluation_ids == ("eval-1",)
    assert summary.eligible_evaluation_ids == ("eval-1",)
    assert summary.completed_count == 1
    assert summary.redacted_document_version_ids == ("redacted-document-v1",)
    assert summary.reference_document_version_ids == ("reference-v1",)
    assert summary.reference_canonical_version_ids == ("reference-canonical-v1",)
    assert summary.verified_score is None
    assert summary.experimental_score is None
    assert summary.score_scale_id is None


def test_document_summary_is_model_specific_and_retains_orthogonal_counts() -> None:
    evaluations = (
        _evaluation("eval-ok", target_id="target-1"),
        _evaluation(
            "eval-unknown",
            target_id="target-2",
            truth_eligible=False,
            process_status="NEEDS_REVIEW",
        ),
        _evaluation(
            "eval-timeout",
            target_id="target-3",
            attempt_status="TIMEOUT",
        ),
    )

    summary = summarize_document(
        evaluations,
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )

    assert summary.summary_level is SummaryLevel.DOCUMENT
    assert summary.scope_id == "redacted-document-v1"
    assert summary.model_id == "model-a"
    assert summary.judge_id == "judge"
    assert summary.requested_count == 3
    assert summary.completed_count == 2
    assert summary.timeout_count == 1
    assert summary.eligible_count == 2
    assert summary.unknown_count == 1
    assert summary.needs_review_count == 1
    assert set(summary.completed_evaluation_ids) == {"eval-ok", "eval-unknown"}
    assert summary.verified_score is summary.experimental_score is None


@pytest.mark.parametrize(
    "field",
    [
        "project_id",
        "redacted_document_version_id",
        "model_id",
        "model_config_id",
        "condition_id",
        "rubric_version",
        "judge_version",
    ],
)
def test_document_summary_rejects_incompatible_records(field: str) -> None:
    first = _evaluation("eval-1", target_id="target-1")
    changed = first.model_copy(
        update={
            "evaluation_id": "eval-2",
            "target_id": "target-2",
            "target_version": "target-2-v1",
            field: f"different-{field}",
        }
    )

    with pytest.raises(SummaryCompatibilityError, match=field):
        summarize_document(
            (first, changed),
            aggregation_version="qualitative-counts-v1",
            generated_at=NOW,
        )


def test_model_summary_spans_documents_but_never_models() -> None:
    first = _evaluation("eval-1", target_id="target-1", document_id="document-1")
    second = _evaluation("eval-2", target_id="target-2", document_id="document-2")

    summary = summarize_model(
        (first, second),
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )

    assert summary.summary_level is SummaryLevel.MODEL
    assert summary.model_id == "model-a"
    assert summary.requested_count == 2

    with pytest.raises(SummaryCompatibilityError, match="model_id"):
        summarize_model(
            (first, second.model_copy(update={"model_id": "model-b"})),
            aggregation_version="qualitative-counts-v1",
            generated_at=NOW,
        )


def test_summary_rejects_duplicate_target_and_document_reference_version_mixing() -> None:
    first = _evaluation("eval-1", target_id="target-1")
    duplicate = first.model_copy(update={"evaluation_id": "eval-2"})
    with pytest.raises(SummaryCompatibilityError, match="target identity"):
        summarize_model(
            (first, duplicate),
            aggregation_version="qualitative-counts-v1",
            generated_at=NOW,
        )

    changed_reference = _evaluation("eval-2", target_id="target-2").model_copy(
        update={"reference_canonical_version_id": "other-reference-canonical"}
    )
    with pytest.raises(SummaryCompatibilityError, match="reference_canonical_version_id"):
        summarize_document(
            (first, changed_reference),
            aggregation_version="qualitative-counts-v1",
            generated_at=NOW,
        )


def test_common_set_identity_is_deterministic_and_requires_same_targets() -> None:
    model_a = summarize_model(
        (
            _evaluation("a-1", target_id="target-1"),
            _evaluation("a-2", target_id="target-2"),
        ),
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )
    model_b = summarize_model(
        (
            _evaluation("b-1", target_id="target-1", model_id="model-b"),
            _evaluation("b-2", target_id="target-2", model_id="model-b"),
        ),
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )

    assert model_a.common_eligible_set_id == model_b.common_eligible_set_id
    assert_comparable_summaries(model_a, model_b)

    different_set = summarize_model(
        (_evaluation("b-1", target_id="target-1", model_id="model-b"),),
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )
    with pytest.raises(SummaryCompatibilityError, match="eligible target set"):
        assert_comparable_summaries(model_a, different_set)


def test_empty_eligible_denominator_is_null_not_zero() -> None:
    summary = summarize_model(
        (
            _evaluation(
                "eval-unknown",
                target_id="target-1",
                truth_eligible=False,
            ),
        ),
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )

    assert summary.eligible_count == 0
    assert summary.common_eligible_set_id.startswith("eligible-set-")
    assert summary.verified_score is None
    assert summary.experimental_score is None


def test_task6_summary_contract_rejects_guessed_numeric_score() -> None:
    summary = summarize_target(
        _evaluation("eval-1", target_id="target-1"),
        aggregation_version="qualitative-counts-v1",
        generated_at=NOW,
    )

    with pytest.raises(ValidationError, match="Task 6 summaries require null"):
        summary.model_copy(update={"experimental_score": 1.0}, deep=True).__class__.model_validate(
            {**summary.model_dump(), "experimental_score": 1.0}
        )
    with pytest.raises(ValidationError, match="version sets must be unique"):
        summary.__class__.model_validate(
            {
                **summary.model_dump(),
                "reference_mapping_versions": ("mapping-v1", "mapping-v1"),
            }
        )
