# RL-MVP-006 Correction 02 Backend handoff

Task ID: RL-MVP-006 Correction 02 — Outcome-Independent Reference Eligibility and Exclusion-Only Summaries
Role / session label: Backend / Codex engineer
UTC time: 2026-10-12T00:45:01Z
State: READY_FOR_REVIEW
Baseline integration SHA / decision epoch: `b81ae54e0326c633a6e43b6cce6d3fe8af117db6` / E0040
Candidate branch / exact commit SHA (or no code change): `codex/rl-mvp-006-evaluator-summaries` / implementation `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`; this handoff is the only post-implementation branch commit.
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0040; DEC-001/003/004/005/011-015/017/020/022; `docs/project/task_packets/RL-MVP-006-CORRECTION-01.md`; owner-approved `docs/project/task_packets/RL-MVP-006-CORRECTION-02.md`; QA CHANGES_REQUESTED `a9614a97188f91e69eb44e94923f6bef94d92b2d`; Research scoped PASS `b3ad3902c95d9333543db23eed670cbcddadb55f`; new `qualitative-summary-evidence-v3` / `qualitative-summary-v3`; legacy v1/v2 parsing and v2 reconstruction retained.
Authorization reference and permitted file/action scope: Correction 02 packet authorizes six source/test files, one unique Backend handoff and normal non-force publication on the existing Task-6 branch. No merge, Task 7, inference, model installation/download, spending or deployment.

## Work performed / artifacts and exact paths

- `src/redaction_lab/contracts.py`: added v3 score-status and separate evaluation-compatibility provenance; v3 exclusion-only summaries require null method provenance, exact exclusions, empty evaluation evidence and null numeric scores; v3 included summaries require complete method provenance. Legacy requirements remain schema-specific.
- `src/redaction_lab/summary.py`: added v3 construction; eligible-reference keys now contain only authoritative target/reference/mapping/hash/trust provenance and exclude source facts, model outcomes and judge output. Prediction and evaluation compatibility are separate. Conflicting non-null source-fact versions still fail. Added authenticated requested-attempt profile support, deterministic empty-set summaries, mixed v2/v3 comparison rejection and schema-aware legacy v2 identity reconstruction.
- `src/redaction_lab/evaluation_store.py`: derives summary profiles from resolver-authenticated Task-4 attempts, persists exclusion-only snapshots/membership atomically, rebuilds v3 from authenticated membership, and dispatches stored v2 records through the unchanged v2 reconstruction semantics without rewriting them.
- `tests/test_contracts.py`, `tests/test_summary.py`, `tests/test_evaluation_store.py`: TDD regressions for SUCCESS/TIMEOUT/REFUSED/MALFORMED/ERROR truth identity, separate method/source-fact compatibility, single/multiple cross-run all-excluded summaries, null method provenance, deterministic replay, transaction rollback, tampering and genuine pre-v3 reopen without payload mutation.

Changed-path audit for implementation `135fa20..0ef37c5`: exactly the six packet-authorized files above. No SQLite schema or dependency change.

## Tests actually run / command / result / environment

Environment: existing isolated worktree `/private/tmp/rl-mvp-006-evaluator-summaries`; existing `.venv` Python 3.12.14; synthetic fixtures and disposable SQLite databases only.

- Pre-change baseline: `.venv/bin/python -m pytest -q` — **334 passed in 8.65s**.
- Focused final: `.venv/bin/python -m pytest -q tests/test_contracts.py tests/test_summary.py tests/test_evaluation_store.py` — **92 passed in 2.88s**.
- Full final: `.venv/bin/python -m pytest -q` — **349 passed in 7.78s**.
- Disposable DB selection: `.venv/bin/python -m pytest -q tests/test_evaluation_store.py::test_store_builds_and_reopens_single_exclusion_only_summary tests/test_evaluation_store.py::test_store_builds_exclusion_only_model_summary_across_compatible_runs tests/test_evaluation_store.py::test_exclusion_only_summary_insert_rolls_back_and_detects_member_tampering tests/test_evaluation_store.py::test_store_reopens_immutable_v2_summary_without_reinterpreting_it tests/test_evaluation_store.py::test_summary_and_membership_insert_is_atomic_and_immutable` — **5 passed in 0.76s**.
- Compilation: `.venv/bin/python -m compileall -q src tests` — **PASS, exit 0**.
- Dependency integrity: `/Users/galiettemita/.local/bin/uv pip check --python .venv/bin/python` — **21 packages checked; all compatible**.
- Whitespace: `git diff --check` — **PASS, no output**.
- Implementation changed paths: `git diff --name-only 135fa20..0ef37c5` — **exactly six authorized files**.

## Tests not run and reason

- `.venv/bin/python -m pip check` — NOT RUN TO COMPLETION because the existing venv has no `pip` module; `uv pip check --python .venv/bin/python` was run instead without installing anything.
- Real model or NLI inference, provider requests, model downloads, paid operations, private/real research data, human adjudication/calibration, deployment and Task 7 — NOT RUN and unauthorized.
- Scientific D03–D06 validation — NOT RUN and not established by this implementation.

Independent review evidence (or not yet reviewed): not yet independently reviewed. Fresh QA and Research review must use exact implementation `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`, not this documentation-only handoff commit.
Research / data approval evidence (or not approved / not applicable): Research Correction 01 scoped PASS was read; D03–D06 and scientific-method approval remain absent. DEC-022 remains synthetic-only. Unvalidated source-fact/mock-judge evidence remains NEEDS_REVIEW and all numeric score channels remain null.
Known issues / risks / stale dependencies: matching model names/configuration do not prove provider weights; EvaluationStore assumes a trusted authorized internal caller and project ID is not authentication; source-fact/mock judgments remain unvalidated; exclusion-only snapshots document no evaluated result and must never display as 0% accuracy; v2 and v3 summaries intentionally fail mixed-schema comparison.
Affected roles / requested next action: QA and Research should independently review exact implementation `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`. Lead should reconcile both verdicts and seek separate owner merge authorization. Do not begin Task 7.
Last freshness check and relevant differences: immediately before implementation publication, live `main` remained `b81ae54e0326c633a6e43b6cce6d3fe8af117db6` / E0040 and remote Backend head remained `f220fd7cd06553ad75f952e5ea6e3807a21d9abe`; implementation was then published by normal non-force push. Branch includes merge commit `135fa20` reconciling the E0040 documentation baseline before the six-file correction.
Rollback or correction approach: preserve published history; revert the Correction 02 implementation and handoff commits if required. Never rewrite v2 rows, downgrade a v3-containing non-test database with older code, force-push, or migrate without a separately approved packet.
Publication: PUBLISHED on `codex/rl-mvp-006-evaluator-summaries` after this unique handoff commit; implementation remains unmerged and unverified pending fresh independent reviews.
