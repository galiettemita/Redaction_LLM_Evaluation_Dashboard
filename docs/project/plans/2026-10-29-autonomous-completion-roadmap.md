# Redaction Lab autonomous completion roadmap

Baseline: `9952d84afe1cf987a4626a1ebf980815fbc44a0a` / E0071  
Authority: RL-OPS-002; confirmed requirements R01-R12 and DEC-001..022 remain controlling.

## Current integrated product

`main` contains typed/versioned contracts, synthetic fixtures, automatic vector/raster text-redaction detection, canonical redacted-only prediction manifests, synthetic-only trusted reference alignment, durable one-shot prediction jobs, qualitative/null-safe evaluation records and target/document/model summaries, descriptor-confined local persistence/migrations, isolated PDF-worker protocol, loopback API, React source and historical v0.1 bundle, local packaging/static serving, and the fail-closed API v0.2 real-inference pathway merged in PR #7.

The current package is intentionally non-distributable: the v0.2 frontend is not built and bound, PDF and model runtime locks are unverified, no genuine inference or clean-recipient run is established, and scientific scoring remains unvalidated.

## Dependency-ordered stages

### Stage A — Stabilize integrated inference code

Status: code complete and independently software-reviewed at E0071. Preserve the 681-Python/24-Node regression baseline, deterministic run identity, one-shot/IN_DOUBT semantics, exact model identity before mutation, bounded HTTP outcome classification, supervisor lifecycle and macOS path attestation.

Exit evidence: merged code SHA, exact full regressions, no Critical/Important review findings, immutable/null/reference-isolation checks. Reopen only for demonstrated defects.

### Stage B1 — Build and bind the API v0.2 frontend

Preflight the unchanged lockfile, licenses, engines, integrity metadata and lifecycle scripts; use a bounded zero-cost install/build task; run typecheck, Node tests and production build; verify no remote runtime dependencies; bind exact dist hashes/sizes/MIME types into the local manifest; exercise same-origin API v0.2 browser flows. Do not silently reuse the v0.1 bundle.

Exit evidence: reviewed lock/install log, typecheck/build/tests, manifest-bound artifact, browser synthetic upload/process/restart/null-state evidence, exact candidate review.

### Stage B2 — Qualify the isolated PDF worker

Inventory Podman/Apple virtualization availability and exact pinned image/dependency sources, hashes, licenses and SBOM. Build without host shares or network at runtime, verify resource/time/output limits and host source-authority binding, then process only synthetic authorized PDFs. Preserve fail-closed behavior when qualification is absent.

Exit evidence: verified runtime lock, image digest/SBOM/licenses, adversarial parser/isolation tests, crash/restart cleanup, synthetic PDF target evidence. Institutional permission is still required before private/lab documents.

### Stage B3 — Qualify one local inference runtime/model

Revalidate disk/hardware headroom; audit exact Ollama binary source/version/hash/license and exact approved model identity/files/digests/license; install only the bounded free local artifacts; generate the verified runtime lock; run synthetic model-identity, timeout/error/malformed, parent-death and repeat-dispatch tests. No commercial key is required for this stage.

Exit evidence: verified model-runtime lock, hashes/licenses/SBOM, actual local synthetic inference with immutable provenance, failure-path evidence, resource measurements and independent security review.

### Stage C — End-to-end document workflow

Connect verified PDF processing to target persistence, prediction dispatch, stored results and the browser. Test required redacted PDF, optional absent/partial/mismatched reference, automatic supported-target discovery, restart/reconnect, duplicate requests, cancellation/error display and immutable historical runs using synthetic or explicitly authorized public fixtures.

Exit evidence: repeatable PDF-to-prediction browser test, persisted exact targets/attempts, no reference leakage, null/UNKNOWN truth where unverified, recovery/concurrency evidence.

### Stage D — Multi-model comparisons

Add provider adapters behind the existing interface only after exact provider/model/version/tool/context policy is frozen. Start with additional local models that fit approved hardware; add commercial providers only when an approved task genuinely needs existing secure credentials and data/vendor permission. Use common frozen inputs and eligible sets.

Exit evidence: adapter contract/security tests, exact model provenance, common-context comparison, bounded cost/concurrency, missing/refusal/error disclosure. No blended accuracy.

### Stage E — Reference-grounded semantic evaluation

Implement only research-human-approved D03-D06 truth acceptance, fact-evidence rubric, benchmark, thresholds/weights, validation and aggregation. Until then, retain qualitative UNVALIDATED evidence and null numeric scores. Engineering can prepare blinded benchmark tooling and synthetic adversarial cases, but cannot certify validity.

Exit evidence: designated human approvals, authorized benchmark provenance/splits, inter-rater/adjudication records, held-out false-high-score bounds, versioned evaluator and transparent denominators.

### Stage F — Complete research UI

Finish document viewing, target navigation, release toggles, model comparison, progress/recovery, errors, provenance/settings/exclusions and accessible result summaries. Render all model/reference text as untrusted content and never calculate scores in the UI.

Exit evidence: accessibility, browser security, responsive document workflows, UNKNOWN/null/refusal/error states, multi-model and provenance acceptance tests.

### Stage G — Portable controlled release

Produce pinned offline-capable prerequisites or a documented verified acquisition path, migrations/backups/recovery, SBOM/license notices, supported hardware disclosure, setup/start/stop/upgrade guides and a clean-recipient acceptance run. Public deployment/distribution and private research use remain separate organizational gates.

Exit evidence: clean supported device installs and launches without owner-machine state, real synthetic PDF-to-local-model flow, restart recovery, security regression, signed/versioned release artifacts and known-limitations report.

## Immediate task order

1. RL-WEB-008: v0.2 frontend dependency preflight, build, manifest binding and synthetic browser acceptance.
2. RL-RUNTIME-009A: PDF worker feasibility/qualification.
3. RL-RUNTIME-009B: local Ollama/model source-license-hash qualification and synthetic inference.
4. RL-E2E-010: complete synthetic PDF-to-prediction browser workflow and recovery.
5. RL-MODELS-011: additional approved local/provider adapters.
6. RL-RESEARCH-012: human-approved evaluation validation; engineering work proceeds around this gate without inventing scores.
7. RL-UX-013 and RL-RELEASE-014: research workspace completion and clean-recipient controlled release.

Each item receives its own bounded task record, TDD, focused/full regressions, independent automated review and additive integration. Critical/Important review findings are repaired within the same task when scope-compatible.

## Current feasibility and blockers

Read-only audit on 2026-10-29: Apple M5, 32 GB RAM, 18 GiB free. This clears the historical 15 GiB minimum only narrowly; every acquisition task must recheck headroom and reserve cleanup space without deleting user data. `web/node_modules` is absent. PDF and model locks remain unverified. Exact runtime/model source, hash, license, SBOM and compatibility evidence is not yet recorded. Commercial credentials are not needed for the local vertical slice.

No persistent unattended runner, scheduler, approved orchestration service or external task queue is installed. The current Codex goal/session can make sustained progress while active and preserves GitHub/task records, but it is not a truthful 24/7 service. True unattended operation requires an explicitly provisioned persistent runner/host, scoped GitHub credentials, durable queue/state, concurrency/resource/cost ceilings, restart policy, audit logs, approval gates and a kill switch. None will be created implicitly.

## Nondelegable gates

Stop only affected work for paid services without budget, missing essential credentials, legal/institutional data permission, unresolved critical security risk, destructive external action, confirmed product-scope change, public deployment/distribution, or designated human scientific/benchmark/release approval. Continue independent safe engineering around a blocked stage.
