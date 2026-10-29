# RL-E2E-010 — Synthetic PDF-to-prediction workflow

State: ACTIVE under RL-OPS-002 standing engineering authority. Decision epoch E0071.  
Baseline: `0a91f16fa3a5239acd1f87a894eb781a860f2937`.  
Accountable role: Codex Engineering Lead / Backend; integration requires independent exact-candidate automated review.

## Objective and non-goals

Complete and verify the existing local API v0.2 vertical slice from synthetic PDF upload through isolated target extraction, immutable one-shot local-model attempts, persisted results and browser-safe presentation. Correct the discovered optional-reference queue starvation so an older untrusted reference job cannot prevent a later redacted document from processing.

This task does not add a scoring method, confirm reference truth, expose reference content to prediction, add a model/provider, change the schema, introduce a dependency, process private data, claim clean-recipient portability, deploy, distribute or assert model accuracy.

## Controlling requirements and contracts

R01-R12, DEC-001 through DEC-022, RL-OPS-002, API v0.2, PDF worker protocol `pdf-worker-v1`, prediction run/service v0.4 and the qualified Task 9A/9B locks remain unchanged. Redacted input is required; reference input is optional and untrusted. Numeric scores remain null and truth remains `UNKNOWN`. Refresh/reconnect/read operations create no processing or prediction work. One explicit process action may resume the same immutable run but must not create a second attempt.

## Allowed files and actions

Implementation is limited to the smallest required changes in:

- `src/redaction_lab/application/application_store.py`
- `src/redaction_lab/api/app.py`
- `tests/application/test_application_store.py`
- `tests/api/test_app.py`
- new focused tests under `tests/e2e/`
- `packaging/local/README.md` only if acceptance instructions need correction
- this task record, its design/plan and one unique Lead/Backend handoff

Use the existing database and service architecture. No migration, new table, dependency, runtime/model/package lock, frontend source/bundle or public API shape change is authorized unless an independently demonstrated stop condition requires a separately recorded amendment.

Host actions may run the already qualified application-owned PDF and model runtimes on literal loopback with repository-generated synthetic fixtures only. Use temporary application state for test records where possible; do not delete unrelated user data. No downloads, paid calls, credentials, private PDFs or external network services.

## Acceptance evidence

1. TDD proves a terminal first redacted job plus its older `ACCEPTED` optional-reference job cannot starve a later redacted job; worker claim order and API preflight order remain identical.
2. Two sequential synthetic reference-bearing uploads can each explicitly process their redacted document while both references remain structurally unavailable to prediction and truth stays `UNKNOWN`.
3. Repeated process, refresh and restart/reconnect preserve one deterministic run and at most one attempt per target; errors, timeout, refusal/malformed output and unsupported/no-redaction documents remain distinct from factual error.
4. API/browser contracts continue rejecting identity mismatches, numeric scores, promoted truth, unsafe origins/IDs and untrusted rendered content.
5. Focused and full Python/Node regressions, compilation, typecheck/build/audit, runtime lock/inventory checks, exact scope/diff checks and a synthetic live PDF-to-local-model canary pass.
6. A fresh independent reviewer checks the exact candidate for queue races, reference leakage, mutation/idempotence, recovery and security regressions. Critical/Important findings are corrected within this task when scope-compatible.

## Stop conditions and rollback

Stop affected work for a required schema/public-contract change, private or institutionally controlled data, paid/credentialed provider, scientific scoring decision, destructive external action, public deployment/distribution or unresolved Critical security risk. Roll back by reverting this task's additive commits; existing Task 9A/9B qualification and immutable records remain intact.
