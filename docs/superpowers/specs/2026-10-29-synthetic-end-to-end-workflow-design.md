# Synthetic end-to-end workflow design

## Intent

Make the already assembled local Redaction Lab vertical slice reliably process more than one synthetic document, including the normal case where each upload carries an optional reference. Success is a repeatable redacted-PDF → isolated targets → frozen local-model attempts → persisted API/browser result flow with explicit uncertainty and recovery semantics.

## Goals, non-goals and constraints

- Preserve API v0.2, the current SQLite schema, qualified PDF/model runtime contracts and existing architecture.
- Prefer a minimal orchestration correction plus black-box acceptance evidence.
- Keep every reference untrusted and structurally absent from prediction input. Truth remains `UNKNOWN`; numeric scores remain null.
- Ensure reads/reconnects never create work and repeated explicit processing resumes rather than duplicates a run.
- Use only synthetic repository fixtures and zero-cost application-owned runtimes.
- Do not add scoring, providers, dependencies, browser PDF parsing, private data, deployment or release claims.

## Approaches considered

1. **Minimal queue-order correction plus vertical acceptance (selected).** Give accepted redacted jobs priority over accepted reference jobs in both the durable worker claim and API's requested-job preflight. This fixes the discovered starvation without changing records, schemas or contracts; references remain available for future separately authorized evaluation processing.
2. **Add a new workflow coordinator and pair state.** This could model both documents explicitly, but requires schema/API expansion and duplicates current job orchestration. It is unnecessary for the present null-truth vertical slice.
3. **Hide or discard reference jobs in the browser/API.** A UI workaround would mask a durable backend ordering defect, while deletion would violate immutable evidence and retention boundaries.

The owner has directed autonomous execution with minimal routine questions, so the architecture-preserving option is adopted under RL-OPS-002.

## Design

`ApplicationStore.claim_next()` remains the only durable claim transition. Its accepted-work ordering becomes: redacted roles first, then reference roles, then existing creation-time/job-ID order. `LocalApi._process()` uses the identical ordering when ensuring the explicitly requested redacted job is next. This preserves one active job and deterministic ordering while preventing an inaccessible older reference job from starving later user-visible redacted work.

No reference is processed as a side effect of redacted prediction. No reference bytes, job fields or pairing metadata enter `PredictionService`; existing redacted-source provenance remains the sole prediction authority. An optional reference may remain accepted until a future explicit evaluation workflow, but it cannot block redacted work.

Portable automated tests exercise durable ordering and two sequential API workflows with controlled application-owned worker/model boundaries. Host acceptance separately runs the exact qualified worker and model against generated synthetic PDFs, verifies persisted target/attempt provenance and null truth, then proves process replay and restart reads do not add attempts. Browser acceptance uses the reviewed same-origin bundle and treats all model text as inert content.

## Failure and recovery behavior

- PDF runtime unavailable: requested redacted job remains `ACCEPTED` and unclaimed.
- PDF unsupported/failure/no redactions: terminal document state, no prediction attempt, no numeric score.
- Model runtime unavailable after PDF readiness: redacted job stays `READY`; an explicit retry resumes prediction.
- Timeout/error/refusal/malformed model output: immutable distinct attempt status, not a factual-error score.
- Browser refresh/restart: GET-only recovery by opaque IDs; no new processing or inference.
- Concurrent/duplicate explicit actions: existing orchestration lock and durable one-shot run identity remain controlling.

## Security and research boundaries

All network listeners remain literal IPv4 loopback. Runtime identities and complete file inventories are re-attested before work. Uploaded/reference bytes stay in descriptor-confined application storage, never browser storage or repository artifacts. The task establishes software operation only; it does not validate accuracy, truth alignment, private-data use, institutional permission or recipient release readiness.
