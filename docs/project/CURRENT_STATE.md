# Current state

Updated: 2026-10-08 (America/New_York). Coordination epoch: **E0027**.
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

E0027 HOLD: Backend stopped Task-3 Correction 01 after local false-CONFIRMED probe using fabricated DocumentVersion; rejected candidate NOT PUBLISHED. Trusted reference provenance/pairing decision pending. No merge, Task 4, paid model calls, scoring or deployment. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; RL-MVP-002 coding approved within its packet. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | MERGED | Backend/Codex + Lead integration | Reviewed implementation `736fa18`, owner-approved PR #2 merged as `35281fb9`; QA PASS and Research Task-2 semantics PASS. |
| RL-MVP-003 | BLOCKED; TRUST_BOUNDARY_PROPOSED | Backend/Codex + Lead | Backend stopped on fabricated-record false CONFIRMED and partially hidden edge punctuation; local rejected candidate `80f9ee1` NOT PUBLISHED. [Owner decision proposal](task_packets/RL-MVP-003-TRUST-BOUNDARY-PROPOSAL.md). No merge/Task 4. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**October 12, 2026 MVP remains AT RISK.** Tasks 1 and 2 merged; Task 3 BLOCKED; Tasks 4+ unauthorized.

Backend reports stopping Correction 01 after an independent local probe falsely CONFIRMED ground truth when a caller fabricated a matching DocumentVersion. SHA-256 checks only establish byte consistency, not the record's authority or true document pairing. A second local finding shows partially covered edge punctuation can be omitted while CONFIRMED. Backend reports 159 full tests passed on local candidate `80f9ee1`, but it is **rejected and NOT PUBLISHED**; Lead has not inspected it or run its tests. Remote Task-3 branch remains at `2d79ee6`.

[Owner decision proposal](task_packets/RL-MVP-003-TRUST-BOUNDARY-PROPOSAL.md): for October 12, use an explicitly trusted synthetic-fixture pairing registry/manifest and keep arbitrary uploaded references unconfirmed/null; or authorize a broader authenticated intake/persistence boundary. Neither option is yet approved. Do not resume Task-3 implementation, merge, start Task 4, use paid services or claim D03 scientific validation without the required approval.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, vector-PDF redaction detector, safe canonicalizer, package metadata and Task 1+2 tests. Absent: reference aligner, persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0027: Task-3 Correction 01 blocked on missing trusted reference provenance; local rejected candidate not published. Owner decision requested; no new design approved.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
