# RL-MVP-007CP Assembly Research / Evaluation independent review

Task ID: RL-MVP-007CP Assembly — bind reviewed frontend assets  
Role / session label: Research / Evaluation independent reviewer  
UTC time: 2026-10-13T19:33:00Z  
State: READY_FOR_REVIEW  
Review verdict: **PASS FOR ASSEMBLY RESEARCH/PROVENANCE SEMANTICS; NOT SCIENTIFIC VALIDATION; NOT FINAL TASK-7D ACCEPTANCE**

Baseline integration SHA / decision epoch: `29cf5cc6a569643d906616ad3937711ff5397aec` / E0058  
Exact implementation SHA reviewed: `0d7a2b56fabd13bb6a2471247b8dcc266ccab093`  
Published branch HEAD: `91808b75896e7f9fc41d1f23e53b05fbddf46542`  
Source requirements: AGENTS.md; CURRENT_STATE.md E0058; DECISIONS.md; AGENT_HANDOFF.md; frozen API v0.1; `docs/project/task_packets/RL-MVP-007CP-ASSEMBLY.md`; previously reviewed Frontend `06b2404...` and static-hosting `9648f2b...`.
Authorization: exact-SHA independent Research review and one unique Research handoff only. No implementation edits, merge, deployment, Podman/VM, private data, real PDF processing, inference, paid calls or final Task 7D acceptance.

## Exact scope and freshness

- Live `main` refreshed before review and before publication: `29cf5cc6a569643d906616ad3937711ff5397aec`, E0058.
- Exact implementation changes only:
  - `packaging/local/manifest.json`
  - `tests/packaging/test_local_preflight.py`
  - `tests/packaging/test_local_static.py`
- Implementation-to-published-head delta is only the unique Packaging assembly handoff.
- No Task-3, Task-4, Task-6, API, static-host source, frontend source, runtime lock, dependency or scoring file changed.

## Research findings

### 1. Reviewed frontend assets are bound without changing research semantics — PASS

The manifest now binds exactly the three previously reviewed frontend build artifacts with the packet-authorized SHA-256 values, byte sizes and MIME types. `frontend_available` is set true only at the manifest level; existing preflight/static verification remains responsible for validating the exact bundle before serving.

This changes delivery availability, not truth, prediction or evaluation semantics.

### 2. Optional reference isolation remains intact — PASS

The assembly does not change upload, prediction, reference registry or mapping code.

The integrated UI still states that adding a reference does not establish trustworthy revealed text or verified accuracy, and the API client requires upload `truth_status === "UNKNOWN"`.

No assembly change can enroll a reference into DEC-022 trust or expose reference content to prediction.

### 3. UNKNOWN truth / no fabricated predictions or targets — PASS

The assembled website continues to require:
- `truth_status === "UNKNOWN"`;
- empty `targets`;
- null target/document/model summaries;
- `score_status === "NONE"`;
- null verified and experimental scores.

The assembly tests exercise the live same-origin API and explicitly confirm UNKNOWN truth, empty targets and null score channels while the worker runtime is unqualified.

No prediction text, target reconstruction or browser-calculated score is introduced.

### 4. NEEDS_REVIEW and READY semantics remain correct — PASS

The integrated frontend still preserves the contract's `NEEDS_REVIEW` state and renders it as unresolved, with predictions/scores unavailable.

Document READY/AVAILABLE remains presentation of document-processing completion only. The UI explicitly states that document readiness is not prediction success and does not interpret it as accuracy.

### 5. Task-4 one-shot provenance remains unchanged — PASS

The assembly modifies only manifest/tests. It does not alter Task-4 source identity, enqueue/claim, prediction attempts, timeout/IN_DOUBT or retry policy.

Refresh/recovery remains read-only and does not create a new run.

The assembly's runtime-unverified test preserves 503 with the job still ACCEPTED and source null, so no Task-4 authority is fabricated by successful website loading.

### 6. Task-6 immutable/null-score semantics remain unchanged — PASS

No Task-6 evaluator, EvaluationStore, summary or evidence contract changes exist in this candidate.

The assembled UI continues to reject non-null score channels and non-null summaries under frozen API v0.1. Mock/source-fact scientific status remains unchanged: unvalidated evidence stays NEEDS_REVIEW / UNVALIDATED_MOCK_EVIDENCE in Task 6.

No scientific score is created by assembly.

### 7. Assembly makes the reviewed frontend genuinely available, but this is not scientific validation — PASS with explicit limits

The manifest now has `frontend_available:true` because exact reviewed artifacts are bound. This establishes website asset availability under existing static verification, not:
- qualified PDF parsing;
- real prediction/inference;
- validated reference truth;
- scientific scoring;
- clean-recipient-machine acceptance.

The runtime remains unverified and the system remains DEGRADED for processing/inference.

## Independent evidence actually run

Exact repository pytest/browser execution: **NOT RUN independently** in this Research environment because direct shell checkout from GitHub remains unavailable. Backend-reported **594 full pytest passes**, focused 98 tests and Chrome/browser evidence are implementer evidence only.

Independent exact-source checks against `0d7a2b5...` through GitHub:
1. manifest frontend inventory present and marked available;
2. no truth-status promotion in assembly files;
3. UI requires `truth_status === UNKNOWN`;
4. UI requires null verified/experimental scores;
5. UI requires null target/document/model summaries;
6. UI requires empty targets;
7. NEEDS_REVIEW remains explicit;
8. UI states READY is not prediction success;
9. reference upload warning remains explicit;
10. assembly tests preserve RUNTIME_UNVERIFIED;
11. tests preserve ACCEPTED/no-source behavior;
12. recovery copy preserves no-new-run semantics.

Result: **12/12 Research/provenance checks PASS**.

## Tests not run / limitations

Not independently run:
- 98 focused / 594 full repository pytest;
- Chrome headless browser render;
- local HTTP upload/status/restart integration;
- static Host/Origin/framing/symlink adversarial suite;
- manual accessibility;
- clean recipient machine;
- qualified PDF worker;
- real/private PDFs;
- model inference;
- D03-D06 scientific validation.

These are either QA/security, implementer, later Task-7D, or prohibited activities for this review.

## Residual limitations

1. This review does not certify static-path/HTTP security; independent QA/security must do that.
2. Website loading does not imply qualified PDF processing or prediction.
3. No real model result or scientific score can be produced while runtime/model gates remain closed.
4. Clean-recipient acceptance and final Task 7D remain pending.
5. D03/D04/D05/D06 remain NOT APPROVED.

## Verdict

**PASS** for RL-MVP-007CP Assembly Research/provenance semantics on exact implementation `0d7a2b56fabd13bb6a2471247b8dcc266ccab093`.

The assembly binds the reviewed frontend bytes without weakening reference isolation, DEC-022, Task-4 one-shot provenance, Task-6 immutable/null-score semantics, NEEDS_REVIEW or UNKNOWN truth handling.

This PASS is not a QA/security verdict, scientific validation, merge authorization, deployment approval or final Task 7D acceptance.

Independent review evidence: exact-SHA source inspection; Backend-reported tests/browser evidence were not inherited.  
Next receiver: **Lead / Architect**, to reconcile this Research PASS with the separate independent QA/security exact-SHA handoff before any owner-authorized merge.  
Rollback/correction: preserve history; any demonstrated defect requires additive correction and fresh exact-SHA review.  
Publication: PUBLISHED on `review/rl-mvp-007cp-assembly-research-e0058`; not merged.
