# RL-MVP-006 Correction 03 independent QA review

Task ID: RL-MVP-006 Correction 03 — Canonical Summary Membership Integrity  
Role / session label: QA / Independent Reviewer  
UTC time: 2026-10-12T02:14:00Z  
State: READY_FOR_REVIEW  
Verdict: **PASS** for the exact reviewed Correction-03 software-integrity scope.

Baseline integration SHA / decision epoch: `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17` / E0041.  
Candidate branch / exact commit SHA: `codex/rl-mvp-006-evaluator-summaries` / `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`.  
Published Backend head: `fa2669c2dcb4dae3d69d214d4656369cbad0ed31`.  
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0041; DECISIONS.md; AGENT_HANDOFF.md; owner-approved `docs/project/task_packets/RL-MVP-006-CORRECTION-03.md`; prior Correction-02 QA CHANGES_REQUESTED `8b9ec308ce3a52b7dc87c040a4e36f14481e9026`; prior Correction-02 Research PASS `2024a37432918e27aab9754786d300e34fdf5da1`; DEC-022 synthetic-only trust; existing immutable v2/v3 summary contracts.
Authorization reference and permitted file/action scope: exact-SHA independent QA review and one unique QA handoff only. No application-code edits, merge, Task 7, inference, model installation/download, provider calls, spending, deployment, private data, or scientific-method approval.

## Freshness and scope

Live GitHub `main` was refreshed before review and immediately before publication and remained `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17`, E0041.

Exact implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc` changes only the two packet-authorized implementation/test paths:

- `src/redaction_lab/evaluation_store.py`
- `tests/test_evaluation_store.py`

The subsequent publication commit `fa2669c2dcb4dae3d69d214d4656369cbad0ed31` adds only the unique Backend handoff.

No contract, schema, summary builder, Task-4 store/worker, evaluator/judge, reference/prediction, dependency, migration, API/UI or Task-7 file is modified.

## Independent tests actually run

### Exact repository checkout attempt

Command:

`git clone --no-checkout https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /tmp/rlqa_c03`

Result:

`fatal: unable to access ... Could not resolve host: github.com`

Therefore the Backend-reported **350 full passes** and associated focused runs are not independent QA execution evidence.

### Independent SQLite canonical-membership probe

I independently reproduced the exact new reader invariant with a disposable SQLite database containing:
- one summary with canonical requested membership `("attempt-a", "attempt-b")`;
- two persisted summary-member rows at ordinals 0 and 1.

Observed before tamper:
- valid canonical binding -> accepted.

Then I performed a collision-safe persisted ordinal swap:
- ordinal 0 -> temporary -1;
- ordinal 1 -> 0;
- temporary -1 -> 1.

Persisted rows remained contiguous but became:
- ordinal 0 -> `attempt-b`;
- ordinal 1 -> `attempt-a`.

Applying the exact new invariant produced:
- `ValueError("stored summary canonical membership binding mismatch")`.

I then reread the SQLite rows and verified:
- failed read/probe did not change the tampered rows;
- persisted state remained byte/logically unchanged by the rejection path.

### Review-environment storage check

Command:

`df -h /tmp /mnt/data`

Observed in the independent QA environment:
- approximately 30 GiB available;
- no local disk-pressure condition.

This does not reproduce Backend's host, but it helps distinguish their reported storage exhaustion from a repository-logic failure.

## Correction-02 blocker — canonical ordinal-to-subject binding

**RESOLVED.**

The exact candidate now performs the new integrity checks in `EvaluationStore.get_summary` before Task-4 attempt resolution, EvaluationRecord loading, SummaryRequestedMember construction, sorting/reconstruction or any dependent authority use.

Order of checks is now:

1. parse stored SummarySnapshot;
2. verify stored summary/project row identity;
3. call `verify_summary_identity(stored)`;
4. verify persisted member count;
5. build exact persisted `(ordinal, subject_id)` tuple;
6. require actual ordinals to equal contiguous `0..N-1`;
7. require actual tuple to equal `tuple(enumerate(stored.requested_attempt_ids))`;
8. only then resolve Task-4 attempts and load included evaluations.

A swapped whole member row therefore fails before downstream normalization can erase the evidence.

The raised message contains the required phrase:
`canonical membership binding`.

## Included-evaluation membership permutations

**PASS by source-path inspection.**

The new invariant is disposition-independent and compares only canonical persisted ordinal/subject binding before reading any included EvaluationRecord.

Therefore swapping complete included rows across ordinals changes the ordered subject-ID tuple and fails the same canonical membership check.

If only `evaluation_id` values are swapped while subject IDs remain canonical, the existing downstream evaluation-to-attempt binding check still rejects the mismatch.

No separate included-row test was added by Backend, but the reviewed control flow covers both cases without branching on exclusion versus inclusion.

## Deterministic stored identity validation

**PASS.**

`verify_summary_identity(stored)` now runs before membership trust.

This preserves versioned v2/v3 deterministic identity verification and prevents the reader from using a corrupted stored payload merely because member rows appear valid.

The later full reconstruction/equality check remains intact, so the candidate adds an early stored-identity guard without weakening dependent-record verification.

## Failed reads remain side-effect-free

**PASS.**

The new checks occur entirely on rows loaded by read-only SELECTs. No repair, reorder, delete, UPDATE or transaction-writing path occurs before or after the canonical membership rejection.

Independent disposable-SQLite probe confirmed the tampered member rows remained unchanged after rejection.

This satisfies the Correction-03 Lead safeguard.

## Legitimate v2/v3 reopen and historical immutability

**PASS in source regression review.**

Correction 03 does not modify:
- v2/v3 schema/version logic;
- `rebuild_authoritative_summary_v2`;
- v3 requested-profile reconstruction;
- deterministic ID algorithms;
- member writer ordering;
- summary transaction logic.

The new canonical member check uses `stored.requested_attempt_ids`, which is already the canonical ordered membership persisted by the existing writer for both v2/v3 repository-authoritative snapshots.

No historical row rewrite or automatic version upgrade is introduced.

## Immutable membership / counts / partitions / rollback

No code in these paths changed.

Existing Correction-02 protections remain:
- member rows immutable under normal trigger protection;
- exact requested/included/excluded partitioning;
- count reconciliation;
- v3 exclusion-only semantics;
- null numeric score channels;
- atomic summary + member insertion rollback;
- foreign-key bindings to Task-4 attempts/evaluations;
- project-scoped authoritative reads;
- deterministic replay.

Correction 03 only strengthens the read-time integrity check.

## Task-4 regression assessment

**No Task-4 regression found.**

The exact implementation touches no Task-4 source/test file.

RunStore enqueue/claim/complete/resolve semantics are unchanged. The new check executes before Task-4 resolver calls and cannot dispatch, enqueue, retry or mutate prediction state.

## Backend host disk exhaustion / SQLite I/O failures

Backend disclosed two chained verification attempts with:
- host data volume at approximately 100% capacity;
- only 143–156 MiB free;
- failures reported uniformly as SQLite `disk I/O error` while creating disposable databases.

Backend then removed only task-created temporary pytest/bytecode directories and reran isolated commands, reporting:
- focused membership suite pass;
- evaluation-store file pass;
- combined suite pass;
- disposable DB selection pass;
- full suite **350 passed**.

QA does **not** adopt those pass counts as independent evidence because the exact repository could not be cloned here.

However, based on:
- the failure mode being storage-layer SQLite I/O rather than assertion/application failure;
- the same affected tests reportedly passing before and after;
- the correction itself being only a read-time tuple integrity check;
- the independent QA environment having ample free storage and the isolated SQLite probe succeeding;

I classify the disclosed disk-I/O failures as **environment-related verification failures**, not observed code defects.

They should remain documented in the Backend evidence, but they do not independently block this exact correction.

## Remaining limitations

- Exact repository pytest was NOT independently rerun because this environment cannot resolve `github.com` for checkout.
- Backend's 350 passes remain author evidence only.
- A malicious trusted process or direct SQLite-file owner remains outside the claimed trust model; this correction provides tamper detection on reopen, not database cryptographic authenticity.
- DEC-022 remains synthetic-only.
- Source-fact segmentation/mock judgments remain unvalidated and NEEDS_REVIEW.
- Numeric score channels remain null.
- D03–D06 scientific approvals remain open.
- No model/runtime/inference quality is established.

## Verdict

**PASS** for RL-MVP-006 Correction 03 QA scope on exact implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`.

The sole Correction-03 blocker is resolved: persisted canonical ordinal-to-subject membership corruption is rejected before normalization/reconstruction, including exclusion-only and included-member permutations, while failed reads remain side-effect-free.

No new blocking software defect was found in the authorized two-file correction.

This PASS is software QA only. It is not scientific validation, merge authorization, Task-7 authorization, deployment approval or evidence of real inference quality.

Tests not run and reason: exact repository focused/full pytest NOT RUN independently because GitHub checkout failed on DNS resolution. No real model/NLI inference, downloads, private data, provider calls, spending, deployment or D03-D06 scientific validation were run.

Independent review evidence: fresh QA review of exact SHA `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`; Backend self-review and 350 reported passes were not inherited.

Research / data approval evidence: QA grants none. Prior Research Correction-02 PASS does not substitute for a fresh Correction-03 Research review. D03-D06 remain NOT APPROVED.

Affected roles / requested next action: Lead / Architect should reconcile this QA PASS with the separate fresh Research review of the exact same SHA, then seek separate owner merge authorization only if all required gates pass. Do not begin Task 7.

Last freshness check and relevant differences: live `main` remained `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17`, E0041, immediately before publication; no superseding hold or decision changed this review.

Rollback or correction approach: preserve published history. If any later exact-SHA review identifies a defect, use an additive scoped correction; no force-push or historical row rewrite.

Publication: PUBLISHED on `qa/rl-mvp-006-correction03-0a0ce9e`; no application code modified, no merge, no Task 7, no inference, no model download, no spending, no deployment, no scientific-validation claim.
