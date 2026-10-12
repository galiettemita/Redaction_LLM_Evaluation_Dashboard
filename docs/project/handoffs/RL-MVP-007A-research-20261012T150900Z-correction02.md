# RL-MVP-007A Correction 02 Research review

Task ID: RL-MVP-007A Correction 02 — Isolated SQLite Migration Helper
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-12T15:09:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-7A CORRECTION-02 RESEARCH/PROVENANCE SEMANTICS; NOT SCIENTIFIC VALIDATION

Baseline integration SHA / decision epoch: `3366fcba7fe929230d3a7e8e2232ad9865f9a5e7` / E0049
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70`
Published Backend HEAD: `5b9523a0e52594ed07c1643eeb60d60a697b646e`

Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0049; DECISIONS.md; AGENT_HANDOFF.md; RESEARCH_METHOD.md; INTERFACES.md; controlling `docs/project/task_packets/RL-MVP-007A-CORRECTION-02.md`; prior Correction-01 QA/security CHANGES_REQUESTED; prior Correction-01 Research scoped PASS; Backend Correction-02 handoff; Task-4 deterministic source/attempt authority; Task-6 immutable qualitative evidence and null-score semantics; DEC-022 synthetic-only reference trust.

Authorization reference and permitted file/action scope: exact-SHA independent Research review plus one unique Research handoff only. No implementation edits, merge, Task 7B/C/P/D, Podman installation/execution, image build/download, VM provisioning, private PDFs, inference, provider/API calls, spending, deployment, or scientific-method approval.

## Freshness and exact scope

- Live GitHub `main` refreshed before review and before publication: `3366fcba7fe929230d3a7e8e2232ad9865f9a5e7`, E0049.
- Exact implementation commit `552b4b0` changes only the two owner-authorized paths:
  - `src/redaction_lab/application/migration.py`
  - `tests/application/test_migrations.py`
- Implementation-to-published-Backend-head delta is exactly one unique Backend handoff.
- No Task-3 reference code, Task-4 source/prediction code, Task-6 evaluator/evidence/summary code, scoring formula, worker runtime lock, dependency or schema-version file changed in this correction.

## Research findings

### 1. Task-4 deterministic source/target identity — PASS

Correction 02 does not modify `prediction_source.py`, Task-4 source-ID formulas, target-ID formulas, detector/canonicalizer versions, or `RunStore` source validation.

At the exact candidate SHA:
- source identity remains a deterministic function of project ID + actual redacted PDF SHA-256 + approved detector/canonicalizer versions;
- changed PDF bytes change source identity;
- changed project changes source identity;
- target identity remains deterministic from project/redacted-version/page/geometry/version;
- persisted sources are still revalidated against exact project and PDF-byte hash.

No migration helper field can mint or rewrite Task-4 source identity.

### 2. Task-4 immutable attempts and one-shot prediction behavior — PASS by unchanged code path

Correction 02 does not change:
- Task-4 enqueue;
- atomic claim;
- attempt creation;
- timeout/IN_DOUBT semantics;
- no-hidden-retry policy;
- immutable attempts;
- model/provider provenance.

The migration helper only changes how application schema migration is opened and backed up. It does not enqueue, retry or mutate prediction attempts.

### 3. Reference isolation / DEC-022 synthetic-only truth — PASS

No Task-3 registry/alignment or reference-trust file changed.

Arbitrary reference upload/pairing therefore remains untrusted and cannot become scoreable truth merely through application migration, document persistence or backup/reopen.

DEC-022 remains the sole checkpoint software-trust exception for pre-registered synthetic redacted/reference byte pairs.

Reference content remains structurally absent from Task-4 prediction-source/manifest paths.

### 4. Unsupported/uncertain truth remains null — PASS

No evaluator or reference-scoreability logic changed.

Missing, partial, unreadable, ambiguous, conflicting or unregistered target truth still yields unknown/null accuracy rather than zero or guessed reconstruction.

The migration helper does not inspect or transform PDF/reference semantics and introduces no route for inferred truth.

### 5. Task-6 immutable evaluation evidence — PASS

No Task-6 evaluator, EvaluationStore, summary, contract or evidence-table semantics changed.

At the exact candidate SHA:
- Task-6 authoritative records still retain immutable Task-4 attempt/source bindings;
- migration tests include legacy Task-4/Task-6 preservation/reopen evidence;
- schema migration remains additive rather than reinterpretive.

Correction 02 therefore does not alter the scientific meaning of previously stored Task-6 evidence.

### 6. NEEDS_REVIEW for unvalidated source facts/mock judgments — PASS

The exact candidate still requires:
- source facts / mock judge evidence to remain `UNVALIDATED_SYNTHETIC`;
- unvalidated semantic evidence to remain `NEEDS_REVIEW` / `UNVALIDATED_MOCK_EVIDENCE`;
- no supplied mock judgment to become scientifically completed accuracy.

No migration change alters this state machine.

### 7. Null numeric score channels — PASS

The exact candidate still requires Task-6 evidence to use:
- `score_status=NONE`;
- `verified_score=None`;
- `experimental_score=None`;
- no score scale;
- no research-validation ID.

Correction 02 creates no scoring path, numerical interpretation or research-validation claim.

### 8. Parent-process cwd isolation is a software-integrity correction, not a research-method change — PASS

The migration helper now moves SQLite relative-path handling into a fresh helper process. Parent migration code launches the helper through a fixed `sys.executable`, with `shell=False`, `cwd=None`, `close_fds=True`, and only the three required inherited descriptors.

The child may `fchdir` within its isolated process before SQLite opens the relative database basename, preserving WAL/hot-journal behavior without altering parent-thread relative path resolution.

Research-wise, this strengthens storage integrity for evidence without changing:
- source identity;
- reference eligibility;
- prediction protocol;
- evaluator semantics;
- aggregation method.

The separate QA/security review remains responsible for deciding whether all concurrency, descriptor, WAL/journal and backup invariants are sufficiently secure.

### 9. Scientific approval state remains unchanged — PASS

Correction 02 is infrastructure-only.

It does not establish:
- D03 automatic truth-validation accuracy;
- D04 rubric/judge validity;
- D05 model roster/protocol validity;
- D06 aggregation validity;
- parser semantic correctness;
- real-document scoring;
- clean-recipient portability.

D03-D06 remain NOT APPROVED.

## Independent tests actually run

### Exact repository execution

I could not independently execute the exact repository pytest suite because this Research environment still cannot obtain a shell checkout from GitHub.

Backend-reported **433 full passes** and related focused tests were reviewed but are not claimed as independent Research execution.

### Independent Research source-level probe

I independently reproduced the unchanged Task-4/Task-6 identity/state predicates from the exact candidate source.

Observed:
- same project + same PDF SHA -> identical deterministic source IDs;
- changed project -> changed source IDs;
- changed PDF SHA -> changed source IDs;
- same target geometry -> identical deterministic target IDs;
- changed geometry -> changed target ID;
- Task-6 current method remains `score_status=NONE` with null verified/experimental scores;
- unvalidated source/judge evidence remains `UNVALIDATED_SYNTHETIC` / `NEEDS_REVIEW` / `UNVALIDATED_MOCK_EVIDENCE`.

Result: **PASS assertions=8**.

This was an isolated source-level reproduction, not byte-for-byte package execution.

## Tests not run and reason

- exact focused/full repository pytest: NOT RUN independently because local shell GitHub checkout remains unavailable;
- migration helper concurrency/WAL/hot-journal/security adversarial suite: not independently executed by Research; those are primarily QA/security responsibilities and Backend-reported results are not inherited;
- separate-process simultaneous startup stress: NOT RUN; Backend also reports this was not separately stress-tested;
- power-loss/fsync fault injection: NOT RUN;
- Podman/VM/image qualification: NOT RUN and prohibited;
- real/private/restricted PDFs: NOT RUN and prohibited;
- model inference/downloads/provider calls/spending/deployment: NOT RUN and prohibited;
- D03-D06 human/scientific validation: NOT RUN and not approved.

## Residual limitations / acceptance boundaries

1. Separate independent process simultaneous startup remains a software/operations edge case for QA/security; Research makes no security PASS claim for it.
2. The helper is process isolation for cwd/path handling, not a sandbox against a compromised same-user host.
3. The PDF runtime remains intentionally unverified and fail-closed; no real parser authority or semantic correctness is established.
4. Clean-recipient-device portability remains a later Task-7P/7D gate.
5. DEC-022 remains synthetic-only.
6. D03/D04/D05/D06 remain NOT APPROVED.

## Verdict

**PASS** for RL-MVP-007A Correction 02 Research/provenance semantics on exact implementation `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70`.

The two-file migration correction does not alter Task-4 identities or attempts, reference isolation, DEC-022 trust, Task-6 immutable evidence, NEEDS_REVIEW treatment or null scores. Its effect is infrastructure/storage integrity only.

This PASS is **not** a QA/security verdict on helper concurrency, FD inheritance, journal recovery or backup lifecycle; that requires the separate independent QA/security review. It is also not scientific validation, merge authorization or permission to begin Task 7B/C/P/D.

Independent review evidence: fresh Research review of exact SHA `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70`; Backend-reported 433 passes were not treated as independent.
Research/data approval evidence: synthetic/mock-only; no private data or inference; D03-D06 NOT APPROVED.
Known risks: unqualified PDF runtime, no scientific parser validation, separate-process startup edge case pending QA/security, no clean-device acceptance.
Affected roles / requested next action: **Lead / Architect** should reconcile this Research PASS with the separate fresh QA/security review of the same exact SHA before any separately authorized merge. Do not begin Task 7B/C/P/D automatically.
Last freshness check: live main remained `3366fcba7fe929230d3a7e8e2232ad9865f9a5e7` / E0049 immediately before publication.
Rollback/correction approach: preserve branch history; any defect requires additive correction and fresh exact-SHA review. No force-push, no immutable-evidence rewrite.
Publication: PUBLISHED on `review/rl-mvp-007a-research-correction02-e0049`; not merged.
