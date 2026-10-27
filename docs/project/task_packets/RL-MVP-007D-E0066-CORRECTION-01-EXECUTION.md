# RL-MVP-007D E0066 Correction 01 — Execution and One-File Scope Amendment (E0068)

**STATE: OWNER APPROVED FOR CODE-ONLY IMPLEMENTATION; NOT IMPLEMENTED, NOT REVIEWED, NOT MERGED.**

**Owner authorization:** 2026-10-27, Lead 3 conversation. Owner explicitly authorizes one grouped four-fix code-only Correction 01; adds exactly `src/redaction_lab/adapters/ollama.py` to the existing E0066 source allowlist; permits changes only to the six source/test files listed below plus one unique Backend handoff; requires TDD, focused/full permitted tests, additive isolated-branch commits and fresh exact-SHA independent QA/security and Research reviews. No downloads, installs, real PDF processing, real inference, paid calls, deployment or merge.

**Integration baseline at authorization:** `cba25ffec76ded1dc87adc4e4c6fb5cb567ad81a` / E0067. Refresh HEAD, decisions, holds and relevant changes at execution time.
**Existing implementation branch:** `codex/rl-mvp-007d-emergency-real-inference`; published Backend HEAD `0998af7afb0218e9bceebe1eb571a62228133c9f`; challenged exact code `e6669c2234dbb683225b40e3642551092628e6aa`.
**Parent documents:** [Correction 01](RL-MVP-007D-E0066-CORRECTION-01.md), [E0066 Code-Only Amendment](RL-MVP-007D-EMERGENCY-CODE-ONLY-AMENDMENT-01.md), [E0065 emergency packet](RL-MVP-007D-EMERGENCY-REAL-INFERENCE.md), [API v0.2](../API_CONTRACT_V0_2.md).
**QA reports:** `qa/rl-mvp-007d-e0066-review-e6669c2` @ `d99c57bdb9a2aaf58bcdee1cbcc4d3a7d3c223c3`; `qa/rl-mvp-007d-e0066-review-e6669c2-qa2` @ `2f39c26cda6b13344abf558777ceb981687a06af`. Both CHANGES_REQUESTED. Research verdict unverified; require fresh review.

## Exact authorized source/test file scope

Modify only:
1. `src/redaction_lab/application/inference_runtime.py`
2. `src/redaction_lab/application/prediction_service.py`
3. `src/redaction_lab/adapters/ollama.py` **(newly added one-file scope authorization)**
4. `tests/application/test_inference_runtime.py`
5. `tests/application/test_prediction_service.py`
6. `tests/test_adapter.py`

Plus **one uniquely named Backend handoff** under `docs/project/handoffs/` on the same approved branch. No other implementation, tests, dependencies, build artifacts, configs, schemas or canonical project files.

## Four grouped required corrections

1. **Crash-safe Ollama process ownership:** Implement an in-module standard-library supervisor with parent-lifetime pipe (or equally robust existing-file design). Retain verified executable FD and all security/attestation checks, never adopt unknown listeners. On abrupt parent death supervisor kills/reaps child. Normal close, startup failure, child exit and bounded cleanup work. Test with harmless local subprocesses only, not Ollama.
2. **Model authority before mutation:** Explicitly bind verified runtime model ID to approved service `MODEL_ID` before constructing RunDefinition or persisting any run/intent. Consistently substituted model/provider values must fail before mutation with owned runtime cleaned up; corrected approved runtime remains usable. Verify all related provenance.
3. **Oversized response semantics:** In the actual stdlib Ollama adapter transport, bounded responses over `MAX_RESPONSE_BYTES` must produce `MALFORMED`, while timeout is `TIMEOUT` and HTTP/connection errors are `ERROR`. Test real transport against a synthetic ephemeral loopback HTTP fixture and boundary/cleanup conditions. No actual model call.
4. **Canonical semantic run identity:** Derive versioned deterministic run ID and RunDefinition from one canonical frozen run-intent including project/source/canonical hash/version, ordered target IDs/versions, model/config/full digest, run version, condition, prompt/settings, common context budget/policy, attempt policy, tools and budget/service identity. Test individual field changes, stable restarts and explicit legacy branch-only ID rejection without rewriting immutable records or changing public API v0.2.

## Execution and evidence

Run TDD, scoped corrections as one additive series on the existing isolated branch. Verify source-only trust isolation, target independence, immutable attempts, IN_DOUBT/no implicit retry, cross-project provenance, null scores, fail-closed PDF runtime and v0.1/v0.2 boundaries. Run focused and full **permitted** Python and Node tests, compilation, lock check and diff/scope checks; don't install missing tools. Report exact commands/results and NOT RUN. Keep historical v0.1 bundle blocked; no unapproved frontend build.

Before delivery recheck current main. Publish exact corrected code SHA, branch HEAD and one unique Backend handoff with changed paths/tests/blockers; **READY_FOR_INDEPENDENT_REVIEW**, never self-VERIFIED. Require independent QA/security and Research reviews of that exact corrected code SHA. Owner authorizes merge only later, separately.

## Stop conditions

STOP and report AMENDMENT_REQUIRED for any need to change a seventh source/test path, introduce helpers/dependencies, modify DB schema, Task 3/6/detection/reference authority, run real PDF or inference, install/download Podman/Ollama/model/wheels, incur money, deploy or merge. Keep the original 15 GiB runtime storage gate unchanged. No force-push or unrelated-file deletion.

**Publication of this amendment grants code-only correction execution, not runtime qualification, scientific approval, merge or release.**
