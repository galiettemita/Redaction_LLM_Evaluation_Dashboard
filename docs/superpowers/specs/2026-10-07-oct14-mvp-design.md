# Redaction Lab — October 14 MVP design

Status: PROPOSED FOR OWNER REVIEW. Not an implementation authorization.
Date: 2026-10-07. Deadline: 2026-10-14. Baseline: 7a3150ceea2d5fb23aa8acfaeef2b0ed2c4c2bc1, E0004.
Authority: MASTER_SPEC.md and DEC-001 through DEC-018.

## Purpose and success

Build the smallest real end-to-end Redaction Lab: upload one redacted PDF and a matching reference PDF; automatically detect every supported black-box text redaction; construct redacted-only canonical text; align exact revealed spans; make one independent prediction per target with ONE real model; use a DIFFERENT local evaluation model plus deterministic checks; display predictions, reference text and clearly qualified scores per target, document and model.

The reference is required for scoring this October 14 demonstration but remains optional for prediction in the long-term product. A working demo is not a research-validated accuracy system.

## Alternatives

Recommended: modular local Python backend, one local open-weight predictor, a separate local factuality/NLI judge, and a thin web UI. This avoids additional API spending if available hardware can run the models; it also supports future commercial-model adapters.

Rejected for the no-spend checkpoint: hosted commercial model APIs (subscriptions do not include API credits, and external data transfer needs lab authorization). Mock-only predictions remain necessary for tests but do NOT satisfy the live-model demonstration.

Exact local models are not selected until hardware, license, download and runtime feasibility are checked. If no suitable machine is available, mark the live-model checkpoint BLOCKED rather than pretending a mock is real.

## Week-one input boundary

Accept short English, digitally born PDFs with selectable visible text and rectangular black text redactions. Process all supported text targets; report the detected count and unsupported/unknown count. Reject or explicitly flag scans needing OCR, complex/reflowed PDFs, tables, images, full-page removals, unreadable references and oversized inputs until validated. These are week-one limits, not changes to the long-term hybrid detector design. Test and document actual size/page/context limits rather than inventing them.

Critically, a black overlay may conceal selectable underlying PDF text: remove all text intersecting detected black boxes from the prediction representation. Do not leak answers through PDF layers, metadata, annotations, filenames, logs, or reference-derived prompts.

## Architecture and contracts

Local browser -> thin viewer/UI -> application API -> PDF processing -> immutable target manifest and canonical redacted text -> local job coordinator -> prediction adapter -> frozen ModelAttempt -> separate evaluator worker -> EvaluationRecord -> SummarySnapshot/UI.

A separate reference-alignment process consumes the reference PDF and outputs exact span mappings with evidence; prediction adapters cannot read those artifacts. Each target is predicted independently from the same frozen redacted-only input, with other redactions still hidden. Prior guesses never become context for later targets.

Keep explicit versioned records: DocumentVersion, RedactionTarget, ReferenceMapping, RunDefinition, ModelAttempt, EvaluationRecord, SummarySnapshot and JobState. Python, FastAPI, React and SQLite are candidate technologies, not a production-stack approval. Use a durable local worker, immutable attempts, idempotent run IDs, and restart-safe state.

## Evaluation rule

Ground truth is scoreable only when complete, readable, uniquely aligned and reliably supported by the reference. Partial, repeated/ambiguous, conflicting or unreadable mappings produce null verified score and visible 'Accuracy unknown'.

Use a separate local factuality/NLI evaluator, not the prediction model grading itself. Candidate evaluation combines fact coverage, fact support, contradiction checks, exact entities/dates/quantities/negation and semantic paraphrase matching. Exact judge, weights, numerical mapping and thresholds remain unvalidated under D04. A provisional demo score may be shown only with a versioned, reviewed demo rubric and an explicit EXPERIMENTAL label. Verified-score field remains null until human benchmark validation and research approval. Do not invent a percentage if that gate is missing.

## UI and operations

Two PDF inputs; Run action; progress; selectable target passages in a document-centered view; prediction, revealed text, experimental evaluation or unknown status on the side; counts/summary for the one model. Simple copy, accessible controls, no technical jargon in the primary view.

Single-user local-only demo; no cloud deployment, provider billing, restricted documents, public data uploads or external API calls. Store artifacts outside the public repository. Model output and PDF text are untrusted data. No automatic retry of an ambiguous paid request.

## Acceptance evidence

- End-to-end local run with two authorized synthetic multi-redaction PDFs, a real predictor and distinct evaluator, and visible per-target results.
- Every supported redaction is represented in the target manifest; unknown/unsupported cases are counted, not silently skipped.
- Tests for black overlays with underlying selectable secret text, adjacent boxes, repeated anchors, wrong pairing, partial truth, negation/role reversal, model refusal/timeout, idempotent rerun, reconnect and null aggregation.
- Exact commands, environment, model/version, input hashes, tests run/not run, known limitations and demonstration recording documented.
- Research/QA review of the exact candidate; any provisional score explicitly marked unvalidated.

Out of scope for October 14: full scan/OCR support, DOCX, multiple prediction models, production deployment/auth, calibrated scientific accuracy claims, large-document scaling, and external retrieval. These remain in the long-term plan.

Review gate: owner must approve this written MVP design and the subsequent detailed Codex implementation plan before product code/scaffolding begins. Approval of scope is not permission for paid calls or release.
