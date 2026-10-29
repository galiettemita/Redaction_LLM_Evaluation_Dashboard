# RL-MVP-007D E0070 — Correction 02 execution

State: OWNER AUTHORIZED / ACTIVE  
Owner: Codex Backend under RL-OPS-002  
Baseline: `f0423defa7b5263c3ffac6658124b13e9ba35227`  
Existing candidate: `f244d1337e51dd188cd2253f3845c5a3d243e144`

## Objective

Implement the two findings already specified and scope-confirmed in [the E0069 plan](RL-MVP-007D-E0069-CORRECTION-02-PLAN.md) as one correction:

1. Replace macOS-incompatible `/dev/fd` version execution with audited absolute-path execution bracketed by retained-FD path identity and digest checks.
2. Close the supervisor lifetime writer unconditionally and idempotently even when the supervisor has already exited.

## Exact implementation scope

- `src/redaction_lab/application/inference_runtime.py`
- `tests/application/test_inference_runtime.py`
- one unique Backend handoff

No new dependency, schema, public API or architecture change. Preserve existing loopback, ownership, fail-closed, immutable experiment and reference-isolation boundaries.

## Evidence and review

Use TDD with adversarial before/during path substitution, version failure/exception cleanup, already-exited supervisor cleanup, repeated idempotent cleanup and descriptor-leak coverage. Run focused tests, full permitted Python and Node regressions, compilation, lock checks and exact diff/file-scope audits. Record tests not run.

Publish an exact implementation SHA, request fresh independent automated QA/security and research-semantics review, fix demonstrated Critical/Important defects under the same grouped scope, and integrate only after the exact candidate and regression evidence pass.

## Operational limits and stop conditions

Do not install/download software, start Ollama, perform real inference or PDF processing, use private data, incur cost, deploy publicly or alter scientific scoring. Stop for any required file outside this scope, unresolved critical security issue or changed integration contract; otherwise continue through correction and review without another owner prompt.
