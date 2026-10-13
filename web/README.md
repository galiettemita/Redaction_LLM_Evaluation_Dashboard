# Redaction Lab local frontend — RL-MVP-007CP

This directory contains the React/TypeScript source and the built local production bundle. It uses exact dependency pins, an integrity-pinned npm lock and no CDN. The generated `dist/` assets are intended to be served by Redaction Lab's same-origin, loopback-only local launcher; opening source `index.html` directly is not supported.

## Reproducible build

Prerequisite: Node 24 and npm 11 on macOS Apple Silicon. From this directory:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run typecheck
npm run build
npm test
```

Do not remove `--ignore-scripts`: the approved build does not authorize dependency lifecycle hooks. The direct dependencies are React and React DOM 19.2.0; development dependencies are TypeScript 5.9.3, Vite 7.3.5 and React type packages 19.2.2. The approved npm override holds esbuild at 0.27.2. `package-lock.json` pins the complete graph with SHA-512 integrity metadata.

The production build emits hashed JavaScript and CSS under `dist/assets/`, with no source maps, remote runtime imports, CDN references, credentials or telemetry. Rebuilding the same source and lock in the verified environment produced byte-identical output. The committed bundle is still subject to fresh independent QA/security and Research review.

## What is implemented

- Accessible labeled redacted PDF upload and optional reference upload, client size/type checks, and API v0.1 multipart submission.
- Same-origin requests restricted to the browser's `127.0.0.1` HTTP(S) origin; redirects fail rather than forwarding files. No analytics, CDN, external service, prediction endpoint or model call.
- Document/job status, recovery with saved document/job IDs, manually refreshed stored status, and three result levels preserving null/unknown accuracy. Reconnect only reads; writes are never automatically retried. No automatic processing.
- A versioned localStorage recovery handle containing only two opaque IDs. File contents, names, reference text and payloads are not stored there. If storage is unavailable, copy the displayed IDs. Restore them with “Restore an existing document.” Recovery refers to the same installation/origin; it is not a portable document export.
- Explicit unqualified-runtime state and disabled processing. Health v0.1 reports `runtime_qualified:false`; a future qualified runtime/schema requires an approved contract change.
- Responsive layout, semantic regions, skip link, associated labels/help, visible keyboard focus, minimum 44px controls, live status and alert feedback, native disclosure controls, and text labels independent of color. Accessibility is source-reviewed only, not browser-verified.

The frozen API returns an empty target list and null target/document/model summaries even when document processing is `AVAILABLE`. This UI therefore shows no fabricated passages, answers, model rankings or scores. Numeric or nonempty future result payloads fail closed as incompatible with this version. File type/size checks aid the user; server validation remains authoritative. Accepted upload and completed processing are distinct states. A reference upload never implies trustworthy truth. The interface does not expose raw server/transport error strings.

Safe native PDF preview is not qualified in this release, so there is no PDF embedding, browser parsing, download endpoint or external preview service. The document workspace says preview is unavailable. Multipage viewing, passage selection and release comparison await a separately approved safe viewer and result contract; they are not claimed implemented.

## Contract and build tests

After the integrity-pinned installation above:

```sh
cd web
npm test
```

Or from the repository root: `node --test web/tests/contract.test.js web/tests/build.test.js`. The tests execute the real `src/api.ts` against complete synthetic API responses and a controlled transport. They also verify exact package configuration, the approved esbuild override, lock integrity metadata, hashed local output, size limits, source-map absence, secret patterns and external URL restrictions. They require no live PDF processing, private PDFs, model, VM or inference runtime.

Serve this compiled app and `/api/v1` from the same `127.0.0.1` origin; do not use an unrelated development-server port or CORS proxy. The build and synthetic browser smoke do not establish screen-reader conformance, clean-recipient installation, qualified PDF processing or final Task 7D acceptance.

## Task acceptance checklist

- [x] Eight authorized source/document/test files only; isolated frontend branch.
- [x] Frozen API v0.1 consumed without route/schema/dependency additions.
- [x] Contract tests written RED before adapter implementation, then GREEN.
- [x] Null scores, unknown truth, unqualified runtime and empty result payloads represented honestly.
- [x] Recovery and refresh never start new work; no automatic POST retry.
- [x] Source layout and accessibility affordances included.
- [x] Exact dependency graph, lock integrity, vulnerability, license, engine and lifecycle preflight.
- [x] Runnable production bundle and strict TSX typecheck.
- [x] Deterministic rebuild and local-bundle security checks.
- [ ] Manual screen-reader testing and clean-recipient installation.
- [ ] Independent exact-candidate QA/security and Research reviews.
- [ ] Owner integration approval, deployment and recipient acceptance.

Implementation and test evidence are recorded in the task's unique frontend handoff. Scientific D03–D06, data approval, PDF runtime qualification, inference, spending, merge and deployment are outside this packet.
