# RL-MVP-007A Correction 01 Backend handoff

Task ID: RL-MVP-007A Correction 01 — Filesystem Confinement and Trusted Worker Authority  
Role / session label: Backend/Codex  
UTC time: 2026-10-12T10:45:14Z  
State: READY_FOR_INDEPENDENT_REVIEW

Baseline integration SHA / decision epoch: `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595` / E0048.  
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `aba0a9cfba2e5216a09ce82c12590f063203db53`. The documentation-only handoff commit is the published branch HEAD and is reported separately.  
Rejected predecessor: `87ae7c5d46e72d3f61dcc325e64fab562c9fa00a`; prior published Backend head: `90a69fba46ebbb780d4fb3bb85337d6c694ea3f2`.  
Authorization: owner-approved `docs/project/task_packets/RL-MVP-007A-CORRECTION-01.md`, including the E0048 two-file migration amendment. The exact QA/security CHANGES_REQUESTED handoff at `a6ca3d35c2cb95538c24f1ce4c7a2bbaf334e673` and Research scoped PASS at `dc2d975b9d427921ecdc62765d684aa83b1b9cc2` were read before implementation.

## Implemented correction

- Application-home and every managed directory are lexically validated and traversed from an open root descriptor with `O_DIRECTORY`, `O_NOFOLLOW`, `dir_fd`, ownership checks and descriptor-anchored creation. All managed roots are preflighted before initialization mutates any of them.
- Artifact and temporary roots remain held by verified directory descriptors. Temporary creation, hash-directory creation, no-clobber hard-link publication, fsync, reads, existing-artifact verification, cleanup and orphan discovery are directory-relative. Symlink leaves/parents, wrong file types, cross-filesystem publication and digest mismatches fail closed. Recovery validates all relevant entries before deleting a stale temporary; failed validation never repairs or mutates evidence.
- Migration paths are preflighted before mutation. Database and backup directory descriptors are no-follow and inode anchored. SQLite opens the database through a serialized descriptor-anchored working directory, verifies the opened pathname against the already-open database inode, and always restores cwd. Backups are created `O_EXCL` through the backup descriptor, populated and verified through the already-open file descriptor, fsynced, and only the newly created backup is removed on failure. Legacy Task 4/6 evidence reopens unchanged.
- `RunStore` no longer accepts `source_deriver`. Legacy `RunStore(path).ingest_redacted_pdf(...)` retains its original parser, validation and deterministic Task 4 identities.
- Production `DocumentWorker` accepts no worker, runner, policy, result, source or material injection. It constructs `ApplicationPdfWorker`, whose policy comes only from the fixed install-owned runtime lock and whose runner is the concrete Podman runner. Runtime lock and runtime inspection succeed before any job claim. The shipped unverified lock therefore leaves jobs ACCEPTED and creates no runtime evidence, Task 4 source or prediction attempt.
- Injectable command/protocol testing is renamed and documented as `NonAuthoritativePdfWorkerProbe`; its `WorkerObservation` is explicitly not authority and has no persistence or job-transition consumer. The application-owned path alone performs verified invocation, response binding, strict material reconstruction and internal Task 4 persistence. Trusted host-process compromise remains outside the threat model; no Python object/hash/flag is claimed as cryptographic proof.
- `packaging/pdf-worker/README.md` now records the production/non-authoritative composition boundary.

## Exact implementation path audit

The implementation commit changes exactly the fourteen E0048-authorized paths:

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

No dependency, schema, runtime-lock, Task 3, Task 6, scoring, model, or shared coordination file changed in the implementation commit. This handoff is the one separately authorized publication artifact.

## TDD and verification evidence

Environment: isolated worktree `/private/tmp/rl-mvp-007a-portable-foundation`; existing Python 3.12.14 environment `/private/tmp/rl-mvp-006-evaluator-summaries/.venv`; mocked/synthetic data and disposable SQLite databases only. No package was installed.

- Pre-change full baseline after merging live E0048 main: `PYTHONPATH=src .../.venv/bin/python -B -m pytest -q` -> **398 passed in 9.87s**.
- RED filesystem tests demonstrated failures for symlinked explicit homes/managed roots/hash parents/leaves, no-mutation preflight, parent replacement and recovery-before-delete. RED migration tests initially produced **4 failed, 6 passed**; the first GREEN migration iteration exposed **2 failed, 8 passed** before immutable descriptor verification and no-mutation ordering were corrected. Worker-authority RED produced **2 collection errors** because the required non-authoritative probe did not yet exist. Each regression was observed failing before implementation.
- Focused path/artifact/migration adversaries: `PYTHONPATH=src .../.venv/bin/python -B -m pytest -q tests/application/test_paths.py tests/application/test_artifact_store.py tests/application/test_migrations.py` -> **29 passed in 0.58s**.
- Focused isolation/document-worker/Task-4 authority: `PYTHONPATH=src .../.venv/bin/python -B -m pytest -q tests/application/test_isolation.py tests/application/test_document_worker.py tests/test_worker.py tests/test_prediction_source.py` -> **51 passed in 1.37s**.
- Full application suite: `PYTHONPATH=src .../.venv/bin/python -B -m pytest -q tests/application` -> **55 passed in 0.59s**.
- Migration/reopen/rollback suite alone: `PYTHONPATH=src .../.venv/bin/python -B -m pytest -q tests/application/test_migrations.py` -> **14 passed in 0.51s**. It covers fresh/legacy reopen, real Task 4/6 evidence preservation, checksum failure, transactional rollback, backup-root and ancestor symlinks, database-leaf symlink and replacement, parent replacement, failed-integrity cleanup, no-clobber backup collision, verified-backup preservation and cwd restoration.
- Full repository: `PYTHONPATH=src .../.venv/bin/python -B -m pytest -q` -> **418 passed in 9.56s**.
- Compilation: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/rl-mvp-007a-c01-final-pycache .../.venv/bin/python -m compileall -q src tests` -> **PASS, exit 0**.
- Installed dependency integrity: `uv pip check --python .../.venv/bin/python` -> **21 packages checked; all compatible**.
- Offline lock integrity: `uv lock --check --offline` -> **22 packages resolved; PASS**.
- Fail-closed scripts: `./scripts/build-pdf-worker.sh` -> expected **exit 2**, `PDF worker runtime lock is unverified; refusing to build.`; `./scripts/verify-pdf-worker.sh` -> expected **exit 2**, `PDF worker runtime lock is unverified; refusing runtime verification.` No Podman command was reached.
- `git diff --check` -> **PASS**. Implementation diff path audit -> **14/14 authorized paths only**.

## Tests not run / limitations

- Podman installation or execution, image build/pull/download, VM provisioning, runtime/image qualification, private or real PDF processing, model download/inference, provider calls, spending, deployment, recipient-device acceptance and Task 7B/C/P/D were **NOT RUN** because prohibited.
- The runtime lock remains intentionally unverified. Consequently, the authoritative positive production path was not executed; its parser semantics, Podman containment and clean-device operability remain later packaging/qualification gates. Mocked worker responses exercise only the explicitly non-authoritative protocol seam.
- The host structurally verifies the exact input hash, nonce, project, role, protocol, versions, geometry, canonical hash and deterministic Task 4 identities. It does not semantically reparse hostile PDF bytes, so semantic parsing correctness remains a qualified isolated-runtime property.
- macOS/Python SQLite cannot open a writable child database through a directory descriptor. Migration therefore uses a process-wide lock plus `fchdir` to an already-open verified directory descriptor for the brief synchronous startup migration, restores cwd in `finally`, and closes SQLite before restoration. Redaction Lab migrations are serialized; unrelated host threads performing relative-path operations during application construction remain an operational limitation. Application startup must remain single-threaded/trusted.
- Same-process malicious Python code or a compromised trusted host is outside the isolation threat model. No claim of cryptographic provenance against arbitrary host code is made.
- DEC-022 synthetic-only reference trust, reference isolation, one-shot Task 4 execution, Task 6 immutable evidence, NEEDS_REVIEW behavior and null numeric scoring remain unchanged.

Independent review evidence: none for `aba0a9cfba2e5216a09ce82c12590f063203db53`; this handoff requests fresh exact-SHA QA/security and Research review and does not claim VERIFIED.  
Research/data approval: none added; no scientific-method approval is claimed.  
Affected consumers / next action: QA/security reviews directory-descriptor confinement, SQLite/backup behavior and worker authority. Research reviews identity preservation, reference isolation and evidence boundaries. Lead reconciles both exact-SHA verdicts before any separate merge authorization.  
Freshness: immediately before the implementation commit, live `origin/main` remained `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595` / E0048. The branch reconciled main in merge commit `f6d4a92db897ef5925cd94e1009f914d834e9e91`.  
Rollback: preserve history. Before integration, abandon the branch; after separately authorized integration, revert the implementation and handoff commits normally. Never relax the runtime lock or rewrite immutable evidence as rollback.  
Publication: to be published by normal non-force push on `codex/rl-mvp-007a-portable-foundation`; final branch HEAD is reported in the delivery response.
