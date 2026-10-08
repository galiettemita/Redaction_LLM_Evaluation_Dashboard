# Coordinated change log

This is a concise index, not a transcript. The containing Git commit identifies each exact revision; no self-referential commit SHA is embedded. Lead maintains this with CURRENT_STATE and DECISIONS.

## 2026-10-06 | E0001 | RL-OPS-001

Documentation-only coordination bootstrap, requested by the owner for this repository.

- Added the eight shared project files, root AGENTS.md, operating/role guide, one-time ChatGPT Project instructions and a PR template.
- Imported a source-aligned working digest of the owner-supplied master PDF; retained the PDF's document date and distinction between Confirmed, Proposed and Open.
- Recorded confirmed DEC-001 through DEC-006 and kept D01-D10 unresolved as appropriate.
- Established snapshot reads, checkpoint refresh, single-writer canonical integration, isolated specialist work, unique handoffs, explicit acknowledgments and evidence-based status transitions.
- Source PDFs, private messages, embedded research HTML and raw inputs were not copied into the repository. The repository's public visibility was not changed.
- No application, test suite, provider trial, numeric scoring validation, deployment, scheduler or running agent team is created by this documentation package.

**Affected roles:** all five. **Next acknowledgment:** each role reads AGENTS and current state on its first active task. No acknowledgment is presumed.
**Verification boundary:** validate documentation content, links and actual committed tree; application tests are not applicable. The delivering session reports its observed commit and verification evidence separately.

## 2026-10-06 | E0002 | system-design approvals

Owner-approved design direction; documentation only, no implementation or empirical validation.

- DEC-007: automatic hybrid detection of visually contiguous black text-redaction boxes; no routine user marking/confirmation; fail unsupported/ambiguous processing rather than ask the user to define targets.
- DEC-008: one target per model request, same frozen canonical redacted document/context across participating models, other redactions remain hidden, no answer insertion between targets, and no reference/evaluator/web/retrieval access in the baseline condition.
- DEC-009: model pretraining/parametric knowledge is allowed; claims are reconstruction-under-protocol, not document-only logical derivability.
- Updated architecture and interface contracts accordingly. D05 still requires research-human sign-off before comparative scientific claims; no exact provider roster, score formula, thresholds or code were approved.

**Affected roles:** Research, Backend, Frontend, QA. **Required next action:** read E0002 at next task checkpoint and incorporate these constraints into proposals/reviews.

## 2026-10-06 | E0003 | reference-alignment design approval

Owner-approved design direction; documentation only.

- DEC-010: text-first reference alignment using canonical token streams, global monotonic alignment, then local left/right anchor alignment to isolate the exact newly revealed span.
- Page number and geometry are secondary evidence rather than primary alignment authority.
- Ambiguous, incomplete, unreadable, partly hidden or conflicting mappings remain unknown and score null; no LLM may invent ground truth.
- D03 still requires research approval of the exact automatic-confirmation criteria and validation evidence before trusted scoring.
- Coordination preference updated: ask the owner only urgent/necessary design questions that materially affect correctness, research validity, security/data policy, contracts, authority or sequencing.

**Affected roles:** Research, Backend, Frontend, QA. **Next action:** consume E0003 at the next active task checkpoint.

## 2026-10-07 | E0004 | owner-approved design directions

DEC-011..017 record owner approval of conservative truth acceptance, fact-level evaluator direction, one-shot trial protocol, transparent aggregation, local/synthetic data boundary, pragmatic modular MVP and seven-day zero-additional-spend constraint. Research calibration, institutional data authorization, final stack, paid calls and code task authorization are **not** granted. D01 and D03-D07 still have gates; D09/D10 are deferred.

Receivers: Research, Backend, Frontend, QA on next active check. Documentation-only change; no application/benchmark tests.

## 2026-10-07 | E0005 | RL-MVP-PLAN-001

Recorded DEC-018 owner-defined October 14 MVP milestone. Published proposed [MVP design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md), [weekly delivery roadmap](plans/2026-10-07-weekly-implementation-roadmap.md), and [RL-MVP-001 proposed packet](task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md). These are planning documents awaiting written design review and detailed Codex plan approval, not evidence of implementation. No paid calls, live models, production data or deployments authorized. No application tests run (documentation only).

Affected roles: Research, Backend, Frontend, QA. Receivers read at next active checkpoint; no automatic cross-chat messages or acknowledgments.

## 2026-10-07 | E0006 | Oct 14 design approved, plan and role kickoffs prepared

DEC-019 records the owner's approval of the written MVP design. Published the detailed [implementation plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md), four role kickoffs under kickoffs/, and CODEX_START_HERE.md. RL-MVP-001 packet remains proposed pending plan review and task approval. This is documentation only; no app code, model calls, new resources, benchmark tests or deployment. Research, institutional data and engineering gates remain outstanding.

Receivers: Backend, Research, Frontend and QA at next active checkpoint; no ACK presumed.

## 2026-10-07 | E0007 | detailed plan and first coding task authorized

The owner approved the detailed Oct 14 implementation plan and asked whether to proceed with the precise RL-MVP-001 Codex implementation prompt. This records bounded authorization for RL-MVP-001 only: typed contracts, synthetic PDF fixtures, local TDD tests, task branch/worktree and task-scoped handoff. No other implementation task, paid API, external data transfer, main merge or deployment is approved. Codex startup/preflight results are not yet available to this Lead chat. No code/tests were run by the Lead in this documentation update.

Receivers: Backend (Codex), Research for semantic contract review, QA for independent candidate review. No ACK presumed.

## 2026-10-08 | E0008 | RL-MVP-001 candidate ready for independent review

Verified on GitHub: `main` at `5743b7a8ff6cc32c3e2a582392030d79047455e8`; branch `codex/rl-mvp-001-contracts-fixtures` at `b0282281e72f37c1cd1f7899d09691024991d150`, including implementation `8fff5f11cd9ce0c1e2ca7943aab7d02f629eff58` and published Backend handoff. Compared candidate to approved baseline: only five scoped implementation files plus one handoff. Codex reports 19 tests passed, but Lead did not independently run tests.

Prepared exact-candidate read-only QA and Research review packets. Preliminary static contract questions include nested mutability, free-form settings/reference isolation, and scoreability invariants. No code changes, scientific approval, independent review, merge, or next-task authorization.

**Receivers:** QA and Research at their next active task checkpoint; no automatic notification/ACK claimed.

## 2026-10-08 | E0009 | RL-MVP-001 corrected reviews reconciled

Independent QA handoff on `qa/rl-mvp-001-corrected-a1d8311` at `046c8b3ada5d9a40aded9d2beb15c91d50007221` reports PASS on exact implementation `a1d831153c726db38fc0c403c4d6d80893f657a5`: 43 repository tests and 11 adversarial tests passed, 1 deselected. Research handoff on `review/rl-mvp-001-research-corrected-e0008` at `a597ee23d397e7d8be3c31cd55b1e06c34f9eac0` reports contract-semantics PASS and 13 independent checks.

No scientific scoring approval. Remaining transactional checks are deferred to authorized downstream work. Integration and Task 2 remain unauthorized pending owner approval. Lead did not run application tests.

## 2026-10-08 | E0010 | RL-MVP-001 merged

Owner authorized and GitHub merged PR #1 at `ba60aaa811fad1ec7d2ad79ab2f4aebfa021b067`. Exact reviewed implementation `a1d8311` is included with its two Backend handoffs. QA PASS (43 repository tests, 11 adversarial passes, 1 deselected); Research contract-semantics PASS (13 independent checks). Lead verified the merge and blob hashes, not runtime tests. No Task 2, deployment or research-scoring authorization. Transactional integrity and summary provenance remain downstream requirements.

## 2026-10-07 | E0011 | RL-MVP-002 authorized for Codex

Following the reviewed RL-MVP-001 merge, the owner directed continued Codex implementation. Published [RL-MVP-002](task_packets/RL-MVP-002-detection-canonicalization.md) as a bounded Backend task: automatic vector black-text-box detection, fail-closed removal of hidden selectable PDF text, deterministic canonical text and synthetic TDD tests. No merge, Task 3, paid calls, restricted data or deployment. No code/test execution claimed.

Affected roles: Backend/Codex (implement), QA and Research (review exact candidate). No ACK presumed.

## 2026-10-08 | E0012 | RL-MVP-002 candidate intake and review routing

Verified Codex branch `codex/rl-mvp-002-detection-canonicalization` at `a6a603f6b11472df5cf36d2acd9eeec215fe81af`, implementation `430467314ca992f36cf3eaab9d49cde45a9805ac`, with five approved source/test/dependency files and one Backend handoff. Codex reports 35 focused and 78 full tests passed, compileall and diff check; Lead inspected code and did not rerun tests.

Published exact-candidate QA and Research review packets. Key review focus: hidden PDF-layer text leakage, unsupported graphics/paint operations, redacted-only canonical context, deterministic target identity and failure reporting. No independent verdict, merge, Task 3, provider call, scientific approval or deployment.

## Entry format

Date / epoch / task or decision ID; approved change vs proposal; affected files/contracts; source/approval evidence; test/benchmark impact; migration/rollback; required receivers; unresolved issues. Never backfill a success claim without evidence.
