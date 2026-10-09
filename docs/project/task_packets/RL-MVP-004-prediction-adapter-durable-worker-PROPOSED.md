# RL-MVP-004 — Redacted-only prediction adapter and durable one-shot worker

**Status: PROPOSED, NOT APPROVED FOR IMPLEMENTATION.** Owner approval requested. Backend/Codex would own implementation; QA and Research independently review exact candidate; Lead integrates after separate merge authorization.
**Baseline:** main `38157bd1b681b3e6e601223a90ff6dff52fc47f7`, epoch E0033. Refresh HEAD/epoch before work. **Deadline:** October 12, 2026.
**Sources:** AGENTS.md; DEC-001/004/008/009/015/017/020/022; Task 4 of `docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md`; current contracts/canonicalizer. Tasks 1–3 are merged.

## Objective

Implement provider-neutral prediction adapter, local-only Ollama-compatible transport, durable SQLite job state and immutable one-shot attempts. One independent prediction per supported text target from the same frozen **redacted-only** context. Preserve future multi-model extensibility without assuming a final provider/model roster. No evaluator, UI, cloud, external APIs or deployment.

## Proposed allowed files

Create `src/redaction_lab/adapters/base.py`, `src/redaction_lab/adapters/ollama.py`, `src/redaction_lab/store.py`, `src/redaction_lab/worker.py`, `tests/test_adapter.py`, `tests/test_worker.py`, plus ONE unique `docs/project/handoffs/RL-MVP-004-backend-<UTC>-<ID>.md`. If `adapters/__init__.py`, new dependencies, a contract modification or additional files are necessary, stop and request a scoped amendment. No edits to existing contracts, Task 1–3 code/tests, shared docs or pyproject.toml. Use stdlib HTTP/SQLite where feasible. New isolated Task-4 branch/worktree only.

## Required boundaries

1. Implement `build_prediction_manifest(doc, target_id, run)` and typed `PredictionAdapter.predict(manifest)`. Validate project/target/version/canonical hash, immutable prompt/model/settings and common context budget. Each request marks only one target and leaves all others hidden. Reference PDFs, revealed text, mappings, filenames, metadata, prior guesses and evaluator data must be structurally absent from serialized manifests and prompts. Fail closed if an input cannot fit the shared budget.
2. Strict response parsing and immutable `ModelAttempt` provenance: attempt/run/target/model/config IDs, request/response hashes, timestamps and distinct SUCCESS/REFUSED/TIMEOUT/ERROR/MALFORMED. Never interpret timeout or refusal as an incorrect factual prediction.
3. Allow only explicit numeric loopback HTTP endpoint `127.0.0.1` with validated port; reject DNS names, non-loopback, redirects, proxies, credentials and other schemes. Tests use injected mock transport; no real calls, model downloads or installations by default.
4. SQLite `RunStore` uses atomic claim/complete, unique scoped job keys, durable pre-dispatch intent, one attempt per run/target/model/attempt-policy and restart-safe idempotency. Crash/ambiguous timeout yields explicit internal IN_DOUBT/unknown outcome, no hidden retries, no false success. Do not misrepresent in-doubt as ordinary factual failure; if public JobState cannot represent it safely, stop for contract review.
5. Test with TDD RED/GREEN: no reference serialization, frozen context for all targets, duplicate delivery, two concurrent claims, restart after dispatch, ambiguous timeout, malformed/refusal/error, blocked remote endpoint, redirects/proxies, hidden selectable text and deterministic request/attempt IDs. Run focused/full pytest, compileall, dependency check, git diff --check; report NOT RUN.

## Local model feasibility and spending

This packet **proposes** read-only Task-0 machine preflight (OS/RAM/GPU/disk, installed runtime/model IDs, license/offline capability and context/latency constraints). Do not install, download, provision or spend. A real local inference is **NOT** authorized by approval of this packet unless owner explicitly authorizes it separately after a passing preflight. Mock tests do not satisfy the real-model demonstration milestone; if no authorized local model exists, label real-model demonstration BLOCKED.

## Stop / publication

Stop for reference leakage, forged provenance, ambiguous retries, non-loopback egress, hardware/license uncertainty, required out-of-scope file/contract change, new decision hold or cost. Publish exact implementation SHA and unique Backend handoff on approved isolated branch; fresh independent QA and Research reviews before a separate owner merge. No Task 5+, scoring validation, private data, paid provider calls, model downloads or deployment.

**Owner approval requested:** authorize this bounded mock-tested Task-4 implementation and read-only local-model preflight, but NOT actual model inference or additional spending.
