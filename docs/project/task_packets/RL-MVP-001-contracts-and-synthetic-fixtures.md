# RL-MVP-001 — typed contracts and synthetic fixtures

Status: PREPARED, NOT YET AUTHORIZED TO IMPLEMENT. See Task 1 in docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md.
Owner: Backend / Infrastructure. Reviewer: QA; Research reviews truth/score semantics.
Baseline: refresh live main HEAD / current epoch before execution. Written design approved at E0006; detailed plan awaits owner review. Source: DEC-001..018, MVP design and roadmap.
Objective: create a minimal typed record/serialization contract and synthetic fixture generator/test harness for later ingestion, alignment, prediction and evaluation work.
Non-goals: no live models, no paid APIs, no cloud, no deployment, no production data, no scoring thresholds.
Allowed proposed file scope: pyproject.toml; src/redaction_lab/contracts.py; src/redaction_lab/fixtures.py; tests/test_contracts.py; tests/test_fixtures.py; task-scoped handoff. No other application files.
Deliverables: DocumentVersion, RedactionTarget, ReferenceMapping, RunDefinition, ModelAttempt, EvaluationRecord, SummarySnapshot and JobState contracts; status/null semantics; deterministic synthetic redacted/reference PDF fixtures with multiple text boxes, partial/ambiguous examples and hidden text-layer trap.
Acceptance: tests prove unknown truth is null, technical errors differ from factual mistakes, reference fields cannot serialize into prediction manifest, target IDs are versioned, fixture generation deterministic. Record actual test commands/results; no fabricated passes.
Constraints: zero new spend, synthetic only, isolated task branch, one owner, no main edits by specialist, unique handoff, no unapproved changes outside scope.
Stop: blocked hardware or licenses are recorded, not bypassed; stop for contract conflict, reference leakage, unexpected cost or changed decision epoch.
Next receiver: Lead for integration review, then Backend RL-MVP-002.
