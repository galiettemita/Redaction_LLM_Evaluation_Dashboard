# RL-MVP-006 Correction 03 Research review

Task ID: RL-MVP-006 Correction 03 — Canonical Summary Membership Integrity
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-12T02:15:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-6 CORRECTION-03 RESEARCH/EVALUATION SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17` / E0041
Candidate branch / exact commit SHA: `codex/rl-mvp-006-evaluator-summaries` / exact implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`; Backend publication head `fa2669c2dcb4dae3d69d214d4656369cbad0ed31`.
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0041; DEC-001/003/004/005/011-015/017/020/022; RESEARCH_METHOD.md; INTERFACES.md; owner-approved `docs/project/task_packets/RL-MVP-006-CORRECTION-03.md`; prior Correction-02 QA CHANGES_REQUESTED handoff on `0ef37c5`; prior Correction-02 Research PASS; latest Backend Correction-03 handoff.
Authorization reference and permitted file/action scope: exact-SHA independent Research review and one unique Research handoff only. No implementation edits, merge, Task 7, inference, model installation/download, spending, deployment, private data, or scientific-method approval.

## Freshness and candidate integrity

- Live GitHub main refreshed before review and before publication: `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17`, E0041.
- Read current AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md, approved Correction-03 packet, prior Correction-02 QA/Research handoffs, latest Backend handoff and exact candidate code/tests.
- Exact correction delta from Backend head `7226d23...` to implementation `0a0ce9e...` changes only:
  - `src/redaction_lab/evaluation_store.py`
  - `tests/test_evaluation_store.py`
- Implementation-to-published-Backend-head delta is one handoff file only.

## Research findings

### 1. Canonical membership integrity fix preserves authoritative provenance — PASS

The corrected `EvaluationStore.get_summary` verifies:
1. stored summary/project identity;
2. deterministic summary identity;
3. membership count;
4. exact persisted ordinal sequence;
5. exact ordered `(ordinal, subject_id)` binding against `enumerate(stored.requested_attempt_ids)`;

all **before** Task-4 attempt resolution, EvaluationRecord loading, SummaryRequestedMember reconstruction, sorting/normalization, or v2/v3 summary rebuild.

A swapped ordinal-to-subject binding therefore fails with a clear canonical-membership error rather than being normalized back into the stored subject set.

This strengthens the repository-authority chain without changing truth, evaluator, prediction, or scoring semantics.

### 2. Failed read is side-effect free — PASS

The new reader check raises on corrupted membership and performs no repair, rewrite, reorder, delete, or other mutation.

My independent disposable-SQLite probe reproduced:
- canonical membership read passes;
- swapping two whole subject bindings while retaining contiguous ordinals causes `canonical membership binding` rejection;
- the failed read leaves the tampered rows unchanged.

This is the correct behavior for immutable historical evidence: detect corruption, do not silently repair it.

### 3. Exact eligible reference sets remain unchanged — PASS

Correction 03 does not modify contracts, summary identity construction, evaluator logic, reference trust, or eligible-reference key semantics.

Therefore the Correction-02 properties remain intact:
- eligible reference identity is outcome-independent;
- source-fact availability does not change truth eligibility;
- exact reference provenance still defines the common truth set;
- changed target/reference/mapping/hash/method/trust still changes or invalidates comparability.

The new ordinal check affects only whether persisted membership can be trusted on reopen.

### 4. All-excluded summary semantics remain unchanged — PASS

The regression test uses an authoritative v3 all-excluded summary, which is the strongest direct exercise of the previously reported corruption gap.

The fix does not alter:
- requested_count;
- excluded_count;
- zero included evaluations;
- zero evaluated outcome counts;
- null rubric/evaluator/judge method provenance when no evaluations exist;
- empty eligible reference set;
- `score_status=NONE`;
- null verified/experimental scores.

An all-excluded summary still means **no evaluated Task-6 result**, not 0% accuracy.

### 5. NEEDS_REVIEW / mock-evidence semantics remain unchanged — PASS

Correction 03 does not touch evaluator, judge, contracts, source-fact, or summary-method logic.

Supplied synthetic source facts and mock judgments therefore remain:
- `UNVALIDATED_SYNTHETIC`;
- `NEEDS_REVIEW`;
- `UNVALIDATED_MOCK_EVIDENCE`;
- null numeric score channels.

No provisional semantic evidence becomes scientifically completed accuracy.

### 6. Null numeric score invariants remain unchanged — PASS

No score-related code changed.

Task-6 v3 summaries and evaluation records remain null-scored under the current synthetic/mock-only method:
- no verified score;
- no experimental score;
- no score scale;
- no research-validation ID.

### 7. Immutable v2/v3 historical evidence distinction remains explicit — PASS

The reader-side canonical membership check is schema-neutral and does not rewrite v2 or v3 payloads.

Downstream reconstruction still dispatches by stored schema version:
- historical v2 uses v2 reconstruction semantics;
- v3 uses v3 corrected semantics;
- no stored evidence is upgraded or reinterpreted by the membership fix.

This preserves historical evidence immutability.

### 8. Scientific meaning is unchanged — PASS with standing limitations

Correction 03 is an integrity correction, not a research-method change.

It does not alter:
- DEC-022 synthetic-only trust;
- D03 truth-confirmation method;
- D04 rubric/fact-judging method;
- D05 model protocol/roster;
- D06 aggregation/weighting;
- model identity assumptions;
- tokenizer/context comparability;
- human validation requirements.

D03-D06 remain NOT APPROVED.

## Independent tests actually run

### Exact repository execution

Exact repository test execution was **NOT independently run** in this Research environment because the container still cannot obtain a local checkout from github.com through shell DNS.

Backend-reported repository evidence was reviewed but not adopted as independent execution:
- 19 evaluation-store tests passed;
- 93 contracts/summary/store tests passed;
- 350 full repository tests passed in the final isolated run;
- compileall passed;
- dependency integrity passed;
- changed-file audit passed.

Backend also disclosed earlier host-storage-pressure failures:
- one chained run: 341 passed / 9 SQLite disk I/O failures;
- another chained run: 86 passed / 7 SQLite disk I/O failures;
- available disk was approximately 143–156 MiB;
- affected tests passed independently before/after cleanup.

From Research review, those failures are consistent with the disclosed host environment and do not by themselves establish a code defect. I do **not** count the Backend's later 350-pass result as independent Research evidence.

### Independent adversarial SQLite membership probe

Executed a disposable SQLite reproduction of the exact canonical-binding predicate:
- valid canonical rows: `[(0, attempt-a), (1, attempt-b)]` -> accepted;
- swapped whole subject ordinal assignment with ordinals still `0,1` -> rejected with `canonical membership binding`;
- failed read left tampered rows byte-for-logically unchanged.

Observed result:
- valid read unchanged: PASS
- swapped canonical binding rejected: PASS
- failed read non-mutating: PASS

This was an isolated reproduction of the exact reviewed predicate, not byte-for-byte repository execution.

Tests not run and reason:
- exact full/focused repository pytest: NOT RUN independently because shell GitHub checkout remains unavailable;
- included-evaluation whole-member permutation: NOT independently executed; source inspection shows the new check is disposition/evaluation-independent because it runs on `ordinal + subject_id` before included/excluded handling;
- real model/NLI inference: NOT RUN and prohibited;
- model downloads/installations: NOT RUN and prohibited;
- human annotation/adjudication/calibration/held-out validation: NOT RUN and requires designated Research Human approval;
- private/real data, provider calls, deployment, Task 7: NOT RUN and unauthorized.

## Nonblocking limitations

1. The new check protects repository reopen integrity only within the trusted local-store architecture; malicious trusted-process or raw-database compromise is not claimed to be contained beyond detection.
2. Backend's host disk was exhausted during some verification attempts. The later isolated passes reduce concern, but independent QA should distinguish reproducible code failures from resource-exhaustion failures and ideally rerun on a healthy filesystem.
3. Matching model names/config IDs still do not prove immutable model weights or provider artifact identity.
4. DEC-022 remains synthetic-only; real-document provenance remains unvalidated.
5. Source-fact/mock evidence remains scientifically unvalidated.
6. D03/D04/D05/D06 remain open.

## Verdict

**PASS** for RL-MVP-006 Correction 03 Research/evaluation semantics on exact implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`.

The correction is narrowly scoped and preserves all Correction-02 research semantics while adding the missing canonical membership-integrity invariant. No scientific-method interpretation changed.

This PASS is not scientific validation, D03-D06 approval, merge authorization, or Task-7 authorization.

Independent review evidence: fresh Research review of exact SHA `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`; Backend author tests were not treated as independent.
Research/data approval evidence: synthetic/mock-only; no private data or real inference; D03-D06 NOT APPROVED.
Affected roles / requested next action: Lead / Architect should reconcile this Research PASS with the separate fresh QA review of the same exact SHA, paying particular attention to independent filesystem-health testing, then seek separate owner merge authorization only if all gates pass. Do not begin Task 7.
Last freshness check: live main remained `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17` / E0041 immediately before publication.
Rollback/correction approach: preserve branch history; any defect requires additive correction and a new exact-SHA review. No force-push.
Publication: PUBLISHED on `review/rl-mvp-006-research-correction03-e0041`; not merged.
