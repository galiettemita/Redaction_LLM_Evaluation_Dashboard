# RL-MVP-003 DEC-022 — fresh independent QA and Research review

**Status:** READY_FOR_REVIEW; independent verdicts NOT YET RECORDED.
**Task:** RL-MVP-003. **Reviewers:** QA and Research, separately on their approved review branches. **Next receiver:** Lead.
**Main baseline:** `ed91947f9f5aff5bba36330df4fc6cc52e295d89`, E0028. **Exact implementation SHA:** `8a751d4af27c8daada1071ec6c9c4fce45581d61`.
**Backend published head:** `cd4cbfafbfe0152adc8c8e68a6cf337f20348814` on `codex/rl-mvp-003-text-first-reference-alignment`.
**Backend handoff:** `docs/project/handoffs/RL-MVP-003-backend-20261009T010827Z-8a751d4.md` at the published head.
**Authority:** DEC-001,004,010,011,020,021,022 and `docs/project/task_packets/RL-MVP-003-TRUSTED-SYNTHETIC-CORRECTION.md`. October 12 deadline; no quality waiver.

## Common review requirements

Refresh live main HEAD, AGENTS.md, CURRENT_STATE, DECISIONS, handoff index, approved packet, exact candidate and Backend handoff. Verify that implementation commit `8a751d4` changes only `src/redaction_lab/reference.py`, new `reference_registry.py`, `tests/test_reference.py` and new `test_reference_registry.py`; the following handoff commit adds only the unique Backend handoff. The cumulative branch contains prior Task-3 history and main coordination commits; do not confuse that with the correction's actual file scope.

Codex reports 56 focused and 176 full tests passed, compileall, dependency check and diff check. Independently rerun focused/full suite if an executable exact-SHA checkout is available; otherwise report NOT RUN and independent reproducible probes. Do not inherit old QA/Research verdicts or count Backend self-review as independent.

## QA checks

1. Independently generate the deterministic `two_boxes` redacted/reference PDFs, verify BOTH literal SHA-256 pins and correct project, version and pair IDs. Check behavior with differing ReportLab versions or generator drift: fail closed, never auto-enroll or silently repin.
2. Probe forged `DocumentVersion` or caller trust object, monkeypatched registry/case input, mismatched project/version, wrong redacted PDF with correct reference, swapped releases, altered bytes, and unregistered user PDFs. None may become CONFIRMED or expose candidate truth. Note explicitly that trusted runtime-code modification is out of scope.
3. Probe forged `CanonicalRedactedDocument`/targets, duplicate/changed IDs, marker integrity, hidden selectable text, partial reference, repeated/adjacent boxes, ambiguous/reordered/wrong-release context, left-only/right-only global support, interior geometry fallback and true document boundaries.
4. Probe exact punctuation and whitespace: a partly hidden edge punctuation character or space must never be silently omitted with CONFIRMED. Verify no reference truth/hints leak into prediction manifests, errors or logs.
5. Check stable IDs/hashes, unsupported/malformed inputs, dependency/test evidence, and all prior Task-1/2 regressions. Publish PASS / CHANGES_REQUESTED / BLOCKED with actual commands, counts, limitations and new exact-SHA handoff. Do not modify implementation.

## Research checks

Independently evaluate the **necessary versus sufficient** distinction: pinned fixture provenance only establishes a known synthetic pair, not full-target truth, archival authenticity or scientific accuracy. Challenge false-CONFIRMED from one-sided alignment, conflicting global context, wrong release, repeated anchors, incomplete/hidden target-edge punctuation, and missing reliable source boundaries. Confirm every unknown mapping is NOT_SCOREABLE with null exact_revealed_text and that arbitrary uploaded references cannot yield verified truth. Verify reference/prediction isolation and target-level exact quotation/locator evidence. Report D03 scientific validation as NOT APPROVED; synthetic test passes cannot validate real-document performance. Publish unique Research handoff with reviewed SHA, actual tests/not-run and PASS / CHANGES_REQUESTED / BLOCKED.

## Publication/stop

Reviewers publish unique role-specific handoffs on their own scoped branches; no main edits or code patches. Lead reconciles both verdicts before requesting separate owner merge authorization. No Task 4, paid calls, private data, deployment or scientifically verified scoring. Any false-CONFIRMED or reference leak is blocking.
