# Synthetic End-to-End Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reliably complete two sequential synthetic optional-reference PDF workflows through persisted local predictions without reference leakage, duplicate attempts or scores.

**Architecture:** Preserve the existing API, store, worker and prediction services. Correct only durable accepted-job ordering so user-visible redacted work precedes inaccessible reference work, then verify the complete composition with portable controlled-boundary tests and a host-qualified live canary.

**Tech Stack:** Python 3.12, SQLite, stdlib WSGI, pytest, React/TypeScript/Vite, existing Podman PDF worker and Ollama adapter.

**Spec:** `docs/superpowers/specs/2026-10-29-synthetic-end-to-end-workflow-design.md`

## Global Constraints

- API remains v0.2; PDF protocol remains `pdf-worker-v1`; prediction run/service remains v0.4.
- No schema, dependency, provider/model, frontend contract or numeric-score change.
- References remain optional, untrusted and unavailable to prediction; truth is `UNKNOWN` and scores are null.
- Only repository-generated synthetic fixtures may reach the qualified runtimes.
- Reads and reconnects must never create work; replay must preserve immutable attempts.

## Review Focus

- An older accepted reference preceding a new redacted job must not starve the redacted job.
- Worker claim ordering and API preflight ordering must select the same exact job under multiple projects/pairs.
- A reference-bearing second upload must not leak reference bytes/identity into any prediction manifest.
- Process replay/restart after partial or complete work must not create a second run or attempt.
- Unsupported, no-redaction, model failure and malformed output must remain null-scored technical outcomes.

---

### Task 1: Durable redacted-first job ordering

**Files:**
- Modify: `src/redaction_lab/application/application_store.py`
- Test: `tests/application/test_application_store.py`

**Interfaces:**
- Consumes: existing immutable `application_jobs(role, status, created_at, job_id)` records.
- Produces: unchanged `ApplicationStore.claim_next(owner, now) -> StoredApplicationJob | None` with deterministic redacted-first accepted-work order.

- [ ] Write a failing test that completes a first redacted job, leaves its older reference accepted, registers a second pair and asserts `claim_next()` returns the second redacted job.
- [ ] Run the exact test and confirm it instead claims the older reference.
- [ ] Change the accepted-job `ORDER BY` to role priority (`REDACTED` before `REFERENCE`) followed by the current stable ordering.
- [ ] Run the focused store tests and commit.

### Task 2: API ordering parity and sequential workflow

**Files:**
- Modify: `src/redaction_lab/api/app.py`
- Test: `tests/api/test_app.py`

**Interfaces:**
- Consumes: the store's deterministic accepted-work ordering and existing `POST /api/v1/jobs/{id}/process` contract.
- Produces: unchanged response contract while allowing the next redacted document to process despite older accepted reference jobs.

- [ ] Write a failing API test with two reference-bearing pairs that asserts the second redacted process request is not rejected because of the first reference.
- [ ] Run the test and confirm `JOB_CONFLICT` from ordering mismatch/starvation.
- [ ] Apply the identical role-priority ordering to API preflight selection.
- [ ] Assert both references remain excluded from prediction inputs, truth stays `UNKNOWN`, and replay performs no additional dispatch.
- [ ] Run focused API/application tests and commit.

### Task 3: Portable vertical-slice regression

**Files:**
- Create: `tests/e2e/test_synthetic_workflow.py`
- Modify only if a demonstrated defect requires it: Task 1/2 authorized source files

**Interfaces:**
- Consumes: `UploadService`, `LocalApi`, `DocumentWorker`, `PredictionService`, existing synthetic fixtures and controlled qualified-boundary fakes.
- Produces: executable acceptance proof for upload → targets → attempts → results → reconnect/replay across two pairs.

- [ ] Write the portable test first and confirm the uncorrected workflow failure is observable.
- [ ] Exercise required-only and optional-reference uploads, exact target IDs, redacted-only manifests, distinct technical outcomes, stored results, second-pair progress and GET-only recovery.
- [ ] Run focused E2E/API/worker/prediction tests, then the full Python suite.
- [ ] Commit the portable acceptance evidence.

### Task 4: Qualified-host and browser acceptance

**Files:**
- Modify if instructions require correction: `packaging/local/README.md`
- Add final evidence: unique `docs/project/handoffs/RL-E2E-010-<role>-<UTC>-<id>.md`

**Interfaces:**
- Consumes: exact Task 9A/9B locks, installed application-owned runtimes, v0.2 static bundle and local launcher composition.
- Produces: synthetic-only host evidence; no portable-release or scientific claim.

- [ ] Recheck live main, lock hashes, complete installed inventories, disk reserve and absence of pre-existing listeners.
- [ ] Run generated synthetic PDFs through actual isolated processing and local inference using temporary durable application state; verify target/attempt provenance, reference isolation and no residual runtime/listener.
- [ ] Run the same-origin browser workflow, refresh/reconnect/replay checks, and inert rendering assertions with installed headless Chrome.
- [ ] Run Node tests, typecheck, production build/hash comparison, audit, Python compilation, full regressions and exact scope/diff checks.
- [ ] Commit the task handoff and submit the exact candidate to a fresh independent automated reviewer.
- [ ] Correct any Critical/Important findings, rerun regressions, push, open a PR and merge only the reviewed exact head after final live-main reconciliation.
