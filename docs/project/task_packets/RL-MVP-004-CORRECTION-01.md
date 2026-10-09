# RL-MVP-004 — Correction 01: trusted prediction source and protocol integrity

**Status: OWNER-APPROVED for bounded implementation, 2026-10-09.** This packet is published on a Lead preparation branch; it does not itself merge the rejected Task-4 candidate or authorize Task 5. **Implementation owner:** Backend/Codex. **Independent reviewers:** QA and Research. **Integration owner:** Lead, subject to separate owner merge approval.

**Integration baseline at packet creation:** `b6fdc226596748a6340c6f85f9e30ae473fd41a8`, decision epoch E0035. Refresh live `main` and decision/hold records before starting and before delivery. **Rejected implementation:** `c3a928ce1aaf2039bc778cb91c272b435fb93aa4`; **published Backend branch:** `codex/rl-mvp-004-prediction-worker` at `de9ad26f7225f5717d2c6ace683e1f21b0fed2fa`. Deadline checkpoint October 12, 2026; no quality-gate waiver.

## Authorization and evidence

The product owner explicitly approved Correction 01 on 2026-10-09, including four additional Lead safeguards, the original six Task-4 code/test files, `prediction_source.py`, `test_prediction_source.py`, `contracts.py`, `test_contracts.py`, and ONE unique Backend handoff. This includes necessary internal interface adjustments in the listed files, not unrelated rewrites. Do not silently extend file scope.

Sources: R04/R05/R08/R11/R12; DEC-001/004/008/009/015/017/020/022; `AGENTS.md`; `docs/project/task_packets/RL-MVP-004-INDEPENDENT-REVIEW.md`; original approved Task-4 packet; independently published exact-candidate handoffs:
- QA `docs/project/handoffs/RL-MVP-004-qa-20261009T141300Z-c3a928c.md` on `qa/rl-mvp-004-review-c3a928c` — FAIL/CHANGES_REQUESTED.
- Research `docs/project/handoffs/RL-MVP-004-research-20261009T142500Z-review.md` on `review/rl-mvp-004-research-e0035` — CHANGES_REQUESTED.
- Read-only Codex design preflight provided to Lead, NOT PUBLISHED separately.

## Objective

Correct four independent-review blockers: (1) forged/self-consistent canonical inputs and direct untrusted manifest enqueue; (2) unrestricted production transport injection; (3) unverified provider-returned model identity; (4) `URLError`-wrapped timeouts incorrectly becoming terminal ERROR/COMPLETE. Preserve redacted-only one-target prediction, SQLite at-most-once dispatch intent, immutable attempts, provenance, and conservative IN_DOUBT/no-retry behavior. Do not imply scientifically verified accuracy or provider-level exactly-once execution.

## Permitted paths only

Modify:
1. `src/redaction_lab/adapters/base.py`
2. `src/redaction_lab/adapters/ollama.py`
3. `src/redaction_lab/store.py`
4. `src/redaction_lab/worker.py`
5. `tests/test_adapter.py`
6. `tests/test_worker.py`
7. `src/redaction_lab/contracts.py`
8. `tests/test_contracts.py`

Create:
9. `src/redaction_lab/prediction_source.py`
10. `tests/test_prediction_source.py`
11. One unique `docs/project/handoffs/RL-MVP-004-backend-<UTC>-<SHORT-ID>.md`.

No edits to `canonical.py`, `pdf_detector.py`, `reference.py`, fixtures, `pyproject.toml`, dependencies, application API/UI, scoring/evaluator, Task 5 files or canonical shared project docs. If a sound change requires any other path or a new contract decision, STOP and request a scoped amendment. Implement on the existing isolated Task-4 branch using additive commits and ordinary non-force pushes; never reset, force-push or edit another worktree.

## Required behavior and contracts

### A. Application-owned canonical-source authority

Provide a narrow trusted ingestion path receiving **actual redacted PDF bytes** plus authenticated project context (project ID is a selector, NOT evidence of authorization). Internally compute source SHA-256 and deterministic, project-scoped identifiers incorporating processing versions; derive targets using existing `detect_targets` and redacted-only canonical text using `canonicalize_redacted`. Preserve authoritative `target_id -> target_version` mapping and detector/canonicalizer version evidence. Fail closed on unsupported/no supported text redactions, mismatched source, malformed PDF, ambiguous targets, or inconsistent outputs. No reference PDF, mapping, recovered text or caller-provided canonical record enters authority creation.

Store an immutable application-owned canonical-source record in SQLite: project/source identity, PDF hash and redacted role, version IDs, detector/canonicalizer versions, canonical text/hash and canonical record, exact target IDs/versions, ingestion time, and provenance. Source IDs MUST be scoped to project to prevent cross-project authorization by identical bytes. Authorize the requesting actor/project at the trusted service boundary; an arbitrary caller-supplied `project_id`, PDF or source ID is never sufficient. If no authenticated access boundary exists in this Task-4 component, limit ingestion/dispatch to a documented trusted internal caller/test harness and **STOP before claiming authorization for arbitrary uploads or external callers**. Do not invent a public authenticated API.

Change `RunStore.enqueue` to accept a stored `source_id`, target ID and frozen RunDefinition, not a caller-supplied `PredictionManifest`. Resolve the source from the store's own immutable record and validate project, redacted role, source/canonical hashes and versions, exact target->version binding, full run target set/order, model, prompt/settings and attempt-policy identity before constructing the manifest **inside the trusted boundary** and atomically enqueuing. A direct forged `PredictionManifest`, self-signed canonical text/hash pair, fabricated source record, swapped target versions, or unregistered source cannot become a dispatchable job. Do not treat hash self-consistency, a `trusted=True` flag, or caller-created `DocumentVersion` as authority. Revalidate stored source/job integrity before claim; corrupt/missing authoritative source => fail closed, no dispatch. Prediction workers must not read original PDF or reference; store validated canonical visible text only as needed.

### B. SQLite state, backward compatibility and run immutability

Add an immutable `canonical_sources` table and foreign-key binding from new jobs. Freeze/persist source, run, generated manifest, scope/attempt policy and configuration identity. Enforce a unique project/run/target/model/attempt-policy scope, atomic PENDING -> IN_DOUBT claim before transport, and no implicit retry. Preserve the existing public-versus-internal state distinction; neither crash nor wrapped timeout is an ordinary terminal factual failure.

Use fail-closed additive migration on **disposable synthetic SQLite databases only**. Old attempts remain readable and immutable, never rewritten or deleted. Legacy PENDING jobs lacking trusted source/run binding are **not claimable**, even after reopen/migration; no automatic promotion or blessing of legacy manifests. Add schema guards/triggers to reject unauthorized mutation/deletion of immutable source, run, manifest, intent and attempt data; protect execution-state transitions from accidental PENDING reset where feasible without breaking the authorized claim/complete sequence. Direct malicious local DB process compromise is not asserted to be solved.

Ensure a run has frozen model/settings/config and attempt policy consistently across target jobs. If the existing `RunDefinition` cannot prove a run-level configuration identity without broader contract scope, reject mixed configurations, surface the limitation explicitly and stop for contract review instead of silently pooling incomparable attempts.

### C. Production local-only transport

Remove arbitrary callable `transport` injection from production `OllamaAdapter.__init__`. Construct transport internally using a strict `http://127.0.0.1:<validated-port>` endpoint, no hostnames/DNS/IPv6/userinfo/path/query/fragment, no environment proxies (`ProxyHandler({})`), no redirects and bounded response size. Tests may mock a **private** I/O seam or pure parsing without exposing a production-configurable egress callback. No actual model/network calls. Do not claim containment against arbitrary already-executing malicious Python inside the trusted process.

### D. Honest provider-reported model identity

Keep `ModelAttempt.model_id` as **requested** identity. Add optional `provider_model_id` to `ModelAttempt` and `PredictionResponse` with backward-compatible default None; older rows remain explicitly unverified. For any new successful or refused Ollama response, require nonblank top-level provider `model` and exact match to requested identity. Absent model => MALFORMED, null prediction; mismatch => technical ERROR, null prediction, preserve both identities and response hash; timeout/no body => None. Record requested versus provider-returned IDs separately; equal names are not proof of stable weights/digest and cannot justify a verified cross-model comparison. No new scoring or model roster approval.

### E. Wrapped timeout ambiguity

Classify direct `TimeoutError`, `socket.timeout`, `OSError(errno.ETIMEDOUT)`, `URLError.reason` wrappers and bounded exception `reason`/`__cause__`/`__context__` chains as TIMEOUT. Persist a TIMEOUT attempt when possible but keep job internal IN_DOUBT; no reconnection/restart re-dispatch. Non-timeout URL failures and deterministic errors remain technical ERROR, not wrong answers. Prevent recursion cycles and cap traversals.

## TDD / acceptance evidence

Create failing regression tests before the fixes where practical. Required independent scenarios:
- Self-consistent forged canonical text plus recomputed hash plus forged matching run cannot enqueue; direct `PredictionManifest` cannot be enqueued; only trusted PDF-derived source yields a dispatchable manifest.
- Project mismatch, unauthorized caller boundary, swapped source IDs, different projects with identical PDF bytes, source role mismatch, missing/altered canonical source and source/run/hash/version/target-order mismatch all fail closed.
- Hidden selectable PDF text never enters a resulting manifest; no reference or metadata/filename/hint leakage; only chosen target is marked TARGET while every other box is masked; exact target versions are validated.
- Source, run, manifest and attempt immutability; legacy untrusted PENDING quarantined across reopen; concurrent claims single winner; crash after claim and duplicate delivery never cause a second dispatch; raw accidental state-reset writes rejected.
- Production adapter rejects `transport` keyword; loopback/proxy/redirect/response-size controls hold under mocks without real network.
- Matching returned model permits success/refusal; missing identity MALFORMED; mismatched identity ERROR with both IDs persisted and no prediction; older attempts remain parseable without false verification.
- Direct and wrapped timeout variants => TIMEOUT/IN_DOUBT with zero subsequent dispatch after restart; non-timeout URLError => ERROR; cyclic exception contexts handled safely.
- Run-level model/config/attempt consistency and unchanged model/request/response hash provenance; no score attribution to refusal/timeout/error/unknown truth.
- Retain every relevant existing Task 1–4 regression.

Before publication run focused pytest, full pytest, compileall, dependency integrity, `git diff --check`, scope/diff audit and migration/reopen tests. Record exact commands, environment, results and all checks NOT RUN. Backend result counts are author-reported until independent review.

## Stop conditions and handoff

Stop and request Lead/owner scope review for additional files, a required authenticated service/API, new dependencies, broken trusted provenance, private-data access, ambiguous or duplicate dispatch, unapproved scientific/method changes, model downloads, live inference, paid provider calls, deployment or Task 5. No new provider/model installation, no external egress, no spending.

Publish new **exact implementation commit SHA** plus one unique Backend handoff on the approved isolated Task-4 branch. Include changed paths, run tests/evidence, legacy migration observations, remaining risks, source/target provenance, last HEAD/epoch check and next receivers. Fresh QA and Research reviews on that exact new SHA are mandatory. Lead reconciles their verdicts; separate product-owner authorization is still required before any merge. Revert correction via normal additive revert if needed; never force-push. Reverting does not make rejected original candidate mergeable.

**Checkpoint:** owner-approved implementation scope only; correction NOT VERIFIED, NOT MERGED, NOT DEPLOYED; real-model demonstration BLOCKED; Task 5 unapproved.
