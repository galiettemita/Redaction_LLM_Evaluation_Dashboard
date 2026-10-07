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

## Research-critical boundaries

The viewer can display both versions, but the prediction path cannot. Reference-derived filenames, hints, summaries, context, caches and evaluator feedback must not leak into prompts. Target detection must not derive the question from the reference answer. Unknown truth and worker errors are separate states. Completed predictions remain immutable when reference mappings are corrected.

## Failure questions each component design must answer

What state is durably committed before a side effect? What happens after a worker crash, duplicate delivery, ambiguous remote timeout, late callback, cancellation or reference edit? Which component owns recovery? What is the idempotency scope? How are budgets/concurrency bounded? Which summary is stale and why? What evidence shows that cross-project permissions hold?

Do not promise exactly-once external billing. Persist and label uncertain provider outcomes; do not create a new experiment under a hidden retry. Restore progress from stored state after reconnect. Only affected evaluations/summaries are superseded when their dependencies change.

## Agent coordination is a separate concern

GitHub documents coordinate engineering work; they are not the product's job queue or database. AGENTS.md and handoff rules are cooperative instructions, not security controls or distributed locks. Shared-state updates use one integration writer and version checks. A real autonomous orchestrator would need its own approved design, credentials, task queue, budgets and failure model; none is installed.

## Architecture decision record template

For a new design, include ID/status, source requirements, options/tradeoffs, selected option and approver, data/permission boundaries, failure and concurrency semantics, observability, test evidence, migration/rollback, cost and affected consumers. Record accepted changes in DECISIONS; proposed changes stay visibly proposed. Do not resolve D01-D10 by choosing defaults in implementation code.
