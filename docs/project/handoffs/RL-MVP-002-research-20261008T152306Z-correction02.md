# RL-MVP-002 Correction 02 Research / prediction-isolation review

Task ID: RL-MVP-002 Correction 02
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-08T15:23:06Z
State: CHANGES_REQUESTED
Review verdict: CHANGES_REQUESTED FOR TASK-2 SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: 72a390c9a2b67b52797c711561789f0eaa105e90 / E0016
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-002-detection-canonicalization / implementation ea930abef319832cf494df5851be1b19d3e2cf1c; Backend publication head e5333602c43d304a21980fc96103d19599e2dd27.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-002-CORRECTION-02-REVIEW.md; RL-MVP-002-CORRECTION-02.md; DEC-002, DEC-004, DEC-007, DEC-008, DEC-010, DEC-011, DEC-015, DEC-020; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; prior exact-candidate Research review 2694967c3b77d531f09a9fd33a50a04df8ca91e0.
Authorization reference and permitted file/action scope: E0016 Correction 02 review packet authorizes read-only independent Research review and one role-specific handoff. No implementation changes, merge, Task 3, paid calls, restricted data, provider/model use, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to 72a390c9a2b67b52797c711561789f0eaa105e90 / E0016 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and RL-MVP-002-CORRECTION-02-REVIEW.md.
- Read RL-MVP-002-CORRECTION-02.md and Backend handoff docs/project/handoffs/RL-MVP-002-backend-20261008T151310Z-ea930ab.md at e5333602c43d304a21980fc96103d19599e2dd27.
- Inspected exact implementation ea930abef319832cf494df5851be1b19d3e2cf1c, especially src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py. Correction 02 changes only detector/test logic; branch-head publication adds only the Backend handoff relative to implementation.
- Confirmed DEC-020 advances the MVP checkpoint to 2026-10-12 but does not waive correctness, review, scientific, cost or merge gates.

## Correction 02 findings

### Sparse/multi-column ambiguity — RESOLVED for routed defects

Detector v3 now rejects:
- two one-line spatial columns;
- one sparse one-line side column next to a repeated main column;
- the earlier ordinary, narrow-gutter and staggered multi-column cases.

Independent probes reproduced the v3 helper logic and confirmed those cases classify as ambiguous while an ordinary one-line sentence and a modest 24-point single-column indent remain non-ambiguous. This closes the specific sparse-column defect that allowed row-major canonical interleaving of those routed layouts.

The heuristic remains intentionally conservative and may reject some complex legitimate positioned layouts. That is an explicit MVP coverage limitation, not a scientific accuracy result.

### Standalone start/end no-glyph redactions — ROUTED CASES RESOLVED, BUT ONE BLOCKING VARIANT REMAINS

Correction 02 replaces the prior vertical-proximity logic with _aligned_with_text_block(), which treats a no-glyph black rectangle as ambiguous when its horizontal interval positively overlaps any visible text character anywhere on the page. This closes the published start/end test cases where the standalone rectangle shares the visible text column's horizontal band, even when only one-sided context is far away.

However, the detector still silently ignores a plausible one-sided boundary redaction when the black rectangle is **near/indented within the same general text region but does not geometrically overlap the short visible line's character boxes in x**. In that case:
- _same_text_flow() is false because the visible text is on another line;
- _aligned_with_text_block() is false because there is no positive x-overlap;
- no occluded extractable characters exist;
- the candidate falls through to ignored_artwork_count += 1 and can yield NO_REDACTIONS.

Independent example: visible one-sided text "Short" begins at x=72 and ends before x=105; a 120-point-wide black rectangle begins at x=105 on a later/earlier boundary line. This is spatially close enough to be a plausible indented text redaction, but v3 classifies it the same as artwork solely because no character bbox horizontally overlaps it.

That still violates the Correction 02 requirement to avoid false NO_REDACTIONS for plausible standalone no-glyph text-region boxes and to require affirmative artwork evidence before ignoring them. The fix should remain fail-closed: use a conservative horizontal text-band/proximity criterion or other affirmative artwork evidence, while preserving confidently remote artwork exclusion. Do not infer hidden text.

## Prior blockers/regressions rechecked

- Project-scoped and delimiter-safe target identity remains resolved; v3 provenance intentionally changes unmerged Task-2 target IDs.
- Overlapping/duplicate text-related rectangles remain rejected before target construction; adjacent non-overlapping boxes remain distinct.
- Clearly remote artwork outside the visible text horizontal band remains ignorable in the independent probe.
- Public detection/canonicalization inputs remain redacted-only; no reference, truth, evaluator feedback or prior prediction input was introduced by Correction 02.
- Canonicalizer was not modified by Correction 02; prior hidden selectable-text suppression and exact-one-marker controls remain part of the candidate test surface. No research score or truth-alignment implementation is added.

## Independent tests actually run

Direct repository checkout was not available in this review environment, so the exact Backend-reported 94-test suite was NOT independently rerun. Exact source/tests were inspected through the live GitHub connector. I executed an isolated synthetic probe implementing the exact v3 helper predicates and target-ID encoding relevant to the routed and adversarial cases.

Command:
python /mnt/data/rl_mvp002_correction02_research_probe.py

Result:
- 11 expectations PASS
- 1 safety expectation FAIL
- process exit status 1 because the unresolved boundary-redaction case was intentionally asserted as fail-closed.

Passing checks:
- two one-line columns -> ambiguous;
- sparse one-line secondary column -> ambiguous;
- ordinary single line -> not ambiguous;
- modest indented single column -> not ambiguous;
- cross-project target IDs differ;
- delimiter-bearing identity tuples remain unambiguous;
- overlapping boxes detected;
- adjacent boxes remain non-overlapping;
- routed start standalone rectangle is ambiguous;
- routed end standalone rectangle is ambiguous;
- remote art outside the horizontal text band is not classified text-related.

Failing safety check:
- near/indented one-sided standalone boundary rectangle with no x-overlap against a short visible line is not treated ambiguous and would follow the ignored-artwork path.

Compile check:
python -m compileall -q /mnt/data/rl_mvp002_correction02_research_probe.py
Result: PASS.

Probe environment: Python 3.13.5, pdfplumber 0.11.9, pypdf 5.9.0, reportlab 4.4.9. These differ from Backend's reported macOS/Python 3.11 environment. The blocking result follows directly from the exact reviewed v3 predicates; local PDF tooling was used only to generate/inspect synthetic character geometry, not to claim a byte-for-byte repository test run.

Backend-reported evidence reviewed but not adopted as independent execution: 51 focused tests and 94 full tests passing, compileall and git diff --check passing, synthetic/local/no-cost.

Tests not run and reason:
- Exact repository 94-test suite: NOT RUN independently because a matching executable checkout was unavailable.
- Task 3 reference alignment, model/provider, evaluator/scoring, persistence, API/UI, private/restricted data, deployment and real-world recall/precision tests: outside this review scope and/or unauthorized.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation ea930abef319832cf494df5851be1b19d3e2cf1c; prior verdicts were not carried forward.
Research / data approval evidence (or not approved / not applicable): Research-human D03-D06 approval NOT OBTAINED. This detector review does not establish scientific validity, scoring validity, Columbia data authorization or production readiness.
Known issues / risks / stale dependencies: One Task-2 false-NO_REDACTIONS path remains for horizontally near/indented one-sided standalone no-glyph rectangles without positive x-overlap. Real-world recall/precision, hostile-input resource bounds, parser sandboxing/process isolation, OCR/raster/hybrid support and production concurrency remain explicitly deferred.
Affected roles / requested next action: Lead should keep ea930abef319832cf494df5851be1b19d3e2cf1c unmerged and route the remaining standalone-boundary ambiguity to Backend/Codex for a minimal additive detector/test correction. Fresh QA and Research review should inspect the new exact SHA. Do not start Task 3. DEC-020's October 12 deadline does not alter this recommendation.
Last freshness check and relevant differences: Immediately before publication, live main remained 72a390c9a2b67b52797c711561789f0eaa105e90 / E0016. Backend publication head e5333602c43d304a21980fc96103d19599e2dd27 contains the supplied handoff after implementation ea930abef319832cf494df5851be1b19d3e2cf1c; no implementation code change after the reviewed SHA was identified.
Rollback or correction approach: This Research branch contains only this handoff. Treat it as stale if a new candidate or governing decision appears. Backend correction should be additive on the isolated Task-2 branch, with no force-push.
Publication: PUBLISHED on review/rl-mvp-002-research-correction02-e0016; not merged to main.
