# Current state

Updated: 2026-10-08 (America/New_York). Coordination epoch: **E0020**.
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

E0020 hold: RL-MVP-002 Correction 04 is published but not independently reviewed. No merge or Task 3 before fresh exact-SHA QA/Research reviews and owner authorization. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | CORRECTION_04_READY_FOR_REVIEW | Backend/Codex | Implementation `df20fe0`, branch head `6ba3e02`; Codex reports 113 full tests passed. [Fresh review packet](task_packets/RL-MVP-002-CORRECTION-04-REVIEW.md). No merge/Task 3. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**October 12, 2026 MVP checkpoint remains AT RISK.** Task 1 merged; Task 2 not integrated; later tasks unbuilt.

Codex published RL-MVP-002 Correction 04 implementation `df20fe074c0bebc7be15971199d3c361469bc6b1` and Backend handoff branch head `6ba3e02af0d13b8ef673ac007f06d08912ff9e38`. GitHub delta confirms detector source, detector tests and one handoff only. Codex reports 70 focused and 113 full tests passing, compileall and dependency/diff checks; Lead has not rerun them.

[Fresh QA/Research review packet](task_packets/RL-MVP-002-CORRECTION-04-REVIEW.md) covers staggered columns, centered heading exception, 18–20 pt no-glyph boxes, remote artwork controls, hidden-text suppression and prior regressions. Both reviewers must assess this exact SHA. No merge, Task 3, paid calls, deployment or scientific score approval.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, package metadata and 43 tests from RL-MVP-001. Absent: detector, canonicalizer, reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0020: Codex published Correction 04 at `df20fe0`; fresh QA and Research review routed. No independent verdict, merge or Task 3.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
