from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from redaction_lab.contracts import (
    EvaluationRecord,
    SummaryExclusion,
    SummaryLevel,
    SummaryRequest,
)
from redaction_lab.summary import (
    SummaryCompatibilityError,
    assert_comparable_summaries,
    build_authoritative_summary,
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


def _authoritative_evaluation(
    evaluation_id: str,
    *,
    target_id: str,
    document_id: str,
    run_id: str,
    model_id: str = "model-a",
    model_config_id: str = "config-a",
    prompt_version: str = "prompt-v1",
    settings_fingerprint: str = "c" * 64,
) -> EvaluationRecord:
    base = _evaluation(
        evaluation_id,
        target_id=target_id,
        document_id=document_id,
        model_id=model_id,
        model_config_id=model_config_id,
        process_status="NEEDS_REVIEW",
    ).model_dump()
    return EvaluationRecord.model_validate(
        {
            **base,
            "evaluation_version": "qualitative-evaluation-v2",
            "evidence_schema_version": "qualitative-fact-evidence-v2",
            "evaluation_series_key": f"series-{evaluation_id}",
            "job_id": f"job-{evaluation_id}",
            "source_id": f"source-{document_id}",
            "source_version": "prediction-source-v1",
            "source_sha256": "d" * 64,
            "run_id": run_id,
            "run_version": "run-v1",
            "run_digest": "e" * 64,
            "manifest_id": f"manifest-{evaluation_id}",
            "manifest_version": "prediction-manifest-v1",
            "manifest_digest": "f" * 64,
            "canonical_document_hash": "1" * 64,
            "provider_model_id": model_id,
            "prompt_id": "prompt-001",
            "prompt_version": prompt_version,
            "settings_fingerprint": settings_fingerprint,
            "attempt_policy": "one-frozen-attempt",
            "context_policy": "common-full-document",
            "common_context_budget": 4096,
            "tool_permissions": (),
            "prediction_protocol_id": (
                f"protocol-{prompt_version}-{settings_fingerprint[:8]}"
            ),
            "model_provenance_id": f"model-provenance-{model_id}-{model_config_id}",
            "reference_target_id": target_id,
            "reference_target_version": f"{target_id}-v1",
            "mapping_id": f"mapping-{document_id}-{target_id}",
            "mapping_method_version": "text-first-reference-v2",
            "redacted_canonical_hash": "2" * 64,
            "reference_canonical_hash": "3" * 64,
            "source_fact_record_id": f"facts-{document_id}-{target_id}",
            "source_fact_record_version": "source-facts-v1",
            "source_fact_validation_state": None,
            "judge_validation_state": None,
            "qualitative_status": "NEEDS_REVIEW",
        }
    )


def _request(*evaluations: EvaluationRecord) -> SummaryRequest:
    first = evaluations[0]
    return SummaryRequest(
        project_id=first.project_id,
        summary_level="MODEL",
        scope_id=first.model_id,
        scope_version=first.model_config_id,
        members=tuple(
            {"attempt_id": item.attempt_id, "evaluation_id": item.evaluation_id}
            for item in evaluations
        ),
        aggregation_version="qualitative-counts-v2",
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


def test_authoritative_model_summary_accepts_compatible_distinct_runs() -> None:
    first = _authoritative_evaluation(
        "eval-1", target_id="target-1", document_id="document-1", run_id="run-1"
    )
    second = _authoritative_evaluation(
        "eval-2", target_id="target-2", document_id="document-2", run_id="run-2"
    )

    summary = build_authoritative_summary(
        _request(first, second), (second, first), (), generated_at=NOW
    )

    assert summary.contributing_run_ids == ("run-1", "run-2")
    assert summary.run_id is None
    assert summary.requested_count == summary.completed_count == 2
    assert summary.excluded_count == 0
    assert len(summary.eligible_provenance_keys) == 2
    assert summary.verified_score is summary.experimental_score is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("prompt_id", "prompt-002"),
        ("prompt_version", "prompt-v2"),
        ("settings_fingerprint", "9" * 64),
        ("condition_id", "different-condition"),
        ("attempt_policy", "different-attempt-policy"),
        ("context_policy", "different-context"),
        ("common_context_budget", 2048),
        ("tool_permissions", ("search",)),
        ("model_config_id", "config-b"),
        ("rubric_version", "rubric-v2"),
        ("judge_version", "judge-v2"),
        ("mapping_method_version", "mapping-method-v2"),
    ],
)
def test_authoritative_summary_rejects_incompatible_protocol_or_evidence(
    field: str, value: object
) -> None:
    first = _authoritative_evaluation(
        "eval-1", target_id="target-1", document_id="document-1", run_id="run-1"
    )
    second = _authoritative_evaluation(
        "eval-2", target_id="target-2", document_id="document-2", run_id="run-2"
    ).model_copy(update={field: value})

    with pytest.raises(SummaryCompatibilityError, match=field):
        build_authoritative_summary(
            _request(first, second), (first, second), (), generated_at=NOW
        )


def test_separate_model_runs_compare_only_on_exact_reference_provenance_set() -> None:
    model_a_evaluations = tuple(
        _authoritative_evaluation(
            f"a-{index}",
            target_id=f"target-{index}",
            document_id=f"document-{index}",
            run_id=f"run-a-{index}",
        )
        for index in (1, 2)
    )
    model_b_evaluations = tuple(
        _authoritative_evaluation(
            f"b-{index}",
            target_id=f"target-{index}",
            document_id=f"document-{index}",
            run_id=f"run-b-{index}",
            model_id="model-b",
            model_config_id="config-b",
        )
        for index in (1, 2)
    )
    model_a = build_authoritative_summary(
        _request(*model_a_evaluations), model_a_evaluations, (), generated_at=NOW
    )
    model_b = build_authoritative_summary(
        _request(*model_b_evaluations), model_b_evaluations, (), generated_at=NOW
    )

    assert model_a.contributing_run_ids != model_b.contributing_run_ids
    assert_comparable_summaries(model_a, model_b)

    changed_reference = model_b_evaluations[1].model_copy(
        update={"reference_canonical_hash": "8" * 64}
    )
    changed = build_authoritative_summary(
        _request(model_b_evaluations[0], changed_reference),
        (model_b_evaluations[0], changed_reference),
        (),
        generated_at=NOW,
    )
    with pytest.raises(SummaryCompatibilityError, match="eligible reference set"):
        assert_comparable_summaries(model_a, changed)


def test_authoritative_summary_requires_exact_attempt_partition() -> None:
    evaluation = _authoritative_evaluation(
        "eval-1", target_id="target-1", document_id="document-1", run_id="run-1"
    )
    request = SummaryRequest(
        project_id=evaluation.project_id,
        summary_level="MODEL",
        scope_id=evaluation.model_id,
        scope_version=evaluation.model_config_id,
        members=(
            {"attempt_id": evaluation.attempt_id, "evaluation_id": evaluation.evaluation_id},
            {"attempt_id": "attempt-missing", "evaluation_id": None},
        ),
        aggregation_version="qualitative-counts-v2",
    )
    summary = build_authoritative_summary(
        request,
        (evaluation,),
        (
            SummaryExclusion(
                attempt_id="attempt-missing", reason="NO_EVALUATION"
            ),
        ),
        generated_at=NOW,
    )

    assert summary.requested_count == 2
    assert summary.excluded_count == 1
    assert summary.completed_count == 1
    assert summary.eligible_count == 1
