# RL-MVP-007A Correction 03 Backend handoff

Task ID: RL-MVP-007A Correction 03 — Interprocess SQLite migration coordination
Role / session label: Backend/Codex
UTC time: 2026-10-12T17:55:20Z
State: READY_FOR_REVIEW

Baseline integration SHA / decision epoch: `951f220511a2bf05ddd35a0f13b61f23e406e82f` / E0050.
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `03d95ec8e6f280693550563f08ebaa65e844afb3`. The handoff commit is the final published branch HEAD and is reported separately.
Rejected predecessor: `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70`; prior published Backend head: `5b9523a0e52594ed07c1643eeb60d60a697b646e`.
Source requirements / approved decisions: owner-approved `docs/project/task_packets/RL-MVP-007A-CORRECTION-03.md`; E0050; the Correction 02 QA/security CHANGES_REQUESTED finding at `9b3c894b77417595af3e7a1b33dda87afc6353e8` and Research scoped PASS at `c7e6b9fdde66f2f65ee6bbc7606814856c7003dc` were read before implementation. DEC-022, Task 4 one-shot/immutable evidence, Task 6 immutable/null-score behavior, parent-cwd isolation, directory-FD confinement and worker-authority protections remain unchanged.

## Work performed

- Added a persistent database-specific sibling lock named `.redaction-lab-migration-<sha256(database basename UTF-8)>.lock`. It is opened relative to the verified database-directory descriptor with create-exclusive/no-follow/close-on-exec semantics and is never unlinked in ordinary operation.
- The lock is required to be a current-user-owned regular file on the database directory's device, mode `0600`, single-linked, and bound to the same device/inode through both descriptor and pathname. Validation occurs before acquisition, after `fcntl.flock(LOCK_EX | LOCK_NB)` succeeds, in the helper, and before parent release. Unsafe type, symlink, owner, mode, link count or identity substitution fails closed.
- A monotonic bounded retry waits up to 125 seconds, exceeding the existing 120-second helper deadline. Timeout reports that another Redaction Lab process is migrating the database and occurs before database or backup mutation.
- The exclusive lock covers database-leaf inspection/open, backup-directory open, incomplete `.part` cleanup, backup publication, SQLite migration/recovery, helper termination, response validation and final database/lock identity verification. A second initializer therefore reopens and reinspects migration state under the lock and returns no new migration or backup.
- The inherited lock descriptor is the helper's fourth exact whitelisted descriptor. The helper validates all four descriptors, makes the lock descriptor non-inheritable for any later exec, holds it through helper exit and never explicitly unlocks it. The parent kills/reaps a failed helper before leaving the locked lifecycle.
- Added deterministic real-process tests for simultaneous legacy startup, live temporary-backup protection, inherited lock liveness after parent death, abrupt-holder recovery, timeout without mutation, unsafe lock leaves and replacement, and byte-equivalent Task 4/6 synthetic evidence after two-process migration plus third-process reopen.

## Exact implementation path audit

Implementation commit `03d95ec8e6f280693550563f08ebaa65e844afb3` changes exactly the two authorized implementation paths:

- `src/redaction_lab/application/migration.py`
- `tests/application/test_migrations.py`

No dependency, lockfile, database schema/version, Task 3/4/6, runtime-lock, scoring or shared coordination file changed. This document is the one separately authorized handoff artifact.

## TDD and verification evidence

Environment: isolated worktree `/private/tmp/rl-mvp-007a-portable-foundation`; existing Python 3.12.14 environment `/private/tmp/rl-mvp-006-evaluator-summaries/.venv`; macOS arm64; synthetic fixtures and disposable SQLite databases only. Nothing was installed.

- Required RED: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q tests/application/test_migrations.py::test_two_independent_processes_serialize_legacy_migration tests/application/test_migrations.py::test_contender_does_not_remove_live_holders_part_backup` -> **2 failed**. The independent initializers raced backup-directory creation, and the active-part holder could not acquire the then-missing interprocess lock interface.
- Adversarial lock-leaf RED during hardening: the lock-focused selection produced **2 failed, 7 passed** because symlink and directory lock leaves leaked raw OS errors rather than the required fail-closed `MigrationError`; both paths were corrected and rerun.
- Final focused migration/security/reopen suite: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q tests/application/test_migrations.py` -> **41 passed in 3.00s**.
- Final complete application suite on the exact candidate: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q tests/application` -> **82 passed in 4.33s**.
- Final full repository suite on the exact candidate: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q` -> **445 passed in 12.07s**.
- Compilation: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/rl-mvp-007a-c03-pycache-final /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -m compileall -q src tests` -> **PASS, exit 0**; no source-tree `__pycache__` was created.
- Installed dependency integrity: `uv pip check --python /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python` -> **21 packages checked; all compatible**.
- Offline lock integrity: `uv lock --check --offline` -> **22 packages resolved; PASS**.
- `git show --check` / `git diff --check` -> **PASS**. Implementation path audit -> exactly the two authorized paths.

## Tests not run / limitations

- Podman installation/execution, image builds/downloads, VM provisioning, private/real PDF processing, model installation/inference, provider calls, spending, deployment, clean-device acceptance and Task 7B/C/P/D were **NOT RUN** because prohibited.
- NFS, SMB, cloud-synchronized directories, non-macOS hosts, power-loss/fsync fault injection and a real alternate-UID owner test were **NOT RUN**. Wrong-owner validation was exercised deterministically by substituting descriptor metadata in a unit test. Supported scope remains local macOS Apple Silicon POSIX filesystems.
- Ruff/static typing was **NOT RUN** because neither is a declared/installed project dependency and installation was unauthorized.
- `flock` is cooperative coordination among Redaction Lab processes, not a sandbox or protection from an arbitrary compromised same-user host. The PDF runtime lock remains intentionally unverified and fail-closed; no isolated PDF runtime or authoritative PDF processing path was invoked.

Independent review evidence: none for `03d95ec8e6f280693550563f08ebaa65e844afb3`; fresh exact-SHA QA/security and Research reviews are required. Prior reviews are inputs, not inherited verification. This handoff does not claim VERIFIED.
Research / data approval evidence: no scientific-method approval, private data or new scoring methodology.
Known issues / risks: kernel lock semantics are qualified only for the supported local macOS/POSIX environment. A hostile same-user process can ignore cooperative locking. Persistent empty lock files are expected and must not be manually deleted during application use.
Affected roles / requested next action: QA/security should review the exact SHA's lock-file validation, lifecycle coverage, helper inheritance, crash release and two-process tests. Research should confirm Task 4/6 evidence, DEC-022 and null-score boundaries remain unchanged. Lead should reconcile both exact-SHA reviews before any owner-authorized merge.
Last freshness check and relevant differences: immediately before implementation publication, live `origin/main` remained `951f220511a2bf05ddd35a0f13b61f23e406e82f` / E0050. The branch incorporated it through merge commit `03c5ac2`; the implementation commit changes only the two authorized implementation paths.
Rollback or correction approach: preserve published history; before integration abandon the branch, or after separately authorized integration revert the implementation and handoff commits normally. Do not delete a potentially live lock, rewrite immutable evidence, restore parent cwd mutation or force-push.
Publication: PUBLISHED on `codex/rl-mvp-007a-portable-foundation` after the handoff commit is pushed normally without force.
