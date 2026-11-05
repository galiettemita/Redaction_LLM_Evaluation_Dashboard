# RL-UX-016 — Experimental document workspace

Baseline integration SHA: `cb0fa4f1242ae8bf12afb084bc9475017040b784` (live GitHub main, 2026-11-05 UTC). Epoch: E0072.
Accountable owner: Codex Engineering Lead; delegated implementers report exact candidates to Lead. State: IMPLEMENTED / READY_FOR_REVIEW; independent exact-candidate review and combined runtime browser acceptance remain open. Not scientifically VERIFIED, MERGED or DEPLOYED.
Authority: owner clarification dated 2026-11-05, DEC-023 and [RL-OPS-002](RL-OPS-002-AUTONOMOUS-ENGINEERING.md). Read the [design](../../superpowers/specs/2026-11-05-experimental-product-completion-design.md), [implementation plan](../../superpowers/plans/2026-11-05-experimental-product-completion.md), [API v0.3](../API_CONTRACT_V0_3.md) and live integration HEAD before work.

## Objective and dependencies

Implement plan Task 5 after the API v0.3 contract is published, consuming RL-EXP-015's persisted evidence without calculating a separate frontend score. Deliver a document-centered accessible React workspace for required redacted/optional reference upload, local PDF viewing/toggle, target/model selection, genuine predictions, experimental agreement and durable recovery. Production build/manifest binding is permitted; enabling the controlled link belongs to RL-LINK-017.

## Exact file/action scope

- `web/src/api.ts`
- `web/src/App.tsx`
- `web/src/styles.css`
- primary-flow imports/use of `web/src/temporaryPrediction.ts` (remove from primary experience; retain historical module only if compatibility tests require it)
- `web/tests/contract.test.js`
- `web/tests/build.test.js`
- `web/tests/workspace.test.js` (new)
- `web/package.json`
- `web/package-lock.json` only if an already-approved test dependency is indispensable; no casual package upgrade
- generated `web/dist/` assets and `packaging/local/manifest.json` to bind their exact inventory
- `tests/packaging/test_local_static.py` only for necessary asset/contract acceptance updates
- this checklist, design/plan checklists and unique RL-UX-016 handoff(s)

Lead-approved Task 5 scope amendment (2026-11-05, RL-OPS-002): `src/redaction_lab/api/static.py` may add only `frame-src blob:` to the CSP so the browser can embed a currently selected local PDF. Keep `default-src` and `object-src` at none and every other boundary unchanged; assert the exact policy in `tests/packaging/test_local_static.py`.

Lead-approved test-only amendment: `tests/packaging/test_local_preflight.py` may update the expected frontend inventory and replace temporary v0.3 rejection/demo assertions with positive v0.3 browser acceptance. No other preflight semantics change.

Frontend manifest writes and Task 6 launch/manifest writes must be sequential with fresh reads. Use isolated writing scope; never reset another agent's checkout. Rebuild from pinned dependencies, verify integrity/lifecycle/license prerequisites before any free install, audit and preserve deterministic packaging. No new model/provider/runtime or scientific method is introduced.

## Acceptance checklist (plan Task 5)

- [x] RED: strict v0.3 contract tests reject numeric verified scores, missing experimental method/scale/provenance, inconsistent IDs/counts, unsafe payloads and incompatible grouped summaries; permit multiple attempt rows sharing a target with distinct model/configuration identity.
- [x] RED: workspace tests cover file-object URL lifecycle/revocation, PDF release toggle, keyboard target selection, technical states, persistent action errors, read-only reconnect, experimental labels and counts.
- [x] GREEN: document workspace includes upload/saved-document recovery, large local PDF viewer, target/page selection and per-model predictions; reference toggle preserves target selection and uses browser object URLs for selected files.
- [x] Restore limitation is explicit: persisted results recover after refresh, but local PDF preview requires selecting the file again. No claim that document bytes were recovered from the server.
- [x] Target/document/model experimental cards display `EXPERIMENTAL — NOT SCIENTIFICALLY VALIDATED`, method/scale, subscores, critical-detail warnings, eligible/scored/unknown/excluded/technical counts and denominators. Empty/unknown remains null/Accuracy unknown.
- [x] Refusal, timeout, malformed output, provider error, unknown truth and processing error have distinct friendly copy; action errors survive status refresh. Technical failure is not a factual error.
- [x] Rule-based temporary candidate generation is absent from the primary product. Only genuine installed Qwen is advertised; one-model limitation and unvalidated lexical agreement are clear.
- [x] Same-origin client uses only its current loopback or controlled HTTPS origin with relative requests; no arbitrary backend override, credentials in assets, redirects or direct Ollama access.
- [x] Node suite, TypeScript typecheck, accessibility interactions, production build and audit pass. Packaging/static checks confirm exact asset manifest binding.
- [ ] Browser acceptance covers upload, view toggle, process, progress/results, selection, labels, errors and refresh/reconnect without duplicate attempt creation.
- [ ] Commit `feat: ship experimental document evaluation workspace`; exact-candidate independent review and unique handoff published.

Implementation evidence: `9da3065819b6086425f4d14a48ba8f095160efc2`; Node 48 passed, typecheck/build/repeat asset hashes passed, npm audit zero vulnerabilities, packaging 100 passed including real Chrome startup, full Python 865 passed. Keyboard/click handlers, release/error transitions, React rendering and actual blob URL revocation are tested. Full genuine upload/process/reconnect browser acceptance remains the combined Task 6 gate; exact-candidate independent review is pending.

## Common gates, review and rollback

Preserve R01–R12 and DEC-001–DEC-023 within DEC-023's explicit experimental-only supersession. `verified_score` remains null; verified `truth_status` remains UNKNOWN. Missing/partial/unreadable/ambiguous/mismatched/unprocessed truth remains Accuracy unknown/null, never zero. Reference data never enters prediction inputs; immutable versions and one-shot recovery remain mandatory. This record authorizes no paid resources, private/restricted research data, credentials in Git, destructive external action, scientific validation or public unauthenticated release. Only generated synthetic fixtures or separately documented authorized public data may be used; the shared demonstration workspace stores synthetic documents only.

Behavior changes require red-green-refactor evidence, focused/full permitted regressions, exact-candidate independent automated QA/security and experimental-semantics review, correction and re-review before normal non-force integration. Self-review is not independent review. No automated reviewer grants D03–D06, institutional permission or scientific/release validation. Stop only affected work for unsafe reference leakage, unexplained score/version changes, scope/contract conflicts, unqualified runtime, essential missing credentials, paid-resource need, private-data need, destructive action or unresolved Critical security risk; continue independent safe work. Record any necessary bounded scope amendment before writes.

Rollback: stop affected services if necessary, revert additive task commits normally, retain original immutable attempts/evaluations and restore a verified pre-migration backup only through the documented safe migration recovery path. Do not overwrite later evidence or roll old validators forward silently. Publish a unique task handoff under `docs/project/handoffs/` using every field in [AGENT_HANDOFF](../AGENT_HANDOFF.md#handoff-template-all-fields-required-explicit-not-applicable-is-valid), with exact artifacts/commits, tests run/unrun, decisions, blockers, affected consumers and next action. Live integration HEAD must be rechecked before consequential writes, runtime calls and final review.
