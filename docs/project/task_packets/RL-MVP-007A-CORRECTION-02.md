# RL-MVP-007A Correction 02 — isolated SQLite migration helper

**OWNER APPROVED for bounded implementation; NOT APPROVED for merge.** Epoch E0049. Baseline main 353fdc12c8ec04bc05ec7c8664cd699a8d5ad595 / E0048. Candidate to correct: aba0a9cfba2e5216a09ce82c12590f063203db53; published Backend head 4ac02c1e3156c572608c499597f70df5623686cb on codex/rl-mvp-007a-portable-foundation. QA/security CHANGES_REQUESTED at 7a91814fbe076d2b8239c22980c7e259ec366e1c; Research scoped PASS at ad5096d1831f989a0040e5aac0bfd80634e3f499.

## Exact scope
Modify ONLY:
- src/redaction_lab/application/migration.py
- tests/application/test_migrations.py

Publish ONE unique Backend handoff docs/project/handoffs/RL-MVP-007A-backend-<UTC>-correction02-<SHORTSHA>.md on the existing isolated Backend branch. No other files, dependencies, schema/version modifications, Task 3/4/6 changes or force push. Stop and ask for amendment if required.

## Correct the blocking defect
The current migration temporarily changes the entire host Python process cwd through fchdir, redirecting unrelated threads' relative file operations. Remove ALL parent-process chdir/fchdir. Keep migrate_database(path, backup_directory=...) and MigrationResult compatible.

The trusted parent preflights lexical absolute paths and safely opens database/backup directory chains and database leaf through directory-FD/O_NOFOLLOW operations, retaining checked descriptors and identities. Launch a fresh subprocess of sys.executable with shell=False, cwd=None, close_fds=True, pass_fds limited to database directory/database leaf/backup descriptors, and NO preexec_fn or caller-provided executable/code. Bound child execution deadline, stdout/stderr/framing/JSON schema; fail closed for nonzero exit, timeout, signal, invalid response, wrong inode/dev, unexpected versions, unsafe names and overwritten/changed path. Parent process cwd and unrelated threads' relative-path resolution must be unchanged.

The helper's private mode lives in migration.py and accepts only strictly parsed inherited FD integers and validated database basename. Verify FD types/dev/inode, require single-threaded helper, and allow fchdir ONLY INSIDE THE FRESH CHILD. Open SQLite using the relative database basename to preserve normal durable DELETE/WAL journal behavior, including hot-journal recovery and uncheckpointed WAL data. Compare opened database identity to retained FD. No journal_mode OFF/MEMORY on authoritative database. No SQLite corruption or skipped transaction durability.

## Atomic backup lifecycle
Use a directory-FD-created unique temporary .part file (O_CREAT|O_EXCL|O_NOFOLLOW), populate through open descriptor using SQLite backup API, close/fsync/check integrity and publish final .bak by atomic no-clobber hard link, fsync directory, then remove .part. journal_mode OFF is permissible only on disposable unpublished backup output if needed, not authoritative database. A crashed or invalid .part is never trusted as .bak. Cleanup uses descriptor-scoped deletion of only validated incomplete files, never existing verified backups or Task 4/6 evidence. Backup failure and helper termination must leave recoverable authoritative DB; after child commits but fails to reply, next startup must read migration checksum and reconcile idempotently.

## TDD and acceptance
Write failing concurrent relative-I/O regression using an unrelated parent thread, and assert parent os.chdir/os.fchdir are never used. Verify safe subprocess flags/FD whitelist and bounded protocol; incorrect inherited descriptors and inode mismatch fail closed. Include uncheckpointed WAL and hot rollback journal recovery, parent/leaf symlink and replacement races, helper crash/invalid JSON/timeout, .part cleanup and collision, backup atomic publication, legacy Task 4/6 byte-equivalent evidence, transactional migration rollback and deterministic reopen. Adapt earlier monkeypatch tests to account for helper boundary without enabling arbitrary injected production migration code or bypass flags. Run focused migration tests, full application and repository pytest, compileall, dependency and offline lock checks, whitespace and exact two-path audit; record actual commands/results, failed attempts, tests not run and limitations. Fresh independent QA/security and Research exact-SHA review mandatory.

## Stop / exclusions
No merge, Podman installation/execution, OCI image build/download, VM provisioning, private PDFs, inference, provider calls, spending, deployment, scientific-method approval or Task 7B/C/P/D. Stop if third file/dependency/custom VFS/C extension/schema modification needed; if parent cwd is mutated; if MEMORY/OFF journal used for authoritative database; if WAL/hot journal discarded; if host/worker trust protections regress; or if a required test remains failing. Previous E0048 security correction controls all unrelated paths. Separate owner approval needed for integration.
