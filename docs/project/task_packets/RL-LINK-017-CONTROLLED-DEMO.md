# RL-LINK-017 — Owner-only controlled experimental demonstration

Baseline integration SHA: `cb0fa4f1242ae8bf12afb084bc9475017040b784` (live GitHub main, 2026-11-05 UTC). Epoch: E0072.
Accountable owner: Codex Engineering Lead; delegated implementers report exact candidates to Lead. State: ACTIVE / AUTHORIZED FOR BOUNDED ENGINEERING, NOT IMPLEMENTED OR VERIFIED by this record.
Authority: owner clarification dated 2026-11-05, DEC-023 and [RL-OPS-002](RL-OPS-002-AUTONOMOUS-ENGINEERING.md). Read the [design](../../superpowers/specs/2026-11-05-experimental-product-completion-design.md), [implementation plan](../../superpowers/plans/2026-11-05-experimental-product-completion.md), [API v0.3](../API_CONTRACT_V0_3.md) and live integration HEAD before work.

## Objective and dependencies

Implement plan Task 6: qualify the changed `pdf-worker-v2` image before live v2 use, serve the reviewed API v0.3/frontend through a loopback gateway and authenticated HTTPS ngrok tunnel, and deliver actual end-to-end evidence and the working link. This task consumes RL-EXP-015 and RL-UX-016. The v2 image qualification substep may run as soon as Task 2 source/tests are reviewed, before Task 4's genuine canary; gateway/delivery waits for the application and bundle. No passing status or link is presumed by this packet.

Owner's 2026-11-05 working-link direction authorizes this temporary owner-only authenticated demonstration. This is a single local workspace, not per-user document authorization or a general public release. Credentials are not shared with other researchers; anyone given credentials could access that demonstration workspace. Store synthetic demonstration documents only. Synthetic or explicitly authorized public fixtures may be used in separate local test state; no private/institutional data or paid resources are authorized.

## Exact file/action scope

Gateway/delivery:

- `src/redaction_lab/api/gateway.py` (new)
- `tests/api/test_gateway.py` (new)
- `packaging/local/launch.sh`
- `packaging/local/preflight.sh`
- `packaging/local/manifest.json`
- `packaging/local/README.md`
- `tests/packaging/test_local_preflight.py`
- `tests/packaging/test_local_static.py`

Explicit v2 worker image rebuild/requalification dependency (Task 2 remains source/test-only):

- `packaging/pdf-worker/Containerfile`
- `packaging/pdf-worker/runtime.lock`
- `packaging/pdf-worker/integrity-manifest.json`
- `packaging/pdf-worker/qualification-sources.json`
- `packaging/pdf-worker/sbom.cdx.json`
- `packaging/pdf-worker/README.md`
- `scripts/build-pdf-worker.sh`
- `scripts/verify-pdf-worker.sh`
- `tests/application/test_isolation.py`
- `tests/application/test_worker_protocol.py` and `tests/application/test_document_worker.py` only for v2 runtime acceptance regressions

Do not change the pinned PDF parser dependencies, Podman executable/base image/model or `requirements.lock`/`containers.conf` merely to rebuild application source into the worker. Record any demonstrated necessary extension before writes. Rebuild/qualify with already installed integrity-checked zero-cost runtime assets; no unverified downloads or paid VM/cloud provisioning. Keep isolated parser network disabled and host shares absent. Populate hashes/SBOM/runtime_verified from observed exact artifacts and qualification only, never copy old qualification onto a new image.

Documentation scope: this packet, completion design/plan checklists, `docs/project/CURRENT_STATE.md`, `docs/project/CHANGELOG.md`, `docs/project/AGENT_HANDOFF.md`, and unique `docs/project/handoffs/RL-EXP-015-lead-<UTC>-<SHORT>.md` plus necessary task-specific runtime/review handoffs. Lead owns shared canonical updates. Normal commits, non-force push, reviewed PR/integration, running/stopping the task-owned local services, owner-only ngrok exposure and authenticated browser checks are included. Keep tunnel config, credentials and real hostname outside Git; deliver access details privately to owner. Missing essential ngrok credentials blocks only the external-link substep.

## Gateway contract

Application remains on `127.0.0.1:8765`; gateway binds only `127.0.0.1:8766`. An explicit configured exact public hostname/HTTPS Origin is validated before forwarding. Authenticate requests at the controlled boundary and verify an unauthenticated request fails; ngrok authentication and local gateway protection must not be bypassable through alternate host/origin paths. Reject wrong or ambiguous Host/Origin, duplicate/conflicting framing, unsupported transfer framing and oversized bodies. Bounded PDF uploads must work without unbounded buffering; preserve response security/content headers, translate only validated requests to the existing local Host/Origin contract and fail closed on bad upstream responses.

No arbitrary upstream selection, redirect/proxy feature or Ollama route. Never expose `11434`, model files, private runtime root or raw configuration. Disable ngrok inspection. HTTPS link exists only while the Mac is awake and the application, gateway and tunnel run. The delivery must describe that operational limit and the one-model/experimental/single-workspace limits plainly. No permanent availability, multi-user security, clean-device portability or scientific readiness claim.

## Acceptance checklist (plan Task 6)

- [ ] Worker v2 rebuild uses reviewed source and pinned installed dependencies; full source/image/runtime hashes, SBOM and provenance recorded; protocol/extraction tests qualify exact image and isolation. Live v2 execution remains blocked until this passes.
- [ ] RED/GREEN gateway tests cover exact Host/Origin, authentication, malformed/ambiguous framing, upload bounds, bounded streaming, loopback translation, security headers, arbitrary-upstream/Ollama rejection and failure cleanup.
- [ ] Launch/preflight tests cover trusted runtime root, API v0.3, exact frontend inventory, gateway loopback binding, occupied ports and clean shutdown.
- [ ] Fresh full Python and Node suites, typecheck/build/audit and packaging checks pass on the delivery candidate; deterministic production asset inventory rebound after the final frontend build.
- [ ] Genuine isolated synthetic PDF + local Qwen canary persists at least one SUCCEEDED prediction and one experimental target score, non-null document/model summaries, exact provenance and verified_score null.
- [ ] Missing, mismatched, partial and ambiguous reference canaries remain null/Accuracy unknown; technical outcomes remain distinct; prompt-like reference text is absent from prediction manifests.
- [ ] Browser acceptance covers upload, local viewer toggle, process, truthful progress/results, selection, experimental labels, actionable errors and refresh/reconnect without a second attempt.
- [ ] Independent exact-candidate whole-branch security/product and experimental-semantics review completed; all Critical/Important findings corrected and affected/full verification rerun. No scientific sign-off invented.
- [ ] Recheck live main; reconcile overlap, update canonical state, all checklists and unique handoff with actual evidence; commit `docs: record experimental application delivery`.
- [ ] Push normally, open/integrate reviewed PR under RL-OPS-002, launch app/gateway/ngrok and verify actual HTTPS application access with authentication. Unauthenticated access and wrong-origin mutations fail. Deliver working link privately without committing credentials/hostname.

## Common gates, review and rollback

### Task 6 bounded engineering amendment (2026-11-05)

The Engineering Lead authorizes `src/redaction_lab/application/isolation.py` in
addition to the above scope solely to resolve the existing explicit
`REDACTION_LAB_RUNTIME_ROOT` for the PDF worker. Apply the same absolute-path,
ownership, no-symlink and no-group/world-write checks as Task 4, use only fixed
locked child paths, and preserve all existing runtime, connection and image
checks. The legacy default remains fail-closed. Regression tests remain in the
already-scoped `tests/application/test_isolation.py`.

The prior 15 GiB acquisition gate is superseded **only for this no-download
reuse/rebuild of installed pinned artifacts** by an 8 GiB minimum free-space
gate before and throughout build/canary. Record exact free space, relevant
artifact/cache sizes and projected incremental use first. Stop if projected use
could cross 8 GiB; if observed free space crosses it, stop and clean only
task-created temporary/build artifacts. Never remove unrelated/user data. This
does not authorize any new model/runtime acquisition. Rationale: all large
runtime/model dependencies are already installed; only bounded application
source layers and synthetic acceptance state are added. Lead authorized this
amendment before implementation after the 15 GiB read-only preflight failed.

The existing wheelhouse is absent. Lead additionally permits the exact locally
present v1 worker image `sha256:7a78eaf7ef812d354f0abe13f40c6c0a4e3684d94f72002245c5249249bf293b`
as an immutable offline dependency stage, preserving the pinned Python base and
installed dependency bytes. Builds use `--pull=never --network=none`, replace
only reviewed application source, and fail closed if that exact source image is
absent. Record its identity as build provenance only. The resulting v2 image
requires new digest/source inventory/SBOM, complete installed inventory/license,
protocol/reference bounds, isolation, cleanup/restart and synthetic acceptance
evidence; the v1 qualification is not inherited.

Preserve R01–R12 and DEC-001–DEC-023 within DEC-023's explicit experimental-only supersession. `verified_score` remains null; verified `truth_status` remains UNKNOWN. Missing/partial/unreadable/ambiguous/mismatched/unprocessed truth remains Accuracy unknown/null, never zero. Reference data never enters prediction inputs; immutable versions and one-shot recovery remain mandatory. This record authorizes no paid resources, private/restricted research data, credentials in Git, destructive external action, scientific validation or public unauthenticated release. Only generated synthetic fixtures or separately documented authorized public data may be used; the shared demonstration workspace stores synthetic documents only.

Behavior changes require red-green-refactor evidence, focused/full permitted regressions, exact-candidate independent automated QA/security and experimental-semantics review, correction and re-review before normal non-force integration. Self-review is not independent review. No automated reviewer grants D03–D06, institutional permission or scientific/release validation. Stop only affected work for unsafe reference leakage, unexplained score/version changes, scope/contract conflicts, unqualified runtime, essential missing credentials, paid-resource need, private-data need, destructive action or unresolved Critical security risk; continue independent safe work. Record any necessary bounded scope amendment before writes.

Rollback: stop affected services if necessary, revert additive task commits normally, retain original immutable attempts/evaluations and restore a verified pre-migration backup only through the documented safe migration recovery path. Do not overwrite later evidence or roll old validators forward silently. Publish a unique task handoff under `docs/project/handoffs/` using every field in [AGENT_HANDOFF](../AGENT_HANDOFF.md#handoff-template-all-fields-required-explicit-not-applicable-is-valid), with exact artifacts/commits, tests run/unrun, decisions, blockers, affected consumers and next action. Live integration HEAD must be rechecked before consequential writes, runtime calls and final review.

### Task 6 test-only compatibility amendment (2026-11-05)

After v2 qualification, the full suite showed two stale environmental/packaging
assumptions (938 passed, two failed). Lead adds only `tests/api/test_app.py` and
`tests/security/test_pdf_worker_container.py`: explicitly give the
unverified-runtime case a missing trusted runtime root, and update the container
security/provenance assertions from v1/wheelhouse installation to the observed
immutable offline dependency-stage v2 contract. No application behavior is
changed to satisfy these tests. Rerun focused and full regressions.

### Task 6 API mapping identity correction (2026-11-05)

Mounted genuine acceptance found that serialized mappings retained the internal
trusted-source redacted document ID while the v0.3 UI requires the uploaded
application document ID. Lead adds only `src/redaction_lab/api/app.py` and
`tests/e2e/test_synthetic_workflow.py` (with `tests/api/test_app.py` already in
scope): authenticate the stored mapping's internal source/version against the
current trusted source, then project the API-facing document ID to the upload
ID without mutating immutable provenance. Add actual API-to-TypeScript contract
and mismatched-identity rejection regressions. Preserve all prior successful
attempts; a prompt-marker reference remains conflicting/null evidence, and an
exact matching reference is a separate declared synthetic scoring canary.
