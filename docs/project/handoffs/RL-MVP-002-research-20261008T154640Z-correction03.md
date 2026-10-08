# RL-MVP-002 Correction 03 Research / prediction-isolation review

Task ID: RL-MVP-002 Correction 03
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-08T15:46:40Z
State: CHANGES_REQUESTED
Review verdict: CHANGES_REQUESTED FOR TASK-2 SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: 84dbf8a4fff620a4f1e63e677878d267c1f823e1 / E0018
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-002-detection-canonicalization / implementation dbae9f79d1d4dcee1aba09978713e27d6939f77e; Backend handoff branch head 821f57348c49845e4d922122cb575e569f22d82c.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-002-CORRECTION-03-REVIEW.md; RL-MVP-002-CORRECTION-03.md; DEC-002, DEC-004, DEC-007, DEC-008, DEC-010, DEC-011, DEC-015, DEC-017, DEC-020; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; prior independent QA/Research findings on ea930ab.
Authorization reference and permitted file/action scope: E0018 Correction 03 review packet authorizes read-only independent Research review and publication of one role-specific handoff. No implementation edits, merge, Task 3, provider/model calls, paid services, restricted data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to 84dbf8a4fff620a4f1e63e677878d267c1f823e1 / E0018 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-002-CORRECTION-03-REVIEW.md.
- Read docs/project/task_packets/RL-MVP-002-CORRECTION-03.md and Backend handoff docs/project/handoffs/RL-MVP-002-backend-20261008T153344Z-dbae9f7.md at branch head 821f57348c49845e4d922122cb575e569f22d82c.
- Inspected exact implementation dbae9f79d1d4dcee1aba09978713e27d6939f77e, especially src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py.
- Verified predecessor publication head e5333602c43d304a21980fc96103d19599e2dd27 -> implementation dbae9f79d1d4dcee1aba09978713e27d6939f77e changes only src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py; implementation -> published branch head adds only the Backend handoff.
- Confirmed DEC-020 advances the first MVP checkpoint to October 12, 2026 without changing quality/review authority.

## Findings

### 1. Routed staggered one-line-column case is improved, but a blocking nearby-separation variant remains

Detector v4 adds positioned-span evidence and rejects the routed case with two horizontally separated one-line blocks whose vertical top difference is at most max(48 points, four text heights). It also retains prior split-line and repeated-column-start checks.

Independent synthetic probes using the exact v4 helper logic confirmed:
- staggered two one-line columns at 20, 40 and 48 point baseline separation -> AMBIGUOUS;
- one-line side column beside a repeated main column -> AMBIGUOUS;
- ordinary single-column paragraph with modest indent -> not ambiguous;
- centered heading plus overlapping body text -> not ambiguous.

However, the new staggered rule has a hard 48-point vertical window for ordinary 11-point text. Two clearly separated x-regions with one line in each at only 52 or 60 points of vertical separation escape all three ambiguity rules because neither start repeats, they are on different lines, and the top separation exceeds 48. No source evidence establishes that reading order becomes reliable at that boundary. The Correction 03 review packet explicitly requires varying separation and says unproven reading order must fail closed.

This is a blocking Task-2 semantics gap: such a page can be treated as supported and later canonicalized in top-to-bottom order even though the one-line blocks can still represent staggered columns/side text.

### 2. Routed near/indented wide boundary boxes are improved, but short plausible boundary redactions can still become false NO_REDACTIONS

Detector v4 expands _aligned_with_text_block(): after exact horizontal overlap, a no-glyph rectangle may be treated as text-related when its width is at least two typical text heights and its nearest horizontal gap is within max(36 points, 1.5x rectangle width). This closes the published wide-box examples at x≈105 and x≈260 and preserves clearly remote wide-artwork negatives.

But the width gate silently excludes plausible short text redactions. With 11-point visible text, a 20-point-wide no-glyph black box just outside a short visible line's character bbox fails the width >= 2x text-height condition. Because it is on a different line, _same_text_flow() is false; because _aligned_with_text_block() returns false, the detector follows ignored_artwork_count += 1 and can return NO_REDACTIONS.

Independent start/end probes reproduced this for 18-20 point boundary boxes. A box of that size can plausibly hide a short name, number or abbreviation; no approved Task-2 requirement sets a minimum target width. Calling it artwork from width alone is not affirmative artwork evidence and recreates the false-completeness problem Correction 03 is meant to close.

### 3. Earlier safety fixes remain intact in the reviewed source

Independent probes/source checks confirmed:
- project-scoped deterministic IDs remain distinct across projects and delimiter-safe;
- detector provenance is now vector-text-rect-v4, intentionally changing unmerged Task-2 target IDs;
- overlapping text-related boxes are detected while edge-adjacent boxes remain separate;
- remote artwork at the existing far-right/far-away controls is not classified as a target;
- no reference, truth, evaluator feedback or prior prediction field was added to the detector/canonicalizer inputs;
- canonicalizer code was not changed by Correction 03.

An independent canonicalization probe using the unchanged exact _page_text logic and a synthetic selectable hidden-text overlay produced "Visible [[TARGET:probe]] after."; SYNTHETIC_TRAP_TOKEN was absent and the marker occurred exactly once.

## Independent tests actually run

Attempted exact repository checkout:
git clone https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /mnt/data/redaction_review_c03
Result: NOT RUN TO COMPLETION — container DNS could not resolve github.com. Therefore the exact 100-test repository suite was not independently rerun and Backend's 100-passing result is not presented as my execution evidence.

Independent Correction-03 probe:
python /mnt/data/rl_mvp002_correction03_research_probe.py
Result: 16 / 22 expectations passed; process exited 1 because six fail-closed safety expectations failed.

Passing checks included:
- routed staggered columns at 20/40/48 point separation;
- one-line secondary column;
- modest-indent single-column and centered-heading negative controls;
- project-scoped/delimiter-safe/stable target IDs;
- routed wide boundary boxes at x≈105 and x≈260;
- 30-point near boundary box;
- far remote artwork negatives;
- overlap detection and adjacent non-overlap.

Failing safety expectations:
- staggered one-line columns at 52, 60 and 80 point vertical separation were not classified ambiguous;
- near one-sided 20-point and 18-point standalone boundary boxes were not classified text-related;
- a 20-point end-boundary mirror case was not classified text-related.

The 52/60-point column cases and 18-20-point boundary boxes are the blocking variants relied on in this verdict; the 80-point column case is exploratory evidence of the same hard-window behavior.

Independent canonical leak/marker probe:
python /mnt/data/rl_mvp002_canonical_probe.py
Result:
- hidden selectable token absent: PASS
- target marker exactly once: PASS

Compile check:
python -m compileall -q /mnt/data/rl_mvp002_correction03_research_probe.py /mnt/data/rl_mvp002_canonical_probe.py
Result: PASS.

Probe environment: Python 3.13.5; pdfplumber 0.11.9; pypdf 5.9.0; reportlab 4.4.9. These differ from Backend's reported Python 3.11/parser environment. The blocking findings arise from exact reviewed v4 predicates and do not rely on parser-version-specific behavior.

Backend-reported evidence reviewed but not adopted as independent execution: 57 focused and 100 full tests passing, compileall, uv dependency check and git diff --check passing; synthetic/local/no-cost.

Tests not run and reason:
- Exact repository complete 100-test suite: NOT RUN independently because the review environment could not obtain a matching checkout due DNS/network restriction.
- Task 3 reference alignment, model/provider, evaluator/scoring, persistence, API/UI, private/restricted data, deployment and real-world recall/precision: outside Task-2 review scope and/or unauthorized.

## Verdict

CHANGES_REQUESTED.

Correction 03 fixes the specifically added regression examples, but two fail-closed classes remain:
1. staggered one-line columns just beyond the hard 48-point vertical window can still be silently accepted despite unproven reading order;
2. plausible short (approximately 18-20 point) no-glyph start/end boundary redactions can still be silently classified as artwork due the width threshold and produce false NO_REDACTIONS.

Both can affect downstream model input completeness/fairness and text-first reference alignment, so they must be corrected before Task 2 integration. The October 12 deadline does not waive these requirements.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation dbae9f79d1d4dcee1aba09978713e27d6939f77e. No prior verdict was inherited.
Research / data approval evidence (or not approved / not applicable): Research-human D03-D06 approval NOT OBTAINED. This detector review does not establish scientific validity, scoring validity, Columbia data authorization or production readiness.
Known issues / risks / stale dependencies: In addition to the blockers above, real-world detector recall/precision, hostile-input resource limits, parser isolation, OCR/raster/hybrid support and production concurrency remain explicitly deferred/unvalidated.
Affected roles / requested next action: Lead should keep dbae9f79d1d4dcee1aba09978713e27d6939f77e unmerged and route a minimal additive Task-2 correction for the two remaining fail-closed variants, with regression tests. Fresh QA and Research review should use the new exact SHA. Do not start Task 3.
Last freshness check and relevant differences: Immediately before publication, live main remained 84dbf8a4fff620a4f1e63e677878d267c1f823e1 / E0018. Backend publication head 821f57348c49845e4d922122cb575e569f22d82c contains the supplied handoff after implementation dbae9f79d1d4dcee1aba09978713e27d6939f77e; no implementation change after the reviewed SHA was identified.
Rollback or correction approach: This Research branch contains only this handoff. Treat it as stale if a new candidate or governing decision appears. Backend correction should be additive on the isolated Task-2 branch, with no force-push.
Publication: PUBLISHED on review/rl-mvp-002-research-correction03-e0018; not merged to main.
