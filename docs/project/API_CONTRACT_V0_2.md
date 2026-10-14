# Redaction Lab local API v0.2 — emergency experimental real-inference contract

**Status:** OWNER-APPROVED FOR BOUNDED IMPLEMENTATION, NOT VERIFIED, MERGED OR DEPLOYED. E0065.  
**Source:** `API_CONTRACT_V0_1.md` (preserved), `RL-MVP-007D-EMERGENCY-REAL-INFERENCE.md`.  
**Baseline:** main `62124fa47b093e5e9a5383c1fd5ba5d055736da9` / E0064. Refresh before action.

## Invariants and compatibility

v0.1 remains the deployed contract until a separately authorized, independently reviewed v0.2 integration. Preserve same-origin literal 127.0.0.1, Host/Origin and request-size checks, 25 MiB/PDF and 50 MiB/pair, 100 pages, one processing job and 60s document processing budget; no new public network exposure. Existing upload, document, job and process shapes and status/error semantics remain backwards compatible. The v0.2 changes below apply only once explicitly implemented and qualified. Maintain versioned contract identification; do not silently emit v0.2 data while identifying as v0.1.

Reference is optional for prediction. Uploads do not confer verified reference truth; DEC-022 synthetic fixture trust restriction remains. Predicted text cannot be displayed as revealed truth. Missing/partial/untrusted truth means `truth_status: "UNKNOWN"`, `score_status: "NONE"`, `verified_score: null`, `experimental_score: null`. No Task 6 changes or numeric score computation.

PDF bytes may produce authoritative canonical text and targets **only** via application-owned, verified isolated PDF worker. Unqualified runtime preserves existing 503 RUNTIME_UNVERIFIED and leaves work unclaimed; never fall back to arbitrary host-side parsing. No reference text, metadata, filename, hints or previous prediction may enter model inputs.

## Proposed v0.2 read behavior

`GET /api/v1/results/{version_id}` retains v0.1 top-level fields:
```json
{
  "version_id": "document-version-id",
  "status": "AVAILABLE",
  "targets": [{
    "target_id": "target-id",
    "target_version": "target-version",
    "page_index": 0,
    "normalized_bbox": [0.1, 0.2, 0.3, 0.4],
    "attempt_id": "attempt-id",
    "attempt_status": "SUCCEEDED",
    "prediction": "genuine model-generated text",
    "model_id": "pinned-experimental-model-id",
    "provider_model_id": "pinned-provider-model-id",
    "model_config_id": "locked-config-id",
    "request_hash": "sha256",
    "response_hash": "sha256"
  }],
  "summaries": {"target": null, "document": null, "model": null},
  "truth_status": "UNKNOWN",
  "score_status": "NONE",
  "verified_score": null,
  "experimental_score": null
}
```

Targets may appear only if bound to an authentic, immutable source/target/run/attempt. If no verified PDF runtime exists, v0.1 empty-target behavior continues. For non-success attempts, `prediction: null`; distinguish `REFUSED`, `TIMEOUT`, `MALFORMED`, `ERROR`, and internal `IN_DOUBT` (never misreport as success or factual mismatch). Include provenance only if it is already trustworthy from RunStore; never invent it. API reads/refresh/reconnect are side-effect-free: they never enqueue, dispatch, retry or overwrite attempts.

## Run creation / process flow

A successful *qualified* processing request may create a deterministic Task 4 RunDefinition for the authentic source, fixed ordered target IDs/versions, canonical source hash, locked exact model/version/digest/config/prompt, condition `redacted-document-only`, full common context when within declared limit, tools disabled, single independent attempt per target. Persist all target intents before dispatch. Each target uses identical frozen redacted visible context with only that target identified; other redactions remain hidden. Do not inject prior predictions into later requests.

The existing process endpoint remains the single intentional entrypoint to processing/inference; repeated process requests cannot create extra attempts. Only explicitly target-scoped durable worker dispatch may run associated attempts. If an external request outcome is ambiguous (crash/timeout), keep `IN_DOUBT`; never auto-retry or claim exactly-once external execution. Fail closed if runtime/model pins, source binding, project permissions, model response provenance, or context compatibility fail.

The local model endpoint must be literal `127.0.0.1`, no proxies/redirects, with exact locked executable/version and full model digest; do not trust caller-supplied adapter or transport, model tag alone, or shortened digest. Model inference is separate from the network-isolated PDF worker. Preserve bounded response handling and safe React text rendering.

## Contract acceptance

Tests: unqualified runtime never creates source/run/attempt; identity/project/source verification; no hidden/reference leakage; one independent request per target; duplicate/restart safety and IN_DOUBT; 503 errors; refusal/timeout/error/malformed separation; authentic Ollama model/version/digest checks; no non-loopback/proxy/redirect egress; browser escaped rendering and score null; old v0.1 clients and routes unaffected.

**Scope limit:** no new endpoints unless explicitly amended, no new DB schema, Task 3/6/detector/canonicalizer/reference authority changes, private data, scientific scores, paid calls, public deployment, or merging without a fresh owner decision.
