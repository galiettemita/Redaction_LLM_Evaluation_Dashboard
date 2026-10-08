# Current state

Updated: 2026-10-07 (America/New_York). Coordination epoch: **E0008**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 14 MVP implementation. **Execution boundary:** RL-MVP-001 contracts and synthetic fixtures ONLY approved for Codex; all other coding tasks remain unapproved.
**Product implementation:** RL-MVP-001 candidate published on a task branch only; no application code merged to main.
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

No specific urgent amendment is recorded at E0008. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 14 design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; only RL-MVP-001 coding authorized. |
| RL-MVP-001 | READY_FOR_REVIEW (branch only) | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); candidate `b0282281` on `codex/rl-mvp-001-contracts-fixtures`; Codex reports 19 passing tests; QA/Research independent review pending; no main merge. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

Codex published RL-MVP-001 at branch `codex/rl-mvp-001-contracts-fixtures`, implementation commit `8fff5f11cd9ce0c1e2ca7943aab7d02f629eff58`, handoff/branch head `b0282281e72f37c1cd1f7899d09691024991d150`. GitHub comparison confirms only five approved implementation files and one scoped handoff. Codex reports 19 passing tests and a clean worktree; Lead has **not** independently run them.

**Next:** independent [QA review](task_packets/RL-MVP-001-QA-review.md) and [Research contract review](task_packets/RL-MVP-001-RESEARCH-review.md) of the exact candidate. Lead's preliminary inspection flags mutable nested dictionaries, unrestricted settings content in the prediction manifest, and insufficient cross-field evidence for confirmed/verified states; these are hypotheses requiring reviewer verification, not independent QA results. No merge or Task 2 authorization until reviews and owner permission.

No paid calls, external provider, restricted data, cloud provisioning or deployment. D02/D03/D04/D05/D06/D07 specialist approvals remain separate.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Absent from main: application code, schemas/migrations, APIs, workers, provider integrations, reference dataset, measured evaluator, UI implementation, test suite and deployment. Candidate branch has contracts, synthetic fixture generator and 19 reported passing tests; no independent verification yet. No CI or cron is installed. Branch protection and permission enforcement were not configured by this setup.

## Latest important change

E0008: RL-MVP-001 candidate branch and handoff verified published; routed independent QA and Research reviews with exact candidate SHA. No QA verdict, research sign-off, merge or next-task approval claimed. See CHANGELOG and AGENT_HANDOFF.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
