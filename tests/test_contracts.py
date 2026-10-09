from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from redaction_lab import contracts


NOW = datetime(2026, 10, 7, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


def _confirmed_mapping(**overrides: object) -> contracts.ReferenceMapping:
    values: dict[str, object] = {
        "mapping_id": "map-001",
        "mapping_version": "mapping-v1",
        "project_id": "project-001",
        "target_id": "target-001",
        "target_version": "target-v1",
        "redacted_document_version_id": "redacted-v1",
        "reference_document_version_id": "reference-v1",
        "status": "CONFIRMED",
        "scoreability": "SCOREABLE",
        "exact_revealed_text": "Agent Cedar",
        "reference_token_locator": "tokens:20-21",
        "redacted_canonical_version_id": "redacted-canonical-v1",
        "reference_canonical_version_id": "reference-canonical-v1",
        "redacted_canonical_hash": HASH_A,
        "reference_canonical_hash": HASH_B,
        "global_alignment_version": "global-align-v1",
        "left_anchor_evidence": ("synthetic courier was",),
        "right_anchor_evidence": ("at 09:00",),
        "left_document_boundary": False,
        "right_document_boundary": False,
        "candidate_unique": True,
        "complete_revelation": True,
        "readable": True,
        "reliably_aligned": True,
        "mapping_method_version": "anchor-align-v1",
        "provenance": "synthetic-test",
    }
    values.update(overrides)
    return contracts.ReferenceMapping.model_validate(values)


def _manifest(**overrides: object) -> contracts.PredictionManifest:
    values: dict[str, object] = {
        "manifest_id": "manifest-001",
        "manifest_version": "prediction-manifest-v1",
        "project_id": "project-001",
        "run_id": "run-001",
        "target_id": "target-001",
        "target_version": "target-v1",
        "canonical_document_version_id": "canonical-v1",
        "canonical_document_hash": HASH_A,
        "canonical_redacted_text": "Visible text [[TARGET:target-001]].",
        "target_marker": "[[TARGET:target-001]]",
        "other_redaction_markers": ("[[REDACTED:target-002]]",),
        "prompt_id": "prompt-001",
        "prompt_version": "prompt-v1",
        "model_id": "synthetic-model",
        "settings": {"temperature": 0},
    }
    values.update(overrides)
    return contracts.PredictionManifest.model_validate(values)


def _run_definition(**overrides: object) -> contracts.RunDefinition:
    values: dict[str, object] = {
        "run_id": "run-001",
        "run_version": "run-v1",
        "project_id": "project-001",
        "target_versions": ("target-v1",),
        "model_ids": ("synthetic-model",),
        "experiment_condition": "redacted-document-only",
        "canonical_document_version_id": "canonical-v1",
        "canonical_document_hash": HASH_A,
        "common_context_budget": 4096,
        "context_policy": "common-full-document",
        "prompt_id": "prompt-001",
        "prompt_version": "prompt-v1",
        "settings": {"temperature": 0},
        "attempt_policy": "one-frozen-attempt",
        "tool_permissions": (),
        "budget_label": "synthetic-no-spend",
        "created_by": "test-suite",
        "created_at": NOW,
    }
    values.update(overrides)
    return contracts.RunDefinition.model_validate(values)


def test_model_attempt_provider_identity_is_optional_for_legacy_rows() -> None:
    values = {
        "attempt_id": "attempt-001",
        "project_id": "project-001",
        "run_id": "run-001",
        "target_id": "target-001",
        "target_version": "target-v1",
        "model_id": "requested-model",
        "model_config_id": "config-v1",
        "request_hash": HASH_A,
        "response_hash": HASH_B,
        "prediction": "guess",
        "status": "SUCCEEDED",
        "usage": {},
        "started_at": NOW,
        "completed_at": NOW,
    }

    legacy = contracts.ModelAttempt.model_validate(values)
    verified = contracts.ModelAttempt.model_validate(
        {**values, "provider_model_id": "requested-model"}
    )

    assert legacy.provider_model_id is None
    assert verified.model_id == verified.provider_model_id == "requested-model"


def test_model_attempt_rejects_success_with_mismatched_provider_identity() -> None:
    with pytest.raises(ValidationError, match="provider model"):
        contracts.ModelAttempt.model_validate(
            {
                "attempt_id": "attempt-001",
                "project_id": "project-001",
                "run_id": "run-001",
                "target_id": "target-001",
                "target_version": "target-v1",
                "model_id": "requested-model",
                "provider_model_id": "different-model",
                "model_config_id": "config-v1",
                "request_hash": HASH_A,
                "response_hash": HASH_B,
                "prediction": "guess",
                "status": "SUCCEEDED",
                "usage": {},
                "started_at": NOW,
                "completed_at": NOW,
            }
        )


def _evaluation(**overrides: object) -> contracts.EvaluationRecord:
    values: dict[str, object] = {
        "evaluation_id": "evaluation-001",
        "evaluation_version": "evaluation-v1",
        "project_id": "project-001",
        "attempt_id": "attempt-001",
        "attempt_status": "SUCCEEDED",
        "mapping_id": None,
        "mapping_version": None,
        "mapping_status": None,
        "mapping_scoreability": None,
        "evaluator_version": "judge-v1",
        "rubric_version": "rubric-v1",
        "process_status": "COMPLETE",
        "score_status": "NONE",
        "score_scale_id": None,
        "research_validation_id": None,
        "verified_score": None,
        "experimental_score": None,
        "fact_comparisons": (),
        "explanation": "Accuracy unknown because truth is unavailable.",
        "created_at": NOW,
    }
    values.update(overrides)
    return contracts.EvaluationRecord.model_validate(values)


def test_unknown_truth_is_null() -> None:
    mapping = contracts.ReferenceMapping(
        mapping_id="map-unknown",
        mapping_version="mapping-v1",
        project_id="project-001",
        target_id="target-001",
        target_version="target-v1",
        redacted_document_version_id="redacted-v1",
        reference_document_version_id="reference-v1",
        status="PARTIAL",
        scoreability="NOT_SCOREABLE",
        exact_revealed_text=None,
        mapping_method_version="anchor-align-v1",
        provenance="synthetic-test",
    )
    evaluation = _evaluation(
        mapping_id=mapping.mapping_id,
        mapping_version=mapping.mapping_version,
        mapping_status=mapping.status,
        mapping_scoreability=mapping.scoreability,
        explanation="Reference is only partly revealed.",
    )

    assert mapping.exact_revealed_text is None
    assert evaluation.verified_score is None
    assert evaluation.experimental_score is None

    with pytest.raises(ValidationError):
        contracts.ReferenceMapping.model_validate(
            {**mapping.model_dump(), "exact_revealed_text": "must not leak"}
        )
    with pytest.raises(ValidationError):
        contracts.EvaluationRecord.model_validate(
            {**evaluation.model_dump(), "verified_score": 0.0}
        )


def test_confirmed_truth_requires_complete_auditable_evidence() -> None:
    mapping = _confirmed_mapping(exact_revealed_text="  Agent Cedar\n")
    assert mapping.exact_revealed_text == "  Agent Cedar\n"

    required_fields = (
        "project_id",
        "redacted_document_version_id",
        "reference_document_version_id",
        "reference_token_locator",
        "redacted_canonical_version_id",
        "reference_canonical_version_id",
        "redacted_canonical_hash",
        "reference_canonical_hash",
        "global_alignment_version",
        "mapping_method_version",
    )
    for field in required_fields:
        with pytest.raises(ValidationError):
            _confirmed_mapping(**{field: None})

    for field in (
        "candidate_unique",
        "complete_revelation",
        "readable",
        "reliably_aligned",
    ):
        with pytest.raises(ValidationError):
            _confirmed_mapping(**{field: False})

    with pytest.raises(ValidationError):
        _confirmed_mapping(exact_revealed_text="   ")


def test_confirmed_truth_requires_anchors_or_explicit_boundaries() -> None:
    with pytest.raises(ValidationError):
        _confirmed_mapping(left_anchor_evidence=(), left_document_boundary=False)
    with pytest.raises(ValidationError):
        _confirmed_mapping(right_anchor_evidence=(), right_document_boundary=False)

    boundary_mapping = _confirmed_mapping(
        left_anchor_evidence=(), left_document_boundary=True
    )
    assert boundary_mapping.left_document_boundary is True


@pytest.mark.parametrize(
    "payload",
    [
        {"reference_text": "LEAK"},
        {"nested": {"exact_revealed_text": "LEAK"}},
        {"evaluation_feedback": "LEAK"},
        {"retrieval": {"answer": "LEAK"}},
        {"web_context": "LEAK"},
    ],
)
def test_prediction_settings_reject_unapproved_or_answer_bearing_fields(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        _manifest(settings=payload)
    with pytest.raises(ValidationError):
        _run_definition(settings=payload)


def test_prediction_manifest_serializes_only_allowlisted_settings() -> None:
    manifest = _manifest(settings={"temperature": 0})
    serialized = manifest.model_dump(mode="json")

    assert serialized["settings"]["temperature"] == 0
    assert "reference_text" not in str(serialized)


def test_contract_records_are_deeply_immutable() -> None:
    target = contracts.RedactionTarget(
        target_id="target-001",
        target_version="target-v1",
        project_id="project-001",
        redacted_document_version_id="redacted-v1",
        page_index=0,
        normalized_bbox=(0.1, 0.2, 0.3, 0.25),
        visible_context_locator="token:12-18",
        scope_status="SUPPORTED",
        detection_method="synthetic-vector-rectangle",
        detection_evidence={"rectangle_count": 1},
        detector_version="detector-v1",
    )
    manifest = _manifest()
    run_definition = _run_definition()
    attempt = contracts.ModelAttempt(
        attempt_id="attempt-001",
        project_id="project-001",
        run_id="run-001",
        target_id="target-001",
        target_version="target-v1",
        model_id="synthetic-model",
        model_config_id="config-v1",
        request_hash=HASH_A,
        response_hash=HASH_B,
        prediction="synthetic answer",
        status="SUCCEEDED",
        usage={"input_tokens": 10, "output_tokens": 2},
        started_at=NOW,
        completed_at=NOW,
    )
    evaluation = _evaluation(
        fact_comparisons=(
            {
                "fact_id": "fact-001",
                "reference_quote": "Agent Cedar",
                "prediction_excerpt": "Agent Cedar",
                "comparison_label": "synthetic-equivalent",
            },
        )
    )

    for mutation in (
        lambda: setattr(target.detection_evidence, "rectangle_count", 2),
        lambda: setattr(manifest.settings, "temperature", 0.5),
        lambda: setattr(run_definition.settings, "temperature", 0.5),
        lambda: setattr(attempt.usage, "input_tokens", 99),
        lambda: setattr(
            evaluation.fact_comparisons[0],
            "comparison_label",
            "silently-changed",
        ),
    ):
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            mutation()


def test_distinct_attempt_statuses() -> None:
    statuses = {
        contracts.AttemptStatus.SUCCEEDED,
        contracts.AttemptStatus.REFUSED,
        contracts.AttemptStatus.TIMEOUT,
        contracts.AttemptStatus.ERROR,
        contracts.AttemptStatus.MALFORMED,
    }
    attempts = [
        contracts.ModelAttempt(
            attempt_id=f"attempt-{status.value.lower()}",
            project_id="project-001",
            run_id="run-001",
            target_id="target-001",
            target_version="target-v1",
            model_id="synthetic-model",
            model_config_id="config-v1",
            request_hash=HASH_A,
            response_hash=HASH_B
            if status is contracts.AttemptStatus.SUCCEEDED
            else None,
            prediction="synthetic answer"
            if status is contracts.AttemptStatus.SUCCEEDED
            else None,
            status=status,
            started_at=NOW,
            completed_at=NOW,
        )
        for status in statuses
    ]

    assert {attempt.status for attempt in attempts} == statuses
    assert contracts.AttemptStatus.TIMEOUT is not contracts.AttemptStatus.ERROR


def test_evaluator_workflow_and_score_channels_are_independent() -> None:
    assert {status.value for status in contracts.EvaluationProcessStatus} == {
        "COMPLETE",
        "NEEDS_REVIEW",
        "DISAGREEMENT",
        "ERROR",
    }
    for process_status in contracts.EvaluationProcessStatus:
        evaluation = _evaluation(process_status=process_status)
        assert evaluation.score_status is contracts.ScoreStatus.NONE
        assert evaluation.verified_score is None
        assert evaluation.experimental_score is None


def test_verified_evaluation_requires_scoreable_mapping_and_successful_attempt() -> None:
    valid = {
        "mapping_id": "map-001",
        "mapping_version": "mapping-v1",
        "mapping_status": "CONFIRMED",
        "mapping_scoreability": "SCOREABLE",
        "attempt_status": "SUCCEEDED",
        "score_status": "VERIFIED",
        "score_scale_id": "research-scale-v1",
        "research_validation_id": "research-release-v1",
        "verified_score": 73.5,
    }
    assert _evaluation(**valid).verified_score == 73.5

    for field, invalid_value in (
        ("mapping_id", None),
        ("mapping_version", None),
        ("mapping_status", "PARTIAL"),
        ("mapping_scoreability", "NOT_SCOREABLE"),
        ("attempt_status", "TIMEOUT"),
        ("research_validation_id", None),
        ("score_scale_id", None),
    ):
        with pytest.raises(ValidationError):
            _evaluation(**{**valid, field: invalid_value})


def test_numeric_score_requires_a_versioned_scale_but_not_an_unapproved_range() -> None:
    confirmed_truth = {
        "mapping_id": "map-001",
        "mapping_version": "mapping-v1",
        "mapping_status": "CONFIRMED",
        "mapping_scoreability": "SCOREABLE",
    }
    low = _evaluation(
        **confirmed_truth,
        score_status="EXPERIMENTAL",
        score_scale_id="signed-diagnostic-v1",
        experimental_score=-5.0,
    )
    high = _evaluation(
        **confirmed_truth,
        score_status="EXPERIMENTAL",
        score_scale_id="percentage-demo-v1",
        experimental_score=73.5,
    )

    assert low.experimental_score == -5.0
    assert high.experimental_score == 73.5
    with pytest.raises(ValidationError):
        _evaluation(
            **confirmed_truth,
            score_status="EXPERIMENTAL",
            experimental_score=5.0,
        )


def _summary_values() -> dict[str, object]:
    return {
        "summary_id": "summary-001",
        "summary_version": "summary-v1",
        "project_id": "project-001",
        "summary_level": "DOCUMENT",
        "scope_id": "redacted-v1",
        "scope_version": "document-v1",
        "included_evaluation_ids": ("evaluation-001", "evaluation-002"),
        "eligible_evaluation_ids": ("evaluation-001",),
        "common_eligible_set_id": "common-set-v1",
        "model_id": "synthetic-model",
        "condition_id": "condition-v1",
        "rubric_version": "rubric-v1",
        "aggregation_version": "unweighted-counts-v1",
        "requested_count": 2,
        "eligible_count": 1,
        "unknown_count": 1,
        "refused_count": 0,
        "timeout_count": 0,
        "malformed_count": 0,
        "error_count": 0,
        "needs_review_count": 0,
        "disagreement_count": 0,
        "score_scale_id": "percentage-demo-v1",
        "experimental_score": 73.5,
        "generated_at": NOW,
        "freshness": "current",
    }


def test_summary_has_explicit_scope_common_set_and_valid_denominator() -> None:
    summary = contracts.SummarySnapshot.model_validate(_summary_values())

    assert summary.summary_level is contracts.SummaryLevel.DOCUMENT
    assert summary.eligible_count == len(summary.eligible_evaluation_ids)

    with pytest.raises(ValidationError):
        contracts.SummarySnapshot.model_validate(
            {**_summary_values(), "eligible_count": 2}
        )
    with pytest.raises(ValidationError):
        contracts.SummarySnapshot.model_validate(
            {**_summary_values(), "requested_count": 3}
        )


def test_zero_eligible_summary_has_null_scores() -> None:
    values = {
        **_summary_values(),
        "summary_level": "MODEL",
        "scope_id": "model-scope-001",
        "scope_version": "scope-v1",
        "included_evaluation_ids": ("evaluation-unknown",),
        "eligible_evaluation_ids": (),
        "common_eligible_set_id": "common-set-empty-v1",
        "requested_count": 1,
        "eligible_count": 0,
        "unknown_count": 1,
        "score_scale_id": None,
        "verified_score": None,
        "experimental_score": None,
    }
    assert contracts.SummarySnapshot.model_validate(values).verified_score is None

    with pytest.raises(ValidationError):
        contracts.SummarySnapshot.model_validate(
            {**values, "score_scale_id": "scale-v1", "verified_score": 1.0}
        )


def test_relationship_records_carry_project_scope() -> None:
    relationship_records = (
        contracts.RedactionTarget,
        contracts.ReferenceMapping,
        contracts.CanonicalRedactedDocument,
        contracts.RunDefinition,
        contracts.PredictionManifest,
        contracts.ModelAttempt,
        contracts.EvaluationRecord,
        contracts.SummarySnapshot,
        contracts.JobState,
    )
    for record in relationship_records:
        assert "project_id" in record.model_fields


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("manifest_id", ""),
        ("manifest_version", "   "),
        ("project_id", ""),
        ("run_id", ""),
        ("target_id", ""),
        ("target_version", ""),
        ("model_id", ""),
        ("prompt_id", ""),
        ("target_marker", ""),
    ],
)
def test_critical_manifest_identifiers_are_nonblank(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        _manifest(**{field: value})


def test_target_ids_are_versioned_and_project_scoped() -> None:
    target = contracts.RedactionTarget(
        target_id="target-001",
        target_version="target-v3",
        project_id="project-001",
        redacted_document_version_id="document-v2",
        page_index=0,
        normalized_bbox=(0.1, 0.2, 0.3, 0.25),
        visible_context_locator="token:12-18",
        scope_status="SUPPORTED",
        detection_method="synthetic-vector-rectangle",
        detection_evidence={"rectangle_count": 1},
        detector_version="detector-v1",
    )

    assert target.target_version == "target-v3"
    assert target.project_id == "project-001"


def test_task6_fact_evidence_requires_typed_label_and_provenance() -> None:
    comparison = contracts.FactComparison(
        fact_id="fact-001",
        reference_quote="Agent Cedar",
        reference_proposition="The courier was Agent Cedar.",
        reference_quote_locator="chars:0-11",
        critical_dimensions=("identity",),
        prediction_excerpt="Agent Cedar",
        comparison_label="SUPPORTED",
        evidence_label="SUPPORTED",
        rationale="Synthetic mock evidence only.",
        provisional=True,
    )

    assert comparison.evidence_label is contracts.FactEvidenceLabel.SUPPORTED
    with pytest.raises(ValidationError):
        comparison.evidence_label = contracts.FactEvidenceLabel.MISSING
    with pytest.raises(ValidationError, match="evidence label"):
        contracts.FactComparison.model_validate(
            {**comparison.model_dump(), "comparison_label": "CONTRADICTED"}
        )


def test_task6_evaluation_schema_requires_complete_binding_and_null_scores() -> None:
    values = {
        **_evaluation().model_dump(),
        "evidence_schema_version": "qualitative-fact-evidence-v1",
        "run_id": "run-v1",
        "target_id": "target-001",
        "target_version": "target-v1",
        "redacted_document_version_id": "redacted-v1",
        "redacted_canonical_version_id": "canonical-v1",
        "model_id": "model-v1",
        "model_config_id": "config-v1",
        "condition_id": "condition-v1",
        "reference_trust": "UNTRUSTED_OR_UNAVAILABLE",
        "judge_id": "judge",
        "judge_version": "judge-v1",
        "qualitative_status": "ACCURACY_UNKNOWN",
        "attempt_request_hash": HASH_A,
    }
    record = contracts.EvaluationRecord.model_validate(values)
    assert record.verified_score is record.experimental_score is None

    for field in (
        "run_id",
        "target_id",
        "target_version",
        "redacted_document_version_id",
        "model_id",
        "model_config_id",
        "condition_id",
        "reference_trust",
        "judge_id",
        "judge_version",
        "qualitative_status",
        "attempt_request_hash",
    ):
        with pytest.raises(ValidationError, match="Task 6 evidence"):
            contracts.EvaluationRecord.model_validate({**values, field: None})

    with pytest.raises(ValidationError, match="Task 6 evidence requires null"):
        contracts.EvaluationRecord.model_validate(
            {
                **values,
                "mapping_id": "mapping-1",
                "mapping_version": "mapping-v1",
                "mapping_status": "CONFIRMED",
                "mapping_scoreability": "SCOREABLE",
                "score_status": "EXPERIMENTAL",
                "score_scale_id": "forbidden-scale",
                "experimental_score": 1.0,
            }
        )

    with pytest.raises(ValidationError, match="approved synthetic trust"):
        contracts.EvaluationRecord.model_validate(
            {
                **values,
                "reference_trust": "APPROVED_SYNTHETIC_PAIR",
                "mapping_id": "mapping-1",
                "mapping_version": "mapping-v1",
                "mapping_status": "CONFLICTING",
                "mapping_scoreability": "NOT_SCOREABLE",
            }
        )
