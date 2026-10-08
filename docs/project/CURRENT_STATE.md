# Current state

Updated: 2026-10-08 (America/New_York). Coordination epoch: **E0026**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 12 MVP implementation. **Execution boundary:** RL-MVP-001 and RL-MVP-002 are merged. RL-MVP-003 reference alignment is owner-approved within its task packet; later tasks remain unapproved.
**Product implementation:** RL-MVP-001 merged in PR #1 (`ba60aaa8`); RL-MVP-002 merged in PR #2 (`35281fb9`).
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

E0026: independent QA FAIL and Research CHANGES_REQUESTED on Task 3. Owner approved bounded Correction 01 and DEC-021; no merge, Task 4, paid model calls, scientific scoring or deployment. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | MERGED | Backend/Codex + Lead integration | Reviewed implementation `736fa18`, owner-approved PR #2 merged as `35281fb9`; QA PASS and Research Task-2 semantics PASS. |
| RL-MVP-003 | CHANGES_REQUESTED; CORRECTION_01_APPROVED | Backend/Codex | QA FAIL and Research CHANGES_REQUESTED on `931fb1c`. [Correction 01 packet](task_packets/RL-MVP-003-CORRECTION-01.md) approved under DEC-021; trusted reference identity, two-sided support and exact span. No merge or Task 4. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**October 12, 2026 MVP remains AT RISK.** Tasks 1 and 2 merged; Task 3 unmerged and under correction; Tasks 4+ not authorized.

Independent [QA](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/007eb0e242a3f43cc01843d0713442a7f02e1e1f/docs/project/handoffs/RL-MVP-003-qa-20261008T202300Z-931fb1c.md) (FAIL) and [Research](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/6406a25012801c3850a10e65c4dc8a11036b7c5a/docs/project/handoffs/RL-MVP-003-research-20261008T205700Z-review.md) (CHANGES_REQUESTED) reviewed `931fb1c`. Both found false-CONFIRMED risk from one-sided global alignment and exact target-edge whitespace loss; Research also found wrong-release acceptance from matching local neighbors. Full 145-test suite was not independently rerun.

The owner approved [Correction 01](task_packets/RL-MVP-003-CORRECTION-01.md) and DEC-021: require both textual sides, preserve exact spans or null, and verify trusted existing DocumentVersion SHA-256/role/project/version against reference bytes. Trusted record provenance and correct release pairing are still external responsibilities; if not provable, do not CONFIRM. Codex may modify only `reference.py`, `test_reference.py` and a new Backend handoff on the existing Task-3 branch. New exact-SHA QA/Research reviews required. No merge, Task 4, model calls, paid services, deployment or D03 scientific approval.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, vector-PDF redaction detector, safe canonicalizer, package metadata and Task 1+2 tests. Absent: reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0026: owner approved DEC-021 and bounded RL-MVP-003 Correction 01 after independent QA and Research requested changes. No corrected implementation yet.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
