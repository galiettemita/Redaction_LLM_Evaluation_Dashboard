# RL-WEB-008 — API v0.2 frontend build and manifest binding

State: ACTIVE under RL-OPS-002  
Owner: Codex Frontend/Packaging  
Baseline: `a06ae33e794c956492ea0ad001c5c90f0ad6576d` / E0071

## Objective

Build the already-reviewed React/TypeScript API v0.2 source with the unchanged pinned lockfile, replace the historical v0.1 dist, bind exact output hashes to the local manifest, and establish synthetic same-origin browser/package evidence.

## Permitted paths

- `web/dist/index.html`
- `web/dist/assets/**` generated production assets only
- `web/package.json`
- `web/package-lock.json`
- `web/tests/build.test.js`
- `packaging/local/manifest.json`
- `packaging/local/README.md`
- `tests/packaging/test_local_preflight.py`
- `tests/packaging/test_local_static.py`
- this packet and one unique Frontend/Packaging handoff

No source, API, schema, model/PDF runtime or scientific-method change. No dependency/lock change is allowed except the exact security amendment below. `web/node_modules` is untracked build state and must not be committed.

### Security amendment — exact Vite patch

Current registry audit on 2026-10-29 reports a high-severity advisory affecting the existing direct `vite@7.3.5` pin and identifies `7.3.7` as the non-major fix. This task therefore permits only `vite 7.3.5 -> 7.3.7` in `web/package.json` and a package-tool-regenerated `web/package-lock.json`. Registry evidence: MIT license, Node engine `^20.19.0 || >=22.12.0`, SHA-512 integrity, HTTPS npm tarball and unchanged dependency families; Node 24.21.0 is compatible. Keep every other direct pin and the `esbuild@0.27.2` override unchanged. Re-run complete audit and abort if high/critical findings remain.

## Dependency and build gates

Before installation, verify the exact lock graph uses npm registry HTTPS URLs, SHA-512 integrity, approved direct pins/override, compatible engines, acceptable licenses, no lifecycle scripts, and no unresolved security advisory requiring a version change. Then one zero-cost `npm ci --ignore-scripts --no-audit --no-fund` is permitted. Abort on any changed/missing/unsafe dependency.

Run typecheck, Node contracts, two consecutive production builds with identical hashes, bundle secret/source-map/remote-runtime checks, manifest/static/preflight tests, full Python/Node regressions, compile and scope audits. Use only synthetic data. Independent automated QA/security review must examine the exact candidate before integration.

## Stop conditions

Stop affected work for a required dependency/lock/source change, unsafe package, paid resource, private data, real PDF/model/inference operation, critical security issue or out-of-scope path. No public deployment, scientific claim or clean-recipient claim.
