# RL-MVP-002 — Correction 01 after independent QA and Research review

**Status:** CHANGES_REQUESTED. **Task:** RL-MVP-002. **Owner:** Backend/Codex. **Reviewers:** QA and Research. **Receiver:** Lead.
**Main baseline:** `ad7b02f57d1d392696974d1678e604431cf7f2ca` / E0012; routing epoch E0013. **Reviewed implementation:** `430467314ca992f36cf3eaab9d49cde45a9805ac` on `codex/rl-mvp-002-detection-canonicalization`; Backend handoff branch head `a6a603f6b11472df5cf36d2acd9eeec215fe81af`.
**Independent evidence:** [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/48adf452178e1e7c38896b088f2e7481846bf275/docs/project/handoffs/RL-MVP-002-qa-20261008T123940Z-4304673.md) (FAIL, 3 blocking findings; independently executed focused probes, not full candidate pytest); [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/a0d56b599a5ba284ef036b813fa8167164189847/docs/project/handoffs/RL-MVP-002-research-20261008T121239Z-rsem02.md) (CHANGES_REQUESTED, 2 blocking findings; focused probes, not full candidate pytest).
**Authority:** Additive correction of defects within already approved RL-MVP-002 implementation scope. No change to product design, scientific score rules, or authorization for Task 3.

## Four blocking corrections

1. **Project-scoped target identity.** `_target_for_rectangle` omits `project_id` from the deterministic target ID material. Ensure two projects with the same local document version/page/bbox cannot produce indistinguishable standalone target IDs (or explicitly enforce a composite identity, but prefer project-scoped deterministic IDs here). Test same PDF/geometry/document-version label across two projects; stable IDs within one project remain stable.

2. **Ambiguous multi-column reading order.** A two-column PDF with one overlay can pass detection, while `_page_text` interleaves columns row-by-row. For this week-one narrow subset, conservatively reject multi-column/ambiguous positioned-text layouts as UNSUPPORTED before canonical text is emitted; do not silently reorder context. Add a realistic two-column PDF regression and ensure ordinary single-column multi-line/adjacent-box fixtures still pass. Do not claim arbitrary multi-column support.

3. **Overlapping/duplicate rectangles.** Two filled black rectangles can overlap the same text, or be duplicates, yielding multiple targets/duplicate IDs for one visually contiguous region. Before declaring SUPPORTED, detect overlapping or duplicate near-black text-redaction rectangles and fail closed as UNSUPPORTED with a stable non-sensitive reason. Do not merge heuristically in Task 2. Adjacent non-overlapping physical boxes must remain distinct. Add both overlapping and exact-duplicate regression tests.

4. **Standalone ambiguous black rectangle.** A redaction-shaped black box on its own line may cover text not present in the extractable PDF layer. Without same-line visible neighbors or intersecting characters, the detector can silently count it as artwork and return NO_REDACTIONS. For plausible text-flow redaction geometry with insufficient evidence, return UNSUPPORTED/ambiguous instead of NO_REDACTIONS. Distinguish this from true remote artwork using conservative layout evidence; if classification cannot be made reliably, reject. Add synthetic standalone redaction and remote-artwork regressions.

## Required test/quality evidence

- TDD: write regression tests first, demonstrate RED against `430467314ca992f36cf3eaab9d49cde45a9805ac`, implement minimal fixes, demonstrate GREEN, then run the full Task 1+2 test suite, `compileall`, and `git diff --check`. Report exact commands/results; no fabricated passes.
- Verify no hidden selectable text enters canonical text or logs, no reference data enters detection, no marker collisions, and no false NO_REDACTIONS from ambiguous black regions.
- Do not change `contracts.py` or `fixtures.py` without stopping for Lead scope review. Keep corrections within `src/redaction_lab/pdf_detector.py`, `src/redaction_lab/canonical.py`, `tests/test_pdf_detector.py`, `tests/test_canonical.py`; `pyproject.toml` only if strictly necessary. Add one unique Backend handoff.
- Make additive commits on the **existing** isolated Codex branch; do not force-push, overwrite prior reviews, edit main, or merge.
- Publish corrected implementation SHA and branch/handoff SHA. Both QA and Research must review the NEW exact candidate; earlier FAIL/CHANGES_REQUESTED findings cannot become PASS automatically.
- No Task 3, commercial model calls, paid services, private data, cloud or deployment.

## Deferred, explicitly not fixed by this task

Hostile PDF resource limits, parser sandbox isolation, real-document recall/precision, and long-term raster/OCR/hybrid detection remain unvalidated. These do not excuse the four blocking defects or authorize broadening the MVP.
