"""Disabled local-NLI boundary; no model, runtime, download, or inference."""

from __future__ import annotations

from dataclasses import dataclass

from redaction_lab.judges.base import JudgeEvidence, SourceFact


class LocalNLIUnavailableError(RuntimeError):
    """Raised until a local model, license, hardware, and method are approved."""


@dataclass(frozen=True, slots=True)
class LocalNLIJudge:
    judge_id: str = "local-nli-disabled"
    judge_version: str = "local-nli-disabled-v1"
    available: bool = False

    def assess(self, reference: SourceFact, prediction: str) -> JudgeEvidence:
        del reference, prediction
        raise LocalNLIUnavailableError(
            "local NLI is disabled pending separate model, license, hardware, "
            "and research-method approval"
        )
