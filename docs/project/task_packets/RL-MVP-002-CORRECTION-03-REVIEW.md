# RL-MVP-002 Correction 03 — fresh independent review

**Status:** REVIEW REQUESTED; no reviewer acknowledgment or PASS presumed.
**Owner:** Lead/Architect routing. **Reviewers:** QA / Independent Reviewer and Research / Evaluation, each on their own approved review branch.
**Integration baseline:** main `51c50b69b13629a7f9fd4712adec97b27218c5c7`, epoch E0017; routing epoch E0018.
**Exact implementation SHA:** `dbae9f79d1d4dcee1aba09978713e27d6939f77e`. **Published Backend branch head:** `821f57348c49845e4d922122cb575e569f22d82c` on `codex/rl-mvp-002-detection-canonicalization`.
**Backend handoff:** `docs/project/handoffs/RL-MVP-002-backend-20261008T153344Z-dbae9f7.md` at branch head.
**Source:** DEC-007/008/015/017/020, approved Task 2 packet and Correction 03 packet, prior independent QA and Research handoffs on `ea930ab`.
**Deadline:** October 12, 2026; quality and research gates unchanged.

## Common review instructions

Read AGENTS.md and the current HEAD/epoch, Correction 03 packet, Backend handoff and exact candidate source. Review only the new exact implementation, not a prior verdict. Confirm that the delta from `e5333602` contains only `src/redaction_lab/pdf_detector.py`, `tests/test_pdf_detector.py` and the new Backend handoff.

Probe staggered two one-line columns on different baselines and distinct x-regions (including varying separation), while checking ordinary single-column paragraphs, headings, modest indents and widely separated unrelated text. A case without provable reading order must be UNSUPPORTED, never silently canonicalized.

Probe no-glyph black boxes at document/section starts and ends with only one-sided visible text: x-aligned, just outside text character bbox, indented, moderately offset, and clearly remote decorative artwork. A plausible text-region redaction must not silently become NO_REDACTIONS; remote art must not be mistaken for a confirmed target. Preserve strict redacted-only input isolation, hidden selectable-text suppression, marker uniqueness, deterministic project-scoped IDs, overlap/duplicate rejection and explicit unsupported statuses. Check v4 provenance and absence of regression in earlier fixes.

## QA-specific deliverable

Run the exact repository focused/full suite if an authorized matching checkout exists; otherwise mark NOT RUN and document reproducible independent probes. Confirm RED/GREEN regression coverage, malformed PDF behavior, failure states, security boundaries and dependency/test evidence. Publish unique QA handoff with reviewed SHA, commands, results, PASS / CHANGES_REQUESTED / BLOCKED and next receiver Lead. Do not patch code.

## Research-specific deliverable

Independently review target identity, redacted-only context, fail-closed ambiguous reading order, plausible boundary boxes versus remote art, and downstream consequences for text-first reference alignment. Report actual tests or source checks and PASS / CHANGES_REQUESTED / BLOCKED for Task-2 semantics only. This does NOT constitute research-human approval of D03-D06 or scoring accuracy.

## Restrictions

No code edits, merge, Task 3, model/provider calls, extra spending, restricted data, cloud or deployment. Each reviewer publishes a new role-specific handoff on their own review branch; if write access is missing, state NOT PUBLISHED. Lead reconciles both fresh verdicts before seeking merge authorization.
