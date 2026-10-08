# RL-MVP-002 Correction 04 Research / prediction-isolation review

Task ID: RL-MVP-002 Correction 04
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-08T18:38:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-2 RESEARCH/PREDICTION-ISOLATION SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: 78126c616ae5660e21773eef1fdc6ab98f8e3eea / E0020
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-002-detection-canonicalization / implementation df20fe074c0bebc7be15971199d3c361469bc6b1; Backend handoff branch head 6ba3e02af0d13b8ef673ac007f06d08912ff9e38.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-002-CORRECTION-04-REVIEW.md; RL-MVP-002-CORRECTION-04.md; DEC-002, DEC-004, DEC-007, DEC-008, DEC-010, DEC-011, DEC-015, DEC-017, DEC-020; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; prior independent QA/Research findings on dbae9f79.
Authorization reference and permitted file/action scope: E0020 Correction 04 review packet authorizes read-only independent Research review and publication of one role-specific handoff. No implementation edits, merge, Task 3, provider/model calls, paid services, restricted data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to 78126c616ae5660e21773eef1fdc6ab98f8e3eea / E0020 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-002-CORRECTION-04-REVIEW.md.
- Read docs/project/task_packets/RL-MVP-002-CORRECTION-04.md and Backend handoff docs/project/handoffs/RL-MVP-002-backend-20261008T181752Z-df20fe0.md at branch head 6ba3e02af0d13b8ef673ac007f06d08912ff9e38.
- Inspected exact implementation df20fe074c0bebc7be15971199d3c361469bc6b1, especially src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py.
- Confirmed the implementation-to-publication delta is handoff-only. No code change exists after the reviewed implementation SHA.
- Confirmed DEC-020 retains the October 12, 2026 checkpoint without waiving correctness, review or no-spend rules.

## Findings

### 1. Staggered one-line columns — RESOLVED within the approved narrow supported-layout boundary

Detector v5 removes the prior hard vertical-distance cutoff from the staggered sparse-column check. Horizontally disjoint line spans whose starts are separated by at least the declared column-separation threshold are now treated as ambiguous regardless of 40/49/52/60/80-point vertical separation.

Independent reproduction of the exact v5 helper logic confirmed:
- 40, 49, 52, 60, 80 and 120-point staggered one-line separations -> AMBIGUOUS;
- one-line secondary column beside a repeated main column -> AMBIGUOUS;
- ordinary left-aligned single-column text with modest indentation -> NOT ambiguous.

This closes the previous false-supported reading-order path. Conservative rejection of more complex positioned layouts remains an explicit MVP limitation rather than an assertion of correct ordering.

### 2. Short black-box redactions — RESOLVED for the routed false-NO_REDACTIONS class

Detector v5 replaces the prior minimum-width and horizontal-gap requirements with a declared text-line-height geometry class. A no-glyph rectangle whose height is between one-half and twice the median visible glyph height is treated as a plausible text rectangle regardless of width or page position and therefore cannot be silently ignored as artwork.

Independent probes confirmed:
- 18, 20, 30 and 120-point-wide boundary boxes with text-line-height geometry -> plausible/ambiguous rather than ignorable;
- moderately offset 120-point boxes at x≈260/280/300 -> plausible/ambiguous;
- remote text-sized decorative rectangles are conservatively UNSUPPORTED, not silently called NO_REDACTIONS;
- clearly tall/square non-text artwork outside the text-line-height class remains ignorable when it has no text overlap/same-line evidence.

This is deliberately conservative. The broad rejection of remote text-height rectangles is documented in the Backend handoff and Correction 04 review packet as an MVP limitation, not a claim that such rectangles are redactions.

### 3. Centered headings — RESOLVED with affirmative single-column-flow evidence

The v5 layout helper now excludes a centered larger heading from multi-column inference only when all of the following hold:
- the heading is a single span containing page center;
- it is above the body;
- it is larger than the body text;
- there are at least two remaining body lines;
- each body line is itself single-span;
- their starts establish one aligned flow.

Independent probes confirmed:
- centered heading + two aligned body lines -> accepted as single-column;
- centered heading + only one body line -> remains AMBIGUOUS/UNSUPPORTED;
- ordinary left-aligned heading + aligned body remains single-column.

This matches the approved safeguard: heading acceptance requires affirmative evidence rather than an unconditional heading exception.

## Regressions / earlier safety requirements rechecked

Independent source/probe checks found no regression in:
- project-scoped deterministic target identity and delimiter-safe encoding;
- v5 target provenance (unmerged v4 IDs intentionally change);
- overlapping/duplicate text-related rectangle rejection;
- adjacent non-overlapping boxes remaining distinct;
- redacted-only detector/canonicalizer interfaces with no reference, truth, evaluator-feedback or prior-prediction input;
- hidden selectable-text suppression and exactly-one marker behavior in canonical output;
- explicit UNSUPPORTED semantics rather than false NO_REDACTIONS for uncertain text-height black boxes.

The v5 detector intentionally narrows the supported subset: some legitimate complex layouts and decorative text-height rectangles will be rejected. Within RL-MVP-002's fail-closed week-one boundary, that is a documented limitation rather than a blocker.

## Independent tests actually run

Attempted exact repository checkout:
git clone --no-checkout https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /mnt/data/rl_mvp002_c04
Result: NOT RUN TO COMPLETION — the review container could not resolve github.com. Therefore the exact repository's 113-test suite was not independently executed.

Exact source/tests were inspected through the live GitHub connector. I then ran isolated independent probes reproducing the exact reviewed v5 predicates relevant to the required review matrix.

Command:
python /mnt/data/rl_mvp002_c04_probe.py

Result:
26 passed, 0 failed.

Checks covered:
- staggered one-line columns at 40/49/52/60/80/120 points;
- sparse one-line secondary column;
- legitimate modest-indent single-column layout;
- centered heading + two-body-line positive control;
- centered heading + one-body-line unsupported control;
- left-aligned heading/body control;
- 18/20/30/120-point boundary rectangles;
- moderately offset 120-point boxes;
- remote text-sized rectangle conservatively treated as text-like/ambiguous;
- remote tall/square artwork remaining outside the text-line-height class;
- project-scoped IDs;
- delimiter-safe ID encoding;
- deterministic ID stability;
- overlap versus adjacency.

Compile check:
python -m compileall -q /mnt/data/rl_mvp002_c04_probe.py
Result: PASS.

Independent canonical leakage/marker probe:
python /mnt/data/rl_mvp002_c04_canonical_probe.py
Result:
Visible [[TARGET:probe-target]] after.
PASS hidden selectable text suppression and marker uniqueness.

Compile check:
python -m compileall -q /mnt/data/rl_mvp002_c04_canonical_probe.py
Result: PASS.

Probe environment: Python 3.13.5; locally installed PDF tooling. These probes reproduce exact reviewed helper/canonical logic for the tested invariants but are not a byte-for-byte execution of the repository checkout.

Backend-reported evidence reviewed but not adopted as independent execution: 70 focused tests and 113 full tests passing, compileall, uv dependency check and git diff --check passing in the Backend environment; synthetic/local/no-cost.

Tests not run and reason:
- Exact repository full 113-test suite: NOT RUN independently because the review environment could not obtain a matching checkout due DNS/network restriction.
- Task 3 reference alignment, model/provider, evaluator/scoring, persistence, API/UI, private/restricted data, deployment and real-world recall/precision tests: outside RL-MVP-002 review scope and/or unauthorized.

## Verdict

PASS for RL-MVP-002 Research/prediction-isolation semantics on exact implementation df20fe074c0bebc7be15971199d3c361469bc6b1.

The three previously blocking classes are resolved within the approved conservative supported-layout envelope:
1. staggered/positioned sparse columns fail closed;
2. short plausible no-glyph black boxes cannot silently become NO_REDACTIONS;
3. centered headings are allowed only with affirmative aligned-body evidence.

No new blocking Research semantics regression was observed in the required matrix. This PASS is not scientific validation, not D03-D06 research-human approval, and not merge authorization.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation df20fe074c0bebc7be15971199d3c361469bc6b1. No earlier FAIL/CHANGES_REQUESTED verdict was inherited.
Research / data approval evidence (or not approved / not applicable): Research-human D03-D06 approval NOT OBTAINED. This detector review does not establish scientific validity, scoring validity, Columbia data authorization or production readiness.
Known issues / risks / stale dependencies: Real-world detector recall/precision, OCR/raster/hybrid support, hostile-input resource limits, parser isolation/process safety, production concurrency and later reference/model/evaluator behavior remain unvalidated/deferred. Conservative rejection may reduce MVP coverage; that limitation must remain visible and must not be presented as complete redaction detection.
Affected roles / requested next action: Lead should reconcile this Research PASS with fresh QA review of the same exact SHA. Do not merge or start Task 3 from this handoff alone; owner merge authorization and all required gates remain separate.
Last freshness check and relevant differences: Immediately before publication, live main remained 78126c616ae5660e21773eef1fdc6ab98f8e3eea / E0020. Backend publication head 6ba3e02af0d13b8ef673ac007f06d08912ff9e38 differs from implementation df20fe074c0bebc7be15971199d3c361469bc6b1 only by the Backend handoff.
Rollback or correction approach: This Research branch contains only this handoff. If the candidate or governing decisions change, this review becomes stale and a new exact-SHA review is required.
Publication: PUBLISHED on review/rl-mvp-002-research-correction04-e0020; not merged to main.
