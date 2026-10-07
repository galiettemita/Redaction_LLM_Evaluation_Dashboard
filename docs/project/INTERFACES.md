# Interfaces and data contracts

**Status:** proposed minimum contracts from B1 sections 6/7/13-15. This is not a database migration, final JSON schema or implemented API. Version tag: `contract-draft-0.1`. Approval of typed schemas belongs to a scoped component task.

## Record boundaries

| Record | Required meaning / dependencies |
| --- | --- |
| DocumentVersion | Project ID, original hash, role (redacted/reference), type, time, provenance, access policy and derivatives. |
| RedactionTarget | Stable target ID, redacted-document version, page coordinates, visible-context locator, scope status and detection version. |
| ReferenceMapping | Target/version, reference version, exact quoted span and locator, mapping version, completeness, review status/provenance. |
| RunDefinition | Fixed target versions, model roster, condition, redacted-only input manifest, prompt/settings/attempt policy, budget, creator. |
| ModelAttempt | Run/target/model/config IDs, request/response hashes, prediction, outcome, usage/timestamps; frozen when complete. |
| EvaluationRecord | Frozen attempt, mapping/reference version, evaluator/rubric version, fact comparisons, contradictions, score or null, status/explanation. |
| SummarySnapshot | Included evaluation IDs, condition/version filters, formula/weights, counts/denominators, time and freshness. |
| ReviewAuditEvent | Actor, action/reason, old/new version pointers and evidence references. |

Stable IDs must not be just page numbers or mutable offsets. All references are project-scoped; matching hashes do not grant cross-project access. Identity/version changes must be visible to downstream consumers.

## Separate state dimensions

The contract must represent reference state, prediction outcome, evaluation state and score independently. Candidate reference states: known/confirmed, partly revealed, still hidden, absent, unreadable/uncertain mapping, conflicting references, unsupported target. These names describe semantics; exact enums remain to be approved.

A successful prediction with absent truth is valid output with unknown accuracy. An evaluation can finish with no numeric score. A failure/refusal/timeout is not a contradiction. Unknown score must serialize as null/absence under one agreed schema, never an implicit zero. Final schema design must choose one representation and test every consumer.

## Version and freshness rules

Completed attempts and evaluation records are not edited in place. A changed redacted input/target creates a new prediction context. A changed reference can create a new evaluation of the same frozen answer. A changed rubric creates a separate evaluation series. Summaries retain the exact included versions and cannot present superseded inputs as current.

A comparison must record its shared eligible set and missing outcomes. The display cannot infer accuracy from a color, confidence score, null coalescing default or provider completion state.

## Minimum permission contracts

Prediction: can read its allowed redacted derivative/target manifest, cannot read reference content or evaluation feedback. Evaluation: can read its authorized frozen answer and approved reference, cannot mutate the answer. UI: access controlled for each project and artifact. Coordinator: dispatches opaque IDs and whitelisted manifests, not a combined question-and-answer object. Raw payloads do not belong in public logs or this repository.

## Required contract evidence

Test missing/partial truth, invalid pairing, target boundary edits, different page numbering, duplicate task delivery, stale summary, refusal vs error, zero scored subset and cross-project access. Include tests proving reference-only fields cannot appear in prediction serialization. The detailed tests are not implemented by this setup.

## Changing a contract

Declare producer, all consumers, contract version, migration/compatibility, fixtures, impact and rollback before approval. Research reviews truth/scoring semantics; Backend and Frontend acknowledge serialization/display effects; QA reviews the exact candidate. A handoff identifies the decision epoch and contract version used. No silent renaming or fallback fields.

## Coordination contract (installed process)

A handoff contains task/role, baseline SHA, candidate SHA where available, decision epoch, input decisions, scope, artifacts, tests, unresolved issues, affected roles and requested next action. Review applies to the exact candidate SHA. An acknowledgment records what was read; it is not implementation approval. See [AGENT_HANDOFF.md](AGENT_HANDOFF.md).
