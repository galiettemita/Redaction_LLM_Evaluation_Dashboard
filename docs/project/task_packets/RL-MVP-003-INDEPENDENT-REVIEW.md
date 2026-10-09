# RL-MVP-003 — Independent QA and Research review

**State:** REVIEW REQUESTED; no independent verdict or receiver ACK presumed.
**Task:** RL-MVP-003. **Owner:** Backend/Codex. **Reviewers:** QA and Research, separately on approved review branches. **Next receiver:** Lead/Architect.
**Integration baseline:** main `4e08b7f1579523dbd44294f02c0ff18d51a754a4`, epoch E0024. Routing epoch E0025.
**Exact implementation candidate:** `931fb1c0012d3b530b837f204d922f0aaa95a602`. **Published Backend branch head:** `2d79ee6a7d5ba2a06148ff257529faa50dfa06e1` (`codex/rl-mvp-003-text-first-reference-alignment`).
**Backend handoff:** `docs/project/handoffs/RL-MVP-003-backend-20261008T201401Z-931fb1c.md` at the published branch head.
**Authority:** AGENTS.md, DEC-001/004/007/008/010/011/015/020, approved Task-3 packet, Task-3 plan, current contracts/canonicalizer/detector. **Deadline:** October 12, 2026. No waiver of scientific or software review gates.

## Shared checks

Refresh main and read AGENTS.md, CURRENT_STATE, DECISIONS and this packet; inspect exact implementation and Backend handoff. Confirm branch delta is **only** `src/redaction_lab/reference.py`, `tests/test_reference.py` and one unique Backend handoff. Review the exact `931fb1c0012d3b530b837f204d922f0aaa95a602`, not Codex's internal review. Codex reports 25 focused and 145 full tests passed, compileall and dependency checks; independently run matching checkout tests if possible, otherwise mark NOT RUN and supply reproducible isolated probes.

This task must never confirm reference truth unless complete, readable, uniquely and reliably aligned to the exact target. Unknown, absent, partially revealed, still hidden, malformed, repeated, reordered, conflicting or untrustworthy truth must remain NOT_SCOREABLE with `exact_revealed_text=None`. A reference must never enter prediction inputs. Do not claim scientific D03 approval from passing software tests.

## QA-specific independent probes

1. **False CONFIRMED:** repeated anchor sequences with one plausible global match, duplicated target passage, a swapped/reordered paragraph, wrong reference release with identical local neighbors, inserted/deleted visible context, punctuation-only reveal and changed whitespace. Test both anchors when present, including a scenario where only one side matches the global monotonic alignment (inspect `_globally_supported` behavior); a single matching side must not silently legitimize conflicting opposite-side evidence.
2. **Boundary and adjacency:** target at document start/end, one-sided anchor, adjacent boxes, same-line duplicate visible words, cross-page flow, reflowed punctuation, and repeated exact text. Geometry must not become a substitute for unique textual evidence. Verify token-to-character locators bind the actual occurrence and quote the exact readable reference span.
3. **Hidden selectable text:** partially covered reference PDF, displaced black box, overlay on punctuation/whitespace, parser unsupported graphics, and malformed/encrypted PDF. Never expose covered reference content via exact text, error messages, debug output, public handoff, or prediction serialization.
4. **Integrity and reproducibility:** tampered canonical hash/marker, duplicate/missing/extra target, cross-project or version mismatch, reference PDF identity not cryptographically tied to supplied document-version ID, deterministic IDs/hashes, parser failure states, no private data, no paid calls.
5. **Regression:** verify 120 prior Task-1/2 tests plus 25 new tests when executable checkout is available. Document environment and test limitations. Report PASS / CHANGES_REQUESTED / BLOCKED on exact SHA; do not edit implementation.

## Research-specific independent probes

1. Determine whether global monotonic alignment plus local unique anchors actually establishes *full-target* truth in repeated, reordered, wrong-release, partial and one-sided cases; specifically test whether `_globally_supported`'s left-or-right support and the geometry candidate fallback can produce false confirmations.
2. Verify complete revelation versus partially hidden reference: no hidden selectable characters or partial candidate text may appear in `exact_revealed_text` for unconfirmed mappings. Examine exact whitespace/punctuation preservation and offset provenance.
3. Verify per-target uniqueness and independence, including adjacent boxes, document boundaries, text reflow, stable version hashes, and unknown/null scoreability. Distinguish a schema's SCOREABLE value from a scientifically verified score.
4. Report unsupported PDF subset, limitations of synthetic evidence and what D03 human calibration still requires. Do not invent approval thresholds or change the scoring method.

## Publication

Each reviewer publishes one unique task-scoped handoff on their own approved branch, including exact reviewed SHA, verdict, tests run/not run, severity/reproduction, known risks and next receiver Lead. If GitHub write access is unavailable, say NOT PUBLISHED. No implementation code edits, main merge, Task 4, provider/model calls, extra spending, private data or deployment. Lead reconciles both handoffs before seeking owner merge authorization.
