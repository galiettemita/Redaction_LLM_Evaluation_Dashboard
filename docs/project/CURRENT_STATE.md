# Current state

Updated: 2026-10-11 (America/New_York). Coordination epoch: **E0056**.
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

E0044: Owner approved RL-MVP-007A planning defaults and publication of [the scoped 007A packet](task_packets/RL-MVP-007A-PORTABLE-FOUNDATION.md): macOS arm64 first, loopback-only, 25 MiB/file, 100 pages, one document job, 60s parse budget, five-table schema direction, retained documents/evidence until authorized deletion, 24h temporary cleanup, 7d content-free logs, pre-migration backups. Packet published ONLY: no implementation, dependency install, inference, spending or deployment authorized.

E0045: Owner-approved, publication-only [007A PDF isolation amendment](task_packets/RL-MVP-007A-PDF-ISOLATION-AMENDMENT.md) published. No Task 7A implementation, installs, downloads, VM, sensitive data, inference, spend or deployment authorized.

E0046: Owner approved Task 7A code-only implementation. [Consolidated authorization packet](task_packets/RL-MVP-007A-IMPLEMENTATION.md) published; mock/synthetic work only, no runtime operations, private data, inference, deployment, spending or merge. Independent QA/security and Research reviews required.

E0047: Owner authorized [RL-MVP-007A Correction 01](task_packets/RL-MVP-007A-CORRECTION-01.md) within twelve scoped files and unique Backend handoff: directory-FD full-lifecycle confinement and application-owned verified-worker authority. No merge, Podman/VM/image operations, private data, inference, spending or deployment. Fresh QA/security and Research reviews required.

E0048: Owner approved [Correction 01 two-file amendment](task_packets/RL-MVP-007A-CORRECTION-01.md), adding application/migration.py and tests/application/test_migrations.py for symlink/race-safe backups and SQLite access. Now 14 authorized implementation paths plus one handoff; all runtime, merge, data, model, spending and deployment prohibitions remain.

E0049: Owner approved [RL-MVP-007A Correction 02](task_packets/RL-MVP-007A-CORRECTION-02.md): two-file subprocess SQLite migration helper, no parent cwd mutation, crash-safe WAL/rollback and verified backups, concurrent-thread TDD. No merge, runtime/model/data operations or Task 7B/C/P/D.

E0050: Owner approved [RL-MVP-007A Correction 03](task_packets/RL-MVP-007A-CORRECTION-03.md) for two-file interprocess flock migration/backup coordination plus unique Backend handoff; independent review required. No merge or runtime, data, model, spending, deployment, Task 7B/C/P/D.

E0051: Owner-authorized RL-MVP-007A portable foundation integrated from Backend published HEAD `64784f752b7a4107e927b07cd8d31453e5e8e2e6` after Correction 03 QA PASS at `0e8ace7b2750c558ac5adca44461780fc8c06021` and Research scoped PASS at `196a545484ce11223567aea9a2ee9df5a80f4a64` on exact implementation `03d95ec8e6f280693550563f08ebaa65e844afb3`. This is code-only foundation; runtime lock remains unverified and operational PDF processing fails closed. No runtime install/qualification, real inference, deployment, private data, cost or Task 7B/C/P/D authorization.

E0052: Owner authorized fast-lane parallel code implementation of [7B API](task_packets/RL-MVP-007B-API.md), [7C frontend](task_packets/RL-MVP-007C-FRONTEND.md), [7P packaging](task_packets/RL-MVP-007P-PACKAGING.md) and [7D synthetic preparation](task_packets/RL-MVP-007D-PREP.md), under frozen [API contract v0.1](API_CONTRACT_V0_1.md). Separate branches/reviews/merge approvals mandatory. No new dependencies or installs, runtime/VM, inference, private data, spend, deployment or final recipient acceptance.

E0053: Owner-authorized guarded integration of RL-MVP-007B API Backend published HEAD `481211796cb499d76bd788d5efe4c1854e867526`, exact implementation `b2a5a16bf16a8f339d9d70b6d2a44471578fa63d`, after independent QA/security PASS at `325a4fee4e7e132e3b449f64796e23cd4444ad38` and Research scoped PASS at `4d04629115226dedec45df6e9b90dd64a104f26f`. Code-only WSGI API is merged, not an independently launched HTTP service or qualified PDF runtime. Task 7C/7P/7D scope unchanged; no dependencies, deployment, Podman/VM, private data, inference or spending approved.

E0054: Owner authorized guarded integration of reviewed RL-MVP-007C frontend source and RL-MVP-007P API-only local launcher. Both exact candidate QA/security and Research reviews PASS within code/provenance scope; runnable website, browser accessibility, clean-recipient acceptance and qualified worker remain NOT ESTABLISHED. [Website build/static-host proposal](task_packets/RL-MVP-007CP-WEBSITE-BUILD-PROPOSAL.md) PUBLISHED FOR OWNER REVIEW ONLY. No implementation, dependency install/download, build, extra merge, deployment, real data or inference authorized by that proposal.

E0055: Owner approved scoped [RL-MVP-007CP website build/static-host packet](task_packets/RL-MVP-007CP-WEBSITE-BUILD.md) with isolated zero-cost pinned frontend dependency build and independent same-origin Packaging branch, synthetic tests and fresh scoped QA/Research; separate merge approvals required. No Podman/VM, private data, real PDF/inference, paid calls, deployment or final 7D acceptance.

E0056: Owner approved exact Vite pin substitution `7.1.12` -> `7.3.5` only within [7CP approved packet](task_packets/RL-MVP-007CP-WEBSITE-BUILD.md). All other pins, file scopes and zero-cost isolated install gates unchanged; repeat full transitive preflight. Static-host branch unmerged, formal reviews still required. No merge, deployment, private data, Podman/VM, inference or final 7D acceptance.
