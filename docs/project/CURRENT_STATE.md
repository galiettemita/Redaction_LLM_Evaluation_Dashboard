# Current state

Updated: 2026-10-07 (America/New_York). Coordination epoch: **E0007**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 14 MVP implementation. **Execution boundary:** RL-MVP-001 contracts and synthetic fixtures ONLY approved for Codex; all other coding tasks remain unapproved.
**Product implementation:** not started in this repository at initialization.
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

No specific urgent amendment is recorded at E0007. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 14 design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; only RL-MVP-001 coding authorized. |
| RL-MVP-001 | APPROVED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); authorized for typed contracts, synthetic fixtures and their tests only; no main merge. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

Owner approved the detailed [Codex implementation plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) and requested to proceed with the exact RL-MVP-001 prompt on 2026-10-07. [RL-MVP-001](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md) is now approved for one isolated Codex task branch: typed records, synthetic PDFs, unit tests and a task-scoped handoff only. Codex must complete/return its read-only preflight first and report any relevant blockers. No code completion or specialist acknowledgment is yet evidenced.

No other task is approved. No merge, paid calls, external provider, restricted data, cloud provisioning or deployment. Model hardware/license feasibility remains a gate for RL-MVP-004 and RL-MVP-006, not a reason to invent a model or block synthetic Task 1 unnecessarily. D02/D03/D04/D05/D06/D07 specialist approvals remain separate.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Absent: application code, schemas/migrations, APIs, workers, provider integrations, reference dataset, measured evaluator, UI implementation, test suite and deployment. No CI or cron is installed. Branch protection and permission enforcement were not configured by this setup.

## Latest important change

E0007: owner approved the detailed implementation plan and authorized only RL-MVP-001 on a task branch, with TDD, synthetic-only data, no extra spending, no merge and a unique handoff. Other tasks remain proposed. See CHANGELOG and AGENT_HANDOFF.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
