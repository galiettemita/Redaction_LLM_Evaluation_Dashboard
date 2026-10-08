from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from redaction_lab.contracts import (
    AttemptStatus,
    EvaluationRecord,
    EvaluationStatus,
    ModelAttempt,
    PredictionManifest,
    RedactionTarget,
    ReferenceMapping,
    ReferenceStatus,
    ScopeStatus,
)


NOW = datetime(2026, 10, 7, tzinfo=UTC)


def test_unknown_truth_is_null() -> None:
    mapping = ReferenceMapping(
        mapping_id="map-001",
        mapping_version="mapping-v1",
        target_id="target-001",
        target_version="target-v1",
        reference_document_version_id="reference-v1",
        status=ReferenceStatus.PARTIAL,
        exact_revealed_text=None,
        mapping_method_version="anchor-align-v1",
        provenance="synthetic-test",
    )
    evaluation = EvaluationRecord(
        evaluation_id="evaluation-001",
        evaluation_version="evaluation-v1",
        attempt_id="attempt-001",
        mapping_id=mapping.mapping_id,
        mapping_version=mapping.mapping_version,
        evaluator_version="judge-v1",
        rubric_version="rubric-v1",
        status=EvaluationStatus.UNKNOWN,
        verified_score=None,
        experimental_score=None,
        explanation="Reference is only partly revealed.",
        created_at=NOW,
    )

    assert mapping.exact_revealed_text is None
    assert evaluation.verified_score is None
    assert evaluation.experimental_score is None

    with pytest.raises(ValidationError):
        ReferenceMapping.model_validate(
            {**mapping.model_dump(), "exact_revealed_text": "must not leak"}
        )

    with pytest.raises(ValidationError):
        EvaluationRecord.model_validate(
            {**evaluation.model_dump(), "verified_score": 0.0}
        )


def test_confirmed_truth_preserves_exact_text() -> None:
    exact_text = "  Agent Cedar\n"
    mapping = ReferenceMapping(
        mapping_id="map-002",
        mapping_version="mapping-v1",
        target_id="target-001",
        target_version="target-v1",
        reference_document_version_id="reference-v1",
        status=ReferenceStatus.CONFIRMED,
        exact_revealed_text=exact_text,
        mapping_method_version="anchor-align-v1",
        provenance="synthetic-test",
    )

    assert mapping.exact_revealed_text == exact_text

    with pytest.raises(ValidationError):
        ReferenceMapping.model_validate(
            {**mapping.model_dump(), "exact_revealed_text": "   "}
        )


def test_prediction_manifest_has_no_reference_fields() -> None:
    manifest = PredictionManifest(
        manifest_id="manifest-001",
        manifest_version="prediction-manifest-v1",
        run_id="run-001",
        target_id="target-001",
        target_version="target-v1",
        canonical_document_version_id="canonical-v1",
        canonical_document_hash="a" * 64,
        canonical_redacted_text="Visible text [[TARGET:target-001]].",
        target_marker="[[TARGET:target-001]]",
        other_redaction_markers=("[[REDACTED:target-002]]",),
        prompt_id="prompt-001",
        prompt_version="prompt-v1",
        model_id="synthetic-model",
        settings={"temperature": 0},
    )

    serialized = manifest.model_dump(mode="json")
    assert not {
        "reference_document_version_id",
        "reference_text",
        "exact_revealed_text",
        "evaluation_feedback",
    }.intersection(serialized)

    with pytest.raises(ValidationError):
        PredictionManifest.model_validate(
            {**serialized, "reference_text": "synthetic secret"}
        )


def test_distinct_attempt_statuses() -> None:
    statuses = {
        AttemptStatus.SUCCEEDED,
        AttemptStatus.REFUSED,
        AttemptStatus.TIMEOUT,
        AttemptStatus.ERROR,
        AttemptStatus.MALFORMED,
    }

    attempts = [
        ModelAttempt(
            attempt_id=f"attempt-{status.value.lower()}",
            run_id="run-001",
            target_id="target-001",
            target_version="target-v1",
            model_id="synthetic-model",
            model_config_id="config-v1",
            request_hash="b" * 64,
            response_hash="c" * 64 if status is AttemptStatus.SUCCEEDED else None,
            prediction="synthetic answer"
            if status is AttemptStatus.SUCCEEDED
            else None,
            status=status,
            started_at=NOW,
            completed_at=NOW,
        )
        for status in statuses
    ]

    assert {attempt.status for attempt in attempts} == statuses
    assert AttemptStatus.TIMEOUT is not AttemptStatus.ERROR


def test_target_ids_are_versioned() -> None:
    target = RedactionTarget(
        target_id="target-001",
        target_version="target-v3",
        redacted_document_version_id="document-v2",
        page_index=0,
        normalized_bbox=(0.1, 0.2, 0.3, 0.25),
        visible_context_locator="token:12-18",
        scope_status=ScopeStatus.SUPPORTED,
        detection_method="synthetic-vector-rectangle",
        detection_evidence={"rectangle_count": 1},
        detector_version="detector-v1",
    )

    assert target.model_dump()["target_version"] == "target-v3"


def test_verified_and_experimental_scores_are_separate() -> None:
    experimental = EvaluationRecord(
        evaluation_id="evaluation-002",
        evaluation_version="evaluation-v1",
        attempt_id="attempt-001",
        mapping_id="map-001",
        mapping_version="mapping-v1",
        evaluator_version="judge-v1",
        rubric_version="rubric-v1",
        status=EvaluationStatus.EXPERIMENTAL,
        verified_score=None,
        experimental_score=0.75,
        explanation="Synthetic demonstration rubric only.",
        created_at=NOW,
    )

    assert experimental.verified_score is None
    assert experimental.experimental_score == 0.75

    with pytest.raises(ValidationError):
        EvaluationRecord.model_validate(
            {**experimental.model_dump(), "verified_score": 0.75}
        )
