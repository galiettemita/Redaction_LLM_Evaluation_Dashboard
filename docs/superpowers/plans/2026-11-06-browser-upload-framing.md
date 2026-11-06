# Browser Upload Framing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make authenticated browser PDF uploads work through ngrok without weakening the fixed-length internal API or bounded gateway security.

**Architecture:** The raw edge gateway admits a single strict chunked mode only for authenticated document uploads, fully decodes it into a bounded private spool, then forwards the exact decoded length to the unchanged loopback application. Fixed-length uploads retain their current streaming path. All gateway errors become valid API v0.3 responses.

**Tech Stack:** Python 3.12 standard library HTTP/socket/tempfile, pytest raw-socket integration tests, existing TypeScript API client and local packaging.

**Spec:** `docs/superpowers/specs/2026-11-06-browser-upload-framing-design.md`

## Global Constraints

- No new dependencies, arbitrary proxy behavior, retry, model/scoring/parser change or user-data fixture.
- Authenticate and validate exact Host/Origin/route before reading any request body.
- Decode at most `MAX_UPLOAD_BODY_BYTES`; reject ambiguous framing and close all spools/sockets on every outcome.
- Preserve fixed-length streaming and unchanged API v0.3 application request semantics.
- Tests use synthetic bytes only; secrets, real hostname and user PDFs remain outside Git.

## Review Focus

- `Content-Length` plus transfer encoding, multiple codings or duplicated fields must fail before upstream connection.
- Malformed/truncated chunk-size lines, chunk bodies and delimiters must fail without partial application work.
- Decoded overflow, many small chunks and slow/aborted clients must remain bounded and clean up resources.
- Authentication, wrong Host/Origin and unsupported routes must reject before any chunk body read.
- Gateway-generated 4xx/5xx responses must be API v0.3 JSON while never leaking internal paths, upstreams or credentials.

---

### Task 1: Strict chunked upload adapter and API-shaped gateway errors

**Files:**
- Modify: `tests/api/test_gateway.py`
- Modify: `src/redaction_lab/api/gateway.py`

**Interfaces:**
- Consumes: authenticated raw HTTP/1.1 request headers/body at `GatewayHandler`.
- Produces: body mode state, strict decoded spool for chunked uploads, unchanged fixed-length forwarding, and API v0.3 JSON rejection responses.

- [x] **Step 1: Write failing raw-socket tests**

Add literal tests for a valid multi-chunk multipart body, decoded `Content-Length`, exact bytes, no forwarded transfer/auth headers, API-versioned gateway errors, authentication-before-read, conflicting/unsupported framing, extensions/trailers, invalid/overlong/truncated sizes and bodies, and decoded overflow.

- [x] **Step 2: Run focused tests and verify RED**

Run: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src <python> -m pytest tests/api/test_gateway.py -q`

Expected: new valid chunked and API-error-contract tests fail because transfer encoding is rejected and gateway errors lack `X-Redaction-Lab-API`.

- [x] **Step 3: Implement the minimal strict adapter**

Add focused private helpers/methods in `gateway.py` for exact transfer-mode selection, bounded chunk-line/exact-byte reads, decoded spooling and body forwarding. Reject unsupported/ambiguous modes; retain direct fixed-length streaming. Import `API_VERSION` for gateway error headers and make overload responses API-shaped.

- [x] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: all gateway tests pass.

- [x] **Step 5: Refactor names/control flow without behavior expansion and rerun focused tests**

- [x] **Step 6: Commit**

Commit message: `fix: support bounded browser chunked uploads`

### Task 2: Operator contract, verification and delivery record

**Files:**
- Modify: `packaging/local/README.md`
- Modify: `docs/project/task_packets/RL-LINK-017-CORRECTION-01-CHUNKED-UPLOAD.md`
- Modify: `docs/project/CURRENT_STATE.md`
- Modify: `docs/project/CHANGELOG.md`
- Modify: `docs/project/AGENT_HANDOFF.md`
- Create: `docs/project/handoffs/RL-LINK-017-lead-<UTC>-<SHORT>.md`

**Interfaces:**
- Consumes: Task 1's exact framing/error contract and reviewed candidate.
- Produces: operator documentation, durable evidence, corrected live service and checklist closure.

- [x] **Step 1: Update operator documentation**

Document strict browser chunked support, decoded bounds/spooling, rejected ambiguity and unchanged fixed-length/internal contracts.

- [x] **Step 2: Verify focused, full and packaging/web suites**

Stop only the task-owned live launcher/tunnel while port-bound tests run. Run full Python, Node tests, typecheck, build, audit and `git diff --check`; record exact results. Restart the prior service immediately if verification is interrupted.

- [x] **Step 3: Obtain exact-candidate independent review**

Review Task 1 against the spec's Review Focus. Correct Critical/Important findings through one RED/GREEN pass and rerun affected/full suites.

- [x] **Step 4: Perform synthetic external acceptance**

After normal integration, relaunch the reviewed candidate and tunnel with existing private configuration. Send a generated synthetic multipart pair through the public HTTPS route using chunked transfer and no `Content-Length`; verify upload, genuine processing/results, API-shaped malformed rejection, unauthenticated rejection and GET-only reconnect. Do not use the user's PDFs.

- [x] **Step 5: Publish handoff/checklists and commit**

Commit message: `docs: record durable browser upload correction`
