# RL-MVP-TEMP-PRED-v1 — temporary text-only experimental guesses
**OWNER APPROVED BOUNDED CODE/SYNTHETIC TEST IMPLEMENTATION ONLY; NOT MERGE OR DEPLOY APPROVED.** E0060; baseline main f2729a62ce3e942e0ebd4bc710ed6cd149048d3f / E0059.

Objective: allow manually entered or synthetic short text containing one or more literal [REDACTED] markers to yield deliberately simple deterministic candidate completions in a separate local demo panel. No claim of truth, reconstruction accuracy, PDF analysis or real AI-model inference. Existing PDF upload/status pipeline and its runtime-unverified warning remain untouched. Feature is temporary, clearly UNVALIDATED, trivially removable, and does not create persistent authoritative research evidence.

## Exact authorized implementation paths
NEW ONLY:
- src/redaction_lab/temporary_prediction.py
- tests/test_temporary_prediction.py
- web/src/temporaryPrediction.ts
- web/tests/temporaryPrediction.test.js
MODIFY ONLY:
- web/src/App.tsx
- web/src/styles.css
ONE unique Backend/Frontend role-specific task handoff on a unique task branch.
No API routes, existing prediction/evaluator/store/manifest/launcher modifications; no dependencies, schema, package, lockfiles, build changes or additional files. Existing built dist is deliberately unchanged; this feature is source-only until a separately approved frontend build/asset-assembly packet. Do not silently label as browser-available.

## Behavior and strict non-authority
Standalone pure stdlib Python baseline accepts only manually supplied text strings, at most 4,000 UTF-8 bytes, max 8 literal [REDACTED] markers; rejects absent markers, markup/script-like payloads for display only using React ordinary escaped text nodes, no external requests. Generate at most three deterministic candidate phrases per marker using simple nearby-word/canned contextual heuristics with transparent static fallback; no PDF input, OCR, model calls or truth access. Never say exact hidden text was recovered. Response status always TEMPORARY_UNVALIDATED, score_status NONE, verified_score null, experimental_score null. No authoritative Task-4 attempts/sources, no Task-6 evaluations, no database or logs of snippets. Use explicit sample/demo badge and a warning that plausible guesses are not proven correct.

Temporary frontend panel is separately marked Experimental text-only demo, optional manual input (never auto-fill from uploaded PDF), output escapes text and no HTML injection, with clear/remove button; implementation may use pure TypeScript local deterministic equivalent with matching fixtures, no network/API. The Python helper is isolated sample baseline for test consistency, not a production worker or server. Document code-removal via isolated files and small App/CSS edits in handoff. The existing web/dist and API remain unchanged.

## TDD, review and acceptance
Red/green tests cover bounds, exact marker semantics, determinism, empty/overlong hostile strings, no fabricated scores, no persistence or file/network access, safe rendering, unknown truth, reference isolation, no accidental POST/retry and no impact to runtime 503. Run focused Node/Python, complete repository pytest, compilation and authorized-scope checks. If existing unmodified TSX requires building to make the panel visible in browser, STOP and request a separate narrow build/manifest amendment; do not edit dist/package/manifest under this packet. Independent QA/security and Research exact-SHA review required before separate owner merge permission. No scientific approval conferred.

No Podman/VM, private research data, real PDF processing, external providers, paid calls, inference-model downloads, deployment or bypass of unverified runtime. No persistent authoritative prediction or numeric scoring.
