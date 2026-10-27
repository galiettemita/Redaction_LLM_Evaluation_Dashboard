# RL-MVP-007D — E0066 Correction 01: grouped QA defects

**STATE: PACKET PUBLICATION APPROVED; CORRECTION IMPLEMENTATION NOT YET AUTHORIZED BY THIS APPROVAL.**  
**Coordination epoch:** E0067 (proposed publication update).  
**Owner authorization:** 2026-10-27, Lead 3: approve preparation and publication of grouped Correction 01 covering four independently reported QA findings; keep any implementation code-only within existing E0066 paths wherever possible, TDD and fresh independent QA/Research reviews; seek explicit approval if additional files or dependencies required; no downloads, installations, real PDF processing, inference, spending, deployment or merge.  
**Integration baseline at publication:** `2e4001d52d5654ad3bc4b158e35353f872e69bfb`, E0066 (refresh before next action).  
**Exact challenged code SHA:** `e6669c2234dbb683225b40e3642551092628e6aa`.  
**Backend handoff branch HEAD:** `0998af7afb0218e9bceebe1eb571a62228133c9f` on `codex/rl-mvp-007d-emergency-real-inference`.  
**QA evidence:** `qa/rl-mvp-007d-e0066-review-e6669c2` @ `d99c57bdb9a2aaf58bcdee1cbcc4d3a7d3c223c3` and `qa/rl-mvp-007d-e0066-review-e6669c2-qa2` @ `2f39c26cda6b13344abf558777ceb981687a06af` (both CHANGES_REQUESTED). Research publication is independently required; do not infer Research PASS.  
**Requirements/decisions:** R04/R05/R08/R09/R11/R12; DEC-001/003/004/008/009/013, E0065/E0066; API contract v0.2 unchanged.  
**Implementer:** Backend/Codex, only after explicit correction-execution authorization and scope feasibility confirmation. **Reviewers:** independent QA/security and Research/Evaluation.

## Objective and exact bounded issues

Correct **as one grouped, test-first change** the following demonstrated E0066 defects. Do not implement new features or refactor unrelated code.

1. **Crash-safe owned Ollama process lifecycle (HIGH).** On abrupt parent process death, an owned local Ollama process must not remain orphaned and block subsequent valid startup. Propose an application-owned watchdog/supervisor or equivalently authenticated recovery, preserving retained verified executable FD, loopback-only binding, rejection of unknown listeners, normal close/kill behavior, no proxy/redirect and model-store provenance. TDD abrupt-parent-death using harmless subprocesses only; no real Ollama process. If an additional module, helper executable, shell script, new dependency, OS-level permission or out-of-scope path is needed, STOP with exact amendment request; do not improvise.
2. **Fail-before-mutation model authority (HIGH).** After verifying the runtime, compare its verified model identity against the owner-approved service model identity **before** constructing or persisting RunDefinition/target intents. Include all relevant model fields, explicit lifecycle cleanup on rejection. TDD a consistently substituted `model_id` plus `provider_model_id` with otherwise internally consistent attestations. No new run/intent/attempt when rejected, and corrected runtime remains usable.
3. **Oversized provider response classification (MEDIUM).** Real stdlib HTTP transport exceeding `MAX_RESPONSE_BYTES` must be `MALFORMED`, not generic `ERROR`; distinguish actual transport failures and timeouts. TDD with a synthetic local ephemeral HTTP server and the real stdlib transport code (no Ollama/provider). Respect bounded reads and connection cleanup.
4. **Complete, versioned deterministic run identity (MEDIUM).** Include every behavior-affecting frozen run semantic (run version, condition, common-context budget, context policy, tools/permissions, budget label/service identity, model/prompt/config/digest and ordered target/version/source hashes) in deterministic canonical run intent. Changing any meaningful field must change ID; identical intent remains stable across restart; preserve source/project binding. Avoid accidental compatibility with previously persisted run IDs: document how old branch-only data is detected or fails closed, without changing existing immutable records.

## Preliminary allowed files (strictly E0065/E0066 preauthorized paths)

Likely: `src/redaction_lab/application/inference_runtime.py`, `src/redaction_lab/application/prediction_service.py`, `src/redaction_lab/store.py`, `src/redaction_lab/worker.py`, `tests/application/test_inference_runtime.py`, `tests/application/test_prediction_service.py`, `tests/test_worker.py`, `tests/test_adapter.py`, `tests/api/test_app.py`. **Important:** `src/redaction_lab/adapters/ollama.py` is NOT in the original E0065 file allowlist; if the oversized-response fix requires touching it, get a narrow explicit owner amendment **before** editing. Likewise a watchdog supervisor file, dedicated helper file, test or build dependency outside the E0065 allowlist requires prior approval. Do not reinterpret this publication approval as authority to add them.

Only one task-scoped Backend handoff may be added under `docs/project/handoffs/`, on the existing isolated implementation branch, under a subsequently authorized correction task. Canonical files are Lead-owned; specialists do not edit them.

## Work sequence and acceptance evidence for subsequent approved execution

A. Inspect actual candidate and transitive callers/tests at exact SHA; provide a short **scope feasibility** report mapping each finding to existing allowed paths. If any finding cannot be corrected within scope, return `AMENDMENT_REQUIRED` listing exact file/dependency additions and rationale; no change to code yet.  
B. Once correction execution and any scope additions are approved, write failing negative tests then minimal fixes as a single grouped implementation. Preserve tests against reference leakage, immutable attempts, deterministic enqueue, concurrent requests, retries, `IN_DOUBT`, model identity, null scores, API v0.1 compatibility and fail-closed runtime.  
C. Run focused/full permitted Python tests, relevant Node tests, compile, `uv lock --check`, scope/diff audit, and mark unavailable TypeScript/browser/runtime tests NOT RUN; do not install dependencies.  
D. Publish exact corrected code SHA, isolated branch HEAD and one unique Backend handoff. Independent QA/security and Research review **the exact corrected SHA**. Neither previous QA review nor an internal helper review is sufficient.  
E. Lead reconciles both reviews, rechecks live HEAD, and requests **separate owner merge approval**. Runtime/model qualification and scientific validation remain separate.

## Hard prohibitions / stop conditions

No Podman/Ollama or model/image/wheel download or installation, no containers/VM, no real or synthetic PDFs through a live worker, no genuine inference, paid calls, private data, network-provider calls, public deployment, merge, Task 3/6 changes, database migrations/schema changes, reference trust changes, scoring formula or verified-score claims. Synthetic local test subprocesses and loopback HTTP fixtures are permitted within the already authorized mock/synthetic code-test boundary. Do not force-push; do not destroy existing unpublished work.

**Publication state:** PACKET PUBLISHED on main; **implementation NOT AUTHORIZED BY THIS PUBLICATION ALONE**, NOT STARTED, NOT REVIEWED, NOT MERGED.
