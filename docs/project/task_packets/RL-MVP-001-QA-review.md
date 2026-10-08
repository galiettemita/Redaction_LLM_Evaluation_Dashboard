# RL-MVP-001 — independent QA review packet

Status: REVIEW REQUESTED, NOT STARTED. Read-only review and scoped QA handoff are within the approved RL-MVP-001 reviewer role; no product code modifications or main edits.
Reviewer: QA / Independent Reviewer.
Main baseline: 5743b7a8ff6cc32c3e2a582392030d79047455e8 / E0007. Current coordination epoch E0008. Candidate branch: codex/rl-mvp-001-contracts-fixtures; **exact candidate SHA: b0282281e72f37c1cd1f7899d09691024991d150**. Implementation commit: 8fff5f11cd9ce0c1e2ca7943aab7d02f629eff58.
Source: AGENTS.md, DECISIONS.md, INTERFACES.md, RL-MVP-001 packet, Task 1 implementation plan, Backend handoff on candidate.

## Objective

Independently inspect the exact six changed files, rerun tests if an authorized local checkout is available, and issue PASS / FAIL / BLOCKED with evidence and severity. Do not take Codex's 19 reported tests as independently verified. Check branch matches main baseline with no unapproved files.

## Mandatory cases

1. Frozen Pydantic records must not allow nested dictionaries or list-like data to mutate after creation. Check settings, detection_evidence, usage, fact_comparisons and nested values; test serialization after attempted mutation.
2. PredictionManifest must not accept or serialize reference-derived content via free-form settings or nested structures; top-level extra='forbid' alone may be insufficient.
3. CONFIRMED ReferenceMapping must not be constructible without the required complete/unique/readable evidence or with a missing reference; VERIFIED EvaluationRecord must not be accepted without scoreable mapping evidence. Distinguish contract-level enforcement from service-level invariants and identify the minimum safe ownership boundary.
4. SummarySnapshot must not permit a positive verified score with an empty eligible denominator, and must have enough document/model identity to support the three required score levels.
5. Recheck synthetic PDFs for overlay coverage, adjacent boxes, repeated anchors, still-hidden reference and exact-text whitespace; confirm no real research content or secrets are included.
6. Check unsupported/error states, IDs, immutability, type constraints, license/dependency risks, deterministic fixture output and README/test setup.
7. Record any test not run and reason. No deployment, model calls, paid tools, or implementation outside approved scope.

## Deliverable

Unique QA handoff on QA's own approved review branch or NOT PUBLISHED in chat if GitHub write access is unavailable. Include candidate SHA, actual commands/results, findings with reproducible steps, severity, PASS/FAIL/BLOCKED, next action to Lead. Do not merge or patch code as the reviewer.
