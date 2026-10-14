# RL-MVP-007D-EMERGENCY-REAL-INFERENCE — owner-approved bounded task

**State:** OWNER APPROVED for task packet publication, isolated-branch implementation and conditional zero-cost local runtime qualification. **NOT IMPLEMENTED / NOT REVIEWED / NOT MERGED / NOT DEPLOYED.** E0065.
**Owner authorization:** Lead 3 conversation, 2026-10-13 America/New_York: bounded scope, pinned acquisitions only after verified hashes/licenses/compatibility/disk capacity, independent QA/security + Research review, separate merge approval; no private PDFs, paid calls, deployment or scientific scoring changes.
**Starting main:** `62124fa47b093e5e9a5383c1fd5ba5d055736da9` / E0064 (refresh HEAD/epoch/holds before work). **Branch:** `codex/rl-mvp-007d-emergency-real-inference` (new isolated branch). **Implementer:** Backend/Codex. **Consumers:** Frontend, Packaging, QA, Research, Lead. 
**Contract:** [API v0.2](../API_CONTRACT_V0_2.md). v0.1 remains intact until separately approved integration.
**Requirements:** R01-R05, R07-R09, R11-R12; DEC-001/002/003/004/005/007/008/009/013/015/022; E0043 portable local delivery. D02-D06 are not approved scientifically/institutionally.

## Objective
One locally testable *synthetic-only* real-model vertical slice:
```
PDF upload -> verified isolated PDF worker -> authentic immutable PredictionSource and text targets
-> deterministic Task 4 run -> one genuine pinned Ollama request per target
-> immutable ModelAttempt -> v0.2 API results -> existing browser displays predictions
```
No numeric scoring, Task 6 changes, scientific validity claim, arbitrary reference trust, private PDFs, public hosting/deployment, general distribution or production rollout. Temporary browser heuristic remains a separately labeled, nonauthoritative experimental feature and never substitutes for failed Ollama inference.

## Execution order and mandatory resource gates
**G0 — no install/download/build/runtime before this gate passes.**
- Refresh main, relevant task packets/handoffs and exact code/branch diff; inspect current disk capacity and estimated peak *real* Podman machine/image/build, Ollama, model, wheels, logs and rollback headroom. Previous preflight saw only ~3 GiB free: **do not proceed** unless sufficient documented reserve exists; don't delete unrelated/user files. Stop and request a user-approved remedy if insufficient.
- Choose and freeze exact official-source distribution URLs and complete SHA-256/signature evidence for Podman macOS arm64 runtime/machine and official Ollama macOS arm64 runtime. Verify license terms and supported OS/hardware. Freeze nonzero immutable base/machine/worker image digests (including build output post-verification), locked Python dependencies, license/SBOM evidence and model manifest/full blob digests. Never use a truncated model ID as verification. Proposed only: `qwen2.5:1.5b-instruct-q4_K_M` (model/version/license/hardware must be verified; no automatic substitution). Any missing license, hash, signature, source, dependency, cost or compatibility: **STOP**.
- Download/install only the verified, zero-cost artifacts necessary to satisfy the frozen inventory. Authorize rootless Podman machine create/start/stop, isolated image build/inspect and synthetic canaries, then Ollama loopback-only startup and model acquisition/inference using approved synthetic documents only. No network for PDF-processing container; downloads/network during explicitly verified acquisition only. Any unexpected paid requirement: STOP.

**G1 — code/test implementation on isolated branch**, in parallel with approved immutable preflight where feasible, but no runtime bypass:
- Preserve application-owned verified worker and reference isolation. Fix incomplete PDF worker Containerfile locked dependency assembly and the bootstrap qualification path rather than flipping `runtime_verified` to true without observed isolated canaries. Retain fail-closed defaults.
- Use application-owned locked Ollama verifier, 127.0.0.1 only, proxy/redirect prohibition, exact version/full manifest digest/model checks; no caller-injected trusted flag, adapter or transport.
- `PredictionService` constructs deterministic immutable run from source ID/canonical hash, ordered target versions, exact model/prompt/settings, redacted-document-only, full shared context when permitted, tools off, one attempt. Timestamp from immutable document creation record; persist every target enqueue before dispatch. Target-specific dispatch only, no unrelated queue drain. GET/reconnect never dispatch. Ambiguous provider timeouts/crashes stay IN_DOUBT.
- API results via validated RunStore, no fake targets; frontend displays page/region/attempt/prediction safely as text and keeps `UNKNOWN`/`NONE` and both scores null. No Task 6 evaluation.
- Rebuild existing frontend deterministically, verify hashed assets, manifest integrity, real browser flow. Preserve existing routes/controls and no public network binding.

## Authorized implementation file scope
Exactly these paths may change/create as relevant; unused paths should remain unchanged:
- Backend: `src/redaction_lab/application/application_store.py`, NEW `src/redaction_lab/application/inference_runtime.py`, NEW `src/redaction_lab/application/prediction_service.py`, `src/redaction_lab/api/app.py`, `src/redaction_lab/api/http.py`, `src/redaction_lab/store.py`, `src/redaction_lab/worker.py`.
- PDF worker packaging: `packaging/pdf-worker/Containerfile`, NEW `packaging/pdf-worker/requirements.lock`, `packaging/pdf-worker/runtime.lock`, `packaging/pdf-worker/README.md`.
- Model/local packaging: NEW `packaging/model-runtime/runtime.lock`, `packaging/local/launch.sh`, `packaging/local/preflight.sh`, `packaging/local/manifest.json`, `packaging/local/README.md`.
- Frontend: `web/src/api.ts`, `web/src/App.tsx`, `web/src/styles.css`, `web/dist/index.html`, replacement/retention of precisely the existing generated hashed JS/CSS assets under `web/dist/assets/` (no source maps, unrelated generated files).
- Tests: `tests/application/test_application_store.py`, `tests/application/test_document_worker.py`, NEW `tests/application/test_inference_runtime.py`, NEW `tests/application/test_prediction_service.py`, `tests/test_adapter.py`, `tests/test_worker.py`, `tests/api/test_app.py`, `tests/api/test_http.py`, `tests/security/test_pdf_worker_container.py`, `tests/packaging/test_local_preflight.py`, `tests/packaging/test_local_static.py`, NEW `tests/acceptance/test_real_inference_demo.py`, `web/tests/contract.test.js`, `web/tests/build.test.js`.
- Exactly one unique Backend task handoff at `docs/project/handoffs/RL-MVP-007D-backend-<UTC>-<shortid>.md`.
The API v0.2 and this packet are Lead-owned files already published to main: specialists must not rewrite these or canonical coordination documents. Any Task 3/6, DB-schema, detector/canonicalizer, reference-authority, dependency manifest outside stated scope, new route or additional file is **AMENDMENT REQUIRED**; no silent changes.

## Required TDD and evidence
Prove failure closed when runtime unverified; isolated-only uploaded-PDF parsing; nonce/hash/project/role/protocol, image digest and target ordering; complete reference-only-field absence; frozen independent context across multiple targets; one target/attempt and immutable identity; no retries on duplicate process, reconnect or ambiguous request; IN_DOUBT on crash/timeout; provider identity/digest mismatch fails closed; restart canonical run membership; cross-project/source/run attempt rejection; distinct REFUSED/TIMEOUT/MALFORMED/ERROR; safe UI escaped text; null verified/experimental scores; temporary predictor never used as substitute; loopback-only inference and offline PDF worker; browser upload -> process -> predictions -> shutdown/restart. Include focused and full pytest, Node/Chrome, compile/dependency/hash/license/scope audit, exact commands/results and NOT RUN. No one may claim real PDF/inference was demonstrated unless observed with approved synthetic fixtures and pinned local model.

**Review:** publish exact implementation SHA and branch HEAD + handoff. Independent QA/security and Research each review the same exact candidate and run what is within their authorized scope; neither agent PASS substitutes for D03-D06 scientific approval. Lead reconciles and requests separate owner merge approval. Do not merge/deploy/publish recipient package without it.

**Rollback:** abandon isolated branch before merge; after authorized merge revert normally; runtime cleanup only with separate safe authorization, retain existing application evidence.
**Stop:** insufficient disk (previously ~3 GiB), missing trusted model/image digests or licenses, Podman/Ollama hardware incompatibility, non-loopback inference, reference leakage, host-side untrusted PDF parsing, duplicate dispatch, new schema, Task 3/6 changes, out-of-scope files, costs, private data, or test/security blockers. Record NOT RUN and blocker, request scoped amendment. No force push, paid services or public deployment.
