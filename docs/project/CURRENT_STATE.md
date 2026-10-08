# Current state

Updated: 2026-10-07 (America/New_York). Coordination epoch: **E0012**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 14 MVP implementation. **Execution boundary:** RL-MVP-002 automatic text-redaction detection and safe canonicalization ONLY approved for Codex; all later coding tasks remain unapproved.
**Product implementation:** RL-MVP-001 merged to main in PR #1 at `ba60aaa811fad1ec7d2ad79ab2f4aebfa021b067`.
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

No new design hold at E0012; RL-MVP-002 remains under review. Do not merge or start Task 3. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 14 design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | READY_FOR_REVIEW (branch only) | Backend/Codex | Implementation `4304673`, handoff branch head `a6a603f`; Codex reports 78 tests passed. [QA packet](task_packets/RL-MVP-002-QA-review.md) and [Research packet](task_packets/RL-MVP-002-RESEARCH-review.md) issued. No merge/Task 3. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

Codex published RL-MVP-002 implementation `430467314ca992f36cf3eaab9d49cde45a9805ac` and Backend handoff at branch head `a6a603f6b11472df5cf36d2acd9eeec215fe81af` on `codex/rl-mvp-002-detection-canonicalization`. Compared to main `0b38e46ec467d9d1c3345b5fe24e03b24e578d0f`: five scoped implementation/test/dependency files plus one handoff, no unauthorized file changes. Codex reports 35 focused and 78 total tests passing, compilation and dependency checks; Lead has **not** independently run them.

**Next:** independent [QA review](RL-MVP-002-QA-review.md) and [Research review](RL-MVP-002-RESEARCH-review.md) of exact implementation SHA. QA prioritizes hidden selectable-text leakage, PDF graphics/occlusion and unsupported cases; Research checks redacted-only target/context semantics. No merge or Task 3 until reviews, reconciliation and required owner approval. No provider calls, paid services, restricted data or deployment.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, package metadata and 43 tests from RL-MVP-001. Absent: detector, canonicalizer, reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0012: RL-MVP-002 published candidate verified on GitHub and routed to independent QA and Research review. No independent verdict, merge or Task 3 authorization.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
