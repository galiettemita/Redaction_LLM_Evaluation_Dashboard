# RL-MVP-003 Correction 01 — owner-approved

Status: APPROVED for bounded implementation, NOT VERIFIED or MERGED.
Owner: Backend/Codex. Reviewers: independent QA and Research. Receiver: Lead.
Baseline main: 7c001af1d25b1dd546d5c4754384a0af71c441b6 / E0025. Refresh current HEAD/epoch before coding.
Reviewed failed candidate: 931fb1c0012d3b530b837f204d922f0aaa95a602; published Backend branch head 2d79ee6a7d5ba2a06148ff257529faa50dfa06e1.
QA FAIL: qa/rl-mvp-003-review-931fb1c @ 007eb0e242a3f43cc01843d0713442a7f02e1e1f.
Research CHANGES_REQUESTED: review/rl-mvp-003-research-e0025 @ 6406a25012801c3850a10e65c4dc8a11036b7c5a.
Authorization: explicit product-owner "yes" on 2026-10-08 approving three corrections and a narrow callable-interface refinement. No scientific D03 approval.

## Required changes

1. Global alignment: require agreement from BOTH available textual sides, not left OR right. Only a genuine document boundary can exempt an absent side. Geometry/sentinel evidence must not substitute for conflicting or missing interior textual support.
2. Trusted reference identity: refine the reference.py callable interface to accept an existing trusted DocumentVersion record, without changing contracts.py. Check reference role, project, version ID and SHA-256 of the actual reference PDF bytes. Caller-supplied IDs or a newly constructed untrusted record do not establish authority. Require the caller to provide an authenticated/trusted immutable record; if that trust cannot be established in this stateless scope, do not CONFIRM. Also require deterministic full-document monotonic coherence of visible redacted-context words, not merely two local neighbors. No invented similarity percentage/threshold. If document pairing cannot be reliably established, return unconfirmed and escalate the specific missing boundary.
3. Exact target span: preserve covered leading/trailing whitespace and punctuation only when physical source bounds can be proven. Otherwise return NOT_SCOREABLE with null exact_revealed_text; never silently strip and claim complete revelation.

## Tests

TDD RED then GREEN on: both directions of one-sided global conflict; interior geometry fallback; true document boundaries; wrong reference with same local neighbors but unrelated global context; trusted-record SHA/role/project/version mismatch; unavailable/untrusted binding; target-edge whitespace; exact punctuation; repeated/adjacent targets; partial and hidden selectable reference; no reference; prediction isolation. Run focused and full pytest, compileall, dependency check and git diff --check; report actual tests and NOT RUN.

## Scope and stops

Allowed changes: src/redaction_lab/reference.py, tests/test_reference.py and one unique Backend handoff on existing isolated Task-3 branch. No contracts.py, detector, canonicalizer, fixtures, other tests, dependencies, scoring, UI, model/provider calls, paid services, private data, cloud or deployment. Stop for needed broader pairing/transactional contract change or false-CONFIRMED risk. Publish exact implementation SHA and handoff head, tests and limitations. Fresh QA and Research review required. No merge or Task 4. Deadline October 12, 2026, without waived gates.
