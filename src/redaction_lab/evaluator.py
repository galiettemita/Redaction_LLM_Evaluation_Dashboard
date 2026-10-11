"""Fail-closed, qualitative-only evaluation of trusted frozen attempts."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json

from redaction_lab.canonical import canonicalize_redacted
from redaction_lab.contracts import (
    AttemptStatus,
    EvaluationProcessStatus,
    EvaluationRecord,
    EvidenceValidationState,
    FactComparison,
    FactEvidenceLabel,
    ReferenceMapping,
    ReferenceScoreability,
    ReferenceStatus,
    ScoreStatus,
)
from redaction_lab.judges.base import FactJudge, SourceFact, SourceFactRecord
from redaction_lab.pdf_detector import DetectionStatus, detect_targets
from redaction_lab.reference import align_reference
from redaction_lab.store import ResolvedAttempt


EVIDENCE_SCHEMA_VERSION = "qualitative-fact-evidence-v2"
EVALUATION_VERSION = "qualitative-evaluation-v2"
TRUSTED_REFERENCE = "APPROVED_SYNTHETIC_PAIR"
UNTRUSTED_REFERENCE = "UNTRUSTED_OR_UNAVAILABLE"


class EvaluationBindingError(ValueError):
    """Raised when immutable attempt/reference identities do not agree."""


def _digest(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"{prefix}-{sha256(encoded).hexdigest()}"


def _sha_payload(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_source_fact_record(
    mapping: ReferenceMapping,
    *,
    facts: tuple[SourceFact, ...],
    rubric_version: str,
    source_fact_record_version: str,
) -> SourceFactRecord:
    """Freeze explicitly unvalidated, reference-only synthetic facts."""

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
        "validation_state": EvidenceValidationState.UNVALIDATED_SYNTHETIC.value,
        "facts": [fact.model_dump(mode="json") for fact in facts],
    }
    return SourceFactRecord(
        source_fact_record_id=_digest("source-facts", identity),
        facts=facts,
        validation_state=EvidenceValidationState.UNVALIDATED_SYNTHETIC,
        **{
            key: value
            for key, value in identity.items()
            if key not in {"facts", "validation_state"}
        },
    )


def _task4_target(resolved: ResolvedAttempt):
    attempt = resolved.attempt
    if (
        attempt.project_id != resolved.source.project_id
        or attempt.project_id != resolved.run.project_id
        or attempt.project_id != resolved.manifest.project_id
        or attempt.run_id != resolved.run.run_id
        or attempt.run_id != resolved.manifest.run_id
        or attempt.model_id != resolved.manifest.model_id
    ):
        raise EvaluationBindingError("resolved attempt provenance mismatch")
    if (
        attempt.target_id != resolved.manifest.target_id
        or attempt.target_version != resolved.manifest.target_version
    ):
        raise EvaluationBindingError("resolved attempt target provenance mismatch")
    matches = tuple(
        target
        for target in resolved.source.targets
        if target.target_id == attempt.target_id
        and target.target_version == attempt.target_version
    )
    if len(matches) != 1:
        raise EvaluationBindingError("resolved attempt target is absent or stale")
    return matches[0]


def _authoritative_mapping(
    resolved: ResolvedAttempt,
    mapping: ReferenceMapping,
    *,
    redacted_pdf: bytes,
    reference_pdf: bytes | None,
):
    if sha256(redacted_pdf).hexdigest() != resolved.source.source_sha256:
        raise EvaluationBindingError("redacted PDF does not match trusted Task-4 source")
    if mapping.project_id != resolved.attempt.project_id:
        raise EvaluationBindingError("mapping project identity mismatch")
    if mapping.redacted_canonical_version_id is None:
        raise EvaluationBindingError("mapping canonical identity is unavailable")

    detection = detect_targets(
        redacted_pdf,
        project_id=mapping.project_id,
        redacted_document_version_id=mapping.redacted_document_version_id,
    )
    if detection.status is not DetectionStatus.SUPPORTED:
        raise EvaluationBindingError("mapping redacted source is unsupported")
    canonical = canonicalize_redacted(
        redacted_pdf,
        detection,
        project_id=mapping.project_id,
        redacted_document_version_id=mapping.redacted_document_version_id,
        canonical_document_version_id=mapping.redacted_canonical_version_id,
    )
    recomputed = align_reference(
        canonical,
        reference_pdf,
        redacted_pdf=redacted_pdf,
        targets=detection.targets,
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

    reference_targets = tuple(
        target for target in detection.targets if target.target_id == authoritative.target_id
    )
    if len(reference_targets) != 1:
        raise EvaluationBindingError("reference authority target is absent")
    task_target = _task4_target(resolved)
    reference_target = reference_targets[0]
    bridge = (
        task_target.page_index == reference_target.page_index
        and task_target.normalized_bbox == reference_target.normalized_bbox
        and task_target.detector_version == reference_target.detector_version
        and task_target.detection_method == reference_target.detection_method
    )
    if not bridge:
        raise EvaluationBindingError("Task-4 and reference authority targets mismatch")
    return authoritative, trusted, task_target, reference_target


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
    if record.validation_state is not EvidenceValidationState.UNVALIDATED_SYNTHETIC:
        raise EvaluationBindingError("source fact validation state is not authorized")
    rebuilt = build_source_fact_record(
        mapping,
        facts=record.facts,
        rubric_version=record.rubric_version,
        source_fact_record_version=record.source_fact_record_version,
    )
    if rebuilt != record:
        raise EvaluationBindingError("source fact record integrity mismatch")


def _record_identity_payload(record: EvaluationRecord) -> dict[str, object]:
    return record.model_dump(
        mode="json", exclude={"evaluation_id", "created_at"}
    )


def verify_evaluation_identity(record: EvaluationRecord) -> None:
    expected = _digest("evaluation", _record_identity_payload(record))
    if record.evaluation_id != expected:
        raise EvaluationBindingError("evaluation deterministic identity mismatch")


def verify_evaluation_bindings(
    record: EvaluationRecord, resolved: ResolvedAttempt
) -> None:
    expected = (
        resolved.attempt.attempt_id,
        resolved.job.job_id,
        resolved.source.source_id,
        resolved.source.source_version,
        resolved.source.source_sha256,
        resolved.run.run_id,
        resolved.run.run_version,
        resolved.run_digest,
        resolved.manifest.manifest_id,
        resolved.manifest.manifest_version,
        resolved.manifest_digest,
        resolved.manifest.canonical_document_hash,
        resolved.attempt.request_hash,
        resolved.attempt.response_hash,
    )
    actual = (
        record.attempt_id,
        record.job_id,
        record.source_id,
        record.source_version,
        record.source_sha256,
        record.run_id,
        record.run_version,
        record.run_digest,
        record.manifest_id,
        record.manifest_version,
        record.manifest_digest,
        record.canonical_document_hash,
        record.attempt_request_hash,
        record.attempt_response_hash,
    )
    if expected != actual:
        raise EvaluationBindingError("evaluation does not match Task-4 provenance")
    verify_evaluation_identity(record)


def evaluate_attempt(
    resolved: ResolvedAttempt,
    mapping: ReferenceMapping,
    *,
    redacted_pdf: bytes,
    reference_pdf: bytes | None,
    source_fact_record: SourceFactRecord | None,
    judge: FactJudge,
    evaluator_version: str,
    rubric_version: str,
    created_at: datetime,
) -> EvaluationRecord:
    """Evaluate a resolver-authenticated attempt; persistence grants authority."""

    attempt = resolved.attempt
    authoritative, trusted, task_target, reference_target = _authoritative_mapping(
        resolved,
        mapping,
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
    )
    trust = TRUSTED_REFERENCE if trusted else UNTRUSTED_REFERENCE
    process_status = EvaluationProcessStatus.COMPLETE
    qualitative_status: str
    comparisons: tuple[FactComparison, ...] = ()
    unsupported: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    record_id: str | None = None
    record_version: str | None = None
    source_validation: EvidenceValidationState | None = None
    judge_validation: EvidenceValidationState | None = None

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
        source_validation = source_fact_record.validation_state
        evidence = []
        try:
            for fact in source_fact_record.facts:
                judged = judge.assess(fact, attempt.prediction or "")
                if (
                    judged.validation_state
                    is not EvidenceValidationState.UNVALIDATED_SYNTHETIC
                ):
                    raise EvaluationBindingError(
                        "judge validation state is not authorized"
                    )
                evidence.append((fact, judged))
        except EvaluationBindingError:
            raise
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
            judge_validation = EvidenceValidationState.UNVALIDATED_SYNTHETIC
            process_status = EvaluationProcessStatus.NEEDS_REVIEW
            qualitative_status = "UNVALIDATED_MOCK_EVIDENCE"
            explanation = (
                "Unvalidated synthetic source-fact segmentation and mock judge "
                "evidence require Research Human review; no accuracy claim was made."
            )

    run = resolved.run
    settings_fingerprint = _sha_payload(run.settings.model_dump(mode="json"))
    protocol_payload = {
        "experiment_condition": run.experiment_condition,
        "prompt_id": run.prompt_id,
        "prompt_version": run.prompt_version,
        "settings_fingerprint": settings_fingerprint,
        "attempt_policy": run.attempt_policy,
        "context_policy": run.context_policy,
        "common_context_budget": run.common_context_budget,
        "tool_permissions": run.tool_permissions,
    }
    prediction_protocol_id = _digest("prediction-protocol", protocol_payload)
    model_provenance_id = _digest(
        "model-provenance",
        {
            "model_id": attempt.model_id,
            "provider_model_id": attempt.provider_model_id,
            "model_config_id": attempt.model_config_id,
        },
    )
    series_key = _digest(
        "evaluation-series",
        {
            "attempt_id": attempt.attempt_id,
            "mapping_id": authoritative.mapping_id,
            "mapping_version": authoritative.mapping_version,
            "source_fact_record_id": record_id,
            "source_fact_record_version": record_version,
            "rubric_version": rubric_version,
            "evaluator_version": evaluator_version,
            "judge_id": judge.judge_id,
            "judge_version": judge.judge_version,
        },
    )
    record = EvaluationRecord(
        evaluation_id="pending-evaluation-identity",
        evaluation_version=EVALUATION_VERSION,
        evidence_schema_version=EVIDENCE_SCHEMA_VERSION,
        evaluation_series_key=series_key,
        project_id=attempt.project_id,
        job_id=resolved.job.job_id,
        source_id=resolved.source.source_id,
        source_version=resolved.source.source_version,
        source_sha256=resolved.source.source_sha256,
        run_id=attempt.run_id,
        run_version=run.run_version,
        run_digest=resolved.run_digest,
        manifest_id=resolved.manifest.manifest_id,
        manifest_version=resolved.manifest.manifest_version,
        manifest_digest=resolved.manifest_digest,
        target_id=attempt.target_id,
        target_version=attempt.target_version,
        redacted_document_version_id=resolved.source.redacted_document_version_id,
        redacted_canonical_version_id=(
            resolved.source.canonical_document.canonical_document_version_id
        ),
        canonical_document_hash=resolved.manifest.canonical_document_hash,
        attempt_id=attempt.attempt_id,
        attempt_status=attempt.status,
        model_id=attempt.model_id,
        provider_model_id=attempt.provider_model_id,
        model_config_id=attempt.model_config_id,
        condition_id=run.experiment_condition,
        prompt_id=run.prompt_id,
        prompt_version=run.prompt_version,
        settings_fingerprint=settings_fingerprint,
        attempt_policy=run.attempt_policy,
        context_policy=run.context_policy,
        common_context_budget=run.common_context_budget,
        tool_permissions=run.tool_permissions,
        prediction_protocol_id=prediction_protocol_id,
        model_provenance_id=model_provenance_id,
        reference_target_id=reference_target.target_id,
        reference_target_version=reference_target.target_version,
        mapping_id=authoritative.mapping_id,
        mapping_version=authoritative.mapping_version,
        mapping_status=authoritative.status,
        mapping_scoreability=authoritative.scoreability,
        mapping_method_version=authoritative.mapping_method_version,
        reference_document_version_id=authoritative.reference_document_version_id,
        reference_canonical_version_id=authoritative.reference_canonical_version_id,
        redacted_canonical_hash=authoritative.redacted_canonical_hash,
        reference_canonical_hash=authoritative.reference_canonical_hash,
        reference_trust=trust,
        evaluator_version=evaluator_version,
        judge_id=judge.judge_id,
        judge_version=judge.judge_version,
        judge_validation_state=judge_validation,
        rubric_version=rubric_version,
        source_fact_record_id=record_id,
        source_fact_record_version=record_version,
        source_fact_validation_state=source_validation,
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
    evaluation_id = _digest("evaluation", _record_identity_payload(record))
    final = record.model_copy(update={"evaluation_id": evaluation_id})
    verify_evaluation_bindings(final, resolved)
    return final
