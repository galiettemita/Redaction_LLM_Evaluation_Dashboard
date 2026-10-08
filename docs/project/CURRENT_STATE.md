# Current state

Updated: 2026-10-07 (America/New_York). Coordination epoch: **E0013**.
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

E0013 hold: RL-MVP-002 reviewed candidate has four blocking QA/Research defects. Do not merge or start Task 3 until corrected and re-reviewed. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 14 design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | CHANGES_REQUESTED (branch only) | Backend/Codex | QA FAIL and Research CHANGES_REQUESTED on `4304673`; [Correction 01](task_packets/RL-MVP-002-CORRECTION-01.md) routed. No merge or Task 3. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

Independent [QA review](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/48adf452178e1e7c38896b088f2e7481846bf275/docs/project/handoffs/RL-MVP-002-qa-20261008T123940Z-4304673.md) reports FAIL on `430467314ca992f36cf3eaab9d49cde45a9805ac`: project-scoped target ID collisions, multi-column reading-order corruption, and overlapping black rectangles treated as multiple targets. Independent [Research review](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/a0d56b599a5ba284ef036b813fa8167164189847/docs/project/handoffs/RL-MVP-002-research-20261008T121239Z-rsem02.md) reports CHANGES_REQUESTED: overlapping/duplicate rectangles and a plausible standalone black text redaction silently treated as artwork/NO_REDACTIONS. Both reviewers used focused independent probes; neither reran the complete 78-test candidate suite.

**Lead disposition: CHANGES_REQUESTED; do not merge or start Task 3.** [Correction 01](task_packets/RL-MVP-002-CORRECTION-01.md) limits work to the existing approved Task 2 files. Codex must publish a new exact candidate and handoff; QA and Research independently re-review the new SHA. Scientific score validation and institutional data approval remain separate.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, package metadata and 43 tests from RL-MVP-001. Absent: detector, canonicalizer, reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0013: independent QA and Research reviewed RL-MVP-002 `4304673`; both request corrections. Four blocking detection/context issues routed in a bounded correction packet. No merge or Task 3.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
