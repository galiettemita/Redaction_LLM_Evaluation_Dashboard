# RL-MVP-001 — typed contracts and synthetic fixtures

Status: PROPOSED, NOT YET AUTHORIZED TO IMPLEMENT.
Owner: Backend / Infrastructure. Reviewer: QA; Research reviews truth/score semantics.
Baseline: 7a3150ceea2d5fb23aa8acfaeef2b0ed2c4c2bc1 / E0004. Source: DEC-001..018, MVP design and roadmap.
Objective: create a minimal typed record/serialization contract and synthetic fixture generator/test harness for later ingestion, alignment, prediction and evaluation work.
Non-goals: no live models, no paid APIs, no cloud, no deployment, no production data, no scoring thresholds.
Allowed proposed file scope: src/redaction_lab/contracts/**, tests/contracts/**, tests/fixtures/synthetic/**, task-scoped handoff; refine exact paths in implementation plan before approval.
Deliverables: DocumentVersion, RedactionTarget, ReferenceMapping, RunDefinition, ModelAttempt, EvaluationRecord, SummarySnapshot and JobState contracts; status/null semantics; deterministic synthetic redacted/reference PDF fixtures with multiple text boxes, partial/ambiguous examples and hidden text-layer trap.
Acceptance: tests prove unknown truth is null, technical errors differ from factual mistakes, reference fields cannot serialize into prediction manifest, target IDs are versioned, fixture generation deterministic. Record actual test commands/results; no fabricated passes.
Constraints: zero new spend, synthetic only, isolated task branch, one owner, no main edits by specialist, unique handoff, no unapproved changes outside scope.
Stop: blocked hardware or licenses are recorded, not bypassed; stop for contract conflict, reference leakage, unexpected cost or changed decision epoch.
Next receiver: Lead for integration review, then Backend RL-MVP-002.
