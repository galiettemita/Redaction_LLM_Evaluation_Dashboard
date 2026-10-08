# RL-MVP-001 — Research semantics review packet

Status: REVIEW REQUESTED, NOT STARTED. Read-only contract review and unique handoff are within the approved RL-MVP-001 Research reviewer role. No product code edits or main updates.
Reviewer: Research / Evaluation.
Main baseline: 5743b7a8ff6cc32c3e2a582392030d79047455e8 / E0007. Current coordination epoch E0008. Candidate branch: codex/rl-mvp-001-contracts-fixtures; **exact candidate SHA: b0282281e72f37c1cd1f7899d09691024991d150**.
Source: AGENTS.md, DECISIONS.md, RESEARCH_METHOD.md, INTERFACES.md, RL-MVP-001 packet and candidate Backend handoff.

## Objective

Check that immutable data contracts preserve verified truth, unknown/null semantics, prediction/reference separation, provenance and distinct evaluation statuses. This is a **contract semantics review**, not approval of any scoring algorithm, numerical thresholds or human benchmark.

## Mandatory questions

1. Can ReferenceMapping become CONFIRMED without reference ID, exact token locator, left/right anchors, unique alignment evidence or full revealed text? Which must be enforced at contract construction vs at the alignment service?
2. Can EvaluationRecord be VERIFIED without a confirmed mapping and a completed successful attempt? Is it safe for the schema to represent that state before validation?
3. Can unknown/partial truth, evaluator uncertainty, model refusal/timeout, and provisional scores be misrepresented or conflated? Are status axes independent enough?
4. Are source exact whitespace/quotations and canonical matching text distinguishable? Are versions/IDs sufficient to prevent stale or cross-project score claims?
5. Can SummarySnapshot represent per-target, per-document and per-model results, verified denominators, exclusions, common-set comparability and null scores without inventing weights?
6. Do synthetic fixtures include necessary adversarial examples? Recommend only changes essential to this Task 1 contract; defer broader rubric and benchmark to RL-MVP-005.

## Deliverable

Unique Research handoff on an approved review branch or NOT PUBLISHED in chat if write access unavailable. Include exact candidate SHA, specific findings, proposed contract changes, tests/evidence reviewed, approval status (research-human sign-off not presumed), and next receiver Lead. No product implementation, scoring weights, paid calls or merge.
