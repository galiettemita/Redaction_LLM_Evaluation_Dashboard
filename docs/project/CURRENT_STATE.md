# Current state

Updated: 2026-10-11 (America/New_York). Coordination epoch: **E0043**.
Integration branch: `main`. Canonical writer: **Lead/Architect**, within the owner's approved scope.
Resolve the actual HEAD with GitHub; do not infer a current SHA from this file's timestamp.

## Read this first

**Stage:** S1 / October 12 MVP implementation. **Execution boundary:** RL-MVP-001, RL-MVP-002 and RL-MVP-003 are merged. RL-MVP-004 has been owner-authorized and MERGED following Correction 01 independent QA and Research PASS; Task 5 is owner-approved for a research-only proposal on an isolated Research branch; Task 6 is owner-approved for bounded synthetic/mock-only implementation under [RL-MVP-006 packet](task_packets/RL-MVP-006-EVALUATOR-SUMMARIES.md); Task 7 implementation remains unapproved; owner selected portable local self-hosting for Task 7 planning, requiring independently runnable installation on another recipient computer; Task 6 integrated after owner approval and independent QA/Research scoped PASS; Task 7+ remains unapproved.
**Product implementation:** RL-MVP-001 merged in PR #1 (`ba60aaa8`); RL-MVP-002 merged in PR #2 (`35281fb9`); RL-MVP-003 merged in PR #3 (`733ae024`).
**Scoring validity:** not established. **Deployment:** none established here.
**Active background agents / scheduler:** none installed by this setup.
**Public-data warning:** repository visibility was public at inspection; unchanged.

The eight shared files and root agent instructions define a coordination protocol. They are not evidence of a running app or five active agents. A local checkout in another environment has not been inspected. Verify new activity before using these statements.

## Holds and urgent changes

E0036: Owner-approved Task-4 Correction 01 merged via PR #4 at `8f4d2f18` after scoped QA and Research PASS on exact implementation `b9ce818`. Real inference remains BLOCKED by missing verified runtime/model/license. No real inference, paid calls, Task 7 or deployment; Task 6 is approved only under its bounded packet. Standing hold: no application code, live model calls, migrations, cloud resources or deployment without the relevant approved task and decisions. Private data must not be put in this public repository.

On a critical new change, the Lead records affected task IDs here as `ON_HOLD`, increments the epoch and links the decision. This stops work only when an active agent next checks; it is not a remote kill switch.

## Work registry

| Task | State | Owner role | Scope / gate |
| --- | --- | --- | --- |
| RL-OPS-001 | DOCUMENTATION_BASELINE | Lead/Architect | This coordination package. Verify committed files against the setup request; no app tests claimed. |
| RL-MVP-PLAN-001 | PLAN_APPROVED | Lead/Architect | [Oct 12 design (legacy filename)](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md) and [weekly roadmap](plans/2026-10-07-weekly-implementation-roadmap.md); [detailed plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) owner approved 2026-10-07; RL-MVP-001 merged; Tasks 1–3 merged; Task 4 not approved. |
| RL-MVP-001 | MERGED | Backend | [Contracts and synthetic fixtures](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md); corrected implementation `a1d8311`, branch head `c698cd4`; QA and Research both PASS for Task 1; owner-approved merge complete. |
| RL-MVP-002 | MERGED | Backend/Codex + Lead integration | Reviewed implementation `736fa18`, owner-approved PR #2 merged as `35281fb9`; QA PASS and Research Task-2 semantics PASS. |
| RL-MVP-003 | MERGED | Backend/Codex + Lead integration | Exact candidate `97db3615`, published branch head `139921de`, owner-authorized [PR #3](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/3) merged as `733ae024`. QA PASS; Research Task-3 semantics PASS. Synthetic-only pairing, no D03 approval. |
| RL-MVP-004 | MERGED; REAL_MODEL_BLOCKED | Backend/Codex + Lead integration | Correction 01 exact implementation `b9ce818`, Backend head `fb4c1f0`; independent QA and Research PASS for scoped infrastructure/protocol, owner-authorized PR #4 merged `8f4d2f18`. Real inference/D03/D05 not validated; Task 5 unapproved. |
| RL-S1-001 | PROPOSED | Lead + Backend | Define document/target/reference records and initial input limits; D01/D02/D03 and component plan required. |
| RL-MVP-005 | APPROVED_RESEARCH_PROPOSAL; NOT IMPLEMENTED | Research/Evaluation | [Research-only Task 5 packet](task_packets/RL-MVP-005-RESEARCH-PROPOSAL.md) explicitly approved by owner; two synthetic proposal artifacts and one unique Research handoff on an isolated branch. No evaluator, merge, scientific-method approval or Task 6. |
| RL-MVP-006 | MERGED; SCIENTIFIC_VALIDATION_PENDING | Backend/Codex + Lead integration | Final exact reviewed implementation `0a0ce9e`, published Backend head `fa2669c2`; independent QA PASS `effcc020` and Research scoped PASS `02c34c7`; owner-authorized [PR #5](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/5) merged at `2d825ee`. Synthetic/mock qualitative evidence and target/document/model summaries only, numeric scores null; no inference/Task 7/D03-D06 approval. |
| RL-S2-001 | PROPOSED | Research | Propose rubric, human benchmark and release criteria; D03/D04/D05; no invented thresholds. |
| RL-UX-001 | PROPOSED | Frontend | Synthetic-data workflow proposal only; D09 and scoped approval before implementation. |

These proposed items are not claimed, running or approved to execute. The Lead allocates the next task packet; specialists must not race to claim a shared task by editing this table.

## Remaining gates and next action

**October 12 MVP remains AT RISK.** Tasks 1–4 merged. Task-4 Correction 01 on exact implementation `b9ce8182751f26109fbd857bcb8d909720bafd13` was independently reviewed: QA PASS with 102 focused/255 full pytest, 27 selected cases and 15 custom probes; Research PASS for scoped prediction-protocol semantics (isolated probes, full pytest not independently run by Research). PR #4 merged at `8f4d2f18aa2c565e3228d4f3568a2bd8c1714b0f`. See owner-approved [Correction 01 packet](task_packets/RL-MVP-004-CORRECTION-01.md) and QA/Research published branch handoffs. Local model/runtime/license absent; real inference BLOCKED. D03/D05 scientific approvals and lab data/vendor authorization NOT OBTAINED. No inference, downloads, paid calls, Task 5 evaluator implementation, Task 6 or deployment authorized. Task 5 research-only proposal is approved.

## What is present / absent

Present: source-aligned product digest, decision register, proposed architectural and record boundaries, research guardrails, operating guide, role prompts, handoff and PR templates.
Present on main: Tasks 1–4 contracts, synthetic fixtures, PDF detector, canonicalizer, synthetic-only reference aligner/registry, trusted internal prediction-source ingestion, local-only adapter, SQLite one-shot worker and tests. Absent: authenticated API, evaluation/scoring engine, UI, deployment, licensed local runtime/model. No CI or cron established.

## Latest important change

E0042: Task 6 merged via owner-approved PR #5 after independent QA/Research scoped PASS. No scientific approval or Task 7. Prior E0041: Task 6 Correction 03 approved; no implementation/merge. Prior E0040: Task 6 Correction 02 approved after QA findings; Research scoped PASS on Correction 01. No implementation/merge. Prior E0039: Task 6 Correction 01 scope owner-approved and packet published; original candidate remains unmerged. Task 4 remains merged; Task 5 proposal still unvalidated; real inference blocked.

## Maintenance rule

Keep this page small (target: roughly 600 words). It is a derived snapshot, not the only evidence. Link task records/commits instead of pasting transcripts. The Lead updates it alongside accepted decisions and handoff index changes. If it conflicts with merged code or approved decisions, flag the discrepancy and reconcile; never hide it.

E0043: Owner selects local, portable, recipient-self-hosted Task 7 delivery: another researcher must independently install and launch the complete application on a compatible computer without access to the owner's MacBook. Required cross-device installation/startup, pinned deps, local persistence and model availability/hardware disclosures; no implementation or deployment authorized.
