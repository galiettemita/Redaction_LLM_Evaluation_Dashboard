# Current state

Updated: 2026-10-08 (America/New_York). Coordination epoch: **E0024**.
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

E0024: RL-MVP-003 is approved for synthetic-only reference alignment; no Task 4, model calls, merge, scientific scoring or deployment authorized. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | MERGED | Backend/Codex + Lead integration | Reviewed implementation `736fa18`, owner-approved PR #2 merged as `35281fb9`; QA PASS and Research Task-2 semantics PASS. |
| RL-MVP-003 | APPROVED (not started) | Backend/Codex | [Reference-alignment task packet](task_packets/RL-MVP-003-text-first-reference-alignment.md); new isolated branch, synthetic TDD, complete/unique/visible truth only, QA/Research review. No merge or Task 4. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**October 12, 2026 MVP remains AT RISK.** Tasks 1 and 2 merged; Task 3 is owner-approved but not implemented; Tasks 4+ remain unapproved.

The owner explicitly approved starting RL-MVP-003 after Task-2 integration. [Approved packet](task_packets/RL-MVP-003-text-first-reference-alignment.md) scopes deterministic text-first global/local anchor alignment with exact source quotation, fully revealed readable unique truth, and fail-closed unknown/null for partial, repeated, wrong-release or unsupported cases. Only new reference.py and test_reference.py plus one Backend handoff are authorized on a new Codex branch. QA and Research must independently review exact SHA before any merge. D03 research-human scientific confirmation criteria remain unvalidated.

No model calls, paid services, private data, Task 4, cloud or deployment.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, vector-PDF redaction detector, safe canonicalizer, package metadata and Task 1+2 tests. Absent: reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0024: owner approved RL-MVP-003 bounded Codex implementation. No Task-3 code, independent review or merge yet.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
