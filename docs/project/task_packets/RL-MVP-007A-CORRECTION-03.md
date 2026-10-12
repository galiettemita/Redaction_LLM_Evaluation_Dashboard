# RL-MVP-007A Correction 03 — interprocess SQLite migration coordination

**OWNER APPROVED for bounded implementation; NOT MERGE APPROVED.** Epoch E0050; baseline main 3366fcba7fe929230d3a7e8e2232ad9865f9a5e7 / E0049.
Correct candidate 552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70, published Backend head 5b9523a0e52594ed07c1643eeb60d60a697b646e on codex/rl-mvp-007a-portable-foundation. Read QA/security CHANGES_REQUESTED published at 9b3c894b77417595af3e7a1b33dda87afc6353e8 and Research scoped PASS at c7e6b9fdde66f2f65ee6bbc7606814856c7003dc. Their exact-SHA findings control.

## Authorized modifications — exact scope

ONLY:
- src/redaction_lab/application/migration.py
- tests/application/test_migrations.py

PLUS one unique Backend handoff docs/project/handoffs/RL-MVP-007A-backend-<UTC>-correction03-<SHORTSHA>.md published on the existing Backend task branch. No new source module, dependency, database schema/version, Task 3/4/6 file, worker runtime lock, packaging file, shared coordination edit by specialist, or other file. Stop and request approval if this scope proves insufficient. Persistent empty runtime lock leaf is authorized, not a source file, SQLite table or evidence file.

## Required design

The current module-local threading.RLock does not coordinate separately launched app processes. Use standard-library fcntl.flock(LOCK_EX | LOCK_NB) with monotonic bounded retry of EACCES/EAGAIN on a **separate persistent database-specific lock file**, not the SQLite database FD. Derive sibling basename `.redaction-lab-migration-<sha256(database basename UTF-8)>.lock` under the verified database directory. Safely open/create via directory FD with O_RDWR|O_CREAT|O_NOFOLLOW|O_CLOEXEC; require current-user owner, regular file, mode 0600, single hard link and pathname/FD device-inode match before/after lock and before release. Never unlink lock file, assume PID/timestamps prove liveness, break an active lock, or lock the authoritative database. Reject identity substitution or unsafe filesystem state.

Within the in-process RLock, preflight paths read-only and open verified database directory, then acquire this interprocess lock **before any database leaf inspection/mutation, backup cleanup, backup creation or migration-state inspection**. Only after acquisition revalidate identity, open/verify database and backup directory, invoke existing isolated SQLite helper, complete WAL/hot rollback recovery and migrations, validate all helper response/backup/database state, and release only after helper has terminated and final checks. A second initializer must re-open/reinspect migration state under the lock; after first successful migration, return no new migration/backup, no uniqueness failure. Timeout should be actionable and happen without migration mutation (suggested 125 seconds lock wait relative to 120-second helper deadline; use monotonic polling). Retain a lock until child completion; kill/reap child before release on failure.

Pass the inherited lock FD as a **fourth exact whitelisted descriptor** to existing isolated helper, validate its type, owner and identity relative to the database directory, set non-inheritable in helper, hold through exit, and NEVER explicitly LOCK_UN from child. This ensures parent termination while child continues does not free lock prematurely. Parent cwd never changes; fchdir only inside the fresh helper process. Retain safe SQLite regular journal/WAL/hot rollback behavior; no OFF/MEMORY on authoritative DB. Preserve prior no-follow paths, bounded subprocess protocol and no-clobber, verified .part-to-.bak backup lifecycle.

Abandoned .part cleanup only when exclusive database-specific lock held; never unlink another live cooperating helper's temporary backup. Do not delete a verified .bak or Task 4/6 immutable records. Local macOS Apple Silicon POSIX filesystems only; NFS, SMB and cloud-sync homes remain unqualified. Kernel flock is cooperative protection among Redaction Lab processes, not defense against arbitrary compromised same-user host.

## Required TDD and tests

First demonstrate RED: real two-independent-process simultaneous legacy migration uniqueness and/or active .part deletion race. Then GREEN with lock and tests based on explicit process readiness/IPC rather than arbitrary sleeps:
1. two processes initialize legacy DB; both succeed, applied versions partition (1,) and (); exactly one migration record and one valid backup;
2. contender cannot remove live holder .part, then can clean validated abandoned .part once holder exits/releases;
3. inherited lock remains held if parent dies before child exits;
4. abrupt holder exit releases kernel lock while lock file persists for reuse;
5. shortened test deadline fails before DB/backup mutation and produces actionable timeout;
6. symlink, wrong type/owner/link count/inode replacement lock leaf fail closed;
7. concurrent two-process Task 4/6 synthetic evidence remains byte-equivalent after third-process reopen.
Preserve/re-run prior parent cwd/thread isolation, uncheckpointed WAL, hot journal recovery, lost-helper-response restart, backup integrity/collision/cleanup, symlink races, immutable evidence and rollback regression. Never add a production test bypass or caller-controlled migration code. Run focused, application and full repository pytest, compileall, dependency and offline lock integrity, git diff --check, and exact two-file audit; report actual evidence, failures and tests not run.

## Stop conditions / restrictions

Stop and request owner amendment for any additional code path/dependency/schema; custom VFS; parent cwd changes; unreliable flock filesystem; deleting/recreating lock leaf in ordinary operation; explicit child unlock; SQLite database FD flock; live .part cleanup outside lock; failing required tests; runtime operations. No merge, Podman/VM operations, image download/build, private data, inference, provider calls, spending, deployment, scientific approvals or Task 7B/C/P/D. Require fresh independent QA/security and Research exact-implementation-SHA reviews. Separate owner merge authorization remains mandatory.
