"""Provider-neutral qualitative judge boundary for synthetic Task 6 evidence."""

from __future__ import annotations

from typing import Protocol

from pydantic import model_validator

from redaction_lab.contracts import FactEvidenceLabel, FrozenRecord, NonEmptyStr


class SourceFact(FrozenRecord):
    """One reference-only proposition frozen before prediction inspection."""

    fact_id: NonEmptyStr
    reference_proposition: NonEmptyStr
    reference_quote: NonEmptyStr
    reference_quote_locator: NonEmptyStr
    critical_dimensions: tuple[NonEmptyStr, ...]
    dependency_fact_id: NonEmptyStr | None = None
    notes: NonEmptyStr | None = None

    @model_validator(mode="after")
    def require_dimensions(self) -> SourceFact:
        if not self.critical_dimensions:
            raise ValueError("source facts require at least one critical dimension")
        if len(set(self.critical_dimensions)) != len(self.critical_dimensions):
            raise ValueError("critical dimensions must be unique")
        return self


class SourceFactRecord(FrozenRecord):
    """Versioned reference-only fact decomposition with mapping provenance."""

    source_fact_record_id: NonEmptyStr
    source_fact_record_version: NonEmptyStr
    project_id: NonEmptyStr
    target_id: NonEmptyStr
    target_version: NonEmptyStr
    mapping_id: NonEmptyStr
    mapping_version: NonEmptyStr
    rubric_version: NonEmptyStr
    facts: tuple[SourceFact, ...]


class JudgeEvidence(FrozenRecord):
    """A qualitative, explicitly provisional assessment from a judge boundary."""

    evidence_label: FactEvidenceLabel
    prediction_excerpt: NonEmptyStr | None = None
    rationale: NonEmptyStr
    unsupported_assertions: tuple[NonEmptyStr, ...] = ()
    provisional: bool = True
    disagreement: bool = False

    @model_validator(mode="after")
    def forbid_nonprovisional_task6_claims(self) -> JudgeEvidence:
        if not self.provisional:
            raise ValueError("Task 6 judge evidence must remain provisional")
        return self


class FactJudge(Protocol):
    """Reusable boundary; implementations must not infer numeric accuracy."""

    judge_id: str
    judge_version: str

    def assess(self, reference: SourceFact, prediction: str) -> JudgeEvidence:
        """Assess one frozen reference fact against one frozen prediction."""
