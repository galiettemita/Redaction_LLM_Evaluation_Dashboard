# RL-MVP-003 — Trusted synthetic pairing, Correction 01 continuation

Status: OWNER-APPROVED for bounded implementation under DEC-022 (owner explicit "yes" 2026-10-08). NOT VERIFIED, NOT MERGED.
Owner: Backend/Codex. Reviewers: independent QA and Research. Receiver: Lead.
Baseline main: f478728311e526416e231f29cab333d025bdeee1 / E0027. Refresh current HEAD and epoch before writing.
Existing task branch: codex/rl-mvp-003-text-first-reference-alignment @ 2d79ee6a7d5ba2a06148ff257529faa50dfa06e1.
Backend rejected local candidate 80f9ee171c6923f9affb3a5259bf93105301e65a: NOT PUBLISHED, NOT VERIFIED; do not push unchanged.
Deadline October 12, 2026; no waived correctness gates.

## Approved synthetic-only trust

For the October 12 demonstration, only an application-owned, source-controlled allowlist of PRE-AUTHORIZED synthetic redacted/reference PDF pairs may establish fixture pairing. Pin literal SHA-256 digests for BOTH actual PDF byte streams, explicit project and document/version IDs, pair association, fixture case and generator provenance. Start with the smallest deterministic fully revealed fixture (such as two_boxes). Independently regenerate/verify pinned digests; do not automatically enroll newly generated or user-uploaded bytes. If fixture bytes differ across supported environments, stop rather than silently repin.

The resolver must be internal to the trusted application. Caller-created DocumentVersion, caller-provided hash, fixture name, registry object or metadata are never evidence of authority. Require actual redacted AND reference PDF bytes to match the SAME pinned pair and bind the redacted canonical project/version to that pair. Refine align_reference keyword-only interface to receive redacted PDF bytes if needed; do not modify immutable contracts. Forged records and swapped/unknown pairs must not CONFIRM.

For arbitrary user-uploaded/unregistered references, return NOT_SCOREABLE, exact_revealed_text=None, Accuracy unknown. Redacted-only prediction remains allowed. Fixture membership is necessary but not sufficient for CONFIRMED: full readable unique target truth, both available non-boundary global word anchors, coherent full-document visible context and exact source span are mandatory. A real document boundary alone permits absent-side evidence; geometry cannot override contradictory text.

Fix the independent edge punctuation/whitespace defect: if any covered leading/trailing space or punctuation cannot be recovered with reliable physical source bounds, return unconfirmed/null, never silently strip and CONFIRM. Preserve no reference/hidden text in prediction manifests, prompts, logs or public handoffs. This registry is synthetic test-fixture provenance only, not archival authenticity, protection against malicious trusted runtime code, or scientific D03 approval.

## Authorized files and stop conditions

On the existing isolated Task-3 branch, modify only src/redaction_lab/reference.py and tests/test_reference.py; create src/redaction_lab/reference_registry.py and tests/test_reference_registry.py; publish ONE new unique Backend task handoff. No contracts.py, fixtures.py, detector, canonicalizer, dependencies, other tests, shared docs, database, API, workers, UI, scoring, providers or deployment. Preserve the rejected local candidate in a named stash/commit/worktree; selectively reuse only safe changes. Stop if additional files, broader authenticated persistence or a new trust assumption are needed. No force push, merge, Task 4, paid services or private data.

## Test-first acceptance

RED then GREEN: fabricated DocumentVersion with matching hashes, forged caller registry/case, unknown pair, swapped reference, one-byte PDF alteration, wrong redacted PDF, cross-project/version, unstable pins; both directions of one-sided global support, interior geometry fallback, repeated anchors, adjacent targets, wrong release with local neighbors, true boundaries, covered edge punctuation/whitespace, partially hidden reference, hidden selectable text, malformed PDF, no-reference input and prediction isolation. A registered, byte-identical fully revealed fixture may CONFIRM only with complete reliable text evidence.

Run focused/full pytest, compileall, dependency check and git diff --check; report exact RED/GREEN commands, counts, NOT RUN and limitations. QA independently checks pinned hashes and forged-input attacks; Research checks truth/null semantics and D03 limits. Publish exact new implementation SHA, branch head, changed paths and handoff. Fresh independent QA and Research review required; owner merge authorization remains separate.
