# RL-MVP-003 DEC-022 Correction 02 — canonical-version provenance

State: CHANGES_REQUESTED; bounded correction under existing owner-approved DEC-022, not a new product decision.
Owner: Backend/Codex. Reviewers: QA and Research independently. Receiver: Lead.
Baseline: main 4146680a3d3efbbebee4f20f0039b9a302ed046f / E0029. Refresh HEAD/epoch before coding.
Failed exact candidate: 8a751d4af27c8daada1071ec6c9c4fce45581d61. Published Backend head: cd4cbfafbfe0152adc8c8e68a6cf337f20348814.
Independent QA FAIL: 45239a0ef8d2e99ee85590a69045fe02ed20da60.
Independent Research PASS for Task-3 trust/truth semantics: 4486f6c4c27acd5d4dba6b9eef9427942cfa2f1e. Research PASS does not override QA's provenance-integrity defect.
Deadline October 12, 2026; quality gates unchanged.

## Blocking issue

The synthetic registry pins both PDF byte hashes, project and document-version IDs but does not pin canonical-document-version IDs. _redacted_records_match_pdf rebuilds the canonical record using the caller's canonical_document_version_id, allowing a forged canonical ID to pass a self-fulfilling equality check. The public align_reference entry also accepts a caller-chosen reference_canonical_version_id, which can be written into a CONFIRMED mapping. This is incorrect provenance, even if the revealed words are unchanged.

## Required correction

1. Pin immutable application-owned expected redacted AND reference canonical-version IDs for the existing two_boxes pair in reference_registry.py, alongside existing hashes and IDs. Use literal values consistent with approved positive fixture cases; no dynamic trust enrollment or caller-derived IDs.
2. Before CONFIRMED, verify both canonical-version IDs against the resolved trusted pair. Rebuild the redacted canonical record with the pinned ID, not a caller-selected ID. Blank/forged/mismatched IDs must be NOT_SCOREABLE/null or a sanitized typed rejection, never CONFIRMED.
3. Confirmed mapping evidence must contain exactly the pinned canonical-version identities. Preserve existing byte-pair checks, target regeneration, strict two-sided alignment, exact punctuation/whitespace or null, hidden-text isolation, stable provenance and no reference in prediction manifests.

## TDD and publication

Write RED then GREEN tests for genuine pinned bytes with forged redacted canonical_document_version_id, forged reference_canonical_version_id, blank/missing canonical IDs and mismatched identities; positive approved-pair confirmation must preserve correct pinned IDs. Re-run forged target/document records, modified/swapped/unregistered PDFs, global alignment, repeated/adjacent targets, edge punctuation, partial/hidden reference and prediction isolation. Run focused/full pytest, compileall, dependency check, git diff --check. Record actual commands, results and NOT RUN.

Allowed files ONLY: src/redaction_lab/reference.py, src/redaction_lab/reference_registry.py, tests/test_reference.py, tests/test_reference_registry.py, and ONE new unique Backend handoff. No contracts, fixtures, canonicalizer, detector, dependencies, shared docs, UI, scoring, provider, database or Task 4. Use existing isolated Task-3 branch and additive commits; no force push, merge, paid services, private data or deployment. Stop if a broader authenticated persistence mechanism is needed. Publish exact new implementation SHA/handoff and obtain fresh independent QA and Research review. D03 scientific validity remains unapproved.
