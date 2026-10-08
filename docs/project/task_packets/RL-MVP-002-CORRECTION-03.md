# RL-MVP-002 — Correction 03: remaining fail-closed ambiguity

**State:** CHANGES_REQUESTED; bounded correction within existing RL-MVP-002 approval. **Owner:** Backend/Codex. **Reviewers:** QA and Research independently. **Receiver:** Lead.
**Integration baseline:** main `72a390c9a2b67b52797c711561789f0eaa105e90`, E0016; coordination epoch E0017.
**Reviewed implementation:** `ea930abef319832cf494df5851be1b19d3e2cf1c` on `codex/rl-mvp-002-detection-canonicalization`, published Backend head `e5333602c43d304a21980fc96103d19599e2dd27`.
**Evidence:** [QA FAIL](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/941a9b9b2ff4f1b39aa105122670aad42ad07ef2/docs/project/handoffs/RL-MVP-002-qa-20261008T150000Z-ea930ab.md) and [Research CHANGES_REQUESTED](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/e1ea57d2cbbedd603637ac79dfffbeda48fe0c5c/docs/project/handoffs/RL-MVP-002-research-20261008T152306Z-correction02.md) on this exact SHA.
**Deadline:** October 12, 2026 (DEC-020). No waiver of quality, research, security or no-spend rules.

## Remaining blockers

1. **Staggered two one-line columns:** QA independently demonstrated that two separated one-line text blocks on different baselines, with neither column start repeated, escape the layout-ambiguity helper. Example one block around x=72/y=720 and another around x=330/y=680, with a supported black overlay. Fail closed as UNSUPPORTED when a reliable single reading order cannot be established. Preserve ordinary single-column paragraphs, modest indents, headings and other legitimate negative controls. Research's PASS for its narrower sparse-column probes does not override QA's separately reproduced staggered variant.

2. **Near/indented no-glyph boundary redaction:** A plausible black text-sized rectangle near a short visible line, but without literal horizontal character-bbox overlap, may be ignored as artwork and return NO_REDACTIONS. Example visible line at x=72..105 and black rectangle starting around x=105 or x=260, positioned above/below in the same general text region. Require affirmative evidence before dismissing plausible one-sided text-region rectangles as artwork. Otherwise mark UNSUPPORTED/ambiguous. Preserve clearly remote decorative-artwork negatives. Do not invent the hidden text or use reference input.

## TDD acceptance

- Add failing regression tests for both variants, including different-baseline sparse columns, one-sided no-glyph near/indented black boxes and remote-artwork/single-column negative controls.
- Demonstrate RED on the current candidate; make minimal detector changes, then GREEN. Run the full suite, compileall, git diff --check and dependency check; record exact commands, counts and NOT RUN.
- Preserve project-scoped IDs, overlapping/duplicate-box rejection, one physical region per target, hidden selectable-text suppression, stable markers, and redacted-only prediction context.
- If a deterministic distinction between valid single-column text and ambiguous sparse columns is not supportable with current evidence, return explicit UNSUPPORTED rather than guessing reading order. Document the limited accepted PDF class; no unsupported silent success.

**Allowed files:** `src/redaction_lab/pdf_detector.py`, `tests/test_pdf_detector.py`; `src/redaction_lab/canonical.py` and `tests/test_canonical.py` only if a proven Task-2 defect requires them; one unique Backend handoff. No contracts, fixtures, other tasks, scoring, model calls, UI, main edits or shared docs. Stop and request Lead approval if scope expands.

Publish additive implementation commit and handoff on the existing task branch, no force push. QA and Research must independently review the NEW exact SHA. No merge, Task 3, paid services, private data, cloud or deployment. Real-world detector recall and hostile-PDF hardening remain unvalidated.
