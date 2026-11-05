# Experimental Product Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a genuine local-Qwen PDF reconstruction application with conservative user-reference alignment, clearly labeled automatic experimental scores, a document-centered browser workspace, and an authenticated working HTTPS demonstration link.

**Architecture:** Extend the isolated PDF-worker protocol to return bounded visible reference text and persist it through an additive migration. Add a pure versioned experimental scorer and an application evaluation service that binds references, attempts, mappings, and summaries without changing verified-score semantics. Expose API v0.3 to a rebuilt React workspace, then serve the unchanged loopback application through a strict authenticated tunnel gateway.

**Tech Stack:** Python 3.12.14, Pydantic, SQLite, pypdf/pdfplumber inside the isolated worker, Ollama/Qwen2.5 1.5B, React/TypeScript/Vite, standard-library WSGI/HTTP, ngrok.

**Spec:** `docs/superpowers/specs/2026-11-05-experimental-product-completion-design.md`

## Global Constraints

- Preserve R01–R12, DEC-001–DEC-022, immutable provenance, one-shot attempts, and reference exclusion from prediction inputs.
- Owner clarification dated 2026-11-05 authorizes clearly labeled experimental numeric evaluation before formal scientific validation.
- `verified_score` remains null; only `score_status = EXPERIMENTAL` may carry a number.
- Missing, partial, unreadable, ambiguous, conflicting, or unprocessed truth always yields null/unknown, never zero.
- Experimental method v1 uses weights 40% token F1, 25% ordered-token agreement, 20% character-trigram F1, 15% critical-detail agreement; negation mismatch cap 35, quantity/date mismatch cap 60, one-decimal rounding.
- Only the installed integrity-pinned `qwen2.5:1.5b-instruct-q4_K_M` is enabled; no synthetic adapter or rule-based demo may be presented as model inference.
- No paid services, private research data, public unauthenticated deployment, or credential material in Git.
- The link is an owner-only authenticated demonstration over one local workspace; it is not multi-user authorization.
- Every product behavior change follows red-green-refactor TDD and receives exact-candidate independent review.

## Review Focus

- A reference containing prompt-like instructions must remain evaluation-only and never enter the prediction request; Task 4 adds an end-to-end manifest assertion.
- A repeated or one-sided anchor must remain unknown rather than selecting a convenient span; Task 2 adds adversarial mapping cases.
- A prediction with the same words but changed negation/quantity/date must receive the specified cap and warnings; Task 3 adds exact score assertions.
- A refresh during or after a technical failure must not create a new attempt or erase the actionable error; Tasks 4 and 5 add API/browser regressions.
- A wrong public Host/Origin, unauthenticated request, or direct Ollama route must be rejected by the tunnel gateway; Task 6 adds socket-level gateway tests.

---

### Task 1: Owner decision, API v0.3 contract, and bounded task records

**Files:**
- Create: `docs/project/API_CONTRACT_V0_3.md`
- Create: `docs/project/task_packets/RL-EXP-015-EXPERIMENTAL-EVALUATION.md`
- Create: `docs/project/task_packets/RL-UX-016-EXPERIMENTAL-WORKSPACE.md`
- Create: `docs/project/task_packets/RL-LINK-017-CONTROLLED-DEMO.md`
- Modify: `docs/project/DECISIONS.md`
- Modify: `docs/project/CURRENT_STATE.md`
- Modify: `docs/project/CHANGELOG.md`
- Modify: `docs/project/AGENT_HANDOFF.md`

**Interfaces:**
- Consumes: owner clarification and the approved design.
- Produces: DEC-023, epoch E0072, API v0.3 response shapes, exact task scopes and acceptance gates for Tasks 2–6.

- [x] **Step 1: Write the contract examples and task checklists with explicit experimental/null invariants.**
- [x] **Step 2: Validate links, unique IDs, decision supersession language, and that no task authorizes private data or paid resources.**
- [x] **Step 3: Record live `main` SHA immediately before the canonical documentation commit.**
- [x] **Step 4: Commit with message `docs: authorize experimental product completion`.**

### Task 2: Isolated reference extraction and experimental alignment provenance

**Files:**
- Modify: `src/redaction_lab/application/worker_protocol.py`
- Modify: `src/redaction_lab/application/document_worker.py`
- Modify: `src/redaction_lab/application/application_store.py`
- Create: `src/redaction_lab/application/migrations/0002.sql`
- Modify: `src/redaction_lab/reference.py`
- Modify: `src/redaction_lab/contracts.py`
- Test: `tests/application/test_worker_protocol.py`
- Test: `tests/application/test_document_worker.py`
- Test: `tests/application/test_application_store.py`
- Test: `tests/application/test_migrations.py`
- Test: `tests/test_reference.py`

**Runtime boundary:** Task 2 is source/test-only. Task 6 explicitly owns the `pdf-worker-v2` image/lock rebuild and requalification after reviewed Task 2 source; no live v2 processing inherits the v1 qualification.

**Interfaces:**
- Consumes: `WorkerRequest`, `WorkerResponse`, `CanonicalRedactedDocument`, `ReferenceMapping`, uploaded `document_pairs`.
- Produces: `StoredReferenceSource`, `ApplicationStore.reference_source(version_id)`, worker protocol `pdf-worker-v2`, and `align_experimental_reference(redacted, reference_text, ...) -> list[ReferenceMapping]` with provenance `USER_SUPPLIED_EXPERIMENTAL`.

- [x] **Step 1: Add failing protocol tests requiring bounded canonical reference text/hash/version only for processable REFERENCE responses and forbidding it for failures/redacted-only misuse.**
- [x] **Step 2: Run focused protocol tests and confirm failures are caused by missing v2 fields/validation.**
- [x] **Step 3: Implement worker v2 extraction and strict response bounds without exposing annotations or changing redacted prediction material.**
- [x] **Step 4: Add failing migration/store/worker tests for immutable reference-source persistence, pair lookup, crash recovery, tamper rejection, and no Task-4 source binding.**
- [x] **Step 5: Run focused persistence tests and confirm the new records are absent.**
- [x] **Step 6: Implement additive migration, persistence, recovery, and reference worker completion.**
- [x] **Step 7: Add failing reference tests for unique complete spans, repeated anchors, partial revelation, mismatch, page shifts, and prompt-like reference text.**
- [x] **Step 8: Implement `align_experimental_reference` by reusing the existing conservative text-first core while keeping verified synthetic `align_reference` behavior unchanged.**
- [x] **Step 9: Run focused tests, then the full Python suite; commit `feat: persist isolated experimental reference evidence`.**

### Task 3: Versioned automatic experimental scoring and aggregation

**Files:**
- Create: `src/redaction_lab/experimental_scoring.py`
- Create: `src/redaction_lab/application/evaluation_service.py`
- Modify: `src/redaction_lab/contracts.py`
- Modify: `src/redaction_lab/evaluator.py`
- Modify: `src/redaction_lab/evaluation_store.py`
- Modify: `src/redaction_lab/summary.py`
- Create: `tests/test_experimental_scoring.py`
- Create: `tests/application/test_evaluation_service.py`
- Modify: `tests/test_contracts.py`
- Modify: `tests/test_evaluator.py`
- Modify: `tests/test_evaluation_store.py`
- Modify: `tests/test_summary.py`

**Interfaces:**
- Consumes: successful immutable attempts and `USER_SUPPLIED_EXPERIMENTAL` scoreable mappings from Task 2.
- Produces: `score_text_agreement(reference: str, prediction: str) -> ExperimentalScore`, experimental evidence schema `experimental-text-agreement-evidence-v1`, target evaluations, and document/model summaries.

- [x] **Step 1: Write failing pure-scoring tests for exact match, empty/invalid input, paraphrase limitation, repetitions, role reversal warning, unsupported additions, and changed number/date/negation caps.**
- [x] **Step 2: Run the scoring tests and verify they fail because the module/API is absent.**
- [x] **Step 3: Implement the exact versioned formula, subscores, warnings, hashes, caps, and one-decimal rounding.**
- [x] **Step 4: Write failing contract/store tests proving experimental numbers are permitted only under the new schema while legacy qualitative records reopen unchanged and verified scores remain null.**
- [x] **Step 5: Implement the new schema dispatch, deterministic identity, immutable persistence, and tamper detection.**
- [x] **Step 6: Write failing service/summary tests for eligible targets, unknown truth, refusal/timeout/malformed/error, zero denominators, equal-target document aggregation, equal-document model aggregation, and no cross-model blend.**
- [x] **Step 7: Implement `EvaluationService` and versioned experimental summaries; GET paths remain read-only.**
- [x] **Step 8: Run focused tests and the full Python suite; commit `feat: add transparent experimental accuracy scoring`.**

### Task 4: Genuine model reliability, API v0.3, and durable workflow

**Files:**
- Modify: `src/redaction_lab/adapters/ollama.py`
- Modify: `src/redaction_lab/application/inference_runtime.py`
- Modify: `src/redaction_lab/application/prediction_service.py`
- Modify: `src/redaction_lab/api/app.py`
- Modify: `src/redaction_lab/api/http.py`
- Modify: `packaging/model-runtime/runtime.lock` only if prompt/runtime identity versioning requires it
- Modify: `tests/test_adapter.py`
- Modify: `tests/application/test_inference_runtime.py`
- Modify: `tests/application/test_prediction_service.py`
- Modify: `tests/api/test_app.py`
- Modify: `tests/api/test_http.py`
- Modify: `tests/e2e/test_synthetic_workflow.py`

**Interfaces:**
- Consumes: Task 2 reference records, Task 3 `EvaluationService`, installed Qwen runtime, API v0.3 contract.
- Produces: provider-valid bounded prediction parsing, configurable trusted runtime root, process/evaluate orchestration, progress, mappings/evaluations/summaries in results.

- [x] **Step 1: Add failing adapter tests using realistic Ollama envelopes for valid JSON reconstruction, rejection of unstructured text, structured refusal, extra keys, wrong model, truncation, and malformed output.**
- [x] **Step 2: Run adapter tests and verify the valid real-provider cases currently become MALFORMED.**
- [x] **Step 3: Implement prompt v2 and strict bounded parsing without treating provider errors or arbitrary prose as success.**
- [x] **Step 4: Add failing runtime tests for one explicit absolute runtime root with owner/no-symlink/no-group-write checks and fail-closed default behavior.**
- [x] **Step 5: Implement configurable trusted runtime-root resolution without weakening file inventory/digest checks.**
- [x] **Step 6: Add failing API/E2E tests for reference-first processing, one attempt per target, evaluation creation only after terminal prediction, progress counts, experimental result shapes, null cases, reference absence from manifests, and GET-only reconnect.**
- [x] **Step 7: Implement API v0.3 orchestration and result serialization; preserve v0.2 stored-record compatibility.**
- [ ] **Step 8: Run focused tests, full Python suite, and a genuine synthetic Qwen canary after Task 6's v2 worker requalification prerequisite; require at least one persisted SUCCEEDED prediction before claiming Task 4 acceptance.**
- [x] **Step 9: Commit `feat: connect genuine inference to experimental evaluation`.**


Task 4 implementation evidence: full Python suite 856 passed; genuine prompt-v2 Qwen canary persisted one SUCCEEDED attempt using an authentic previously-qualified v1 isolated PDF source, with replay/reopen stability and cleanup. Step 8 remains open only for Task 6 v2 PDF/reference runtime requalification and full combined canary. This is not a v2 runtime acceptance claim.

### Task 5: Document-centered experimental React workspace

**Files:**
- Modify: `web/src/api.ts`
- Modify: `web/src/App.tsx`
- Modify: `web/src/styles.css`
- Delete: primary-flow imports/use of `web/src/temporaryPrediction.ts` (retain file only if legacy tests require historical compatibility)
- Modify: `web/tests/contract.test.js`
- Modify: `web/tests/build.test.js`
- Create: `web/tests/workspace.test.js`
- Modify: `web/package.json`
- Modify: `web/package-lock.json` only if an already-approved test dependency is indispensable
- Generate: exact `web/dist/` assets
- Modify: `packaging/local/manifest.json` for exact frontend binding
- Modify: `tests/packaging/test_local_static.py` only for necessary asset/contract checks

**Interfaces:**
- Consumes: API v0.3 `Health`, `Snapshot`, target attempts, mappings, experimental evaluations, and summaries.
- Produces: redacted/reference local PDF viewer, target selection, comparison/results panels, persistent experimental labels, friendly state rendering, and accessible interactions.

- [x] **Step 1: Add failing contract tests accepting only the exact v0.3 experimental shapes, multiple attempts per target/model identity, progress, null denominators, and rejecting numeric verified scores or missing method labels.**
- [x] **Step 2: Add failing workspace tests for file-object URL lifecycle, release toggle, keyboard target selection, error persistence after refresh, technical-state copy, reconnect without POST, and score labels/counts.**
- [x] **Step 3: Run Node tests and confirm failures describe the absent v0.3 workspace.**
- [x] **Step 4: Implement strict API parsing and the document-centered workspace; remove the rule-based demo from the primary product.**
- [x] **Step 5: Run Node tests, typecheck, accessibility interaction checks, production build, and audit.**
- [x] **Step 6: Rebind exact `web/dist` assets in `packaging/local/manifest.json`; run packaging/static tests.**
- [x] **Step 7: Commit `feat: ship experimental document evaluation workspace`.**

### Task 6: Owner-only authenticated gateway, launch evidence, and delivery

**Files:**
- Create: `src/redaction_lab/api/gateway.py`
- Create: `tests/api/test_gateway.py`
- Modify: `packaging/pdf-worker/Containerfile`
- Modify: `packaging/pdf-worker/runtime.lock`
- Modify: `packaging/pdf-worker/integrity-manifest.json`
- Modify: `packaging/pdf-worker/qualification-sources.json`
- Modify: `packaging/pdf-worker/sbom.cdx.json`
- Modify: `packaging/pdf-worker/README.md`
- Modify: `scripts/build-pdf-worker.sh`
- Modify: `scripts/verify-pdf-worker.sh`
- Modify: `tests/application/test_isolation.py`
- Modify: `tests/application/test_worker_protocol.py`, `tests/application/test_document_worker.py` only for v2 runtime acceptance
- Modify: `tests/packaging/test_local_preflight.py`, `tests/packaging/test_local_static.py`
- Modify: `packaging/local/launch.sh`
- Modify: `packaging/local/preflight.sh`
- Modify: `packaging/local/manifest.json`
- Modify: `packaging/local/README.md`
- Create: `docs/project/handoffs/RL-EXP-015-lead-<UTC>-<SHORT>.md`
- Modify: `docs/project/CURRENT_STATE.md`
- Modify: `docs/project/CHANGELOG.md`
- Modify: `docs/project/AGENT_HANDOFF.md`

**Runtime prerequisite:** After reviewed Task 2 source, rebuild the v2 PDF-worker image using pinned already-installed zero-cost dependencies and record observed hashes/SBOM/qualification. This substep precedes Task 4's live canary; gateway/delivery waits for all application tasks. Keep Task 2 source/test-only and never inherit v1 qualification.

**Interfaces:**
- Consumes: reviewed API v0.3 application on `127.0.0.1:8765`, configured exact public hostname, private basic-auth/ngrok policy outside Git.
- Produces: loopback gateway on `127.0.0.1:8766`, reviewed launch instructions, final handoff/checklist, and working authenticated HTTPS link.

- [ ] **Prerequisite: Rebuild/requalify the exact pdf-worker-v2 image and record source/image/inventory/SBOM/protocol/isolation evidence before any live v2 processing.**
- [ ] **Step 1: Write failing gateway tests for exact Host/Origin, auth, body/framing bounds, streaming-safe PDF upload, translated loopback headers, response headers, and rejection of any Ollama/direct arbitrary upstream path.**
- [ ] **Step 2: Run gateway tests and verify failure because no gateway exists.**
- [ ] **Step 3: Implement the smallest standard-library gateway and private configuration contract; no secrets or tunnel hostname are committed.**
- [ ] **Step 4: Extend preflight/launch tests for runtime-root, API v0.3, frontend integrity, gateway binding, occupied ports, and clean shutdown.**
- [ ] **Step 5: Run full Python and Node suites, typecheck/build/audit, packaging checks, genuine PDF/Qwen/evaluation canary, and authenticated browser workflow.**
- [ ] **Step 6: Dispatch exact-candidate whole-branch security/product review; correct all Critical/Important findings and rerun affected/full verification.**
- [ ] **Step 7: Recheck live `main`, reconcile, update all checklist/handoff records, and commit `docs: record experimental application delivery`.**
- [ ] **Step 8: Push normally, open/integrate the reviewed PR under RL-OPS-002, launch application/gateway/ngrok, and verify the returned HTTPS link through browser acceptance without exposing credentials in Git.**

## Self-review result

- Spec coverage: reference isolation, scoring, genuine model, UI, runtime-root, authenticated link, documentation, reviews, and null/scientific boundaries are assigned to Tasks 1–6.
- Known deferred product requirements: second/commercial models, permanent cloud hosting, multi-user authorization, and validated semantic scoring remain explicit non-goals rather than silent omissions.
- Type consistency: Task 2 mapping/source types feed Task 3; Task 3 results feed Task 4 API; Task 4 shapes feed Task 5; Task 6 only wraps the reviewed loopback interface.
- Review-focus cases are pinned to Tasks 2–6.
