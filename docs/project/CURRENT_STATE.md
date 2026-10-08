# Current state

Updated: 2026-10-07 (America/New_York). Coordination epoch: **E0006**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S0 / October 14 MVP implementation-plan review. **Execution boundary:** DOCUMENTATION_ONLY; written MVP design approved, detailed plan and first coding task still awaiting owner review.
**Product implementation:** not started in this repository at initialization.
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

No specific urgent amendment is recorded at E0006. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | DESIGN_APPROVED_PLAN_READY_FOR_REVIEW | Lead/Architect | [Oct 14 design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) ready for review; no code authorized. |
| RL-MVP-001 | PROPOSED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); requires detailed plan review and task approval. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

DEC-019 records owner approval of the Oct 14 written MVP design. The [detailed Codex implementation plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) is READY FOR OWNER REVIEW. [Backend](kickoffs/BACKEND.md), [Research](kickoffs/RESEARCH.md), [Frontend](kickoffs/FRONTEND.md) and [QA](kickoffs/QA.md) kickoff packets and [Codex startup guide](CODEX_START_HERE.md) are published. No other chat has been awakened or acknowledged these records.

Next owner action: review and approve detailed plan; authorize first bounded coding packet. Read-only Codex startup and local feasibility check may happen before coding approval. Research-human D03-D06, lab/data D02, engineering/lab D07 and local model hardware/license feasibility remain separate gates. Zero additional spending.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Absent: application code, schemas/migrations, APIs, workers, provider integrations, reference dataset, measured evaluator, UI implementation, test suite and deployment. No CI or cron is installed. Branch protection and permission enforcement were not configured by this setup.

## Latest important change

E0006: written Oct 14 design approved; detailed TDD implementation plan and all four role-specific kickoffs published, with a read-only Codex startup guide. Application code, model smoke tests, and QA are NOT started. See CHANGELOG and AGENT_HANDOFF.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
