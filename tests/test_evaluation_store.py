from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
import sqlite3

import pytest

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.canonical import canonicalize_redacted
from redaction_lab.contracts import (
    AttemptStatus,
    EvaluationProcessStatus,
    RunDefinition,
    ScoreStatus,
    SummaryRequest,
    TokenUsage,
)
from redaction_lab.evaluation_store import EvaluationStore
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.judges.base import JudgeEvidence, SourceFact
from redaction_lab.pdf_detector import DetectionStatus, detect_targets
from redaction_lab.reference import align_reference
from redaction_lab.store import RunStore
from redaction_lab.summary import assert_comparable_summaries
from redaction_lab.worker import run_pending_once


PROJECT_ID = "project-rl-mvp-003"
REFERENCE_VERSION_ID = "reference-document-v1"
REFERENCE_CANONICAL_ID = "reference-canonical-v1"
RUBRIC_VERSION = "fact-evidence-rubric-v0.1-proposed"
NOW = datetime(2026, 10, 11, tzinfo=UTC)


class StoredAttemptAdapter(PredictionAdapter):
    model_config_id = "synthetic-config-v1"

    def request_hash(self, manifest) -> str:
        return sha256(
            (manifest.model_dump_json() + self.model_config_id).encode()
        ).hexdigest()

    async def predict(self, manifest) -> PredictionResponse:
        return PredictionResponse(
            status=AttemptStatus.SUCCEEDED,
            request_hash=self.request_hash(manifest),
            response_hash=sha256(b"synthetic raw response").hexdigest(),
            prediction="Agent Cedar",
            usage=TokenUsage(input_tokens=8, output_tokens=2, total_tokens=10),
            model_config_id=self.model_config_id,
            started_at=NOW,
            completed_at=NOW,
            provider_model_id=manifest.model_id,
        )


class SupportedMockJudge:
    judge_id = "synthetic-mock-judge"
    judge_version = "synthetic-mock-judge-v1"

    def assess(self, reference, prediction) -> JudgeEvidence:
        return JudgeEvidence(
            evidence_label="SUPPORTED",
            prediction_excerpt=prediction,
            rationale="Caller-supplied synthetic evidence only.",
        )


class DisagreementMockJudge(SupportedMockJudge):
    def assess(self, reference, prediction) -> JudgeEvidence:
        return JudgeEvidence(
            evidence_label="NEEDS_REVIEW",
            prediction_excerpt=prediction,
            rationale="Synthetic mock judges disagree.",
            disagreement=True,
        )


def _run(
    source,
    *,
    run_id: str = "run-document-1",
    model_id: str = "synthetic-model-v1",
) -> RunDefinition:
    return RunDefinition(
        run_id=run_id,
        run_version="run-v1",
        project_id=source.project_id,
        target_versions=source.target_versions,
        model_ids=(model_id,),
        experiment_condition="redacted-document-only",
        canonical_document_version_id=(
            source.canonical_document.canonical_document_version_id
        ),
        canonical_document_hash=source.canonical_document.canonical_hash,
        common_context_budget=4096,
        context_policy="common-full-document",
        prompt_id="prompt-001",
        prompt_version="prompt-v1",
        settings={"temperature": 0},
        attempt_policy="one-frozen-attempt",
        tool_permissions=(),
        budget_label="synthetic-no-spend",
        created_by="trusted-test-harness",
        created_at=NOW,
    )


def _authoritative_inputs(tmp_path):
    redacted_path, reference_path = make_synthetic_pair("two_boxes", tmp_path)
    redacted_pdf = redacted_path.read_bytes()
    reference_pdf = reference_path.read_bytes()
    db_path = tmp_path / "evidence.sqlite3"
    run_store = RunStore(db_path)
    source_id = run_store.ingest_redacted_pdf(redacted_pdf, project_id=PROJECT_ID)
    source = run_store.source(source_id)
    run = _run(source)
    job_id = run_store.enqueue(source_id, source.targets[0].target_id, run)
    assert asyncio.run(run_pending_once(run_store, StoredAttemptAdapter())) is True
    attempt = run_store.attempts()[0]

    registry_detection = detect_targets(
        redacted_pdf,
        project_id=PROJECT_ID,
        redacted_document_version_id="redacted-document-v1",
    )
    assert registry_detection.status is DetectionStatus.SUPPORTED
    registry_canonical = canonicalize_redacted(
        redacted_pdf,
        registry_detection,
        project_id=PROJECT_ID,
        redacted_document_version_id="redacted-document-v1",
        canonical_document_version_id="redacted-canonical-v1",
    )
    mappings = align_reference(
        registry_canonical,
        reference_pdf,
        redacted_pdf=redacted_pdf,
        targets=registry_detection.targets,
        reference_document_version_id=REFERENCE_VERSION_ID,
        reference_canonical_version_id=REFERENCE_CANONICAL_ID,
        mapping_version="mapping-v1",
    )
    mapping = mappings[0]
    fact = SourceFact(
        fact_id="courier-identity",
        reference_proposition="Agent Birch authorized 99 missiles.",
        reference_quote="Agent Cedar",
        reference_quote_locator="chars:0-11",
        critical_dimensions=("identity",),
    )
    return (
        db_path,
        run_store,
        source,
        run,
        job_id,
        attempt,
        mapping,
        fact,
        redacted_pdf,
        reference_pdf,
    )


def _evaluate(store: EvaluationStore, inputs):
    (
        _,
        _,
        _,
        _,
        _,
        attempt,
        mapping,
        fact,
        redacted_pdf,
        reference_pdf,
    ) = inputs
    source_facts = store.record_source_facts(
        mapping,
        facts=(fact,),
        rubric_version=RUBRIC_VERSION,
        source_fact_record_version="source-facts-v1",
    )
    return store.evaluate_and_store(
        project_id=PROJECT_ID,
        attempt_id=attempt.attempt_id,
        mapping=mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        source_fact_record_id=source_facts.source_fact_record_id,
        judge=SupportedMockJudge(),
        evaluator_version="qualitative-evaluator-v2",
        rubric_version=RUBRIC_VERSION,
    )


def test_evaluation_store_binds_authentic_attempt_and_unvalidated_evidence(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path, _, source, run, job_id, attempt, *_ = inputs
    store = EvaluationStore(db_path)

    evaluation = _evaluate(store, inputs)

    assert evaluation.attempt_id == attempt.attempt_id
    assert evaluation.job_id == job_id
    assert evaluation.source_id == source.source_id
    assert evaluation.source_sha256 == source.source_sha256
    assert evaluation.redacted_canonical_version_id == (
        source.canonical_document.canonical_document_version_id
    )
    assert evaluation.mapping_redacted_canonical_version_id == "redacted-canonical-v1"
    assert evaluation.run_id == run.run_id
    assert evaluation.condition_id == run.experiment_condition
    assert evaluation.prompt_id == run.prompt_id
    assert evaluation.prompt_version == run.prompt_version
    assert evaluation.process_status is EvaluationProcessStatus.NEEDS_REVIEW
    assert evaluation.qualitative_status == "UNVALIDATED_MOCK_EVIDENCE"
    assert evaluation.source_fact_validation_state == "UNVALIDATED_SYNTHETIC"
    assert evaluation.judge_validation_state == "UNVALIDATED_SYNTHETIC"
    assert evaluation.score_status is ScoreStatus.NONE
    assert evaluation.verified_score is evaluation.experimental_score is None
    assert store.get_evaluation(
        evaluation.evaluation_id, project_id=PROJECT_ID
    ) == evaluation


def test_evaluation_store_rejects_forged_attempt_and_cross_project_access(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path, _, _, _, _, attempt, mapping, fact, redacted_pdf, reference_pdf = inputs
    store = EvaluationStore(db_path)
    facts = store.record_source_facts(
        mapping,
        facts=(fact,),
        rubric_version=RUBRIC_VERSION,
        source_fact_record_version="source-facts-v1",
    )

    for attempt_id, project_id in (
        ("attempt-forged", PROJECT_ID),
        (attempt.attempt_id, "project-other"),
    ):
        with pytest.raises((KeyError, ValueError)):
            store.evaluate_and_store(
                project_id=project_id,
                attempt_id=attempt_id,
                mapping=mapping,
                redacted_pdf=redacted_pdf,
                reference_pdf=reference_pdf,
                source_fact_record_id=facts.source_fact_record_id,
                judge=SupportedMockJudge(),
                evaluator_version="qualitative-evaluator-v2",
                rubric_version=RUBRIC_VERSION,
            )


def test_evaluation_store_replay_is_deterministic_and_rows_are_immutable(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path = inputs[0]
    store = EvaluationStore(db_path)

    first = _evaluate(store, inputs)
    second = _evaluate(EvaluationStore(db_path), inputs)

    assert first == second
    assert first.evaluation_id.startswith("evaluation-")
    assert first.evaluation_series_key.startswith("evaluation-series-")
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT count(*) FROM evaluations").fetchone()[0] == 1
    assert connection.execute("SELECT count(*) FROM source_fact_records").fetchone()[0] == 1
    for sql in (
        "UPDATE evaluations SET payload_json = '{}'",
        "DELETE FROM evaluations",
        "UPDATE source_fact_records SET payload_json = '{}'",
        "DELETE FROM source_fact_records",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(sql)
    connection.close()


def test_evaluation_store_has_no_caller_record_save_path_and_rolls_back_failure(
    tmp_path,
) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path, _, _, _, _, attempt, mapping, fact, redacted_pdf, reference_pdf = inputs
    store = EvaluationStore(db_path)
    facts = store.record_source_facts(
        mapping,
        facts=(fact,),
        rubric_version=RUBRIC_VERSION,
        source_fact_record_version="source-facts-v1",
    )

    assert not hasattr(store, "save_evaluation")
    with pytest.raises(ValueError, match="redacted PDF"):
        store.evaluate_and_store(
            project_id=PROJECT_ID,
            attempt_id=attempt.attempt_id,
            mapping=mapping,
            redacted_pdf=redacted_pdf + b"changed",
            reference_pdf=reference_pdf,
            source_fact_record_id=facts.source_fact_record_id,
            judge=SupportedMockJudge(),
            evaluator_version="qualitative-evaluator-v2",
            rubric_version=RUBRIC_VERSION,
        )
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT count(*) FROM evaluations").fetchone()[0] == 0
    connection.close()


def test_summary_store_binds_exact_evaluations_and_explicit_exclusions(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path, run_store, source, run, _, _, _, _, _, _ = inputs
    store = EvaluationStore(db_path)
    evaluation = _evaluate(store, inputs)
    excluded_run = _run(source, run_id="run-excluded-document")
    missing_job_id = run_store.enqueue(
        source.source_id, source.targets[1].target_id, excluded_run
    )
    assert asyncio.run(run_pending_once(run_store, StoredAttemptAdapter())) is True
    missing_attempt_id = run_store.job(missing_job_id).attempt_id
    assert missing_attempt_id is not None
    request = SummaryRequest(
        project_id=PROJECT_ID,
        summary_level="MODEL",
        scope_id=evaluation.model_id,
        scope_version=evaluation.model_config_id,
        members=(
            {
                "attempt_id": evaluation.attempt_id,
                "evaluation_id": evaluation.evaluation_id,
            },
            {"attempt_id": missing_attempt_id, "evaluation_id": None},
        ),
        aggregation_version="qualitative-counts-v2",
    )

    summary = store.build_summary(request)
    reopened = EvaluationStore(db_path).get_summary(
        summary.summary_id,
        project_id=PROJECT_ID,
        expected_compatibility_profile_id=summary.compatibility_profile_id,
    )

    assert reopened == summary
    assert summary.included_evaluation_ids == (evaluation.evaluation_id,)
    assert summary.requested_count == 2
    assert summary.excluded_count == 1
    assert summary.exclusions[0].attempt_id == missing_attempt_id
    assert summary.contributing_run_ids == tuple(
        sorted((run.run_id, excluded_run.run_id))
    )
    assert summary.needs_review_count == 1
    assert summary.eligible_count == 1
    assert not hasattr(store, "save_summary")
    with pytest.raises(ValueError, match="stale"):
        store.get_summary(
            summary.summary_id,
            project_id=PROJECT_ID,
            expected_compatibility_profile_id="different-profile",
        )
    with pytest.raises(KeyError):
        store.build_summary(
            SummaryRequest.model_validate(
                {
                    **request.model_dump(),
                    "members": (
                        {
                            "attempt_id": evaluation.attempt_id,
                            "evaluation_id": "evaluation-fictional",
                        },
                    ),
                }
            )
        )


def test_summary_rejects_incompatible_excluded_attempt(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path, run_store, source, _, _, _, _, _, _, _ = inputs
    store = EvaluationStore(db_path)
    evaluation = _evaluate(store, inputs)
    incompatible_run = _run(
        source,
        run_id="run-incompatible-exclusion",
        model_id="synthetic-model-b-v1",
    )
    job_id = run_store.enqueue(
        source.source_id, source.targets[1].target_id, incompatible_run
    )
    assert asyncio.run(run_pending_once(run_store, StoredAttemptAdapter())) is True
    excluded_attempt_id = run_store.job(job_id).attempt_id
    assert excluded_attempt_id is not None

    with pytest.raises(ValueError, match="model scope"):
        store.build_summary(
            SummaryRequest(
                project_id=PROJECT_ID,
                summary_level="MODEL",
                scope_id=evaluation.model_id,
                scope_version=evaluation.model_config_id,
                members=(
                    {
                        "attempt_id": evaluation.attempt_id,
                        "evaluation_id": evaluation.evaluation_id,
                    },
                    {"attempt_id": excluded_attempt_id, "evaluation_id": None},
                ),
                aggregation_version="qualitative-counts-v2",
            )
        )
def test_summary_disagreement_is_an_orthogonal_review_subset(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path, _, _, _, _, attempt, mapping, fact, redacted_pdf, reference_pdf = inputs
    store = EvaluationStore(db_path)
    facts = store.record_source_facts(
        mapping,
        facts=(fact,),
        rubric_version=RUBRIC_VERSION,
        source_fact_record_version="source-facts-v1",
    )
    evaluation = store.evaluate_and_store(
        project_id=PROJECT_ID,
        attempt_id=attempt.attempt_id,
        mapping=mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        source_fact_record_id=facts.source_fact_record_id,
        judge=DisagreementMockJudge(),
        evaluator_version="qualitative-evaluator-v2",
        rubric_version=RUBRIC_VERSION,
    )
    summary = store.build_summary(
        SummaryRequest(
            project_id=PROJECT_ID,
            summary_level="MODEL",
            scope_id=evaluation.model_id,
            scope_version=evaluation.model_config_id,
            members=(
                {
                    "attempt_id": evaluation.attempt_id,
                    "evaluation_id": evaluation.evaluation_id,
                },
            ),
            aggregation_version="qualitative-counts-v2",
        )
    )

    assert summary.completed_count == 1
    assert summary.needs_review_count == 1
    assert summary.disagreement_count == 1
    assert summary.disagreement_evaluation_ids == (evaluation.evaluation_id,)


def test_summary_and_membership_insert_is_atomic_and_immutable(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path = inputs[0]
    store = EvaluationStore(db_path)
    evaluation = _evaluate(store, inputs)
    request = SummaryRequest(
        project_id=PROJECT_ID,
        summary_level="MODEL",
        scope_id=evaluation.model_id,
        scope_version=evaluation.model_config_id,
        members=(
            {
                "attempt_id": evaluation.attempt_id,
                "evaluation_id": evaluation.evaluation_id,
            },
        ),
        aggregation_version="qualitative-counts-v2",
    )
    connection = sqlite3.connect(db_path)
    connection.execute(
        """CREATE TRIGGER test_summary_member_failure BEFORE INSERT ON summary_members
           BEGIN SELECT RAISE(ABORT, 'injected member failure'); END"""
    )
    connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="injected member failure"):
        store.build_summary(request)
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT count(*) FROM summaries").fetchone()[0] == 0
    assert connection.execute("SELECT count(*) FROM summary_members").fetchone()[0] == 0
    connection.execute("DROP TRIGGER test_summary_member_failure")
    connection.close()

    summary = store.build_summary(request)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(summary_members)"
    ).fetchall()
    assert any(
        row[2] == "attempts" and row[3] == "subject_id" and row[4] == "attempt_id"
        for row in foreign_keys
    )
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        connection.execute(
            """INSERT INTO summary_members (
                summary_id, ordinal, subject_id, evaluation_id,
                disposition, exclusion_reason
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                summary.summary_id,
                99,
                "attempt-fictional",
                None,
                "EXCLUDED",
                "NO_EVALUATION",
            ),
        )
    for sql in (
        "UPDATE summaries SET payload_json = '{}'",
        "DELETE FROM summaries",
        "UPDATE summary_members SET disposition = 'EXCLUDED'",
        "DELETE FROM summary_members",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(sql)
    connection.close()
    assert store.get_summary(summary.summary_id, project_id=PROJECT_ID) == summary


def test_model_summary_uses_distinct_task4_runs_across_documents(tmp_path) -> None:
    first_inputs = _authoritative_inputs(tmp_path / "first")
    db_path, run_store, _, first_run, _, _, _, _, _, _ = first_inputs
    store = EvaluationStore(db_path)
    first_evaluation = _evaluate(store, first_inputs)

    redacted_path, reference_path = make_synthetic_pair(
        "adjacent_boxes", tmp_path / "second"
    )
    redacted_pdf = redacted_path.read_bytes()
    reference_pdf = reference_path.read_bytes()
    second_source_id = run_store.ingest_redacted_pdf(
        redacted_pdf, project_id=PROJECT_ID
    )
    second_source = run_store.source(second_source_id)
    second_run = _run(second_source, run_id="run-document-2")
    run_store.enqueue(
        second_source_id, second_source.targets[0].target_id, second_run
    )
    assert asyncio.run(run_pending_once(run_store, StoredAttemptAdapter())) is True
    second_attempt = next(
        item for item in run_store.attempts() if item.run_id == second_run.run_id
    )
    detection = detect_targets(
        redacted_pdf,
        project_id=PROJECT_ID,
        redacted_document_version_id="redacted-document-v1",
    )
    assert detection.status is DetectionStatus.SUPPORTED
    canonical = canonicalize_redacted(
        redacted_pdf,
        detection,
        project_id=PROJECT_ID,
        redacted_document_version_id="redacted-document-v1",
        canonical_document_version_id="redacted-canonical-v1",
    )
    mapping = align_reference(
        canonical,
        reference_pdf,
        redacted_pdf=redacted_pdf,
        targets=detection.targets,
        reference_document_version_id=REFERENCE_VERSION_ID,
        reference_canonical_version_id=REFERENCE_CANONICAL_ID,
        mapping_version="mapping-v1",
    )[0]
    second_evaluation = store.evaluate_and_store(
        project_id=PROJECT_ID,
        attempt_id=second_attempt.attempt_id,
        mapping=mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        source_fact_record_id=None,
        judge=SupportedMockJudge(),
        evaluator_version="qualitative-evaluator-v2",
        rubric_version=RUBRIC_VERSION,
    )
    request = SummaryRequest(
        project_id=PROJECT_ID,
        summary_level="MODEL",
        scope_id=first_evaluation.model_id,
        scope_version=first_evaluation.model_config_id,
        members=tuple(
            {
                "attempt_id": item.attempt_id,
                "evaluation_id": item.evaluation_id,
            }
            for item in (first_evaluation, second_evaluation)
        ),
        aggregation_version="qualitative-counts-v2",
    )

    summary = store.build_summary(request)

    assert summary.contributing_run_ids == tuple(
        sorted((first_run.run_id, second_run.run_id))
    )
    assert len(summary.redacted_document_version_ids) == 2
    assert summary.eligible_count == 1
    assert summary.unknown_count == 1


def test_cross_model_comparison_uses_separate_model_specific_task4_runs(tmp_path) -> None:
    inputs = _authoritative_inputs(tmp_path)
    (
        db_path,
        run_store,
        source,
        first_run,
        _,
        _,
        mapping,
        fact,
        redacted_pdf,
        reference_pdf,
    ) = inputs
    store = EvaluationStore(db_path)
    first = _evaluate(store, inputs)
    second_run = _run(
        source, run_id="run-model-b", model_id="synthetic-model-b-v1"
    )
    run_store.enqueue(source.source_id, source.targets[0].target_id, second_run)
    assert asyncio.run(run_pending_once(run_store, StoredAttemptAdapter())) is True
    second_attempt = next(
        item for item in run_store.attempts() if item.run_id == second_run.run_id
    )
    source_facts = store.record_source_facts(
        mapping,
        facts=(fact,),
        rubric_version=RUBRIC_VERSION,
        source_fact_record_version="source-facts-v1",
    )
    second = store.evaluate_and_store(
        project_id=PROJECT_ID,
        attempt_id=second_attempt.attempt_id,
        mapping=mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        source_fact_record_id=source_facts.source_fact_record_id,
        judge=SupportedMockJudge(),
        evaluator_version="qualitative-evaluator-v2",
        rubric_version=RUBRIC_VERSION,
    )

    def model_summary(evaluation):
        return store.build_summary(
            SummaryRequest(
                project_id=PROJECT_ID,
                summary_level="MODEL",
                scope_id=evaluation.model_id,
                scope_version=evaluation.model_config_id,
                members=(
                    {
                        "attempt_id": evaluation.attempt_id,
                        "evaluation_id": evaluation.evaluation_id,
                    },
                ),
                aggregation_version="qualitative-counts-v2",
            )
        )

    first_summary = model_summary(first)
    second_summary = model_summary(second)

    assert first_summary.contributing_run_ids == (first_run.run_id,)
    assert second_summary.contributing_run_ids == (second_run.run_id,)
    assert first_summary.model_provenance_ids != second_summary.model_provenance_ids
    assert_comparable_summaries(first_summary, second_summary)


@pytest.mark.parametrize(
    ("trigger", "sql"),
    [
        ("source_fact_records_no_update", "UPDATE source_fact_records SET payload_json = '{}'") ,
        ("evaluations_no_update", "UPDATE evaluations SET payload_json = '{}'") ,
        ("summaries_no_update", "UPDATE summaries SET payload_json = '{}'") ,
        (
            "summary_members_no_update",
            "UPDATE summary_members SET disposition = 'EXCLUDED'",
        ),
    ],
)
def test_reopen_rejects_tampered_authoritative_rows(
    tmp_path, trigger: str, sql: str
) -> None:
    inputs = _authoritative_inputs(tmp_path)
    db_path = inputs[0]
    store = EvaluationStore(db_path)
    evaluation = _evaluate(store, inputs)
    summary = store.build_summary(
        SummaryRequest(
            project_id=PROJECT_ID,
            summary_level="MODEL",
            scope_id=evaluation.model_id,
            scope_version=evaluation.model_config_id,
            members=(
                {
                    "attempt_id": evaluation.attempt_id,
                    "evaluation_id": evaluation.evaluation_id,
                },
            ),
            aggregation_version="qualitative-counts-v2",
        )
    )
    connection = sqlite3.connect(db_path)
    connection.execute(f"DROP TRIGGER {trigger}")
    connection.execute(sql)
    connection.commit()
    connection.close()

    with pytest.raises((ValueError, KeyError)):
        EvaluationStore(db_path).get_summary(
            summary.summary_id, project_id=PROJECT_ID
        )
