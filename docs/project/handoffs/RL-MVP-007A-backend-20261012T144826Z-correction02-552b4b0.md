# RL-MVP-007A Correction 02 Backend handoff

Task ID: RL-MVP-007A Correction 02 — Isolated SQLite Migration Helper  
Role / session label: Backend/Codex  
UTC time: 2026-10-12T14:48:26Z  
State: READY_FOR_REVIEW

Baseline integration SHA / decision epoch: `3366fcba7fe929230d3a7e8e2232ad9865f9a5e7` / E0049.  
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70`. The handoff commit is the final published branch HEAD and is reported separately.  
Rejected predecessor: `aba0a9cfba2e5216a09ce82c12590f063203db53`; prior published Backend head: `4ac02c1e3156c572608c499597f70df5623686cb`.  
Source requirements / approved decisions: owner-approved `docs/project/task_packets/RL-MVP-007A-CORRECTION-02.md`; E0049; DEC-022, Task 4 one-shot/immutable evidence, Task 6 immutable/null-score behavior, and all E0048 filesystem/worker-authority safeguards remain unchanged. The Correction 01 QA/security CHANGES_REQUESTED and Research scoped PASS handoffs were read before implementation.

## Work performed

- Removed every parent-process `chdir`/`fchdir` operation from migration. `migrate_database` retains its public signature and launches an application-owned private helper using `sys.executable -B -m redaction_lab.application.migration`, `shell=False`, `cwd=None`, `close_fds=True`, and an exact three-descriptor `pass_fds` whitelist. No `preexec_fn`, caller executable, callback, migration code, or production bypass was added.
- The fresh single-threaded helper strictly parses descriptor integers, the database basename, and the existing-file marker; validates descriptor type, ownership, database device/inode and path binding; then and only then performs `fchdir` inside the child. SQLite opens the relative basename so ordinary WAL and rollback-journal discovery/recovery remains active. The authoritative database never uses MEMORY or OFF journaling.
- The parent enforces a 120-second deadline, bounded stdout/stderr, exact and duplicate-free JSON fields, protocol/status, database identity, known ordered migration versions, safe backup names, successful exit, and post-helper database pathname identity. Invalid output, timeout, signal/nonzero exit, replacement, and unsafe names fail closed.
- Legacy backups now use an `O_CREAT|O_EXCL|O_NOFOLLOW` descriptor-relative unique `.part`, SQLite backup through the open descriptor, close/fsync/integrity verification, atomic no-clobber hard-link publication, directory fsync, and descriptor-relative temporary cleanup. Restart removes only ownership/type/name-validated incomplete files and never existing `.bak` evidence.
- Same-process concurrent initializers are serialized by a narrow parent migration lock that never changes cwd. The database-leaf creation race re-enters no-follow validation. A database-file advisory-lock experiment was rejected before commit because it conflicts with SQLite locking on macOS; the candidate uses SQLite's normal journal locks in the isolated helper.
- A committed migration whose valid helper response is lost is reconciled by the existing immutable migration checksum on restart. Existing Task 4/6 records reopen unchanged.

## Exact implementation path audit

Implementation commit `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70` changes exactly the two authorized paths:

- `src/redaction_lab/application/migration.py`
- `tests/application/test_migrations.py`

No dependency, lockfile, schema/version, Task 3/4/6, runtime-lock, scoring, or shared coordination file changed. This file is the one separately authorized handoff artifact.

## TDD and verification evidence

Environment: isolated worktree `/private/tmp/rl-mvp-007a-portable-foundation`; existing Python 3.12.14 environment `/private/tmp/rl-mvp-006-evaluator-summaries/.venv`; synthetic fixtures and disposable SQLite databases only. Nothing was installed.

- Pre-change focused migration suite: **14 passed in 0.64s**. Pre-change full repository: **418 passed in 10.07s**.
- Required RED: the new parent-cwd/concurrent-relative-I/O pair produced **2 failed** because the parent called `os.fchdir` and the unrelated thread observed the database directory. The initial command pointed to a nonexistent worktree-local virtualenv (**exit 127; no tests run**) and the system Python 3.10 could not import `datetime.UTC` (**collection error; no test executed**); both were corrected by using the existing project-compatible Python 3.12 environment.
- Boundary adaptation evidence: after introducing the helper, the inherited suite produced **5 failed, 10 passed** because five old tests monkeypatched parent memory that no longer crosses the process boundary. Those tests were converted to black-box subprocess races or direct private-unit checks without adding a production injection seam. Strict duplicate-field TDD separately produced **1 failed** before the parser was added. Concurrent initialization produced **1 failed** before serialization and no-follow creation-race handling were added.
- Focused final migration/reopen/security suite: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q tests/application/test_migrations.py` -> **29 passed in 1.70s**.
- The focused suite covers parent cwd prohibition, unrelated-thread relative I/O, subprocess flags/FD whitelist, timeout/output bounds, duplicate/invalid protocol, identity/version/name rejection, leaf and parent replacement, symlink rejection, helper failure, committed-response loss/restart, repeated concurrent initialization, uncheckpointed WAL, hot rollback-journal recovery, atomic backup/no-clobber/integrity, validated `.part` cleanup, rollback, deterministic reopen, and Task 4/6 evidence preservation.
- Full application suite: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q tests/application` -> **70 passed in 3.08s**.
- Full repository: `PYTHONPATH=src /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -q` -> **433 passed in 10.79s**.
- Compilation: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/rl-mvp-007a-c02-pycache /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -m compileall -q src tests` -> **PASS, exit 0**.
- Installed dependency integrity: `uv pip check --python /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python` -> **21 packages checked; all compatible**.
- Offline lock integrity: `uv lock --check --offline` -> **22 packages resolved; PASS**.
- `git diff --check` -> **PASS**. Pre-commit implementation path audit -> exactly the two authorized paths. Helper `-B` test also confirmed no source-tree `__pycache__` was created.

## Tests not run / limitations

- Podman installation/execution, image builds/downloads, VM provisioning, private/real PDF processing, model installation/inference, provider calls, spending, deployment, clean-device acceptance, and Task 7B/C/P/D were **NOT RUN** because prohibited.
- No separate-process simultaneous-launch stress test or power-loss/fsync fault injection was run. Supported application startup is single-instance; same-process concurrent initialization is covered. SQLite WAL/hot-journal recovery and committed-response-loss restart were exercised with real disposable databases.
- The helper is process isolation for cwd and SQLite pathname anchoring, not a sandbox against a compromised same-user host. The trusted-host and verified PDF-worker assumptions are unchanged.
- The PDF runtime lock remains intentionally unverified/fail-closed. No worker runtime or authoritative PDF processing path was invoked.

Independent review evidence: none for `552b4b0068d5955d03a3bb78f5ceab4e1f4f9c70`; fresh exact-SHA QA/security and Research reviews are required. This handoff does not claim VERIFIED.  
Research / data approval evidence: no new research or scientific-method approval; no private data used.  
Known issues / risks: simultaneous independent application processes are outside this correction's tested startup model; helper termination can leave only a non-authoritative `.part`, which restart validates and removes. The existing unverified runtime lock remains a separate intentional gate.  
Affected roles / requested next action: QA/security should review the exact SHA's parent/child boundary, FD and protocol validation, journal recovery, and backup lifecycle. Research should confirm Task 4/6 evidence and null-score boundaries remain unchanged. Lead should reconcile both reviews before any owner-authorized merge.  
Last freshness check and relevant differences: immediately before commit, live `origin/main` remained `3366fcba7fe929230d3a7e8e2232ad9865f9a5e7` / E0049. The branch incorporated it through merge commit `f60f651` and the implementation commit contains only the authorized two files.  
Rollback or correction approach: preserve history; before integration abandon the branch, or after separately authorized integration revert the implementation and handoff commits normally. Do not rewrite immutable evidence or restore parent cwd mutation.  
Publication: PUBLISHED on `codex/rl-mvp-007a-portable-foundation` after the handoff commit is pushed normally without force.
