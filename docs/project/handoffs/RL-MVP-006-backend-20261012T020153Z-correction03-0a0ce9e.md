# RL-MVP-006 Correction 03 Backend handoff

Task ID: RL-MVP-006 Correction 03 — Canonical Summary Membership Integrity
Role / session label: Backend/Codex
UTC time: 2026-10-12T02:01:53Z
State: READY_FOR_REVIEW
Baseline integration SHA / decision epoch: `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17` / E0041
Candidate branch / exact commit SHA: `codex/rl-mvp-006-evaluator-summaries` / implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`; subsequent publication HEAD recorded after this handoff commit.
Source requirements / approved decisions / contract versions: `AGENTS.md`; E0041 `CURRENT_STATE.md`, `DECISIONS.md` and `AGENT_HANDOFF.md`; owner-approved `docs/project/task_packets/RL-MVP-006-CORRECTION-03.md`; QA CHANGES_REQUESTED `8b9ec308ce3a52b7dc87c040a4e36f14481e9026`; Research scoped PASS `2024a37432918e27aab9754786d300e34fdf5da1`; DEC-001/003/004/005/011-015/017/020/022; immutable `qualitative-summary-evidence-v2` and v3 contracts.
Authorization reference and permitted file/action scope: owner-approved Correction 03 permits only `src/redaction_lab/evaluation_store.py`, `tests/test_evaluation_store.py`, and this one unique Backend handoff on the existing branch. It does not authorize merge, Task 7, schema/dependency changes, inference, model downloads, provider calls, private data, spending, deployment or scientific approval.

## Work performed / artifacts and exact paths

- `src/redaction_lab/evaluation_store.py`: `get_summary` now verifies stored deterministic identity before trusting requested membership, validates contiguous ordinals, and compares the exact persisted `(ordinal, subject_id)` tuple with `enumerate(stored.requested_attempt_ids)` before Task-4 resolution, EvaluationRecord loading or summary reconstruction. A mismatch raises `ValueError` containing `canonical membership binding`. Retrieval does not repair, reorder or mutate stored rows.
- `tests/test_evaluation_store.py`: added a real disposable-SQLite adversarial regression. It creates a two-member authenticated v3 exclusion-only summary, verifies canonical storage and valid reopen, drops only `summary_members_no_update`, swaps whole member ordinals through temporary ordinal `-1`, proves contiguous ordinals now bind reversed subjects, requires retrieval rejection, and proves the failed read leaves payload and membership rows unchanged.
- No contract, summary builder, Task-4 worker/store, schema, migration, dependency or version change.
- TDD RED against the rejected implementation behavior: `PYTHONPATH=src .venv/bin/python -B -m pytest -q tests/test_evaluation_store.py::test_reopen_rejects_swapped_canonical_membership_ordinals` -> **1 failed in 0.63s**, expected `Failed: DID NOT RAISE ValueError`.
- TDD GREEN after the minimal reader invariant: same command -> **1 passed in 0.53s**.

## Tests actually run / command / result / environment

Environment: existing isolated worktree, existing `.venv` Python 3.12.14; no dependency installation or model/runtime download.

- Clean pre-change repository baseline: `PYTHONPATH=src .venv/bin/python -B -m pytest -q` -> **349 passed in 8.33s**.
- Final focused ordinal/membership: `PYTHONPATH=src .venv/bin/python -B -m pytest -q --basetemp=/private/tmp/rl-mvp-006-c03-run tests/test_evaluation_store.py -k 'ordinal or membership'` -> **2 passed, 17 deselected in 0.67s**.
- Final evaluation-store file: `PYTHONPATH=src .venv/bin/python -B -m pytest -q --basetemp=/private/tmp/rl-mvp-006-c03-run tests/test_evaluation_store.py` -> **19 passed in 2.73s**.
- Final combined contracts/summary/store: `PYTHONPATH=src .venv/bin/python -B -m pytest -q --basetemp=/private/tmp/rl-mvp-006-c03-run tests/test_contracts.py tests/test_summary.py tests/test_evaluation_store.py` -> **93 passed in 2.87s**.
- Final disposable DB reopen/immutability/rollback selection: `PYTHONPATH=src .venv/bin/python -B -m pytest -q --basetemp=/private/tmp/rl-mvp-006-c03-run tests/test_evaluation_store.py::test_reopen_rejects_swapped_canonical_membership_ordinals tests/test_evaluation_store.py::test_store_builds_and_reopens_single_exclusion_only_summary tests/test_evaluation_store.py::test_store_builds_exclusion_only_model_summary_across_compatible_runs tests/test_evaluation_store.py::test_exclusion_only_summary_insert_rolls_back_and_detects_member_tampering tests/test_evaluation_store.py::test_store_reopens_immutable_v2_summary_without_reinterpreting_it tests/test_evaluation_store.py::test_summary_and_membership_insert_is_atomic_and_immutable` -> **6 passed in 0.93s**.
- Final full repository: `PYTHONPATH=src .venv/bin/python -B -m pytest -q --basetemp=/private/tmp/rl-mvp-006-c03-run` -> **350 passed in 8.81s**.
- Compilation: `PYTHONPYCACHEPREFIX=/private/tmp/rl-mvp-006-c03-compile-cache PYTHONPATH=src .venv/bin/python -m compileall -q src tests` -> **PASS, exit 0**.
- Dependency integrity: `/Users/galiettemita/.local/bin/uv pip check --python .venv/bin/python` -> **21 packages checked; all compatible**.
- `git diff --check HEAD^ HEAD` -> **PASS, exit 0**.
- Implementation changed-file audit from `7226d23fcd2d83568e3d9c561ea75d3a8289468d` to `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc` -> exactly `src/redaction_lab/evaluation_store.py` and `tests/test_evaluation_store.py`.

Two verification attempts encountered host storage pressure before clean reruns: the data volume reported only 143–156 MiB available. One chained full run produced **341 passed / 9 failed**, and one chained combined run produced **86 passed / 7 failed**; every failure was SQLite `disk I/O error` while creating a new disposable database. The same affected tests passed independently before and after. Only task-created temporary pytest/bytecode directories were cleaned, then the final isolated commands above passed. These failed attempts are not counted as passing evidence.

## Tests not run and reason

- A separate included-evaluation whole-row swap case was not added; the approved required v3 exclusion-only attack exercises the same disposition-independent pre-resolution `(ordinal, subject_id)` invariant, while existing tests retain evaluation-to-attempt binding coverage.
- System `pytest -q` was not usable: system Python 3.10 produced 12 collection errors because the project requires Python >=3.11 and imports `datetime.UTC`. The existing project venv was used instead.
- `uv run --frozen pytest -q` was not usable because the repository has no `uv.lock`; no lockfile or dependency state was created.
- Ruff was not run because it is not a declared/installed project dependency; nothing was installed.
- No real model/NLI inference, model installation/download, provider call, private/real data, human benchmark/calibration, UI/API, deployment, spending, Task 7, or D03-D06 scientific validation was run; all are prohibited or outside scope.

Independent review evidence (or not yet reviewed): Correction 03 implementation has not yet received independent review. Prior Correction 02 QA was CHANGES_REQUESTED and Research passed scoped semantics; neither is inherited for this new SHA. Fresh exact-SHA QA and Research reviews are required.
Research / data approval evidence: DEC-022 synthetic/mock-only boundary preserved. Source facts and mock judging remain unvalidated/NEEDS_REVIEW; numeric score channels remain null. D03-D06 are NOT APPROVED.
Known issues / risks / stale dependencies: the repository assumes a trusted internal caller; project ID is not authentication. Matching model names/config IDs do not prove immutable model weights. Host storage was at 100% capacity during verification, causing the disclosed transient SQLite failures; isolated final commands passed.
Affected roles / requested next action: Lead/Architect, independent QA and independent Research should inspect exact implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc`. Do not merge or begin Task 7 without fresh reviews and separate owner authorization.
Last freshness check and relevant differences: live GitHub `main` remained `c1b395e25d29f8c9189c38bf39cfb9b54cbbaa17`, E0041, immediately before implementation publication. Remote Backend branch advanced normally from `7226d23fcd2d83568e3d9c561ea75d3a8289468d` to the implementation SHA; no force-push.
Rollback or correction approach: additive revert of implementation and publication commits; no data migration, stored payload rewrite or branch-history rewrite is needed.
Publication: PUBLISHED on `codex/rl-mvp-006-evaluator-summaries` after the subsequent handoff commit; exact final branch HEAD recorded in the delivery response.
