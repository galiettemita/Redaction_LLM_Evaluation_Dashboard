# RL-MVP-006 — Correction 03: canonical summary membership integrity

**OWNER APPROVED** 2026-10-11. **Coordination epoch E0041.** Scope is Backend/Codex implementation on existing Task-6 branch, followed by mandatory fresh independent QA and Research review. This packet approves no merge, Task 7, model inference/downloads, spending, deployment, private data, or scientific method.

**Baseline at approval:** `b81ae54e0326c633a6e43b6cce6d3fe8af117db6` / E0040. **Rejected candidate:** `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`; Backend published HEAD `7226d23fcd2d83568e3d9c561ea75d3a8289468d`. **QA finding:** `qa/rl-mvp-006-correction02-0ef37c5` at `8b9ec308ce3a52b7dc87c040a4e36f14481e9026`: CHANGES_REQUESTED — a swapped canonical summary-member ordinal survives reopen due to normalization. Research `review/rl-mvp-006-research-correction02-e0040` at `2024a37432918e27aab9754786d300e34fdf5da1`: scoped PASS, not scientific approval. Read AGENTS and current coordination records and refresh main/holds before action.

## Exact authorized implementation scope

Modify ONLY:
- `src/redaction_lab/evaluation_store.py`
- `tests/test_evaluation_store.py`

Add ONE unique `docs/project/handoffs/RL-MVP-006-backend-<UTC>-correction03-<shortSHA>.md` after implementation. No other file, dependency, schema, version, fixture, prediction, evaluator, reference, UI or Task 7 changes. Preserve existing Backend branch history; additive normal commits only, no force-push. Stop if wider changes or migrations prove necessary.

## Required integrity fix

In `EvaluationStore.get_summary`, after loading/parsing and validating the stored summary/project identity but **before** Task-4 attempt resolution, EvaluationRecord loading, `SummaryRequestedMember` construction, any sorting, or v2/v3 reconstruction:

1. Verify stored summary identity against the stored signed/normalized payload under the appropriate versioned v2 or v3 identity rules as far as available without external reconstruction. Do not mistakenly treat an unverified caller value as authority. If current code's identity check requires dependent records, do not bypass it: retain full downstream verification and enforce the new membership binding first.
2. Retain existing membership count/contiguous-ordinal checks.
3. Require exact ordered bindings `tuple((ordinal, row["subject_id"]) for ordinal,row in enumerate(member_rows)) == tuple(enumerate(stored.requested_attempt_ids))`, and verify actual persisted row ordinal equals its expected ordinal. Compare ordered tuples directly — NEVER sorted IDs, sets, or normalized-after-rebuild sequences.
4. Reject swapped ordinal-to-subject associations, including whole subject/evaluation or exclusion membership swaps, by raising a clear `ValueError` containing `canonical membership binding`.
5. Preserve all disposition, evaluation-to-attempt, exclusion reason, membership count, project, deterministic identity, compatibility, immutability and versioned reconstruction checks.
6. **Lead read-only safeguard:** corrupted rows must be rejected **without repairing, rewriting, reordering, deleting or otherwise mutating** database rows. Retrieval remains side-effect-free. Successful valid reads unchanged.

The approved writer already inserts rows ordered as `snapshot.requested_attempt_ids`; this correction is a strict reader integrity invariant, not a new writer algorithm.

## Required TDD and adversarial regression

First author a failing test in the existing evaluation-store tests against `0ef37c5`. Use a disposable SQLite DB with at least two resolver-authenticated compatible Task-4 attempts and an authoritative v3 all-excluded summary. Verify valid read before tampering and canonical persisted binding. Drop only the member no-update trigger in the disposable DB; swap complete member-row ordinal assignments with a collision-safe temporary index; demonstrate raw SQL still returns contiguous ordinals with inverted subjects. Then require `get_summary` to raise `ValueError` containing `canonical membership binding`. Verify bytes/rows unchanged by failed read. Also test swapping complete included subject/evaluation bindings if practical within the two-file scope.

Preserve/re-run: untampered multi-member v3 reopen; reversed request order deterministic replay; single/multi exclusion-only summaries; included/excluded exact partitions; tampered count/disposition/exclusion reasons/evaluation-to-attempt; atomic rollback; ordinary immutability triggers; legacy v2 identity and byte-for-byte reopen without upgrade; v3 null score/nullable method-provenance; full Task 1–6 regression suite.

Run and report actual focused ordinal/membership subset, full evaluation-store tests, combined contracts/summary/store suite, full pytest, compileall, dependency integrity (use established uv pip check if pip unavailable), `git diff --check`, disposable-database rollback and v2/v3 reopen probes. Audit implementation delta is exactly/only the two authorized source/test paths and handoff publication adds only unique handoff. Include every command/result and tests NOT RUN.

## Stop conditions and handoff

Stop for incompatible change to live main/decision epoch, scope enlargement, valid historical writer rows violating canonical binding, inability to verify identity without weakening provenance, schema/version migration, any unresolved regression, or any violation of DEC-022 synthetic-only truth, Task-4 immutability, reference isolation or null numeric scores.

Publish implementation SHA and subsequent branch HEAD separately with one Backend handoff recording actual evidence, limitations and next receivers QA/Research. Fresh independent exact-SHA QA AND Research review required; author-reported tests are not independent verification. Task 6 integration into main requires separate explicit owner authorization. Dates are checkpoints rather than permission to relax gates.
