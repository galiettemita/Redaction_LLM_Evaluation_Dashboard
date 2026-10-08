# RL-MVP-002 Correction 04 — conservative supported-layout boundary

Status: CHANGES_REQUESTED; bounded corrective work under the existing approved Task 2, not a new task.
Owner: Backend/Codex. Reviewers: QA and Research. Receiver: Lead.
Baseline main: 84dbf8a4fff620a4f1e63e677878d267c1f823e1, E0018. Routing epoch E0019.
Failed implementation: dbae9f79d1d4dcee1aba09978713e27d6939f77e; published Backend head 821f57348c49845e4d922122cb575e569f22d82c.
Independent QA: qa/rl-mvp-002-correction03-dbae9f7 @ b18f947639713b255d2c88adbc1dfbe03832417e — FAIL.
Independent Research: review/rl-mvp-002-research-correction03-e0018 @ 48377ce048b538a7f80bf962177f1d9b61e37483 — CHANGES_REQUESTED (16/22 adversarial expectations passed).
Deadline October 12, 2026 (DEC-020). No quality, data, cost or review gates waived.

## Three blocking cases

1. **Staggered one-line columns:** The v4 48-point vertical window misses separated single-line columns at 49, 52, 60 or 80 points. Vertical distance alone is not evidence of a single reading flow. Reject ambiguous sparse/positioned layouts as UNSUPPORTED unless a reliable single-column order is supported.
2. **Short standalone no-glyph redactions:** Width >= 2x text height and horizontal gap cutoffs allow 18–20 point plausible black boxes at document/section boundaries to be silently classified as artwork, yielding false NO_REDACTIONS. Require affirmative artwork evidence; otherwise fail closed as UNSUPPORTED. Include moderately offset 120-point boxes and remote artwork controls.
3. **Short centered heading regression:** A short 16-point centered heading near x=300 above an 11-point left-aligned body near x=72, with ~44-point vertical separation, is incorrectly rejected as multi-column. Preserve legitimate single-column headings and indents when evidence supports them.

## Implementation approach and tests

Before coding, document a small, testable *supported-layout envelope*: simple digitally born single-column visible text and rectangular text redactions; reject ambiguous positioned content. Avoid another patch based only on new arbitrary distance/width thresholds. If valid single-column and ambiguous layouts cannot be reliably distinguished, return UNSUPPORTED and document the conservative rejection. Do not invent hidden text or use reference data.

Write failing synthetic PDF/parser-level regressions and predicate tests (RED) for staggered columns at 40/49/52/60/80 pt, short centered heading/body, 18/20/30/120 pt boundary boxes and negative controls for remote artwork, normal single-column paragraphs and modest indents. Then minimal GREEN implementation; rerun all prior tests for project-scoped IDs, overlap/duplicate boxes, hidden selectable-text suppression, markers and redacted-only isolation. Run focused/full pytest, compileall, dependency check, git diff --check; report actual commands/results and NOT RUN.

Allowed product files: src/redaction_lab/pdf_detector.py, tests/test_pdf_detector.py; canonical.py and test_canonical.py only if a proven Task-2 reading-order defect requires them; one new unique Backend handoff. No contracts, fixtures, reference alignment, scoring, model adapters, UI, database, cloud, private data or deployment. Stop if scope expands.

Publish additive implementation commit and handoff on existing isolated Codex branch, no force-push. QA and Research must independently review NEW exact SHA. No merge or Task 3. No scientific score validity or real-world detector recall claimed.
