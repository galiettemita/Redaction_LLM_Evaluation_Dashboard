# Current state

Updated: 2026-10-07 (America/New_York). Coordination epoch: **E0014**.
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

E0014 hold: RL-MVP-002 corrected candidate is ready for fresh independent QA and Research review. Do not merge or start Task 3 before reviews and authorization. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 14 design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | CORRECTED_READY_FOR_REVIEW (branch only) | Backend/Codex | Corrected implementation `12698b9`, handoff branch head `c3783766`; Codex reports 88 tests passing. [Fresh QA/Research packet](task_packets/RL-MVP-002-CORRECTED-REVIEW.md); no merge/Task 3. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

Codex published RL-MVP-002 corrected implementation `12698b92d883af658266d54a9223b5619dedc7ee` and Backend handoff at branch head `c37837669ce9e538a3afa8db0e25ef92cbbdd327`. GitHub comparison from prior handoff `a6a603f6` confirms only `src/redaction_lab/pdf_detector.py`, `tests/test_pdf_detector.py` and one new handoff changed. Codex reports 45 focused and 88 full tests passing, compileall, diff check and 21 compatible packages; these tests have **not** been independently rerun by Lead.

[Fresh QA/Research review packet](task_packets/RL-MVP-002-CORRECTED-REVIEW.md) requires re-testing all four prior blockers, redacted-only safety and regression behavior on the **new exact SHA**. No independent verdict yet; no merge or Task 3. Cross-record/version integrity and D03–D06 research validity remain separate gates.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, package metadata and 43 tests from RL-MVP-001. Absent: detector, canonicalizer, reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0014: corrected RL-MVP-002 candidate verified published on task branch; fresh QA and Research review routed. No merge, new model call, scientific approval or Task 3 authorization.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
