# RL-MVP-002 corrected Research / prediction-isolation review

Task ID: RL-MVP-002 Correction 01
Role / session label: Research / Evaluation independent corrected-candidate reviewer
UTC time: 2026-10-08T15:05:00Z
State: CHANGES_REQUESTED
Review verdict: CHANGES_REQUESTED FOR TASK-2 SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: e769d2d48d2de2d402b23b504e2d933a5926d6ae / E0014
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-002-detection-canonicalization / corrected implementation 12698b92d883af658266d54a9223b5619dedc7ee; Backend handoff branch head c37837669ce9e538a3afa8db0e25ef92cbbdd327.
Source requirements / approved decisions / contract versions: AGENTS.md; RL-MVP-002-CORRECTED-REVIEW.md; RL-MVP-002-CORRECTION-01.md; DEC-002, DEC-004, DEC-007, DEC-008, DEC-010, DEC-011, DEC-015; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; merged RL-MVP-001 contracts.
Authorization reference and permitted file/action scope: E0014 corrected-review packet authorizes read-only Research review of exact implementation commit 12698b92d883af658266d54a9223b5619dedc7ee and publication of one unique Research handoff. No implementation edits, merge, Task 3, provider/model calls, paid services, private data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-002-CORRECTED-REVIEW.md at E0014.
- Read docs/project/task_packets/RL-MVP-002-CORRECTION-01.md and the prior QA/Research findings.
- Inspected exact corrected source/tests at 12698b92d883af658266d54a9223b5619dedc7ee, especially src/redaction_lab/pdf_detector.py and tests/test_pdf_detector.py; canonical.py/test_canonical.py were unchanged by Correction 01.
- Read Backend handoff docs/project/handoffs/RL-MVP-002-backend-20261008T141115Z-12698b9.md at branch head c37837669ce9e538a3afa8db0e25ef92cbbdd327.
- Verified the branch-head delta after the implementation is handoff-only.

## Four routed blockers: corrected-candidate result

1. **Project-scoped deterministic target identity — RESOLVED.**
   - Target identity now includes project_id, redacted_document_version_id, page index, normalized geometry and DETECTOR_VERSION=v2.
   - JSON encoding with fixed separators removes the delimiter ambiguity that a simple string join could create.
   - Independent probes confirmed different projects and the adversarial pairs ("a|b","c") versus ("a","b|c") produce different target IDs.
   - v2 intentionally changes target IDs. No prior Task-2 target IDs were merged; downstream Task 3/4 must consume v2 provenance only.

2. **Ambiguous multi-column reading order — PARTIALLY RESOLVED; BLOCKING EDGE REMAINS.**
   - Corrected code now rejects the routed 2x2, narrow-gutter and staggered repeated-column fixtures as AMBIGUOUS_TEXT_LAYOUT.
   - A normal single-column/indented layout remains accepted in the independent probe.
   - However, _has_ambiguous_multicolumn_layout only treats a spatial start as a column when that start repeats on at least two spans. A page with a multi-line left column and a one-line secondary right column is therefore not classified as ambiguous. That positioned side column can still be emitted in row-major canonical order, changing model-visible context.
   - This remains within the Task-2 week-one rule that ambiguous positioned-text layouts must fail closed rather than be silently reordered.

3. **Overlapping/duplicate black rectangles — RESOLVED for the routed cases.**
   - The detector now constructs text-related black boxes and rejects positive-area overlaps before target construction with OVERLAPPING_REDACTION_RECTANGLES.
   - Independent probes confirmed both overlapping and exact-duplicate text-related rectangles are caught.
   - Adjacent non-overlapping boxes remain distinct by the strict positive-area intersection test.
   - Overlapping remote artwork remains outside the text-related set, preserving the intended remote-artwork exclusion behavior.

4. **Standalone redaction-like rectangle with no extractable hidden text — PARTIALLY RESOLVED; BLOCKING DOCUMENT-BOUNDARY VARIANT REMAINS.**
   - Corrected _near_text_block now catches the routed case where a standalone redaction lies between visible text above and below, including the farther-between-lines regression.
   - Remote artwork far outside the text column remains ignored, as required.
   - But a plausible standalone redaction at the **start or end of a text column/document section**, with visible text only on one side and farther than nearby_gap, still makes both _same_text_flow and _near_text_block return False. The detector then follows ignored_artwork_count += 1 and can return NO_REDACTIONS.
   - That is still a false-completeness path: absence of extractable hidden glyphs plus one-sided surrounding text is insufficient evidence to call the black region artwork. Under the packet's fail-closed rule it should be UNSUPPORTED/ambiguous unless stronger artwork evidence exists.

## Redacted-only / canonical safety and regression checks

Positive checks:
- detect_targets continues to accept only redacted PDF bytes plus project/document identity; no reference, mapping, prior prediction or evaluator input is present.
- canonicalize_redacted remains unchanged by Correction 01 and re-verifies detection/source/project identity before emitting canonical text.
- Independent canonical probe confirmed an extractable SYNTHETIC_TRAP_TOKEN covered by a target box is absent from canonical output and replaced by exactly one target marker.
- Single-column text probe was not falsely flagged by the new repeated-column heuristic.
- Remote black artwork probe was not falsely treated as a redaction-like rectangle.
- No correction touched contracts.py, fixtures.py, canonical.py, dependency metadata, scoring or reference code.

No new scientific/research claim is inferred from these positives.

## Independent tests actually run

A direct read-only git clone of the public repository was attempted:

git clone https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git

Result: NOT RUN TO COMPLETION — the review container could not resolve github.com. Therefore I did not claim independent execution of the exact repository's reported 88-test suite.

Exact candidate source and tests were read through the live GitHub connector. I then ran isolated adversarial probes implementing the exact corrected helper logic for target identity, multicolumn detection, overlap classification and standalone text-block classification against synthetic ReportLab/pdfplumber PDFs.

Command:
pytest -q /mnt/data/test_rl_mvp002_corrected_research_probe.py

Result:
9 passed, 3 failed in 0.34s.

The 9 passing checks covered:
- project-scoped + delimiter-safe target identity;
- routed ordinary/narrow/staggered multi-column rejection;
- a legitimate single-column layout not rejected;
- overlapping and duplicate text-related rectangles caught;
- standalone rectangle between surrounding text caught;
- remote artwork not treated as text-related.

The 3 failing safety expectations reproduced remaining gaps:
- one-line secondary column was not classified ambiguous;
- standalone redaction at end of text column was not classified ambiguous;
- standalone redaction at start of text column was not classified ambiguous.

Passing-subset command:
pytest -q /mnt/data/test_rl_mvp002_corrected_research_probe.py -k 'not one_line_secondary_column_should_be_rejected and not standalone_end_of_column_should_be_ambiguous and not standalone_start_of_column_should_be_ambiguous'

Result: 9 passed, 3 deselected in 0.17s.

Additional independent canonical probe:
python /mnt/data/rl_mvp002_canonical_probe.py

Result:
- hidden token absent from canonical text: PASS
- target marker occurs exactly once: PASS

Compile check:
python -m compileall -q /mnt/data/test_rl_mvp002_corrected_research_probe.py /mnt/data/rl_mvp002_canonical_probe.py
Result: PASS.

Probe environment: Python 3.13.5; pdfplumber 0.11.9; pypdf 5.9.0; reportlab 4.4.9. These are not the Backend's exact Python/parser versions. The remaining findings follow directly from the reviewed exact source predicates; the local libraries were used to generate and inspect adversarial geometry, not to claim a byte-for-byte exact-candidate suite run.

Backend-reported evidence reviewed but not adopted as independent execution: 45 focused and 88 full tests passing, compileall/diff/dependency checks passing on macOS/Python 3.11.

Tests not run and reason:
- Exact repository 88-test suite was not independently run because GitHub DNS/checkout was unavailable in the execution container.
- No Task-3 reference alignment, provider/model, evaluator/scoring, persistence, API/UI, deployment, private-data or real-document recall tests were run because they are outside RL-MVP-002 and/or not authorized.

## Verdict and required next action

CHANGES_REQUESTED. The corrected candidate resolves project identity and overlap/duplicate target construction, and fixes the routed multi-line column and between-lines standalone cases. It does **not** yet fully close the fail-closed ambiguity requirement for:
1. positioned secondary-column content that appears only once; and
2. standalone no-underlying-text redaction-like boxes at the start/end of a text column where visible context exists only on one side outside nearby_gap.

These can change model-visible context or falsely produce NO_REDACTIONS, so they can compromise downstream model comparison/reference alignment. Lead should keep 12698b92d883af658266d54a9223b5619dedc7ee unmerged and route a minimal additive Task-2 correction plus regression tests for those variants. Fresh QA and Research review should use the new exact SHA.

Independent review evidence (or not yet reviewed): This is a fresh Research/Evaluation review of exact corrected implementation 12698b92d883af658266d54a9223b5619dedc7ee; no prior verdict was carried forward.
Research / data approval evidence (or not approved / not applicable): Research-human approval NOT OBTAINED. D03-D06 remain open. Synthetic-only review; no scientific accuracy, Columbia data authorization or production readiness is claimed.
Known issues / risks / stale dependencies: Real-document detector recall/precision, hostile-input resource limits, parser sandbox/process isolation and production concurrency remain explicitly unvalidated/deferred. These are separate from the two Task-2 blockers above.
Affected roles / requested next action: Lead -> Backend/Codex for minimal additive correction; then fresh QA and Research review. Do not merge current candidate and do not start Task 3.
Last freshness check and relevant differences: Immediately before publication live main remained e769d2d48d2de2d402b23b504e2d933a5926d6ae / E0014. Branch head c37837669ce9e538a3afa8db0e25ef92cbbdd327 differs from implementation 12698b92d883af658266d54a9223b5619dedc7ee only by the Backend handoff commit.
Rollback or correction approach: This review branch contains only this handoff. If Backend publishes a new candidate, treat this handoff as stale; corrections should be additive on the isolated Task-2 branch, never force-pushed.
Publication: PUBLISHED on review/rl-mvp-002-research-corrected-e0014; not merged to main.
