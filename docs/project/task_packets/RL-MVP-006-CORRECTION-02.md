# RL-MVP-006 — Correction 02: outcome-independent truth sets and exclusion-only summaries

**OWNER APPROVED** 2026-10-11. Coordination epoch E0040. Backend/Codex implementation only; independent QA and Research reviews mandatory. This is a bounded amendment to the approved Task 6 Correction 01, NOT approval to merge, implement Task 7, use models, spend, deploy or claim scientific validity.

**Baseline at approval:** main `d846f91e0394ef3d6348cfa8a7856746676c5648` / E0039. **Implementation correction base:** `8f2fa74b5c7c988735a572e682c506aed28afe94`, Backend published head `f220fd7cd06553ad75f952e5ea6e3807a21d9abe`. **Review evidence:** QA CHANGES_REQUESTED at `a9614a97188f91e69eb44e94923f6bef94d92b2d` (two blocking summary defects); Research scoped PASS at `b3ad3902c95d9333543db23eed670cbcddadb55f`. Refresh current HEAD, decisions, handoffs and AGENTS before implementation and publication. Preserve branch history; no force push.

## Exact authorized files

Modify only:
- `src/redaction_lab/contracts.py`
- `src/redaction_lab/summary.py`
- `src/redaction_lab/evaluation_store.py`
- `tests/test_contracts.py`
- `tests/test_summary.py`
- `tests/test_evaluation_store.py`

Create one unique `docs/project/handoffs/RL-MVP-006-backend-<UTC>-correction02-<shortSHA>.md` on existing `codex/rl-mvp-006-evaluator-summaries` branch. No other source/tests, Task 4 store, evaluator/judges, prediction/reference code, dependencies, database schema migration, shared canonical docs, UI or API changes. Stop and request approval for any expansion.

## Objective 1 — outcome-independent comparable truth

The common eligible reference-set identity must be determined **only by trustworthy target/reference truth provenance**, never by model outcome or presence of source-fact evidence. Define deterministic key with project, redacted document and target ID/version, reference target ID/version, mapping ID/version/method and redacted-canonical version, reference document/canonical version and both canonical hashes, DEC-022 trust. Exclude source_fact_record_id/version, evaluation ID, attempt/process/qualitative status, model and run, rubric/evaluator/judge identity. These remain available as separate evidence/protocol compatibility information. Eligible set and digest must be stable for the same trusted target when model A answers and model B TIMEOUTs, REFUSEs, produces MALFORMED output or ERRORs, while each model's technical outcome counts remain distinct. Changed target, mapping, method, version, hashes or trust must change key or fail closed. Reference is optional for prediction, but scores remain null unless fully revealed, readable, aligned text truth; arbitrary/unregistered truth remains UNKNOWN/null. Preserve source-fact version checks independent of eligible set: reject conflicting non-null versions; null for technical nonanswer must not distort truth set or invent facts. Distinct rubric/evaluator/judge incompatibility still blocks comparison.

## Objective 2 — all-excluded authoritative summaries

For nonempty `SummaryRequest` whose requested Task-4 attempts are authenticated via read-only RunStore resolver, allow zero included evaluations when **every** requested attempt is an explicit NO_EVALUATION exclusion. Derive project/model/config/condition/prompt/settings/attempt/context/budget/tool/run/protocol profile from authenticated requested attempts. TARGET and DOCUMENT summaries remain run-local; MODEL may span compatible distinct runs. Do not derive evaluation method identities from absent evaluations. Persist exact requested IDs, reasons and membership atomically; requested_count=excluded_count=N, included/eligible/unknown evaluated counts and all evaluated outcome counts zero, eligible truth provenance collection empty, deterministic empty common-set ID. No fabricated rubric/evaluator/judge/reference/source-fact values or NO_EVALUATION sentinel as methodological provenance. Null verified_score and experimental_score, score_status NONE, no scale or research-validation ID. An all-excluded summary documents **no evaluated results**, not 0% accuracy or a completed evaluation. Task-4 attempt outcomes remain in Task 4, not misclassified as evaluated outcomes.

## Versioned contract and compatibility

Introduce additive `qualitative-summary-evidence-v3` and `qualitative-summary-v3` for corrected identity and nullable evaluation-method semantics. Existing v1/v2 evidence remains immutable and readable; never reinterpret or rewrite stored v2 snapshots. v2/v3 comparison fails closed. For v3 with included evaluations, rubric/evaluator/judge/version and evaluation compatibility profile MUST be populated; for zero included all MUST be null (reject partial values). Resolver-derived project/model/prompt/settings/protocol/run fields always required. Keep `compatibility_profile_id` for prediction protocol and separate nullable `evaluation_compatibility_profile_id` for rubric/evaluator/judge/mapping method. Legacy contract parsing semantics preserved. No SQLite schema modification anticipated: versioned JSON stored in existing tables and exclusion membership already permits null evaluation ID; STOP if migration needed.

## Transactional authority and replay

`EvaluationStore.build_summary` must resolve all requested attempts, validate compatible requested-attempt profile, load/verify included evaluations, construct v3 summary, and insert snapshot plus memberships as one transaction. `get_summary` re-resolves every member, reconstructs correct schema-specific snapshot, verifies exact content and deterministic identity, rejects altered/missing/duplicated/cross-project records and does not silently upgrade v2. Deterministic replay stable independent of ordering and creation timestamps. Historical rows immutable; no automatic latest selection. The surrounding caller remains a trusted authorized component; project_id alone is not authentication and no public API trust is claimed.

## Required TDD and Lead quality guards

Write failing tests before implementation, including:
- v3 exclusion-only accepts all-null method provenance, rejects partial/populated invented method provenance; v3 included evaluations require all methodology fields; legacy v1/v2 requirements preserved.
- same trusted reference with SUCCESS vs TIMEOUT, REFUSED, MALFORMED, ERROR yields identical eligible keys/common target set while attempt counts differ; adding/removing source fact evidence does not change reference truth.
- changed target/reference/mapping/byte hash/method/trust changes comparable key or fails; rubric/evaluator/judge or conflicting non-null source fact version still rejects incompatible comparison.
- one/multiple all-excluded authenticated attempts, MODEL across distinct compatible runs, zero evaluations/null scores and explicit zero-result presentation fields; altered prompt/settings/condition/context/budget/tools/model config fails before insert.
- full summary/membership transaction rollback on failure, deterministic replay, reopen/tamper/member-order/ordinal/reason/duplication verification; v2 fixture reopened unchanged without mutation.
- maintain all prior Task 1–6 adversarial and regression suites, DEC-022 byte-pinned truth and Task-4 one-shot guarantees.
Run focused `tests/test_contracts.py tests/test_summary.py tests/test_evaluation_store.py`, full pytest, compileall, dependency integrity, git diff --check, disposable-database v2/v3 reopen, rollback/immutability. Report exact outputs plus NOT RUN checks; audit changed paths. No numeric scores, models/inference, provider APIs, private data, spending, deployment or Task 7.

## Handoff and stop

Publish the new exact implementation commit SHA and branch HEAD separately, one unique Backend correction handoff with actual tests/results, scope, limits, blocker disposition and receivers QA/Research. Fresh independent QA and Research must review exact new SHA. Stop for changed relevant HEAD/hold, scope enlargement, migration, v2 rewrite, inability to resolve Task-4 profiles, weakening DEC-022, nonnull scores, unresolved test regressions or unauthorized operations. Lead reconciles both reviews and separately requests owner merge approval. Date is a checkpoint, not permission to lower gates.
