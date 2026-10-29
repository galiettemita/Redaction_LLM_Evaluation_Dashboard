# RL-RUNTIME-009A — PDF worker feasibility and qualification

Status: ACTIVE under RL-OPS-002 standing engineering authority. Decision epoch E0071.  
Baseline: `34e4c06f8840d01ca5c5b99be778467835c79c28`.  
Accountable role: Backend / Infrastructure; Engineering Lead integrates after independent exact-candidate review.

## Objective

Qualify the existing isolated PDF-worker design on this Apple Silicon Mac using only free, official, integrity-verified artifacts and synthetic project fixtures. Preserve the application-owned authority boundary, fail-closed runtime lock, offline/no-mount/no-network worker execution, immutable evidence, and all scientific/data/deployment gates.

## Preflight and phased authority

Phase 1 is read-only apart from this task record and its handoff: inventory hardware, disk, existing runtimes and code; verify exact official sources, versions, complete hashes/signatures, licenses, security advisories, architecture support, transitive Python wheel inventory, base/machine image provenance, SBOM tooling and estimated peak storage. Official release assets may be downloaded into a task-specific temporary directory solely for byte-hash, code-signature/notarization and archive inspection; they must not be installed or executed and are removed after the retained verification evidence is recorded. No install or runtime execution occurs before that evidence is complete.

If Phase 1 passes with a documented rollback reserve, Phase 2 may acquire/install only the frozen zero-cost Podman/Python-wheel/base-image artifacts, create the dedicated rootless no-volume machine, assemble the worker offline, and run synthetic-only adversarial qualification. Stop the affected phase for a password/credential request, paid term, missing integrity/license evidence, unsupported host, inadequate reserve, unresolved Critical security risk, or unexpected host sharing/network exposure.

## Authorized paths and actions

Source/package changes are limited to:

- `packaging/pdf-worker/Containerfile`
- `packaging/pdf-worker/requirements.lock`
- `packaging/pdf-worker/runtime.lock`
- `packaging/pdf-worker/README.md`
- `packaging/pdf-worker/containers.conf`
- `scripts/build-pdf-worker.sh`
- `scripts/verify-pdf-worker.sh`
- `src/redaction_lab/application/isolation.py`
- `src/redaction_lab/application/worker_protocol.py`
- `src/redaction_lab/application/document_worker.py`
- `tests/security/test_pdf_worker_container.py`
- `tests/application/test_isolation.py`
- `tests/application/test_worker_protocol.py`
- `tests/application/test_document_worker.py`

New qualification artifacts may be added only under `packaging/pdf-worker/` for an SBOM, license/source inventory, and integrity manifest. One unique `docs/project/handoffs/RL-RUNTIME-009A-backend-<UTC>-<SHA>.md` is authorized. This task record may be updated with observed evidence. No database schema, API contract, prediction/reference contract, frontend, scoring, model-runtime, or shared canonical-state file is in scope.

Host actions are limited to zero-cost verified Podman installation if no privileged credential is required, dedicated rootless machine create/start/stop, exact image acquisition/build/inspect, offline/no-mount disposable canaries, and cleanup of task-created temporary/container state. Never delete unrelated user data or broaden host access.

## TDD and acceptance evidence

1. Existing unverified locks continue to fail before job claim or durable source mutation.
2. Exact Podman executable/version, rootless dedicated machine, no host volumes, base/worker digests and protocol are verified from application-owned state.
3. Build consumes only a complete hash-locked wheelhouse and exact digest-pinned base; runtime has no network, mounts, secrets, capabilities, writable root, elevated UID, unbounded resources or pulls.
4. Adversarial tests cover forged/mismatched digest, nonce/hash/project/role/protocol, excess output, timeout/crash cleanup, absent image/runtime, network and host-file canaries, and idempotent recovery.
5. Only project-generated synthetic PDFs are processed. Observed target/source identity must remain deterministic and reference fields must not enter prediction material.
6. Produce exact source/hash/license inventory and SBOM; run focused and full Python/Node regressions, compilation, lock/file-scope/diff audits, and independent exact-candidate security review.

## Stop conditions and exclusions

Stop or retain `runtime_verified: false` for inadequate disk reserve; missing/changed official source, digest, signature, license or architecture support; privileged credential requirement; runtime policy mismatch; any isolation canary failure; nondeterministic or unbound output; required regression failure; or need for an out-of-scope file/schema/contract change.

No private/restricted PDF, model acquisition or inference, provider call, paid service, scientific/benchmark approval, public deployment/distribution, clean-recipient claim, force push, or destructive cleanup is authorized. Qualification on this host is not institutional permission and is not a release claim.
