# RL-LINK-017 Correction 01 — Browser chunked upload framing

Task ID / state / single owner: RL-LINK-017 Correction 01 / APPROVED by the owner's 2026-11-06 durable-fix request and RL-OPS-002 / Codex Engineering Lead.

Objective / non-goals: Correct authenticated browser uploads translated to chunked HTTP/1.1 at the tunnel boundary; preserve the fixed-length application API, exact Host/Origin/authentication, body bounds, reference isolation and immutable evidence. No proxy expansion, parser/model/scoring change, private-data test, dependency addition or paid resource.

Rxx requirements / DEC decisions / unresolved Dxx gates: R01–R12; DEC-001–DEC-023; E0072; D03–D06 scientific validation and D07 permanent hosting remain open.

Baseline SHA / prerequisites: live GitHub `main` `733a1ae32d87ce0286756666692b4bd7f996aded`; API v0.3, gateway and owner-only tunnel already deployed. Reported PDFs were inspected only for local metadata and were not read, copied, uploaded or committed by this task.

Inputs / outputs / exact contract versions: consumes raw HTTP/1.1 gateway requests and API v0.3; produces strict chunked-upload decoding to the unchanged fixed-length loopback request and API v0.3 gateway errors. Design: `docs/superpowers/specs/2026-11-06-browser-upload-framing-design.md`.

Allowed files, actions and artifact publication scope: `src/redaction_lab/api/gateway.py`, `tests/api/test_gateway.py`, `packaging/local/README.md`, this packet, design/plan, `docs/project/CURRENT_STATE.md`, `docs/project/CHANGELOG.md`, `docs/project/AGENT_HANDOFF.md`, and one unique `docs/project/handoffs/RL-LINK-017-lead-*.md`. Because the qualified PDF image intentionally copies the complete `src/` tree, the owner-authorized completion scope also includes an offline, no-download source refresh of `packaging/pdf-worker/{runtime.lock,integrity-manifest.json,qualification-sources.json,sbom.cdx.json}` and the resulting `packaging/local/manifest.json` lock binding; this does not change worker behavior or dependencies. Running/stopping/restarting the task-owned launcher/tunnel for synthetic acceptance, normal commits/push/PR/integration and private link continuity are included. No user PDF processing is authorized for testing.

Tests and acceptance evidence: mandatory RED/GREEN raw-socket tests; malformed/ambiguous/overflow/auth/route/error-contract cases; existing gateway and packaging regressions; fresh full Python/Node/typecheck/build/audit; exact-candidate independent security/code review; external synthetic multipart upload using chunked framing with no `Content-Length`, followed by process/results/reconnect evidence. Record environmental baseline failures caused by the already-live fixed ports; stop only task-owned services before final full verification.

Data, provider, cost and runtime limits: generated synthetic bytes only; no download, dependency, model/provider, worker-protocol or scoring change; no cost. The qualified PDF-worker image may receive the mandatory offline full-source refresh described above, followed by its existing synthetic qualification. Decoded body bound remains `MAX_UPLOAD_BODY_BYTES`; authentication precedes body reads; private spool files close on every path.

Consumers and expected handoffs: owner/browser users, frontend API client, gateway/operator, QA/security and Lead. Publish exact commit, commands/results, remaining limits and rollback.

Independent reviewer / required human approvals: fresh exact-candidate automated reviewer required for code/security. Owner's request authorizes the correction and normal integration; it grants no scientific, institutional, private-data or permanent-hosting approval.

Rollback / stop conditions: stop for authentication regression, unbounded memory/disk, request-smuggling ambiguity, partial upstream forwarding before chunk validation, private-data need, paid-resource need or unresolved Critical security finding. Rollback by stopping services and reverting normally; never mutate stored evidence.
