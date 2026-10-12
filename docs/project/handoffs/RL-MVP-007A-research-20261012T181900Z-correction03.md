# RL-MVP-007A Correction 03 Research review

Task ID: RL-MVP-007A Correction 03 — Interprocess SQLite Migration Coordination  
Role / session label: Research / Evaluation independent reviewer  
UTC time: 2026-10-12T18:19:00Z  
State: READY_FOR_REVIEW  
Review verdict: **PASS FOR TASK-7A CORRECTION-03 RESEARCH/PROVENANCE SEMANTICS; NOT SCIENTIFIC VALIDATION**

Baseline integration SHA / decision epoch: `951f220511a2bf05ddd35a0f13b61f23e406e82f` / E0050.  
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `03d95ec8e6f280693550563f08ebaa65e844afb3`.  
Published Backend HEAD: `64784f752b7a4107e927b07cd8d31453e5e8e2e6`.

Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0050; DECISIONS.md; AGENT_HANDOFF.md; RESEARCH_METHOD.md; INTERFACES.md; owner-approved `docs/project/task_packets/RL-MVP-007A-CORRECTION-03.md`; prior Correction-02 QA/security CHANGES_REQUESTED; prior Correction-02 Research scoped PASS; Backend Correction-03 handoff; Task-4 deterministic source and immutable-attempt authority; Task-6 immutable qualitative evidence/null-score semantics; DEC-022 synthetic-only reference trust.

Authorization reference and permitted file/action scope: exact-SHA independent Research review and one unique Research handoff only. No implementation edits, merge, Task 7B/C/P/D, Podman/VM operations, downloads, private data, inference, spending, deployment or scientific-method approval.

## Freshness and scope

- Live GitHub `main` refreshed before review and before publication: `951f220511a2bf05ddd35a0f13b61f23e406e82f`, E0050.
- Exact implementation changes only the two Correction-03-authorized paths:
  - `src/redaction_lab/application/migration.py`
  - `tests/application/test_migrations.py`
- Implementation-to-published-Backend-head delta is one Backend handoff only.
- No Task-3 reference code, Task-4 prediction/source formulas, Task-6 evaluator/evidence/summary code, scoring formula, runtime lock or dependency file changed in this correction.

## Research findings

### Task-4 deterministic source/target identity — PASS

The exact candidate retains the existing Task-4 source identity derivation from project ID + actual redacted PDF SHA-256 + approved detector/canonicalizer versions. Target IDs remain deterministic from project/redacted-version/page/geometry/version.

Correction 03 does not touch `prediction_source.py` or those formulas. No migration lock value, PID, backup name or process identity enters Task-4 source/target identity.

### Task-4 immutable attempts / one-shot behavior — PASS

No Task-4 enqueue, claim, retry, timeout, IN_DOUBT, attempt persistence or model/provider provenance code changed.

The new migration coordination cannot create, retry or reinterpret prediction attempts.

### Reference isolation and DEC-022 — PASS

No Task-3 registry/alignment or reference-trust path changed.

Arbitrary reference uploads remain untrusted; DEC-022 remains limited to pre-registered synthetic byte-pinned pairs. Reference content remains outside Task-4 prediction inputs.

### Task-6 immutable evidence — PASS

No Task-6 evaluator, EvaluationStore, summary or evidence contract file changed.

The Backend candidate's two-process regression explicitly seeds Task-4/Task-6 evidence, runs two independent migration processes, reopens from a third process and compares stored source/fact rows byte-for-value equality. That is relevant preservation evidence, but remains Backend-authored test evidence rather than independent Research execution.

### NEEDS_REVIEW / unvalidated mock evidence — PASS

Exact candidate source still preserves:
- `UNVALIDATED_SYNTHETIC` source/judge validation state;
- `NEEDS_REVIEW`;
- `UNVALIDATED_MOCK_EVIDENCE`;
- no scientific completion claim for mock semantic evidence.

Correction 03 does not touch these semantics.

### Null verified/experimental scores — PASS

Task-6 current evidence still requires:
- `score_status=NONE`;
- `verified_score=None`;
- `experimental_score=None`;
- no score scale;
- no research-validation ID.

No numeric score path is introduced.

### Interprocess flock correction is infrastructure only — PASS

The new persistent database-specific flock serializes migration/backup operations across cooperating Redaction Lab processes. From Research scope, that strengthens durability of existing evidence but does not change the meaning, eligibility or scoring of any research record.

The lock file is not research evidence, reference provenance or a target identity input.

### Scientific approval state — unchanged

Correction 03 does not establish D03, D04, D05 or D06. It does not validate parser semantics, model quality, reference truth on real documents or aggregation methodology.

D03–D06 remain **NOT APPROVED**.

## Independent tests actually run

### Exact repository tests

Exact repository pytest was **NOT RUN independently** because this Research environment still cannot obtain a shell checkout from GitHub.

Backend-reported **445 full pytest passes** and its 41 migration / 82 application passes were reviewed but are not presented as independent Research evidence.

### Independent Research source-level probe

Executed a source-level reproduction of the unchanged identity/state invariants from the exact candidate:

- same project + same PDF SHA -> identical source identity;
- changed project -> different source identity;
- changed PDF SHA -> different source identity;
- same target geometry -> same target identity;
- changed target geometry -> different target identity;
- Task-6 score status remains NONE with null verified/experimental scores;
- unvalidated source/judge evidence remains UNVALIDATED_SYNTHETIC / NEEDS_REVIEW / UNVALIDATED_MOCK_EVIDENCE.

Result: **PASS assertions=7**.

This was an isolated reproduction, not byte-for-byte repository package execution.

## Tests not run / limitations

- exact focused/full pytest: not independently run due shell checkout restriction;
- real two-process flock tests: not independently executed by Research; these are primarily QA/security acceptance responsibilities;
- power-loss/fsync fault injection: not run;
- NFS/SMB/cloud-sync lock behavior: not run and outside qualified scope;
- Podman/VM/image operations: prohibited/not run;
- private/real PDFs: prohibited/not run;
- inference/provider calls/spending/deployment: prohibited/not run;
- D03–D06 human/scientific validation: not run/not approved.

## Residual limitations

1. Kernel flock is cooperative coordination for the qualified local POSIX environment, not protection from a hostile same-user process.
2. Real PDF-worker runtime remains intentionally unverified/fail-closed.
3. Parser semantic correctness remains unvalidated.
4. Clean-recipient portability remains a later Task-7P/7D gate.
5. Research does not certify the new interprocess lock security; QA/security must independently assess lock lifetime, inherited FD behavior, parent death and simultaneous-process races.

## Verdict

**PASS** for RL-MVP-007A Correction 03 Research/provenance semantics on exact implementation `03d95ec8e6f280693550563f08ebaa65e844afb3`.

The correction changes only migration coordination and does not alter Task-4 identities/attempts, reference isolation, DEC-022 truth, Task-6 evidence, NEEDS_REVIEW handling or null score semantics.

This PASS is **not** a QA/security verdict on flock correctness, not scientific validation, not merge authorization and not permission to begin Task 7B/C/P/D.

Independent review evidence: fresh Research review of exact SHA `03d95ec8e6f280693550563f08ebaa65e844afb3`; Backend-reported 445 passes were not treated as independent.  
Research/data approval evidence: synthetic/mock-only; no private data or inference; D03–D06 NOT APPROVED.  
Affected roles / requested next action: **Lead / Architect** should reconcile this Research PASS with the fresh independent QA/security review of the same exact SHA before any separately authorized merge.  
Rollback/correction approach: preserve branch history; any later defect requires additive correction and fresh exact-SHA review.  
Publication: PUBLISHED on `review/rl-mvp-007a-research-correction03-e0050`; not merged.
