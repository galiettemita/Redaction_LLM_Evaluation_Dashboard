"""Fail-closed, qualitative-only evaluation of frozen model attempts."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from redaction_lab.contracts import (
    AttemptStatus,
    CanonicalRedactedDocument,
    EvaluationProcessStatus,
    EvaluationRecord,
    FactComparison,
    FactEvidenceLabel,
    ModelAttempt,
    RedactionTarget,
    ReferenceMapping,
    ReferenceScoreability,
    ReferenceStatus,
    ScoreStatus,
)
from redaction_lab.judges.base import FactJudge, SourceFact, SourceFactRecord
from redaction_lab.reference import align_reference


EVIDENCE_SCHEMA_VERSION = "qualitative-fact-evidence-v1"
EVALUATION_VERSION = "qualitative-evaluation-v1"
TRUSTED_REFERENCE = "APPROVED_SYNTHETIC_PAIR"
UNTRUSTED_REFERENCE = "UNTRUSTED_OR_UNAVAILABLE"


class EvaluationBindingError(ValueError):
    """Raised when immutable attempt/reference identities do not agree."""


def _digest(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"{prefix}-{sha256(encoded).hexdigest()}"


def build_source_fact_record(
    mapping: ReferenceMapping,
    *,
    facts: tuple[SourceFact, ...],
    rubric_version: str,
    source_fact_record_version: str,
) -> SourceFactRecord:
    """Freeze caller-supplied reference-only facts before prediction inspection.

    This function does not grant trust to ``mapping``. ``evaluate_attempt`` later
    re-derives the mapping from both registered PDF byte streams before using it.
    """

    if (
        mapping.status is not ReferenceStatus.CONFIRMED
        or mapping.scoreability is not ReferenceScoreability.SCOREABLE
        or mapping.exact_revealed_text is None
        or not all(
            (
                mapping.candidate_unique,
                mapping.complete_revelation,
                mapping.readable,
                mapping.reliably_aligned,
            )
        )
    ):
        raise EvaluationBindingError("source facts require complete exact reference text")
    if not facts:
        raise EvaluationBindingError("source fact record cannot be empty")
    fact_ids = tuple(fact.fact_id for fact in facts)
    if len(set(fact_ids)) != len(fact_ids):
        raise EvaluationBindingError("source fact IDs must be unique")
    if any(fact.reference_quote not in mapping.exact_revealed_text for fact in facts):
        raise EvaluationBindingError("source fact quote must occur in exact reference text")
    for fact in facts:
        starts = []
        start = mapping.exact_revealed_text.find(fact.reference_quote)
        while start >= 0:
            starts.append(start)
            start = mapping.exact_revealed_text.find(fact.reference_quote, start + 1)
        valid_locators = {
            f"chars:{start}-{start + len(fact.reference_quote)}" for start in starts
        }
        if fact.reference_quote_locator not in valid_locators:
            raise EvaluationBindingError(
                "source fact locator must identify its exact reference quote"
            )
    if any(
        fact.dependency_fact_id is not None
        and fact.dependency_fact_id not in set(fact_ids)
        for fact in facts
    ):
        raise EvaluationBindingError("source fact dependency must name a record fact")

    identity = {
        "source_fact_record_version": source_fact_record_version,
        "project_id": mapping.project_id,
        "target_id": mapping.target_id,
        "target_version": mapping.target_version,
        "mapping_id": mapping.mapping_id,
        "mapping_version": mapping.mapping_version,
        "rubric_version": rubric_version,
        "facts": [fact.model_dump(mode="json") for fact in facts],
    }
    return SourceFactRecord(
        source_fact_record_id=_digest("source-facts", identity),
        facts=facts,
        **{key: value for key, value in identity.items() if key != "facts"},
    )


def _validate_bindings(
    attempt: ModelAttempt,
    mapping: ReferenceMapping,
    redacted: CanonicalRedactedDocument,
    targets: tuple[RedactionTarget, ...],
) -> RedactionTarget:
    if attempt.project_id != mapping.project_id or attempt.project_id != redacted.project_id:
        raise EvaluationBindingError("project identity mismatch")
    if attempt.target_id != mapping.target_id:
        raise EvaluationBindingError("target identity mismatch")
    if attempt.target_version != mapping.target_version:
        raise EvaluationBindingError("target version mismatch")
    if (
        mapping.redacted_document_version_id
        != redacted.redacted_document_version_id
    ):
        raise EvaluationBindingError("redacted document identity mismatch")
    matches = tuple(target for target in targets if target.target_id == attempt.target_id)
    if len(matches) != 1 or matches[0].target_version != attempt.target_version:
        raise EvaluationBindingError("target binding is absent or stale")
    return matches[0]


def _authoritative_mapping(
    mapping: ReferenceMapping,
    *,
    redacted_pdf: bytes,
    reference_pdf: bytes | None,
    redacted: CanonicalRedactedDocument,
    targets: tuple[RedactionTarget, ...],
) -> tuple[ReferenceMapping, bool]:
    recomputed = align_reference(
        redacted,
        reference_pdf,
        redacted_pdf=redacted_pdf,
        targets=targets,
        reference_document_version_id=(
            mapping.reference_document_version_id if reference_pdf is not None else None
        ),
        reference_canonical_version_id=(
            mapping.reference_canonical_version_id if reference_pdf is not None else None
        ),
        mapping_version=mapping.mapping_version,
    )
    matches = tuple(item for item in recomputed if item.target_id == mapping.target_id)
    if len(matches) != 1:
        raise EvaluationBindingError("mapping target is absent from verified alignment")
    authoritative = matches[0]
    trusted = (
        authoritative.status is ReferenceStatus.CONFIRMED
        and authoritative.scoreability is ReferenceScoreability.SCOREABLE
    )
    if trusted and authoritative != mapping:
        raise EvaluationBindingError("mapping identity or evidence does not match verified bytes")
    return authoritative, trusted


def _fact_record_matches(
    record: SourceFactRecord,
    mapping: ReferenceMapping,
    rubric_version: str,
) -> None:
    expected = (
        record.project_id == mapping.project_id
        and record.target_id == mapping.target_id
        and record.target_version == mapping.target_version
        and record.mapping_id == mapping.mapping_id
        and record.mapping_version == mapping.mapping_version
    )
    if not expected:
        raise EvaluationBindingError("source fact record mapping binding mismatch")
    if record.rubric_version != rubric_version:
        raise EvaluationBindingError("source fact record rubric mismatch")
    rebuilt = build_source_fact_record(
        mapping,
        facts=record.facts,
        rubric_version=record.rubric_version,
        source_fact_record_version=record.source_fact_record_version,
    )
    if rebuilt != record:
        raise EvaluationBindingError("source fact record integrity mismatch")


def _qualitative_status(
    labels: tuple[FactEvidenceLabel, ...],
    *,
    has_unsupported: bool,
    disagreement: bool,
) -> str:
    if disagreement or FactEvidenceLabel.NEEDS_REVIEW in labels:
        return "NEEDS_REVIEW"
    has_supported = FactEvidenceLabel.SUPPORTED in labels
    has_missing = FactEvidenceLabel.MISSING in labels
    has_contradiction = FactEvidenceLabel.CONTRADICTED in labels
    if has_contradiction and not has_supported and not has_missing and not has_unsupported:
        return "PROVISIONAL_CONTRADICTED"
    if has_missing and not has_supported and not has_contradiction and not has_unsupported:
        return "PROVISIONAL_INCOMPLETE"
    if all(label is FactEvidenceLabel.SUPPORTED for label in labels) and not has_unsupported:
        return "PROVISIONAL_ALL_FACTS_SUPPORTED"
    return "PROVISIONAL_MIXED"


def evaluate_attempt(
    attempt: ModelAttempt,
    mapping: ReferenceMapping,
    *,
    redacted_pdf: bytes,
    reference_pdf: bytes | None,
    redacted: CanonicalRedactedDocument,
    targets: tuple[RedactionTarget, ...],
    source_fact_record: SourceFactRecord | None,
    judge: FactJudge,
    evaluator_version: str,
    rubric_version: str,
    condition_id: str,
    created_at: datetime,
) -> EvaluationRecord:
    """Evaluate after independently verifying reference bytes and exact bindings."""

    _validate_bindings(attempt, mapping, redacted, targets)
    authoritative, trusted = _authoritative_mapping(
        mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        redacted=redacted,
        targets=targets,
    )
    trust = TRUSTED_REFERENCE if trusted else UNTRUSTED_REFERENCE
    process_status = EvaluationProcessStatus.COMPLETE
    qualitative_status: str
    comparisons: tuple[FactComparison, ...] = ()
    unsupported: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    record_id: str | None = None
    record_version: str | None = None

    if attempt.status is not AttemptStatus.SUCCEEDED:
        qualitative_status = f"TECHNICAL_{attempt.status.value}"
        explanation = (
            f"{attempt.status.value} is a technical prediction outcome; no semantic "
            "fact evidence or numeric score was produced."
        )
    elif not trusted:
        qualitative_status = "ACCURACY_UNKNOWN"
        explanation = (
            "Accuracy unknown because both PDFs did not reproduce an approved, "
            "complete, readable, uniquely aligned synthetic reference mapping."
        )
    elif source_fact_record is None:
        qualitative_status = "NEEDS_REVIEW"
        process_status = EvaluationProcessStatus.NEEDS_REVIEW
        explanation = (
            "Trusted target truth exists, but no frozen reference-only source fact "
            "record was supplied; semantic evidence was not fabricated."
        )
    else:
        _fact_record_matches(source_fact_record, authoritative, rubric_version)
        record_id = source_fact_record.source_fact_record_id
        record_version = source_fact_record.source_fact_record_version
        evidence = []
        try:
            for fact in source_fact_record.facts:
                judged = judge.assess(fact, attempt.prediction or "")
                evidence.append((fact, judged))
        except Exception:
            process_status = EvaluationProcessStatus.ERROR
            qualitative_status = "EVALUATOR_ERROR"
            explanation = (
                "The qualitative judge was unavailable or failed; no partial semantic "
                "evidence or numeric score was retained."
            )
        else:
            comparisons = tuple(
                FactComparison(
                    fact_id=fact.fact_id,
                    reference_quote=fact.reference_quote,
                    prediction_excerpt=judged.prediction_excerpt,
                    comparison_label=judged.evidence_label.value,
                    reference_proposition=fact.reference_proposition,
                    reference_quote_locator=fact.reference_quote_locator,
                    critical_dimensions=fact.critical_dimensions,
                    evidence_label=judged.evidence_label,
                    rationale=judged.rationale,
                    provisional=True,
                )
                for fact, judged in evidence
            )
            unsupported = tuple(
                dict.fromkeys(
                    assertion
                    for _, judged in evidence
                    for assertion in judged.unsupported_assertions
                )
            )
            contradictions = tuple(
                fact.reference_proposition
                for fact, judged in evidence
                if judged.evidence_label is FactEvidenceLabel.CONTRADICTED
            )
            disagreement = any(judged.disagreement for _, judged in evidence)
            labels = tuple(judged.evidence_label for _, judged in evidence)
            qualitative_status = _qualitative_status(
                labels,
                has_unsupported=bool(unsupported),
                disagreement=disagreement,
            )
            if disagreement:
                process_status = EvaluationProcessStatus.DISAGREEMENT
            elif FactEvidenceLabel.NEEDS_REVIEW in labels:
                process_status = EvaluationProcessStatus.NEEDS_REVIEW
            explanation = (
                "Provisional synthetic/mock qualitative fact evidence only; the "
                "rubric and judge are not scientifically validated."
            )

    identity = {
        "evaluation_version": EVALUATION_VERSION,
        "project_id": attempt.project_id,
        "run_id": attempt.run_id,
        "target_id": attempt.target_id,
        "target_version": attempt.target_version,
        "attempt_id": attempt.attempt_id,
        "attempt_status": attempt.status.value,
        "attempt_request_hash": attempt.request_hash,
        "attempt_response_hash": attempt.response_hash,
        "model_id": attempt.model_id,
        "model_config_id": attempt.model_config_id,
        "mapping_id": authoritative.mapping_id,
        "mapping_version": authoritative.mapping_version,
        "mapping_status": authoritative.status.value,
        "evaluator_version": evaluator_version,
        "judge_id": judge.judge_id,
        "judge_version": judge.judge_version,
        "rubric_version": rubric_version,
        "source_fact_record_id": record_id,
        "condition_id": condition_id,
        "process_status": process_status.value,
        "qualitative_status": qualitative_status,
        "comparisons": [item.model_dump(mode="json") for item in comparisons],
        "unsupported_assertions": unsupported,
    }
    return EvaluationRecord(
        evaluation_id=_digest("evaluation", identity),
        evaluation_version=EVALUATION_VERSION,
        evidence_schema_version=EVIDENCE_SCHEMA_VERSION,
        project_id=attempt.project_id,
        run_id=attempt.run_id,
        target_id=attempt.target_id,
        target_version=attempt.target_version,
        redacted_document_version_id=redacted.redacted_document_version_id,
        reference_document_version_id=authoritative.reference_document_version_id,
        redacted_canonical_version_id=redacted.canonical_document_version_id,
        reference_canonical_version_id=authoritative.reference_canonical_version_id,
        attempt_id=attempt.attempt_id,
        attempt_status=attempt.status,
        model_id=attempt.model_id,
        model_config_id=attempt.model_config_id,
        condition_id=condition_id,
        mapping_id=authoritative.mapping_id,
        mapping_version=authoritative.mapping_version,
        mapping_status=authoritative.status,
        mapping_scoreability=authoritative.scoreability,
        reference_trust=trust,
        evaluator_version=evaluator_version,
        judge_id=judge.judge_id,
        judge_version=judge.judge_version,
        rubric_version=rubric_version,
        source_fact_record_id=record_id,
        source_fact_record_version=record_version,
        process_status=process_status,
        qualitative_status=qualitative_status,
        score_status=ScoreStatus.NONE,
        score_scale_id=None,
        research_validation_id=None,
        verified_score=None,
        experimental_score=None,
        fact_comparisons=comparisons,
        contradictions=contradictions,
        unsupported_assertions=unsupported,
        attempt_request_hash=attempt.request_hash,
        attempt_response_hash=attempt.response_hash,
        explanation=explanation,
        created_at=created_at,
    )
