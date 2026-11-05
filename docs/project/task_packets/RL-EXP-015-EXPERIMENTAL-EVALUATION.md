# RL-EXP-015 — Experimental evidence, scoring and genuine inference

Baseline integration SHA: `cb0fa4f1242ae8bf12afb084bc9475017040b784` (live GitHub main, 2026-11-05 UTC). Epoch: E0072.
Accountable owner: Codex Engineering Lead; delegated implementers report exact candidates to Lead. State: ACTIVE / AUTHORIZED FOR BOUNDED ENGINEERING, NOT IMPLEMENTED OR VERIFIED by this record.
Authority: owner clarification dated 2026-11-05, DEC-023 and [RL-OPS-002](RL-OPS-002-AUTONOMOUS-ENGINEERING.md). Read the [design](../../superpowers/specs/2026-11-05-experimental-product-completion-design.md), [implementation plan](../../superpowers/plans/2026-11-05-experimental-product-completion.md), [API v0.3](../API_CONTRACT_V0_3.md) and live integration HEAD before work.

## Objective and dependencies

Implement plan Tasks 2–4: isolated reference extraction, conservative experimental alignment, transparent versioned experimental text-agreement scoring, immutable persistence/aggregation, genuine local-Qwen parsing and API v0.3 orchestration. Task 1 publishes the foundation first. Task 2 evidence feeds Task 3; Task 4 consumes both. Scope includes synthetic tests and already qualified loopback model use; Task 2 is source/test-only. A changed PDF protocol cannot run live until the v2 image/lock is rebuilt and requalified under [RL-LINK-017 Task 6](RL-LINK-017-CONTROLLED-DEMO.md).

The algorithm is an experimental agreement baseline. It does not satisfy the eventual validated semantic/commercial multi-model requirement or approve a scientific model roster. Only installed integrity-pinned `qwen2.5:1.5b-instruct-q4_K_M` is enabled; no substitute rule-based/synthetic adapter is model inference.

## Exact file/action scope

Task 2 source/tests:

- `src/redaction_lab/application/worker_protocol.py`
- `src/redaction_lab/application/document_worker.py`
- `src/redaction_lab/application/application_store.py`
- `src/redaction_lab/application/migrations/0002.sql` (new additive migration)
- `src/redaction_lab/application/migration.py` (necessary migration-registry scope correction under RL-OPS-002: register additive 0002 only; all gates unchanged)
- `src/redaction_lab/reference.py`
- `src/redaction_lab/contracts.py`
- `tests/application/test_worker_protocol.py`
- `tests/application/test_document_worker.py`
- `tests/application/test_isolation.py` (necessary v2 response-fixture compatibility correction under RL-OPS-002 only; hardening assertions unchanged)
- `tests/application/test_application_store.py`
- `tests/application/test_migrations.py`
- `tests/test_reference.py`

Task 3 source/tests:

- `src/redaction_lab/experimental_scoring.py` (new)
- `src/redaction_lab/application/evaluation_service.py` (new)
- `src/redaction_lab/contracts.py`
- `src/redaction_lab/evaluator.py`
- `src/redaction_lab/evaluation_store.py`
- `src/redaction_lab/summary.py`
- `tests/test_experimental_scoring.py` (new)
- `tests/application/test_evaluation_service.py` (new)
- `tests/test_contracts.py`
- `tests/test_evaluator.py`
- `tests/test_evaluation_store.py`
- `tests/test_summary.py`

Task 4 source/tests:

- `src/redaction_lab/adapters/ollama.py`
- `src/redaction_lab/application/inference_runtime.py`
- `src/redaction_lab/application/prediction_service.py`
- `src/redaction_lab/api/app.py`
- `src/redaction_lab/api/http.py`
- `packaging/model-runtime/runtime.lock` only for required prompt/runtime identity versioning; never to substitute an unqualified model
- `tests/test_adapter.py`
- `tests/application/test_inference_runtime.py`
- `tests/application/test_prediction_service.py`
- `tests/api/test_app.py`
- `tests/api/test_http.py`
- `tests/e2e/test_synthetic_workflow.py`

Also permitted: this packet's checklist, the approved design/plan checklists and unique RL-EXP-015 handoff(s). Lead alone reconciles shared canonical state under Task 1/Task 6. No unrelated files/dependencies; record demonstrated necessary amendments before writes. Use isolated task branches/worktrees or sequential exclusive ownership of the owner-authorized completion branch, never simultaneous writes to shared contracts.

## Interfaces and immutable provenance

Task 2 produces `StoredReferenceSource`, `ApplicationStore.reference_source(version_id)`, isolated protocol `pdf-worker-v2` and `align_experimental_reference(redacted, reference_text, ...) -> list[ReferenceMapping]`. Reference evidence stores visible bounded canonical text, SHA-256, canonicalizer version, page count, immutable document version/pair binding and `USER_SUPPLIED_EXPERIMENTAL` provenance. It must never be registered as a Task-4 prediction source. Existing verified synthetic `align_reference`/registry remains unchanged. Keep two-sided anchors/global coherence, exact edges and conservative nulls; no inferred reference text or geometry override.

Task 3 produces `score_text_agreement(reference: str, prediction: str) -> ExperimentalScore`, method `experimental-text-agreement-v1`, schema `experimental-text-agreement-evidence-v1`, and `EvaluationService`. Preserve old qualitative schema dispatch/readability. Engineering experimental weights are exactly 40% token F1, 25% ordered-token agreement, 20% character-trigram F1, 15% critical-detail agreement. Normalized exact match returns 100. Negation mismatch cap 35; quantity/date mismatch cap 60; tighter cap wins; round to one decimal. Expose subscores/warnings/caps and method provenance. No probability-of-truth or validated semantics claim.

Task 4 implements exact v0.3 flat attempt rows, nested experimental mapping/evaluation, identity-grouped summary arrays and durable counts/progress. Only intentional process may create work; GET remains read-only. Configured runtime root must be one explicit owner-controlled absolute root, no symlinks, checked ownership/permissions, unchanged digest inventory and fail-closed defaults. Genuine provider envelope and bounded reconstruction parsing must distinguish refusal, truncation, extra keys, malformed and errors. Provider model identity is checked before mutation; no retry-until-success or guessed completion.

## Acceptance checklist (plan Tasks 2–4)

- [x] Task 2 RED: reference-only bounded visible text/hash/version and strict role/failure validation tests fail for missing v2 behavior.
- [x] Task 2 GREEN: immutable reference persistence, additive migration/backup, crash recovery, pair lookup, tamper rejection and no prediction-source binding pass.
- [x] Task 2 adversarial mappings: unique exact span, repeated/one-sided anchors, partial revelation, wrong document, changed pagination and prompt-like reference instructions preserve correct experimental/null states; verified synthetic behavior unchanged.
- [x] Task 2 focused/full Python suite passes; commit `feat: persist isolated experimental reference evidence`.
- [x] Task 3 RED/GREEN: exact match, invalid/empty input, repetition, paraphrase/role-reversal limitations, unsupported additions, number/date/negation caps and exact rounding verified.
- [x] Task 3 persistence: deterministic identities, version dispatch, legacy qualitative reopening, tamper rejection and immutable scores pass; verified scores always null.
- [x] Task 3 summaries: eligible denominator independent of outcome, unknown truth, refusal/timeout/malformed/error, zero denominators, equal-target document/equal-document model means and no cross-model blend pass.
- [x] Task 3 focused/full Python suite passes; commit `feat: add transparent experimental accuracy scoring`.
- [x] Task 3 review correction round 1: Unicode minus sign preservation/ambiguous-sign rejection and transactionally authenticated new snapshot statuses pass RED/GREEN regressions; historical snapshots preserved. Focused 72/full 817 passed; independent re-review pending.
- [x] Task 4 RED/GREEN: realistic valid Ollama JSON/bounded reconstruction, refusal, extra keys, wrong model, truncation and malformed handling verified.
- [x] Task 4 runtime root: explicit absolute owner-controlled root works only with no-symlink/ownership/permission/inventory checks; unsafe/default unqualified paths fail closed.
- [x] Task 4 API/E2E: paired processing, one attempt, evaluation only after terminal prediction, progress counts, exact v0.3 shapes, reference absence from manifests, nulls and GET/reconnect idempotence pass.
- [ ] Task 4 focused/full Python suite passes; after v2 worker requalification, genuine synthetic Qwen canary persists at least one SUCCEEDED attempt; commit `feat: connect genuine inference to experimental evaluation`. If sequencing requires the Task 6 runtime prerequisite first, record that dependency and complete the genuine canary before claiming Task 4 acceptance.
- [ ] Exact-candidate independent review and unique handoff published; Lead reconciles against current main before integration.

## Common gates, review and rollback

Preserve R01–R12 and DEC-001–DEC-023 within DEC-023's explicit experimental-only supersession. `verified_score` remains null; verified `truth_status` remains UNKNOWN. Missing/partial/unreadable/ambiguous/mismatched/unprocessed truth remains Accuracy unknown/null, never zero. Reference data never enters prediction inputs; immutable versions and one-shot recovery remain mandatory. This record authorizes no paid resources, private/restricted research data, credentials in Git, destructive external action, scientific validation or public unauthenticated release. Only generated synthetic fixtures or separately documented authorized public data may be used; the shared demonstration workspace stores synthetic documents only.

Behavior changes require red-green-refactor evidence, focused/full permitted regressions, exact-candidate independent automated QA/security and experimental-semantics review, correction and re-review before normal non-force integration. Self-review is not independent review. No automated reviewer grants D03–D06, institutional permission or scientific/release validation. Stop only affected work for unsafe reference leakage, unexplained score/version changes, scope/contract conflicts, unqualified runtime, essential missing credentials, paid-resource need, private-data need, destructive action or unresolved Critical security risk; continue independent safe work. Record any necessary bounded scope amendment before writes.

Rollback: stop affected services if necessary, revert additive task commits normally, retain original immutable attempts/evaluations and restore a verified pre-migration backup only through the documented safe migration recovery path. Do not overwrite later evidence or roll old validators forward silently. Publish a unique task handoff under `docs/project/handoffs/` using every field in [AGENT_HANDOFF](../AGENT_HANDOFF.md#handoff-template-all-fields-required-explicit-not-applicable-is-valid), with exact artifacts/commits, tests run/unrun, decisions, blockers, affected consumers and next action. Live integration HEAD must be rechecked before consequential writes, runtime calls and final review.

### Task 4 bounded queue amendment (2026-11-05)

Engineering Lead authorizes, under RL-OPS-002, adding only `src/redaction_lab/application/application_store.py` and `tests/application/test_application_store.py` to Task 4. Explicit `expected_job_id` may claim a REFERENCE job when its paired REDACTED job is terminal. Ordinary claims retain global redacted-first ordering, and every claim retains the one-active-job invariant. This enables processing an associated reference before evaluation even when later redacted uploads are queued. TDD acceptance includes multiple pairs and concurrent claim regressions; no other queue/runtime/data authority changes.

Task 4 compatibility amendment: Engineering Lead additionally authorizes updating only the model-runtime-lock SHA-256 binding in `packaging/local/manifest.json`, required by the permitted prompt-v2 model configuration identity change. Frontend assets and all readiness/qualification flags remain untouched. Acceptance includes packaging preflight and the full Python suite.

Task 4 test-only transition amendment: Engineering Lead authorizes two updates in `tests/packaging/test_local_preflight.py`: `test_synthetic_loopback_api_upload_fail_closed_and_restart` expects API v0.3 health, and the existing-Chrome old-bundle case asserts truthful fail-closed v0.2/v0.3 incompatibility. No assets are changed. Task 5/6 must rebuild/rebind the matching v0.3 browser bundle and restore positive browser acceptance.

Task 4 partial runtime acceptance evidence: implementation and full Python suite pass (856 tests). A genuine Qwen prompt-v2/run-v0.5 canary persisted one SUCCEEDED attempt against an authentic previously qualified v1 isolated PDF source; replay/reopen were stable and the runtime closed. The combined checklist item remains open for Task 6 v2 worker requalification and full PDF/reference/evaluation canary.
