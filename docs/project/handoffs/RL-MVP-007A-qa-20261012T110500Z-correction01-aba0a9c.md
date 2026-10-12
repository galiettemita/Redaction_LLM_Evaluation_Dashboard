# RL-MVP-007A Correction 01 independent QA / security review

Task ID: RL-MVP-007A Correction 01 — Filesystem Confinement and Trusted Worker Authority  
Role / session label: QA / Independent Reviewer  
UTC time: 2026-10-12T11:05:00Z  
State: CHANGES_REQUESTED  
Verdict: **FAIL / CHANGES_REQUESTED** for exact implementation `aba0a9cfba2e5216a09ce82c12590f063203db53`.

Baseline integration SHA / decision epoch: `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595` / E0048.  
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `aba0a9cfba2e5216a09ce82c12590f063203db53`.  
Published Backend HEAD: `4ac02c1e3156c572608c499597f70df5623686cb`.  
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0048; DECISIONS.md; AGENT_HANDOFF.md; owner-approved `docs/project/task_packets/RL-MVP-007A-CORRECTION-01.md`; original QA/security CHANGES_REQUESTED `a6ca3d35c2cb95538c24f1ce4c7a2bbaf334e673`; original Research scoped PASS `dc2d975b9d427921ecdc62765d684aa83b1b9cc2`; DEC-022 synthetic-only reference trust; Task-4 one-shot source/prediction authority; Task-6 immutable qualitative evidence/null-score semantics.  
Authorization reference and permitted file/action scope: exact-SHA independent QA/security review plus one unique QA handoff only. No application-code edits, merge, Task 7B/C/P/D, Podman install/run, image build/download, VM provisioning, private PDFs, inference, provider calls, spending, deployment or scientific-method approval.

## Freshness and scope

Live GitHub `main` was refreshed before review and immediately before publication and remained `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595`, E0048.

The exact implementation commit changes exactly the fourteen E0048-authorized implementation/test paths:
- `src/redaction_lab/application/paths.py`
- `src/redaction_lab/application/artifact_store.py`
- `src/redaction_lab/application/isolation.py`
- `src/redaction_lab/application/document_worker.py`
- `src/redaction_lab/application/migration.py`
- `src/redaction_lab/store.py`
- `packaging/pdf-worker/README.md`
- `tests/application/test_paths.py`
- `tests/application/test_artifact_store.py`
- `tests/application/test_isolation.py`
- `tests/application/test_document_worker.py`
- `tests/application/test_migrations.py`
- `tests/test_worker.py`
- `tests/test_prediction_source.py`

Implementation-to-published-Backend-head delta is one unique Backend handoff only.

No schema version, runtime lock, Task-3, Task-6, scoring, model, dependency or shared coordination file was changed by the implementation commit.

## Independent tests actually run

### Exact repository checkout attempt

Command:

`git clone --filter=blob:none --no-checkout https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /mnt/data/rlqa_007a_c01`

Result:

`fatal: unable to access ... Could not resolve host: github.com`

Therefore Backend-reported **29 focused path/artifact/migration**, **51 authority/isolation**, **55 application**, **14 migration**, and **418 full** pytest passes are author evidence only and are not presented as independent QA execution.

GitHub Actions lookup for exact implementation `aba0a9c...` returned no workflow runs.

### Independent process-wide cwd/thread-safety probe

I independently reproduced the exact `_anchored_working_directory` mechanism used by the candidate:
- module-level `RLock`;
- save current cwd descriptor;
- `os.fchdir(database_directory_fd)`;
- execute work;
- restore original cwd in `finally`.

While the migration thread held the anchored cwd, a second unrelated thread performed a normal relative-path write.

Observed:
- unrelated thread observed cwd = the database directory;
- its relative write landed inside the database directory;
- it did not land in the original process cwd;
- cwd was restored after the migration context exited.

Independent output:
- `landed_in_dbdir=True`
- `landed_in_original=False`
- `cwd_restored=True`

An exception-path probe also confirmed that the candidate's `finally` pattern restores cwd after an exception.

This isolates the defect below: restoration works, but process-wide cwd mutation is visible to unrelated threads while the migration is active.

## Original QA high-severity finding 1 — filesystem symlink confinement

**RESOLVED for the reviewed artifact/path lifecycle.**

The correction now:
- rejects explicit symlinked application-home components before normalization;
- preflights all managed directories before creation/mutation;
- traverses directories with descriptor-relative `O_DIRECTORY | O_NOFOLLOW`;
- holds verified artifact/temporary directory descriptors;
- creates SHA/prefix directories descriptor-relatively;
- publishes using no-clobber `os.link(..., src_dir_fd=..., dst_dir_fd=..., follow_symlinks=False)`;
- rejects cross-filesystem publication;
- reads regular files through verified parent descriptors and no-follow leaf opens;
- performs temporary cleanup/orphan discovery through descriptor-anchored directories;
- fails recovery before deletion if an unsafe symlink entry is encountered.

Source review and candidate tests directly cover:
- symlinked home leaf/intermediate;
- managed-root symlinks;
- `sha256`, digest-prefix and leaf symlinks;
- digest-prefix replacement race;
- stale-temp cleanup with malicious symlink present;
- no-mutation preflight ordering.

I found no remaining path-traversal escape in the artifact lifecycle under the stated trusted-host/same-user threat model.

## Original QA high-severity finding 2 — mocked/custom worker authority

**RESOLVED within the declared trusted-host process boundary.**

The production `DocumentWorker` constructor now accepts only:
- `ApplicationStore`;
- `ArtifactStore`.

It no longer accepts a worker, runner, policy, result object or source material.

On every production run it constructs `ApplicationPdfWorker`, whose policy comes from the fixed install-owned runtime lock and whose runner is the concrete `SubprocessPodmanRunner`.

Runtime policy parsing and runtime inspection occur **before** `claim_next`, so the shipped `runtime_verified:false` lock fails before:
- job claim;
- owner/runtime evidence assignment;
- Task-4 source insertion;
- application READY state;
- prediction dispatch.

The prior `RunStore(..., source_deriver=...)` constructor injection is removed. Public `ingest_redacted_pdf` retains the legacy deterministic byte-derived source path.

Injectable protocol testing has been renamed `NonAuthoritativePdfWorkerProbe`; passing it to `DocumentWorker` raises `TypeError` and leaves application/Task-4 state unchanged.

`RunStore._persist_prediction_source` remains an internal underscore persistence primitive used by the application-owned sequence. It accepts a structurally validated `PredictionSource`, but arbitrary same-process Python execution is explicitly outside the approved threat model. I therefore do not treat that private helper alone as an untrusted application-caller bypass in this review.

## Migration and backup confinement

The correction materially improves database/backup path handling:
- database parent and backup directory are preflighted before mutation;
- both are opened through no-follow directory descriptors;
- the database leaf is opened `O_NOFOLLOW`;
- SQLite's relative database open is checked against the already-open inode;
- backup files are created `O_EXCL` via the verified backup directory descriptor;
- backup population and verification use the already-open descriptor via `/dev/fd`;
- failed backup integrity removes only the newly created backup via `dir_fd`;
- backup filename collisions do not overwrite existing files;
- database-parent replacement stays anchored to the original directory inode;
- migration failure preserves verified backup and rolls back the schema transaction.

I found no direct source path that opens, overwrites or unlinks a backup outside the verified backup descriptor.

## BLOCKING finding — SQLite migration uses process-wide `fchdir`, so unrelated threads can have relative I/O redirected

Severity: **High / process-wide filesystem integrity and thread-safety defect**.

The E0048 packet explicitly required review of:
- thread safety;
- process-wide effects;
- relative-path operations;
- exception restoration;

and stated that if stdlib SQLite semantics could not be made safe, implementation should stop for a scope amendment rather than rely on an unsafe fallback.

The candidate's `_anchored_working_directory` uses:

`os.fchdir(database_directory_fd)`

for the full synchronous SQLite migration/backup sequence.

The module-level `_CWD_LOCK` only serializes **other callers that also acquire that exact lock**. It cannot prevent unrelated application/library threads from performing relative-path operations while cwd points at the database directory.

Independent adversarial reproduction confirms that an unrelated thread's relative write is redirected into the database directory during the migration window.

This is a real process-wide effect, not a hypothetical restoration bug.

### What does work

The candidate correctly restores cwd:
- after normal exit;
- after exceptions.

Two simultaneous Redaction Lab migrations using this module are serialized.

### What remains unsafe

Any unrelated thread that does not know about `_CWD_LOCK` can:
- open/read/write the wrong relative file;
- create files in the application database directory;
- resolve a relative config/log/temp path against the wrong directory.

The migration context spans SQLite open, table inspection, backup, migration scripts and integrity checks, so this is not a one-instruction window.

Backend itself records the operational limitation: application startup must remain single-threaded/trusted. That restriction is not an enforceable property of this module and is not equivalent to process-safe filesystem confinement.

### Required correction

Do not mutate process cwd as part of the security boundary.

Use a SQLite access strategy that remains descriptor/inode anchored without `chdir/fchdir`, or stop and request a scope/platform amendment if supported stdlib/macOS SQLite cannot provide that guarantee.

At minimum add a regression with:
- migration running in one thread;
- an unrelated second thread performing a relative file operation without using `_CWD_LOCK`;
- proof that the second thread's path resolution remains unchanged.

The current implementation fails that requirement.

## Other reviewed responsibilities

### Unverified runtime

PASS: shipped runtime lock cannot create `RuntimePolicy`; `DocumentWorker.run_once` fails before job claim or Task-4 persistence.

### Task-4 one-shot behavior

No enqueue/claim/attempt/timeout/retry logic changed. The correction affects source-ingestion authority only. No automatic prediction dispatch is added to document processing.

### Task-6 immutable evidence

No Task-6 evaluator/evaluation-store/summary files changed. Existing source facts/mock judgments remain UNVALIDATED_SYNTHETIC / NEEDS_REVIEW; numeric verified/experimental score channels remain null.

### Reference trust

No Task-3 trust path changed. Arbitrary reference uploads remain untrusted and DEC-022 remains synthetic-only.

## Residual risks / limitations

1. Real Podman/VM/image qualification remains unrun and prohibited; the runtime lock is intentionally unusable.
2. Host structural verification still does not independently prove isolated parser semantic correctness.
3. Same-process malicious Python/trusted-host compromise remains outside the declared threat model.
4. Clean-recipient-device portability and runtime packaging are later gates.
5. Exact repository pytest could not be independently rerun because shell GitHub checkout remains DNS-blocked.
6. Backend's 418-pass report is not independent QA evidence.

## Verdict

**FAIL / CHANGES_REQUESTED** for exact implementation `aba0a9cfba2e5216a09ce82c12590f063203db53`.

Both original high-severity QA findings are materially resolved:
1. descriptor-anchored filesystem confinement closes the prior symlink/path escape;
2. production composition removes caller worker/source-deriver injection and fails unverified runtime before durable authority.

A new/remaining E0048 blocker exists in the migration security amendment: process-wide `fchdir` redirects unrelated threads' relative filesystem operations during migration.

Do not merge this SHA and do not begin Task 7B/C/P/D.

Tests not run and reason: exact repository focused/full pytest NOT RUN independently because direct shell GitHub checkout failed DNS resolution. Podman/VM/image operations, real/private PDFs, inference, provider calls, spending, deployment, recipient-device acceptance and D03-D06 scientific validation were not run and remain unauthorized.

Independent review evidence: fresh QA/security review of exact implementation `aba0a9cfba2e5216a09ce82c12590f063203db53`; Backend author-reported tests were not inherited.

Research / data approval evidence: QA grants none. Separate Correction-01 Research review may be reconciled by Lead; D03-D06 remain NOT APPROVED.

Known issues / risks / stale dependencies: process-wide cwd mutation during migration; unqualified runtime; parser semantic correctness unverified; trusted-host compromise out of scope; no clean-device portability evidence.

Affected roles / requested next action: **Lead / Architect** should keep the candidate unmerged, route a narrow migration-access correction or owner-approved scope/platform amendment, then require fresh exact-SHA QA/security and Research review as applicable. Do not begin later Task-7 stages automatically.

Last freshness check / relevant differences: live `main` remained `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595`, E0048, immediately before publication; no superseding hold or decision changed this verdict.

Rollback or correction approach: preserve branch history; additive correction only, no force-push, no runtime-lock relaxation, no immutable evidence rewrite.

Publication: PUBLISHED on `qa/rl-mvp-007a-correction01-aba0a9c`; no application code modified, no merge, no Podman/runtime operation, no inference, no model download, no spending, no deployment, no scientific-validation claim.
