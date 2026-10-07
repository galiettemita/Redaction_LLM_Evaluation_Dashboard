# Architecture

**Status:** proposed logical boundaries from source B1 sections 6/13-16; no stack selected and no services implemented. Read [MASTER_SPEC.md](MASTER_SPEC.md) and [DECISIONS.md](DECISIONS.md) before treating a design as approved.

## Direction

Start with a small modular application plus durable workers. Responsibilities do not imply one microservice per row. Hosting, languages, framework, database, queue and authentication require D07 review against the lab environment.

| Boundary | Responsibility |
| --- | --- |
| Web UI | Upload, authorized viewing, progress, target selection, answers, research details. No provider secrets. |
| Application API | Identity, permissions, immutable run setup, result queries, corrections and export. |
| Document processor | Validate, derive visible content, detect text targets, align references, establish completeness. Does not score predictions. |
| Prediction worker | Approved adapter calls using redacted-only manifests; no reference-data access. |
| Evaluation worker | Frozen prediction plus approved reference; versioned assessment; never edits the answer. |
| Summary logic | Declared aggregation of eligible evaluation records, not frontend labels. |
| Metadata store | Project-scoped versions, attempts, mappings, evaluations, reviews and audit. |
| Protected artifact store | Original/derived artifacts with role-specific access. |
| Job coordination | Durable dispatch, bounded retry/concurrency, cancellation, progress and usage. |

## Approved redaction-detection direction

The document processor must discover supported text redactions automatically. Treat one visually contiguous blacked-out region in text flow as one immutable RedactionTarget. Normal product use does not ask the user to draw, approve or correct target boxes.

Detection is hybrid and independent:
1. Parse PDF graphics operators for filled near-black rectangles/polygons and normalize their page coordinates.
2. Render each page deterministically and run raster dark-region/contour detection for scans or flattened PDFs.
3. Fuse geometrically equivalent candidates.
4. Validate text context using native text and/or approved OCR baselines, neighboring visible words, line geometry, paragraph/column structure and region dimensions.
5. Exclude image/table/whole-page/non-redaction candidates under DEC-002.
6. If supported targets cannot be established reliably, return a document-processing failure/unsupported state rather than requesting manual target marking.

Detection output is versioned. Improved detectors create a new detection/target version; they do not silently mutate prior experiments. Adjacent physical black boxes stay distinct targets; raster fragments may be merged only when they are evidence of the same physical rectangle.

## Approved baseline prediction-context direction

Prediction workers consume a canonical redacted-document representation generated from the redacted artifact, not provider-specific PDF parsing. Every participating model in one comparative run gets the same frozen visible text/context representation and one specially marked target. Other redactions remain hidden. Each target is predicted in an independent request from the same frozen source; a prior prediction is never inserted into later target context.

The preferred baseline supplies the full canonical redacted document when it fits the common approved context budget of every participating model. The initial comparative condition must not silently truncate differently per provider. Reference content, evaluator feedback, web and retrieval tools are excluded from this baseline. Models may use their existing parametric/pretraining knowledge; the experiment does not claim document-only logical derivability.

## Approved reference-alignment direction

Reference alignment is content-first, not page-first. Build a canonical token stream for the redacted release and for the uploaded reference release while retaining exact source text/locators separately.

Alignment runs in two stages:
1. Compute a global monotonic alignment over stable matching token sequences across the two canonical streams. This establishes broad correspondence despite inserted covers, page-number changes, line wrapping, punctuation differences, or modest OCR noise.
2. For each RedactionTarget, take stable left/right token windows surrounding the target in the redacted stream, locate their aligned counterparts in the reference stream, widen context when needed, and extract only the intervening reference span as the candidate reveal.

Use deterministic/versioned sequence-alignment and diff-style methods as the primary authority. Page number, geometry and layout may corroborate or reject a candidate but are not the primary locator. An LLM must not manufacture ground truth.

A mapping is eligible for verified scoring only when the exact revealed span is unique, complete, readable and reliably aligned under the approved D03 acceptance criteria. Multiple plausible matches, substantial rewrite, unreadable OCR, conflicting releases, or a still/partly redacted candidate produce an unknown/uncertain mapping and therefore null score. Store the exact revealed quotation plus alignment evidence/version so the mapping is auditable and reproducible.

## Owner-approved MVP direction (DEC-015..017)

Prefer a small local modular Python evaluation/document pipeline, lightweight API/worker and durable local state with a simple web viewer. FastAPI, React and SQLite are candidates, not finalized technology decisions. Use synthetic or explicitly authorized public fixtures, mockable providers and no new paid calls/cloud resources. Preserve reference/prediction isolation, idempotency, immutable versions and recovery.

## Research-critical boundaries

The viewer can display both versions, but the prediction path cannot. Reference-derived filenames, hints, summaries, context, caches and evaluator feedback must not leak into prompts. Target detection must not derive the question from the reference answer. Unknown truth and worker errors are separate states. Completed predictions remain immutable when reference mappings are corrected.

## Failure questions each component design must answer

What state is durably committed before a side effect? What happens after a worker crash, duplicate delivery, ambiguous remote timeout, late callback, cancellation or reference edit? Which component owns recovery? What is the idempotency scope? How are budgets/concurrency bounded? Which summary is stale and why? What evidence shows that cross-project permissions hold?

Do not promise exactly-once external billing. Persist and label uncertain provider outcomes; do not create a new experiment under a hidden retry. Restore progress from stored state after reconnect. Only affected evaluations/summaries are superseded when their dependencies change.

## Agent coordination is a separate concern

GitHub documents coordinate engineering work; they are not the product's job queue or database. AGENTS.md and handoff rules are cooperative instructions, not security controls or distributed locks. Shared-state updates use one integration writer and version checks. A real autonomous orchestrator would need its own approved design, credentials, task queue, budgets and failure model; none is installed.

## Architecture decision record template

For a new design, include ID/status, source requirements, options/tradeoffs, selected option and approver, data/permission boundaries, failure and concurrency semantics, observability, test evidence, migration/rollback, cost and affected consumers. Record accepted changes in DECISIONS; proposed changes stay visibly proposed. Do not resolve D01-D10 by choosing defaults in implementation code.
