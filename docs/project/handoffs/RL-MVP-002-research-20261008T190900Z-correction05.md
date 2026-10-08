# RL-MVP-002 Correction 05 Research / prediction-isolation review

Task ID: RL-MVP-002 Correction 05
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-08T19:09:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-2 RESEARCH/PREDICTION-ISOLATION SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: 73e82d883bb5fd352e6fffd5a794adc71826b1ee / E0021
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-002-detection-canonicalization / implementation 736fa18419340b9fcb8dd5e121e8eebcc24b22f7; Backend publication head 395d2321012092bd619a34711cb0b4ca4855abf2.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-002-CORRECTION-05-REVIEW.md; DEC-002, DEC-004, DEC-007, DEC-008, DEC-010, DEC-011, DEC-015, DEC-017, DEC-020; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; predecessor Correction 04 Research PASS 2dc858c908c94f64da92edd9fe790e73c49d3fbd and QA remote-artwork blocker.
Authorization reference and permitted file/action scope: E0021 Correction 05 review packet authorizes read-only independent Research review and publication of one role-specific handoff. No implementation edits, merge, Task 3, provider/model calls, paid services, restricted data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to 73e82d883bb5fd352e6fffd5a794adc71826b1ee / E0021 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-002-CORRECTION-05-REVIEW.md.
- Read Backend handoff docs/project/handoffs/RL-MVP-002-backend-20261008T184710Z-736fa18.md at publication head 395d2321012092bd619a34711cb0b4ca4855abf2.
- Inspected exact implementation commit 736fa18419340b9fcb8dd5e121e8eebcc24b22f7 and its diff from predecessor df20fe074c0bebc7be15971199d3c361469bc6b1.
- Confirmed implementation changes are limited to src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py; implementation-to-publication head adds only the unique Backend handoff.
- Confirmed detector provenance advances to vector-text-rect-v6 and prior unmerged target IDs intentionally change.

## Findings

### 1. Remote x-aligned square/wide artwork — RESOLVED

Correction 05 removes horizontal character-range overlap as standalone evidence that a no-glyph rectangle is text-related. For no-glyph rectangles, the detector now relies on:
- actual two-dimensional character intersection, checked by the caller;
- same-line nearby text-flow evidence from _same_text_flow(); or
- text-line-height plausibility from _plausible_text_rectangle().

Independent probes confirmed that vertically remote 40x40 and 120x30 black rectangles remain ignorable artwork even when their x-range is aligned with visible text. This closes the QA false-positive that blocked Correction 04.

### 2. Nearby/overlapping non-text-height black rectangles remain fail-closed

Independent probes confirmed 40x40 and 120x30 rectangles in the same line flow remain UNSUPPORTED through _same_text_flow(), and actual two-dimensional glyph intersection remains positive for overlapping shapes. The correction therefore does not weaken nearby/occluding safety while fixing the vertically unrelated artwork case.

Overlap/duplicate-target safeguards from prior corrections remain present in the reviewed source, and edge-adjacent rectangles remain non-overlapping under the strict positive-area intersection predicate.

### 3. Text-sized ambiguous rectangles remain UNSUPPORTED

The v6 _plausible_text_rectangle() still classifies black rectangles by vertical geometry: a rectangle between one-half and twice the median visible glyph height remains a plausible text rectangle independent of horizontal position. Independent probes confirmed both x-aligned and off-axis remote 12-point-high rectangles remain ambiguous/UNSUPPORTED rather than being silently converted to NO_REDACTIONS.

This is deliberately conservative and may reject decorative text-height rectangles. That is a documented MVP coverage limitation, not a false claim that such rectangles are confirmed redactions.

### 4. Earlier layout, identity and canonical-context protections remain intact

Independent probes/source checks confirmed:
- staggered one-line columns at 40/49/52/60/80/120-point vertical separation remain ambiguous;
- sparse one-line secondary columns remain ambiguous;
- ordinary single-column text with modest indentation remains accepted;
- centered heading + at least two aligned body lines remains accepted;
- centered heading + only one body line remains ambiguous/UNSUPPORTED;
- project-scoped target IDs remain distinct;
- delimiter-bearing project/document identity tuples remain unambiguous;
- repeated target-ID derivation is deterministic within the same project/document/geometry/version;
- hidden selectable text is removed before canonical output;
- exactly one target marker is emitted for the tested target;
- visible order in the canonical probe remained Visible -> target marker -> after;
- detector/canonicalizer interfaces remain redacted-only, with no reference, truth, evaluator feedback or prior prediction input introduced.

No new blocking Research target-semantics or prediction-isolation regression was observed.

## Independent tests actually run

Exact repository checkout/full-suite execution was attempted conceptually but a matching checkout is not available in this review environment; prior review attempts in the same environment could not resolve github.com. I therefore did not claim independent execution of the exact repository 120-test suite. Exact source/tests were read from GitHub at the requested SHA and isolated probes reproduced the exact reviewed helper/canonical predicates relevant to this packet.

Command:
python /mnt/data/rl_mvp002_c05_probe.py
Result: 12/12 passed.

Covered:
- remote x-aligned 40x40 artwork excluded;
- remote x-aligned 120x30 artwork excluded;
- same-line 40x40 remains UNSUPPORTED;
- same-line 120x30 remains UNSUPPORTED;
- remote text-height rectangle x-aligned remains UNSUPPORTED;
- remote text-height rectangle off-axis remains UNSUPPORTED;
- actual 2D glyph intersection remains detected;
- project-scoped ID distinction;
- delimiter-safe ID encoding;
- target-ID stability;
- positive-area overlap detection;
- edge adjacency remains non-overlap.

Command:
python /mnt/data/rl_mvp002_c05_layout_probe.py
Result: 10/10 passed.

Covered:
- staggered columns at 40/49/52/60/80/120 points;
- centered heading + two aligned body lines accepted;
- centered heading + one body line remains ambiguous;
- modest-indent single-column negative control;
- sparse side-column ambiguity.

Command:
python /mnt/data/rl_mvp002_c05_canonical_probe.py
Result:
Visible [[TARGET:probe-target]] after.
PASS hidden text removed; marker unique; visible order preserved.

Compile checks:
python -m compileall -q /mnt/data/rl_mvp002_c05_probe.py
python -m compileall -q /mnt/data/rl_mvp002_c05_layout_probe.py
python -m compileall -q /mnt/data/rl_mvp002_c05_canonical_probe.py
Result: PASS.

Probe environment: local review container; isolated exact-logic reproductions, not a byte-for-byte execution of the repository checkout.

Backend-reported evidence reviewed but not adopted as independent execution: 77 focused tests and 120 full tests passing, compileall, uv dependency check and git diff --check passing; synthetic/local/no-cost.

Tests not run and reason:
- Exact repository full 120-test suite: NOT RUN independently because a matching executable checkout was unavailable in the review environment.
- OCR/scans, real-world recall/precision, hostile-PDF resource limits, parser sandbox/process isolation, Task 3 reference alignment, model/provider, evaluator/scoring, persistence, API/UI, private/restricted data and deployment: outside RL-MVP-002 review scope and/or unauthorized.

## Verdict

PASS for RL-MVP-002 Correction 05 Research/prediction-isolation semantics on exact implementation 736fa18419340b9fcb8dd5e121e8eebcc24b22f7.

The Correction 05 change fixes the predecessor QA false-positive for vertically remote x-aligned non-text-height artwork without weakening nearby/overlapping or text-height ambiguity handling. Earlier layout, centered-heading, target-identity, hidden-text and marker protections remain intact in the reviewed scope.

This PASS is not scientific validation, not D03-D06 research-human approval, not merge authorization and not Task 3 authorization.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation 736fa18419340b9fcb8dd5e121e8eebcc24b22f7. No predecessor verdict was automatically inherited.
Research / data approval evidence (or not approved / not applicable): Research-human D03-D06 approval NOT OBTAINED. No scientific accuracy, Columbia data authorization or production-readiness claim is made.
Known issues / risks / stale dependencies: The supported subset remains deliberately narrow. Remote text-line-height decorative rectangles remain conservatively UNSUPPORTED; complex positioned layouts may be rejected; real-world recall/precision, OCR/raster/hybrid detection, hostile-input resource limits, parser isolation and production concurrency remain unvalidated/deferred.
Affected roles / requested next action: Lead should reconcile this fresh Research PASS with fresh QA review of exact implementation 736fa18419340b9fcb8dd5e121e8eebcc24b22f7. Do not merge or start Task 3 from this handoff alone; owner merge authorization and all required gates remain separate.
Last freshness check and relevant differences: Immediately before publication, live main remained 73e82d883bb5fd352e6fffd5a794adc71826b1ee / E0021. Backend publication head 395d2321012092bd619a34711cb0b4ca4855abf2 differs from implementation 736fa18419340b9fcb8dd5e121e8eebcc24b22f7 only by the Backend handoff commit.
Rollback or correction approach: This Research branch contains only this handoff. If the candidate or governing decisions change, this review becomes stale and a new exact-SHA review is required.
Publication: PUBLISHED on review/rl-mvp-002-research-correction05-e0021; not merged to main.
