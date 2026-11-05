# Experimental Product Completion Design

Date: 2026-11-05

Owner direction: finish the application autonomously, use genuine LLM inference, display clearly labeled experimental accuracy results without waiting for formal scientific validation, and provide a working link.

## Intent

Turn the merged synthetic engineering vertical slice into a usable local-first experimental application. A researcher uploads a redacted PDF and optionally a matching reference PDF, starts genuine local-model prediction, sees per-target results and progress, and receives automatic experimental accuracy results when the supplied reference yields complete, readable, reliably aligned text.

The application must never present an experimental score as scientifically validated, verified truth, or historical correctness. `verified_score` remains null. Missing, partial, ambiguous, unreadable, mismatched, or unprocessed reference content remains `Accuracy unknown` with a null experimental score.

## Goals

- Use the installed, integrity-pinned Qwen2.5 1.5B Ollama model for genuine predictions; remove the rule-based demo from the primary workflow.
- Process reference PDFs inside the same isolated PDF-worker boundary and preserve versioned reference provenance.
- Automatically align user-supplied matching references conservatively for the experimental channel without promoting them into verified truth.
- Produce a transparent, deterministic 0–100 experimental text-agreement score with subscores and critical-detail warnings.
- Show target, document, and model experimental summaries with eligible, scored, unknown, excluded, and technical-failure counts.
- Provide a document-centered UI with local PDF viewing, redacted/reference toggle, target selection, friendly technical states, visible experimental labels, and durable refresh/reconnect behavior.
- Improve prediction parsing so genuine model text is retained when the provider envelope is valid and the model returns the required bounded reconstruction shape.
- Publish the reviewed local application through an authenticated HTTPS ngrok gateway without exposing Ollama or bypassing the loopback application boundary.
- Keep exact provenance, immutable attempts/evaluations, one-shot semantics, null unknowns, and reference exclusion from prediction inputs.

## Non-goals

- Scientific validation, calibrated probability-of-truth claims, or a `verified_score`.
- Private, institutional, or controlled document use through the public tunnel.
- A permanent cloud-native service, public unauthenticated deployment, or paid provider calls.
- Claiming that one local Qwen model satisfies the eventual commercial multi-model comparison requirement.
- Inferring scores when exact reference text is not confidently isolated.

## Approaches considered

### 1. Local-first application plus authenticated HTTPS tunnel — selected

Build on the existing Python/React/SQLite application and the already qualified macOS PDF/Ollama runtimes. Add an explicit gateway that validates the configured public Host and Origin, then forwards to the loopback-only application. This produces the fastest honest working link with genuine inference and no new spend. The Mac must remain awake and the release is a controlled experimental demonstration, not a permanent deployment.

### 2. Fully hosted Vercel application

Rejected for this completion pass. The current application depends on a macOS Ollama binary, local model files, a Podman PDF-worker VM, durable SQLite, and 25 MiB uploads. Vercel Functions have a smaller request-body limit and no compatible persistent/runtime boundary. A cloud port would be a separate backend and infrastructure project requiring model-provider credentials or paid compute.

### 3. Browser-downloaded model and browser-only PDF processing

Rejected because it would replace the reviewed isolation, persistence, and provenance architecture; model/browser hardware support would be inconsistent, and the rewrite would not preserve the established contracts.

## Owner clarification and decision effect

The owner's 2026-11-05 clarification authorizes the application to compute and display automatic experimental evaluation before formal scientific validation. It creates an experimental channel only:

- `score_status = EXPERIMENTAL`
- `experimental_score` may be numeric only when exact target truth is completely and reliably aligned
- `verified_score = null`
- the UI says `EXPERIMENTAL — NOT SCIENTIFICALLY VALIDATED`
- user-supplied reference mappings remain experimental evidence, not verified reference truth
- formal D03–D06 validation remains open for verified/scientific claims

This supersedes DEC-022's synthetic-registry restriction only for the explicitly labeled experimental channel. It does not weaken the verified channel, null/unknown rule, prediction/reference isolation, or institutional data gates.

## Experimental scoring method

Method ID: `experimental-text-agreement-v1`; scale: `0–100 text agreement`.

Eligibility requires a successful prediction plus a unique, complete, readable, reliably aligned exact reference span for the same immutable target. Otherwise the score is null.

The versioned deterministic method reports:

- normalized exact match;
- token multiset precision, recall, and F1;
- ordered-token longest-common-subsequence agreement;
- character trigram F1 for limited wording variation;
- critical-detail agreement for numbers, dates/months, negation markers, and capitalized entities;
- explicit mismatch warnings for changed quantities, dates, or negation.

The owner's request for a functioning experimental algorithm delegates selection of the versioned experimental weights and contradiction caps to engineering. It does not approve those values for verified or scientific scoring. Version 1 weights token F1 at 40%, ordered-token agreement at 25%, character-trigram F1 at 20%, and critical-detail agreement at 15%. Exact match returns 100. Any explicit negation mismatch caps the result at 35; any quantity/date mismatch caps it at 60. Scores are rounded to one decimal place.

The composite is a transparent weighted agreement heuristic, not a semantic probability. Critical-detail contradictions cap the composite so identical topic words cannot erase changed quantities or negation. The UI exposes each subscore and warns that paraphrases and role reversals can still challenge this baseline. The method is independently versioned so a later semantic/NLI judge never rewrites old evaluations.

## Reference processing and trust

The isolated worker returns bounded canonical visible reference text, its SHA-256, canonicalizer version, and page count for `REFERENCE` requests. It never returns hidden annotations, arbitrary files, or executable content. The application persists this derived reference record immutably and associates it with the uploaded pair.

Alignment consumes the persisted redacted canonical source and isolated reference canonical text. It uses the existing text-first, two-sided-anchor algorithm. A new experimental provenance label distinguishes user-supplied alignment from the pinned synthetic verified fixture path. Ambiguous, partial, still-redacted, or incoherent mappings are unscoreable.

Reference bytes/text never enter prediction manifests, prompts, or model adapters.

Task 2 is source/test-only. Task 6 explicitly owns rebuilding and requalifying the changed `pdf-worker-v2` image, source/image hashes, SBOM and runtime lock with existing pinned zero-cost runtime assets. That prerequisite follows reviewed Task 2 source and precedes live Task 4 processing/canary; v1 qualification does not carry over automatically.

## API and persistence

API v0.3 extends, rather than reinterprets, v0.2:

- processing starts durable redacted and associated reference work;
- results include per-target attempts, experimental evaluation, mapping state, and aggregate summaries;
- GET remains read-only and never starts model or evaluator work;
- refresh/reconnect never creates another attempt;
- legacy qualitative records remain readable under their original validators;
- new experimental evidence has its own schema/version and immutable identity;
- progress exposes pending/running/terminal counts even if the first implementation keeps one bounded worker.

Schema migrations are additive. Existing application data receives a pre-migration backup through the current migration helper.

## UI

The primary workspace has:

- upload and saved-document recovery;
- local browser PDF view using object URLs for files currently selected by the user, with redacted/reference toggle and multipage browser controls;
- target list with keyboard selection, page number, status, model identity, prediction, exact revealed passage when eligible, and mapping explanation;
- experimental score cards at target/document/model levels, visible eligibility denominators, and a persistent non-validation badge;
- distinct refusal, timeout, malformed, provider error, unknown-truth, and processing-error messages;
- action errors that remain visible after status refresh;
- no rule-based candidate generator presented as part of the real product.

A restored document can show persisted results but cannot recreate a browser-local PDF preview unless the user selects the file again; this limitation is stated plainly.

## Link and security

The first link is an owner-only authenticated demonstration backed by one local workspace. It is not a multi-user service and does not provide per-user document authorization. Anyone given its credentials could see that demonstration workspace, so credentials are not shared with other researchers and only synthetic demonstration documents are stored there.

The application remains bound to `127.0.0.1`. A new gateway binds only to a second loopback port, accepts only the configured ngrok hostname and HTTPS Origin, rejects ambiguous framing and oversized bodies, then translates the request to the existing local Host/Origin contract. It never forwards to Ollama directly.

ngrok uses authentication, inspection disabled, and private configuration outside the repository. Only synthetic or explicitly authorized public documents may be used. The link is available only while the Mac, application, gateway, and tunnel are running.

## Acceptance

- Fresh full Python and Node suites pass.
- Production frontend build is deterministic and rebound in the packaging manifest.
- A genuine local Qwen run produces at least one persisted `SUCCEEDED` prediction on a supported synthetic PDF.
- A matching synthetic reference yields at least one persisted experimental target score and non-null document/model experimental summaries while `verified_score` remains null.
- Missing/mismatched/partial reference cases remain null/unknown.
- Browser acceptance covers upload, view toggle, process, progress/results, target selection, score labels, error states, and reconnect without paid duplicate work.
- Authenticated HTTPS link returns the application and rejects unauthenticated or wrong-origin mutations.
- Canonical state, decision, checklist, task handoff, commits, and review evidence are reconciled before integration.

## Builder calls

- Ship one genuine local model in this pass because no second qualified model or provider credential exists; label the roster limitation.
- Prefer deterministic text agreement over pretending that the existing small predictor is an independent semantic judge.
- Keep synchronous orchestration if a safe background worker would jeopardize the completion; expose truthful progress and preserve durable state rather than simulating streaming.
- The authenticated tunnel is a temporary controlled link, not a cloud deployment or data authorization.
- Resolve the qualified runtime from one explicitly configured, owner-controlled absolute runtime root after no-symlink/ownership/permission checks; default behavior remains fail-closed and legacy relative package resolution remains compatible.
