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

## Entry format

Date / epoch / task or decision ID; approved change vs proposal; affected files/contracts; source/approval evidence; test/benchmark impact; migration/rollback; required receivers; unresolved issues. Never backfill a success claim without evidence.
