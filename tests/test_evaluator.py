from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from redaction_lab.canonical import canonicalize_redacted
from redaction_lab.contracts import (
    AttemptStatus,
    EvaluationProcessStatus,
    ModelAttempt,
    ReferenceScoreability,
    ReferenceStatus,
    ScoreStatus,
)
from redaction_lab.evaluator import (
    EvaluationBindingError,
    build_source_fact_record,
    evaluate_attempt,
)
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.judges.base import (
    FactEvidenceLabel,
    JudgeEvidence,
    SourceFact,
)
from redaction_lab.judges.local_nli import (
    LocalNLIJudge,
    LocalNLIUnavailableError,
)
from redaction_lab.pdf_detector import DetectionStatus, detect_targets
from redaction_lab.reference import align_reference


PROJECT_ID = "project-rl-mvp-003"
REDACTED_VERSION_ID = "redacted-document-v1"
REDACTED_CANONICAL_ID = "redacted-canonical-v1"
REFERENCE_VERSION_ID = "reference-document-v1"
REFERENCE_CANONICAL_ID = "reference-canonical-v1"
MAPPING_VERSION = "mapping-v1"
RUBRIC_VERSION = "fact-evidence-rubric-v0.1-proposed"
NOW = datetime(2026, 10, 9, 22, 0, tzinfo=UTC)


class StubJudge:
    judge_id = "synthetic-mock-judge"
    judge_version = "synthetic-mock-judge-v1"

    def __init__(self, evidence: dict[str, JudgeEvidence]) -> None:
        self.evidence = evidence
        self.calls: list[tuple[SourceFact, str]] = []

    def assess(self, reference: SourceFact, prediction: str) -> JudgeEvidence:
        self.calls.append((reference, prediction))
        return self.evidence[reference.fact_id]


def _trusted_context(tmp_path: Path):
    redacted_path, reference_path = make_synthetic_pair("two_boxes", tmp_path)
    redacted_pdf = redacted_path.read_bytes()
    reference_pdf = reference_path.read_bytes()
    detection = detect_targets(
        redacted_pdf,
        project_id=PROJECT_ID,
        redacted_document_version_id=REDACTED_VERSION_ID,
    )
    assert detection.status is DetectionStatus.SUPPORTED
    canonical = canonicalize_redacted(
        redacted_pdf,
        detection,
        project_id=PROJECT_ID,
        redacted_document_version_id=REDACTED_VERSION_ID,
        canonical_document_version_id=REDACTED_CANONICAL_ID,
    )
    mappings = align_reference(
        canonical,
        reference_pdf,
        redacted_pdf=redacted_pdf,
        targets=detection.targets,
        reference_document_version_id=REFERENCE_VERSION_ID,
        reference_canonical_version_id=REFERENCE_CANONICAL_ID,
        mapping_version=MAPPING_VERSION,
    )
    return redacted_pdf, reference_pdf, canonical, detection.targets, mappings


def _attempt(target, **updates: object) -> ModelAttempt:
    values: dict[str, object] = {
        "attempt_id": f"attempt-{target.target_id}",
        "project_id": PROJECT_ID,
        "run_id": "run-synthetic-v1",
        "target_id": target.target_id,
        "target_version": target.target_version,
        "model_id": "synthetic-model-v1",
        "provider_model_id": "synthetic-model-v1",
        "model_config_id": "synthetic-config-v1",
        "request_hash": "a" * 64,
        "response_hash": sha256(b"Agent Cedar").hexdigest(),
        "prediction": "Agent Cedar",
        "status": AttemptStatus.SUCCEEDED,
        "started_at": NOW,
        "completed_at": NOW,
    }
    values.update(updates)
    return ModelAttempt.model_validate(values)


def _fact_record(mapping, facts: tuple[SourceFact, ...]):
    return build_source_fact_record(
        mapping,
        facts=facts,
        rubric_version=RUBRIC_VERSION,
        source_fact_record_version="source-facts-v1",
    )


def _evaluate(
    *,
    attempt,
    mapping,
    fact_record,
    judge,
    redacted_pdf,
    reference_pdf,
    canonical,
    targets,
    rubric_version: str = RUBRIC_VERSION,
):
    return evaluate_attempt(
        attempt,
        mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        redacted=canonical,
        targets=targets,
        source_fact_record=fact_record,
        judge=judge,
        evaluator_version="qualitative-evaluator-v1",
        rubric_version=rubric_version,
        condition_id="redacted-only-condition-v1",
        created_at=NOW,
    )


def test_reference_only_fact_record_is_versioned_deterministic_and_immutable(
    tmp_path: Path,
) -> None:
    *_, mappings = _trusted_context(tmp_path)
    mapping = mappings[0]
    facts = (
        SourceFact(
            fact_id="courier-identity",
            reference_proposition="The courier was Agent Cedar.",
            reference_quote="Agent Cedar",
            reference_quote_locator="chars:0-11",
            critical_dimensions=("identity",),
        ),
    )

    first = _fact_record(mapping, facts)
    second = _fact_record(mapping, facts)

    assert first == second
    assert first.mapping_id == mapping.mapping_id
    assert first.target_id == mapping.target_id
    with pytest.raises(ValidationError):
        first.facts[0].reference_quote = "Agent Birch"  # type: ignore[misc]


def test_fact_record_rejects_fabricated_quote_and_duplicate_fact_ids(
    tmp_path: Path,
) -> None:
    *_, mappings = _trusted_context(tmp_path)
    mapping = mappings[0]
    fabricated = SourceFact(
        fact_id="f1",
        reference_proposition="A fabricated proposition.",
        reference_quote="Agent Birch",
        reference_quote_locator="chars:0-11",
        critical_dimensions=("identity",),
    )
    duplicate = fabricated.model_copy(update={"reference_quote": "Agent Cedar"})

    with pytest.raises(EvaluationBindingError, match="exact reference text"):
        _fact_record(mapping, (fabricated,))
    with pytest.raises(EvaluationBindingError, match="unique"):
        _fact_record(mapping, (duplicate, duplicate))
    with pytest.raises(EvaluationBindingError, match="locator"):
        _fact_record(
            mapping,
            (
                duplicate.model_copy(
                    update={"reference_quote_locator": "chars:99-110"}
                ),
            ),
        )


def test_trusted_pair_produces_provisional_qualitative_evidence_only(
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )
    mapping = mappings[0]
    facts = (
        SourceFact(
            fact_id="courier-identity",
            reference_proposition="The courier was Agent Cedar.",
            reference_quote="Agent Cedar",
            reference_quote_locator="chars:0-11",
            critical_dimensions=("identity",),
        ),
    )
    record = _fact_record(mapping, facts)
    judge = StubJudge(
        {
            "courier-identity": JudgeEvidence(
                evidence_label=FactEvidenceLabel.SUPPORTED,
                prediction_excerpt="Agent Cedar",
                rationale="Synthetic mock evidence; equivalent identity wording.",
                provisional=True,
            )
        }
    )

    evaluation = _evaluate(
        attempt=_attempt(targets[0]),
        mapping=mapping,
        fact_record=record,
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        canonical=canonical,
        targets=targets,
    )

    assert evaluation.process_status is EvaluationProcessStatus.COMPLETE
    assert evaluation.score_status is ScoreStatus.NONE
    assert evaluation.verified_score is None
    assert evaluation.experimental_score is None
    assert evaluation.qualitative_status == "PROVISIONAL_ALL_FACTS_SUPPORTED"
    assert evaluation.fact_comparisons[0].evidence_label == "SUPPORTED"
    assert evaluation.reference_trust == "APPROVED_SYNTHETIC_PAIR"
    assert evaluation.judge_id == "synthetic-mock-judge"
    assert evaluation.judge_version == "synthetic-mock-judge-v1"
    assert judge.calls == [(facts[0], "Agent Cedar")]


@pytest.mark.parametrize(
    ("label", "expected_status"),
    [
        (FactEvidenceLabel.MISSING, "PROVISIONAL_MIXED"),
        (FactEvidenceLabel.CONTRADICTED, "PROVISIONAL_MIXED"),
        (FactEvidenceLabel.NEEDS_REVIEW, "NEEDS_REVIEW"),
    ],
)
def test_adversarial_semantics_remain_explicit_provisional_evidence(
    label: FactEvidenceLabel,
    expected_status: str,
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )
    mapping = mappings[1]
    fact = SourceFact(
        fact_id="quantity-unit",
        reference_proposition="The package contained 12 paper stars.",
        reference_quote="12 paper stars",
        reference_quote_locator="chars:0-14",
        critical_dimensions=("quantity", "unit"),
    )
    judge = StubJudge(
        {
            fact.fact_id: JudgeEvidence(
                evidence_label=label,
                prediction_excerpt="20 metal stars",
                rationale="Synthetic mock covers quantity, unit, negation, role, date, modality, or attribution review.",
                unsupported_assertions=("an unreferenced cash bonus",),
                provisional=True,
            )
        }
    )

    evaluation = _evaluate(
        attempt=_attempt(
            targets[1],
            attempt_id="attempt-second",
            prediction="20 metal stars or perhaps 12 paper stars, repeated twice",
            response_hash="b" * 64,
        ),
        mapping=mapping,
        fact_record=_fact_record(mapping, (fact,)),
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        canonical=canonical,
        targets=targets,
    )

    assert evaluation.qualitative_status == expected_status
    assert evaluation.unsupported_assertions == ("an unreferenced cash bonus",)
    assert evaluation.fact_comparisons[0].evidence_label is label
    assert evaluation.verified_score is evaluation.experimental_score is None


@pytest.mark.parametrize(
    ("scenario", "prediction", "label"),
    [
        ("equivalent paraphrase", "The courier had the Cedar identity.", "SUPPORTED"),
        ("actor/object reversal", "Cedar was delivered by the courier.", "CONTRADICTED"),
        ("negation", "The courier was not Agent Cedar.", "CONTRADICTED"),
        ("changed date", "The courier arrived on July 8.", "CONTRADICTED"),
        ("lost attribution", "The committee approved it.", "MISSING"),
        ("changed modality", "The courier might be Agent Cedar.", "CONTRADICTED"),
        ("multiple alternatives", "Cedar or Birch.", "NEEDS_REVIEW"),
        ("repeated claim", "Agent Cedar. Agent Cedar.", "SUPPORTED"),
    ],
)
def test_mock_judge_evidence_preserves_adversarial_distinctions_without_scores(
    scenario: str,
    prediction: str,
    label: str,
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )
    mapping = mappings[0]
    fact = SourceFact(
        fact_id="courier-proposition",
        reference_proposition="The courier was Agent Cedar.",
        reference_quote="Agent Cedar",
        reference_quote_locator="chars:0-11",
        critical_dimensions=("actor", "relation", "identity"),
    )
    judge = StubJudge(
        {
            fact.fact_id: JudgeEvidence(
                evidence_label=label,
                prediction_excerpt=prediction,
                rationale=f"Synthetic mock evidence for {scenario}.",
                provisional=True,
            )
        }
    )
    attempt = _attempt(
        targets[0],
        prediction=prediction,
        response_hash=sha256(prediction.encode()).hexdigest(),
    )

    evaluation = _evaluate(
        attempt=attempt,
        mapping=mapping,
        fact_record=_fact_record(mapping, (fact,)),
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        canonical=canonical,
        targets=targets,
    )

    assert evaluation.fact_comparisons[0].evidence_label.value == label
    assert evaluation.fact_comparisons[0].provisional is True
    assert evaluation.verified_score is evaluation.experimental_score is None
    assert attempt.prediction == prediction


@pytest.mark.parametrize(
    "status",
    [
        AttemptStatus.REFUSED,
        AttemptStatus.TIMEOUT,
        AttemptStatus.ERROR,
        AttemptStatus.MALFORMED,
    ],
)
def test_nonanswers_preserve_status_without_semantic_evidence(
    status: AttemptStatus,
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )
    judge = StubJudge({})
    attempt = _attempt(
        targets[0],
        status=status,
        prediction=None,
        response_hash=None,
        provider_model_id=None,
    )

    evaluation = _evaluate(
        attempt=attempt,
        mapping=mappings[0],
        fact_record=None,
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        canonical=canonical,
        targets=targets,
    )

    assert evaluation.attempt_status is status
    assert evaluation.qualitative_status == f"TECHNICAL_{status.value}"
    assert evaluation.fact_comparisons == ()
    assert evaluation.verified_score is evaluation.experimental_score is None
    assert judge.calls == []


def test_changed_or_unregistered_reference_bytes_are_unknown_and_never_judged(
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )
    judge = StubJudge({})

    evaluation = _evaluate(
        attempt=_attempt(targets[0]),
        mapping=mappings[0],
        fact_record=None,
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf + b"\nchanged",
        canonical=canonical,
        targets=targets,
    )

    assert evaluation.qualitative_status == "ACCURACY_UNKNOWN"
    assert evaluation.mapping_status is not ReferenceStatus.CONFIRMED
    assert evaluation.mapping_scoreability is ReferenceScoreability.NOT_SCOREABLE
    assert evaluation.reference_trust == "UNTRUSTED_OR_UNAVAILABLE"
    assert evaluation.fact_comparisons == ()
    assert judge.calls == []


@pytest.mark.parametrize(
    ("attempt_update", "mapping_update", "message"),
    [
        ({"project_id": "wrong-project"}, {}, "project"),
        ({"target_id": "wrong-target"}, {}, "target"),
        ({"target_version": "stale-target-v0"}, {}, "target"),
        ({}, {"mapping_id": "forged-mapping"}, "mapping"),
        ({}, {"mapping_version": "stale-mapping-v0"}, "mapping"),
    ],
)
def test_wrong_bindings_and_forged_mapping_fail_closed(
    attempt_update: dict[str, object],
    mapping_update: dict[str, object],
    message: str,
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )

    with pytest.raises(EvaluationBindingError, match=message):
        _evaluate(
            attempt=_attempt(targets[0], **attempt_update),
            mapping=mappings[0].model_copy(update=mapping_update),
            fact_record=None,
            judge=StubJudge({}),
            redacted_pdf=redacted_pdf,
            reference_pdf=reference_pdf,
            canonical=canonical,
            targets=targets,
        )


def test_stale_source_fact_rubric_fails_and_changed_rubric_changes_record_id(
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf, canonical, targets, mappings = _trusted_context(
        tmp_path
    )
    mapping = mappings[0]
    fact = SourceFact(
        fact_id="f1",
        reference_proposition="The courier identity is Agent Cedar.",
        reference_quote="Agent Cedar",
        reference_quote_locator="chars:0-11",
        critical_dimensions=("identity",),
    )
    record = _fact_record(mapping, (fact,))
    judge = StubJudge(
        {
            "f1": JudgeEvidence(
                evidence_label="SUPPORTED",
                rationale="Synthetic mock evidence.",
                provisional=True,
            )
        }
    )
    original = _evaluate(
        attempt=_attempt(targets[0]),
        mapping=mapping,
        fact_record=record,
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        canonical=canonical,
        targets=targets,
    )

    with pytest.raises(EvaluationBindingError, match="rubric"):
        _evaluate(
            attempt=_attempt(targets[0]),
            mapping=mapping,
            fact_record=record,
            judge=judge,
            redacted_pdf=redacted_pdf,
            reference_pdf=reference_pdf,
            canonical=canonical,
            targets=targets,
            rubric_version="changed-rubric-v2",
        )
    changed_record = build_source_fact_record(
        mapping,
        facts=(fact,),
        rubric_version="changed-rubric-v2",
        source_fact_record_version="source-facts-v1",
    )
    changed = _evaluate(
        attempt=_attempt(targets[0]),
        mapping=mapping,
        fact_record=changed_record,
        judge=judge,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        canonical=canonical,
        targets=targets,
        rubric_version="changed-rubric-v2",
    )

    assert changed.evaluation_id != original.evaluation_id
    assert original.attempt_id == changed.attempt_id

    with pytest.raises(EvaluationBindingError, match="integrity"):
        _evaluate(
            attempt=_attempt(targets[0]),
            mapping=mapping,
            fact_record=record.model_copy(
                update={"source_fact_record_id": "forged-source-facts"}
            ),
            judge=judge,
            redacted_pdf=redacted_pdf,
            reference_pdf=reference_pdf,
            canonical=canonical,
            targets=targets,
        )


def test_local_nli_boundary_is_disabled_without_import_or_inference() -> None:
    judge = LocalNLIJudge()

    assert judge.available is False
    with pytest.raises(LocalNLIUnavailableError, match="disabled"):
        judge.assess(
            SourceFact(
                fact_id="f1",
                reference_proposition="Synthetic proposition.",
                reference_quote="Synthetic",
                reference_quote_locator="chars:0-9",
                critical_dimensions=("identity",),
            ),
            "prediction",
        )
