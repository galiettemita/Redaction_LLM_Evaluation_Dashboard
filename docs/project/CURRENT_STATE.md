# Current state

Updated: 2026-10-08 (America/New_York). Coordination epoch: **E0034**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 12 MVP implementation. **Execution boundary:** RL-MVP-001, RL-MVP-002 and RL-MVP-003 are merged. RL-MVP-004 is approved for mock-tested implementation and read-only local feasibility preflight only. Task 5+ remains unapproved.
**Product implementation:** RL-MVP-001 merged in PR #1 (`ba60aaa8`); RL-MVP-002 merged in PR #2 (`35281fb9`); RL-MVP-003 merged in PR #3 (`733ae024`).
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

E0034: owner approved bounded RL-MVP-004 mock-tested adapter/durable-worker implementation and read-only machine/model feasibility preflight. No real inference, downloads, paid calls, scientific scoring or deployment authorized. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; Tasks 1–3 merged; Task 4 not approved. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | MERGED | Backend/Codex + Lead integration | Reviewed implementation `736fa18`, owner-approved PR #2 merged as `35281fb9`; QA PASS and Research Task-2 semantics PASS. |
| RL-MVP-003 | MERGED | Backend/Codex + Lead integration | Exact candidate `97db3615`, published branch head `139921de`, owner-authorized [PR #3](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/3) merged as `733ae024`. QA PASS; Research Task-3 semantics PASS. Synthetic-only pairing, no D03 approval. |
| RL-MVP-004 | APPROVED; NOT STARTED | Backend/Codex | [Bounded adapter/durable worker packet](task_packets/RL-MVP-004-prediction-adapter-durable-worker-PROPOSED.md). Mock-only implementation + read-only local preflight. No real inference, downloads, extra spend, merge or deployment. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**October 12 MVP remains AT RISK.** Tasks 1–3 merged. The owner approved [RL-MVP-004](task_packets/RL-MVP-004-prediction-adapter-durable-worker-PROPOSED.md) for Codex to implement a strictly redacted-only provider-neutral prediction adapter, mock-tested loopback transport and durable SQLite one-shot worker, plus a **read-only local hardware/model/license preflight**. No real inference, model download/install, external API, additional spend, deployment or Task 5+ authorization.

Codex must create a new isolated Task-4 branch, perform TDD, publish one unique Backend handoff and submit an exact candidate for independent QA and Research review. If the approved file/contract scope is insufficient or the in-doubt retry boundary cannot be represented safely, STOP for review. No local model or hardware has been verified; mocks do not count as a real-model demonstration. D03 scientific scoring validity remains pending.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: typed contracts, synthetic PDF fixtures, vector-PDF redaction detector, safe canonicalizer, text-first reference aligner, synthetic two_boxes trust registry, package metadata and Task 1–3 tests. Absent: persistence, API, workers, model adapters, evaluator, UI and deployment. No CI or cron is installed.

## Latest important change

E0034: owner-approved Task-4 mock-only implementation and read-only feasibility preflight; no inference or merge.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.
