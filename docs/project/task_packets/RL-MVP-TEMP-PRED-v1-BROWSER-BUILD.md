# RL-MVP-TEMP-PRED-v1 Browser Build — scoped follow-up
**OWNER APPROVED PACKET PUBLICATION AND SUBSEQUENT BOUNDED IMPLEMENTATION; NOT MERGE/DEPLOY APPROVED. E0061.**

## Objective
Rebuild the existing pinned React/Vite frontend to include the reviewed temporary text-only experimental panel, then bind exactly the newly generated, integrity-verified assets to the existing local Packaging manifest. No new API or PDF runtime. Source candidate approved at a5017315c6cdb4b69b0503a32a2e49525530f4f9, QA PASS 3bbc81b1e0e5ad74bec622ee74fc86785436745a, Research scoped PASS c7bc59f84582860b4b4e17c9e2f45e730b2b9e55.

## Exact file scope
Modify ONLY:
- web/dist/index.html
- web/dist/assets/** (only replace/add generated immutable hashed build assets; removal of superseded tracked prior hashed assets within this path permitted)
- packaging/local/manifest.json
- web/tests/build.test.js
- tests/packaging/test_local_preflight.py
- tests/packaging/test_local_static.py
- one unique Frontend/Packaging scoped handoff in docs/project/handoffs.

No changes to web/src/**, package.json, package-lock.json, Vite/TypeScript config, API, worker, store, Task 4/6 evidence, launcher/static host code or canonical coordination files.

## Execution
Use the existing pinned lockfile and reviewed toolchain only, in isolated working tree, no new dependencies/versions, no lifecycle hooks. If dependencies are unavailable, stop and request separate installation authorization; this packet does not approve downloads/installs. Build using the already-approved deterministic npm scripts, reproduce identical hashes on consecutive builds, verify emitted regular assets/paths/count/size/SHA-256/MIME and inspect for secrets, sourcemaps, CDN links, remote runtime fetch. Update exact Packaging manifest inventory from actual verified bytes, not guessed hashes. Do not fake successful build or edit bundle manually.

## Tests and semantics
TDD and full focused/web and repository suites; genuine local headless Chrome synthetic render proving temporary panel is visible and usable, manual [REDACTED] text yields TEMPORARY_UNVALIDATED guesses, clear works, no PDF upload auto-fill, no API calls from baseline, normal PDF runtime remains unverified/503; UNKNOWN truth, NONE score and verified/experimental null. Tamper/symlink/Host/Origin/restart and static hash controls remain intact. Report actual tests and unrun manual screen-reader/clean-device checks.

## Review and boundaries
Publish implementation SHA, branch HEAD and unique scoped handoff. Require fresh independent QA/security and Research exact-SHA reviews; obtain separate owner merge approval. No deployment, Podman/VM, private data, real PDFs, external providers, model inference, paid calls, authoritative Task 4/6 writes or final Task 7D acceptance. If new files outside specified output or dependency changes needed, STOP.
