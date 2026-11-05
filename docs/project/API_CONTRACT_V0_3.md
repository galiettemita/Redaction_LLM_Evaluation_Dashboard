# Redaction Lab API v0.3 — experimental evaluation

Status: AUTHORIZED FOR BOUNDED IMPLEMENTATION at E0072 / DEC-023; this contract is not implementation, independent verification, deployment or scientific validation.
Baseline: live `main` `cb0fa4f1242ae8bf12afb084bc9475017040b784`, observed 2026-11-05 UTC.
Sources: [v0.2](API_CONTRACT_V0_2.md), [DEC-023](DECISIONS.md#dec-023--automatic-experimental-evaluation-and-controlled-demonstration), [design](../superpowers/specs/2026-11-05-experimental-product-completion-design.md), [plan](../superpowers/plans/2026-11-05-experimental-product-completion.md).

## Invariants and compatibility

The required redacted PDF and optional reference rules, 25 MiB/PDF, 50 MiB/pair, 100 pages, bounded canonical text/response sizes, one document processing job, isolated PDF parser and existing 60-second PDF processing budget remain. Model inference has its separately declared bounded runtime budget. Reference bytes, visible text, metadata, filenames and hints never enter prediction manifests, prompts or adapters. No host-side fallback parsing, paid model call, private/restricted data use or unqualified runtime is authorized.

`truth_status: "UNKNOWN"` describes the verified channel and remains unchanged even when experimental reference alignment succeeds. `verified_score` is always null at every level. A successful experimental mapping is explicitly `USER_SUPPLIED_EXPERIMENTAL`; its `CONFIRMED` status means the engineering alignment checks passed, not verified or scientifically validated truth. The UI must display `EXPERIMENTAL — NOT SCIENTIFICALLY VALIDATED` beside numeric experimental results and `Accuracy unknown` when unavailable.

An experimental target score requires a successful immutable prediction and a unique, complete, readable, reliably aligned exact reference span for the same immutable target. Missing, partial, still-redacted, unreadable, ambiguous, conflicting, mismatched or unprocessed reference yields null, never zero. Refusal, timeout, malformed output, provider error and uncertain execution are technical outcomes, not factual errors. Only an eligible successful prediction can receive a genuine numeric zero.

Route prefix remains `/api/v1`; contract identification changes together to `X-Redaction-Lab-API: 0.3` and health `api_version: "0.3"`. v0.2 route meanings and stored records remain readable; old qualitative evaluation schemas retain their original validators. A strict v0.2 browser needs the matching rebuilt v0.3 bundle; this contract does not promise a v0.2 validator can accept a v0.3 payload. New experimental persistence is additive, version-dispatched and immutable, with a pre-migration backup; no old evaluation is rewritten or promoted.

## Routes and workflow

- `POST /api/v1/documents`: same multipart redacted/optional-reference upload, accepted receipt and content limits as v0.2. Upload alone grants no truth status. Its reference handle identifies immutable paired bytes.
- `GET /api/v1/documents/{version_id}` and `GET /api/v1/jobs/{job_id}`: existing document/job shapes and states remain. Reference processing uses the associated immutable pair and project; reference errors cannot discard a valid redacted prediction.
- `POST /api/v1/jobs/{job_id}/process`: the single intentional entrypoint. Process redacted PDF and associated reference through the qualified isolated worker, freeze redacted-only prediction inputs, persist target intents, run/resume the same one-shot prediction run, then persist versioned experimental mapping/evaluation/summary evidence after terminal attempts. Repeated actions cannot create extra attempts or replace terminal evidence. Reference failure leaves predictions usable with null evaluation.
- `GET /api/v1/results/{version_id}`: returns persisted predictions, mappings, evaluations, counts and summaries. GET, refresh and reconnect never enqueue, dispatch, align, evaluate, retry or modify evidence. An interrupted/ambiguous external outcome remains `IN_DOUBT` without automatic retry.
- `GET /api/v1/health`: `{ "api_version": "0.3", "state": "READY" | "DEGRADED", "runtime_qualified": false, "mode": "local" }`. The legacy aggregate qualification flag remains false until final recipient qualification; it does not negate separately recorded host PDF/model qualification. READY/DEGRADED must reflect actual available capabilities, not claimed scientific readiness.

Process receipts retain `job_id`, `status`, `reason_code`, `source_id`; processing states remain `ACCEPTED`, `PROCESSING`, `READY`, `NO_REDACTIONS`, `UNSUPPORTED`, `FAILED`. Results states remain `PENDING`, `AVAILABLE`, `NO_REDACTIONS`, `UNSUPPORTED`, `FAILED`, `NEEDS_REVIEW`. Processing READY/AVAILABLE alone never asserts prediction success or known accuracy. Unqualified PDF/model boundaries retain `503 RUNTIME_UNVERIFIED` / `503 MODEL_RUNTIME_UNVERIFIED`; errors retain `{ "error": { "code": "...", "message": "..." } }` and existing HTTP security/status semantics.

## Result records

`targets` remains a flat array of actual persisted attempt rows. Multiple model/configuration rows may share a target; `attempt_id` is unique, and `(target_id, target_version, model_id, model_config_id)` identifies the one-shot comparison cell. Existing fields remain: target ID/version, zero-based page index, normalized bounding box, attempt ID/status, prediction, model ID, provider model ID, model config ID, request hash, nullable response hash. Prediction is nonempty bounded text only for `SUCCEEDED`; `REFUSED`, `TIMEOUT`, `MALFORMED`, `ERROR`, `IN_DOUBT` have null prediction. Do not fabricate rows/IDs for undispatched work; progress reports pending intents separately.

Each row adds `mapping` (nullable) and `evaluation` (nullable). Both are absent/null until persisted; absence is not an invitation for a GET to calculate them. Mapping exposes its immutable ID/version, reference document version, method/version, explicit provenance, status/scoreability, exact revealed text or null, canonical source hashes, locator and explanation. Successful experimental mappings carry all original exact-span/two-sided-anchor and boundary evidence in persisted provenance; unknown mappings never expose an invented or partial exact quote. A null mapping means no processed reference evidence; a persisted NOT_SCOREABLE mapping explains why.

Evaluation schema is `experimental-text-agreement-evidence-v1`, method ID `experimental-text-agreement-v1`, scale `0–100 text agreement`. It binds immutable attempt ID, mapping ID/version, target ID/version, prediction/reference hashes and exact model/configuration identity. API may use enclosing row identity for these fields only when serialization validates that exact binding. Its `score_status` is `EXPERIMENTAL` only for numeric experimental evidence; otherwise `NONE`, `experimental_score: null`, subscores null, with a reason. `verified_score` remains null. A mapping can be eligible while an attempt fails technically; that evaluation stays null/unknown and does not reduce an agreement average as a zero.

Numeric subscores are finite values on 0–1, alongside boolean `normalized_exact_match`: `token_precision`, `token_recall`, `token_f1`, `ordered_token_agreement`, `character_trigram_f1`, `critical_detail_agreement`. The score is `100 * (0.40 * token_f1 + 0.25 * ordered_token_agreement + 0.20 * character_trigram_f1 + 0.15 * critical_detail_agreement)`. Normalized exact match returns 100. Explicit negation mismatch caps at 35; quantity/date mismatch caps at 60; apply the tighter cap when both occur. Round to one decimal. Evidence stores the deterministic normalization/tokenization version, hashes, warnings and applied caps. These are engineering experimental defaults, not approved scientific weights. Lexical agreement cannot certify semantic role direction, paraphrases or historical correctness; report that limitation without inventing semantic confidence.

Example, synthetic placeholders (IDs/hashes illustrate shape, not observed runtime evidence):

```json
{
  "version_id": "redacted-version-1",
  "status": "AVAILABLE",
  "targets": [
    {
      "target_id": "target-1",
      "target_version": "target-version-1",
      "page_index": 0,
      "normalized_bbox": [
        0.1,
        0.2,
        0.3,
        0.4
      ],
      "attempt_id": "attempt-1",
      "attempt_status": "SUCCEEDED",
      "prediction": "twelve aircraft",
      "model_id": "qwen2.5:1.5b-instruct-q4_K_M",
      "provider_model_id": "qwen2.5:1.5b-instruct-q4_K_M",
      "model_config_id": "locked-config-id",
      "request_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "response_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "mapping": {
        "mapping_id": "mapping-1",
        "mapping_version": "mapping-version-1",
        "reference_document_version_id": "reference-version-1",
        "mapping_method_version": "text-first-experimental-reference-v1",
        "provenance": "USER_SUPPLIED_EXPERIMENTAL",
        "status": "CONFIRMED",
        "scoreability": "SCOREABLE",
        "exact_revealed_text": "twelve aircraft",
        "reference_token_locator": "tokens:4:6",
        "redacted_canonical_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "reference_canonical_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "explanation": "Unique complete span supported by both surrounding anchors."
      },
      "evaluation": {
        "evaluation_id": "evaluation-v1",
        "schema_version": "experimental-text-agreement-evidence-v1",
        "method_id": "experimental-text-agreement-v1",
        "scale": "0–100 text agreement",
        "score_status": "EXPERIMENTAL",
        "experimental_score": 100.0,
        "verified_score": null,
        "reason": null,
        "prediction_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "reference_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "subscores": {
          "normalized_exact_match": true,
          "token_precision": 1.0,
          "token_recall": 1.0,
          "token_f1": 1.0,
          "ordered_token_agreement": 1.0,
          "character_trigram_f1": 1.0,
          "critical_detail_agreement": 1.0
        },
        "warnings": [],
        "applied_caps": []
      }
    }
  ],
  "progress": {
    "total": 1,
    "pending": 0,
    "running": 0,
    "terminal": 1
  },
  "counts": {
    "requested": 1,
    "eligible": 1,
    "scored": 1,
    "unknown": 0,
    "excluded": 0,
    "technical_failures": 0
  },
  "summaries": {
    "target": [
      {
        "summary_id": "summary-target-v1",
        "schema_version": "experimental-summary-v1",
        "model_id": "qwen2.5:1.5b-instruct-q4_K_M",
        "model_config_id": "locked-config-id",
        "method_id": "experimental-text-agreement-v1",
        "scale": "0–100 text agreement",
        "score_status": "EXPERIMENTAL",
        "experimental_score": 100.0,
        "verified_score": null,
        "counts": {
          "requested": 1,
          "eligible": 1,
          "scored": 1,
          "unknown": 0,
          "excluded": 0,
          "technical_failures": 0
        },
        "denominator": 1,
        "member_ids": [
          "evaluation-v1"
        ],
        "target_id": "target-1",
        "target_version": "target-version-1"
      }
    ],
    "document": [
      {
        "summary_id": "summary-document-v1",
        "schema_version": "experimental-summary-v1",
        "model_id": "qwen2.5:1.5b-instruct-q4_K_M",
        "model_config_id": "locked-config-id",
        "method_id": "experimental-text-agreement-v1",
        "scale": "0–100 text agreement",
        "score_status": "EXPERIMENTAL",
        "experimental_score": 100.0,
        "verified_score": null,
        "counts": {
          "requested": 1,
          "eligible": 1,
          "scored": 1,
          "unknown": 0,
          "excluded": 0,
          "technical_failures": 0
        },
        "denominator": 1,
        "member_ids": [
          "evaluation-v1"
        ],
        "document_version_id": "redacted-version-1"
      }
    ],
    "model": [
      {
        "summary_id": "summary-model-v1",
        "schema_version": "experimental-summary-v1",
        "model_id": "qwen2.5:1.5b-instruct-q4_K_M",
        "model_config_id": "locked-config-id",
        "method_id": "experimental-text-agreement-v1",
        "scale": "0–100 text agreement",
        "score_status": "EXPERIMENTAL",
        "experimental_score": 100.0,
        "verified_score": null,
        "counts": {
          "requested": 1,
          "eligible": 1,
          "scored": 1,
          "unknown": 0,
          "excluded": 0,
          "technical_failures": 0
        },
        "denominator": 1,
        "member_ids": [
          "summary-document-v1"
        ],
        "document_version_ids": [
          "redacted-version-1"
        ],
        "document_count": 1
      }
    ]
  },
  "truth_status": "UNKNOWN",
  "score_status": "EXPERIMENTAL",
  "verified_score": null,
  "experimental_score": null
}
```

The legacy top-level `experimental_score` remains null; numbers live only in identity-bound target evaluations and summary records. Top-level `score_status` is `EXPERIMENTAL` when any numeric experimental evaluation exists, otherwise `NONE`; it is not a cross-model score. The verified `truth_status` stays `UNKNOWN` in either case.

Unknown example fragment (all other row identity/provenance fields remain required):

```json
{
  "mapping": {
    "mapping_id": "mapping-unknown-1",
    "mapping_version": "mapping-version-1",
    "provenance": "USER_SUPPLIED_EXPERIMENTAL",
    "status": "PARTIAL",
    "scoreability": "NOT_SCOREABLE",
    "exact_revealed_text": null,
    "explanation": "The exact target is not fully revealed."
  },
  "evaluation": {
    "evaluation_id": "evaluation-unknown-1",
    "schema_version": "experimental-text-agreement-evidence-v1",
    "method_id": "experimental-text-agreement-v1",
    "scale": "0–100 text agreement",
    "score_status": "NONE",
    "experimental_score": null,
    "verified_score": null,
    "subscores": null,
    "reason": "PARTIAL_REFERENCE",
    "warnings": [],
    "applied_caps": []
  }
}
```

## Counts, progress and aggregates

`summaries.target`, `.document`, `.model` are arrays (empty when none exist), never one blended cross-model number. Every record binds exact model/configuration, method/schema and immutable member IDs; document records bind document version, target records bind target/version, model records disclose the selected document set. Incompatible provider/model/configuration, prompt/condition, target/reference versions or scoring methods cannot be pooled.

`counts` at document-results and each summary has nonnegative integers:

| Field | Meaning |
| --- | --- |
| `requested` | Frozen in-scope target/model intents in that scope, including pending intents. |
| `eligible` | Requested cells whose complete, readable, reliably aligned reference meets experimental eligibility, independent of attempt outcome. |
| `scored` | Eligible cells with successful predictions and persisted numeric experimental evaluations. |
| `unknown` | Requested cells without reliable complete truth (includes unprocessed reference); accuracy unknown. |
| `excluded` | Unsupported candidate targets excluded before in-scope request creation; never a score denominator. |
| `technical_failures` | Terminal refusal, timeout, malformed, error or IN_DOUBT cells, counted separately from factual agreement. |

`requested = eligible + unknown`; `scored <= eligible`; technical-failure counts may overlap eligible or unknown, and must never be added as a disjoint truth category. Top-level counts are target/model cells; with one model they equal target counts. Exclusions are unique excluded candidates in scope and must not be multiplied by the number of models. Model summaries additionally expose a `document_count` and their denominator counts scored documents; target/document summary denominators count scored cells. `document_count` is required for model summaries and is not required at target/document level.

`progress = { total, pending, running, terminal }` counts durable prediction intents; `total = pending + running + terminal = requested`. Terminal includes technical failures. Before intents exist, all are zero; PDF job status separately reports extraction. Counts come from actual persisted states and must not simulate parallel work. Synchronous orchestration is permitted; it must not invent intermediate observations.

Document experimental score is the equal-target mean of its scored target cells for that exact model/configuration. Model experimental score is the equal-document mean of scored document summaries within the declared compatible selected set; show `document_count`, scored-document denominator and target counts. Empty scored denominator yields null/`NONE`, never zero. These completed-answer agreement averages are not recovery rates over all requested targets; eligible/scored/unknown/excluded/technical counts remain visible. Unsupported-only documents may produce exclusion-only null summaries. Summary identities include their immutable members so later evidence creates a new revision rather than mutating history.

## Local and controlled-link security

The application still binds literal `127.0.0.1` and preserves local Host/Origin, framing, content-length and response limits. Browser clients use same-origin relative requests, no redirects or arbitrary backend override. The controlled-link build may use its current HTTPS browser origin; this does not authorize direct remote access to the loopback API. A separately reviewed gateway accepts only its configured exact public Host/HTTPS Origin and authenticated requests, then translates validated requests to the existing loopback boundary. Reject ambiguous framing, wrong origins/hosts and attempts to route to Ollama. No credentials, tunnel hostname, raw documents or provider payloads enter Git. [Controlled demo packet](task_packets/RL-LINK-017-CONTROLLED-DEMO.md) owns that exposure.

## Acceptance consumers

[RL-EXP-015](task_packets/RL-EXP-015-EXPERIMENTAL-EVALUATION.md) implements isolated evidence/scoring/orchestration; [RL-UX-016](task_packets/RL-UX-016-EXPERIMENTAL-WORKSPACE.md) validates and renders this contract; [RL-LINK-017](task_packets/RL-LINK-017-CONTROLLED-DEMO.md) verifies the authenticated delivery boundary. Tests must cover unknown/null cases, exact identity, tamper/legacy reopening, adversarial alignment, detail caps, one-shot recovery, GET read-only behavior, reference exclusion, no cross-model blend, safe text rendering and wrong-origin rejection. Passing software checks cannot close D03–D06 or institutional/data gates.
