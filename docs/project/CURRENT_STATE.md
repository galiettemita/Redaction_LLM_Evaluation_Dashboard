# Current state

Updated: 2026-10-08 (America/New_York). Coordination epoch: **E0016**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 12 MVP implementation. **Execution boundary:** RL-MVP-002 automatic text-redaction detection and safe canonicalization ONLY approved for Codex; all later coding tasks remain unapproved.
**Product implementation:** RL-MVP-001 merged to main in PR #1 at `ba60aaa811fad1ec7d2ad79ab2f4aebfa021b067`.
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

E0016 hold: RL-MVP-002 Correction 02 candidate is published but not independently reviewed. No merge or Task 3 until exact-SHA QA/Research review and authorization. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | CORRECTION_02_READY_FOR_REVIEW | Backend/Codex | Implementation `ea930ab`, branch head `e5333602`; Codex reports 94 tests passed; [fresh review packet](task_packets/RL-MVP-002-CORRECTION-02-REVIEW.md). No merge/Task 3. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**DEC-020 first MVP checkpoint: October 12, 2026. Schedule remains AT RISK.** No scope, QA or research gates waived.

Codex published RL-MVP-002 Correction 02 implementation `ea930abef319832cf494df5851be1b19d3e2cf1c` and Backend handoff branch head `e5333602c43d304a21980fc96103d19599e2dd27` (detector v3, sparse-column and one-sided boundary black-box handling). Codex reports 51 focused and 94 full tests passed, but Lead has not independently rerun them. [Fresh QA/Research review packet](task_packets/RL-MVP-002-CORRECTION-02-REVIEW.md) is routed; no independent verdict yet. No merge or Task 3 authorization.

Only Task 1 is merged. Reference alignment, real predictor, independent evaluator, UI and end-to-end demo remain unbuilt. Hardware/model licensing, scientific scoring and Columbia data approval remain open. No extra spend or deployment.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, package metadata and 43 tests from RL-MVP-001. Absent: detector, canonicalizer, reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0016: Codex published Task 2 Correction 02 at `ea930ab`; exact-SHA QA and Research review requested. October 12 deadline unchanged. No merge or Task 3.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
