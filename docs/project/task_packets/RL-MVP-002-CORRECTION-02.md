# RL-MVP-002 Correction 02 — sparse layouts and boundary redactions

State: ROUTED under existing approved RL-MVP-002 correction scope. Backend/Codex owner; QA and Research independent reviewers; Lead next receiver.
Baseline main: e769d2d48d2de2d402b23b504e2d933a5926d6ae / E0014. Coordination epoch E0015. Reviewed implementation: 12698b92d883af658266d54a9223b5619dedc7ee; Backend branch head c37837669ce9e538a3afa8db0e25ef92cbbdd327.
Independent QA FAIL: qa/rl-mvp-002-corrected-12698b9 @ 1203aece4b88bce06a1aed7887a97dd71cec0861.
Independent Research CHANGES_REQUESTED: review/rl-mvp-002-research-corrected-e0014 @ 2694967c3b77d531f09a9fd33a50a04df8ca91e0 (9 passing/3 failing independent probes).
DEC-020 advances checkpoint to October 12, 2026, but does not change this task scope, scientific validation or approval gates.

## Blocking fixes

1. Sparse positioned/multi-column text: reject ambiguous one-line secondary columns and two one-line columns before canonicalizing; the current repeated-column-start heuristic can accept them and corrupt reading order. Preserve legitimate single-line/single-column controls; do not treat every word gap as a separate column. Return explicit UNSUPPORTED/AMBIGUOUS_TEXT_LAYOUT when ordering cannot be proven.
2. Standalone no-glyph black rectangles at section/document boundaries: a plausible redaction at the first/last line with one-sided visible context beyond nearby_gap can be incorrectly ignored as artwork, yielding false NO_REDACTIONS. Require affirmative artwork evidence to ignore plausible text-region black boxes; otherwise return UNSUPPORTED. Preserve clearly remote artwork exclusion.

## TDD, scope and publication

Write failing synthetic tests first for sparse/two one-line columns, side column, start/end standalone boxes, and negative controls for legitimate single-column text and remote artwork. Show RED and GREEN; rerun previous ID, overlap, hidden-text and marker tests, full suite, compileall, git diff --check and dependency checks. Report exact commands/results and NOT RUN tests; do not claim real-document recall.

Allowed files: src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py; canonical.py and test_canonical.py only if needed for a demonstrated Task 2 defect; one unique Backend handoff. No contracts, fixtures, alignment, scoring, models, UI, shared docs, cloud or paid services. Stop for scope expansion.

Make additive commits on existing Codex task branch, no force push. Publish new implementation SHA and handoff branch head. QA and Research must review the NEW exact SHA. No merge, Task 3 or deployment.
