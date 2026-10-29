# RL-RUNTIME-009B — Local Ollama/model qualification

Status: ACTIVE under RL-OPS-002 standing engineering authority. Decision epoch E0071.
Baseline: `f85204fc142a5a4c2cece30f401b3566d8f45a25`.
Accountable role: Backend / Infrastructure; Engineering Lead integrates after independent exact-candidate review.

## Objective

Qualify one zero-cost application-owned local Ollama runtime and the already frozen `qwen2.5:1.5b-instruct-q4_K_M` operational canary on this Apple Silicon Mac using exact official sources, hashes, licenses and synthetic-only prompts. Preserve literal-loopback ownership, parent-death process supervision, exact model identity before mutation, immutable experiment records, bounded outcomes, null scores and every scientific/data/deployment gate.

This task does not approve a scientific model roster, benchmark, accuracy claim or private/lab-data use.

## Preflight and phased authority

Phase 1 is read-only apart from this task record and its handoff: recheck hardware/disk, inspect existing state, resolve exact official Ollama/model sources, versions, manifests, file sizes, hashes/signatures, licenses, advisories, architecture support, SBOM inputs and estimated peak storage. No executable or model blob runs during Phase 1.

Phase 2 may proceed only if all acquired artifacts are free, officially sourced, immutable/hash-verifiable, license-compatible and leave at least 8 GiB host free space after the complete runtime/model plus rollback inputs are staged. It may install only beneath the application root, run only literal-loopback Ollama under the existing application supervisor, and perform only synthetic prompts. Stop for a credential/password, paid term, missing integrity/license evidence, unsupported host, inadequate reserve, unresolved Critical risk, pre-existing listener, model identity mismatch or unexpected external exposure.

## Authorized paths and actions

Source/package changes are limited to:

- `packaging/model-runtime/runtime.lock`
- `packaging/local/manifest.json`
- `packaging/local/preflight.sh`
- `packaging/local/README.md`
- `src/redaction_lab/application/inference_runtime.py`
- `src/redaction_lab/application/prediction_service.py`
- `src/redaction_lab/adapters/ollama.py`
- `tests/application/test_inference_runtime.py`
- `tests/application/test_prediction_service.py`
- `tests/test_adapter.py`
- `tests/packaging/test_local_preflight.py`

New provenance, integrity, SBOM and license/source artifacts may be added only under `packaging/model-runtime/`. One unique `docs/project/handoffs/RL-RUNTIME-009B-backend-<UTC>-<SHA>.md` is authorized. This task record may be updated with observed evidence.

Host actions are limited to task-specific temporary downloads for verification; application-owned portable Ollama payload/model-store acquisition; literal-loopback supervised runtime start/stop; synthetic-only inference and failure canaries; and exact cleanup of task-created temporary state. No schema, API, PDF-worker, frontend, scoring, evaluator or shared canonical-state change is in scope.

## TDD and acceptance evidence

1. Unverified/missing/substituted locks, executable, model inventory, manifest digest, tag or API identity fail before durable run/intent mutation.
2. Runtime paths resolve beneath the application root and reject symlinks, aliases, unsafe ownership/modes and before/after identity changes.
3. The application owns the literal-loopback process lifecycle; parent/lifetime-pipe death, timeout, malformed/oversized/error outcomes and idempotent cleanup are adversarially covered.
4. Exact Ollama and model source/hash/license inventories and a machine-readable SBOM are published; no credentials, raw private prompts or model output are committed.
5. Actual synthetic inference verifies exact model identity, immutable provenance, deterministic run identity, no reference input, repeat-dispatch behavior and bounded resource measurements without asserting semantic accuracy.
6. Focused/full Python and Node regressions, compilation, lock/file-scope/diff checks and independent exact-candidate security review pass before integration.

## Stop conditions and exclusions

Stop or retain `runtime_verified: false` for inadequate reserve; missing/changed source, digest, signature or license; privileged installation; pre-existing/unowned listener; runtime/model identity mismatch; parent-death/cleanup failure; required regression failure; or need for an out-of-scope contract/schema change.

No private/restricted PDF or reference data, paid provider, commercial credential, benchmark/scientific validation, public deployment/distribution, clean-recipient claim, force push or destructive cleanup is authorized. Qualification on this host is not institutional permission or a release claim.
