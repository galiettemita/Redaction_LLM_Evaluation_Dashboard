# Redaction Lab frontend source — RL-MVP-007C

This is a **source-only React/TypeScript interface**, not a runnable frontend build or an installed application. The E0052 packet prohibits dependency downloads/installs and adding external dependencies. `package.json` deliberately declares no runtime or build packages, no build script, and no CDN. Opening `index.html` cannot execute TSX or resolve React. A separately authorized packaging/build step must supply approved pinned local React, React DOM, TypeScript and bundler dependencies and a reproducible build/lockfile before recipient acceptance. Do not run `npm install` or fetch packages for this packet.

## What is implemented

- Accessible labeled redacted PDF upload and optional reference upload, client size/type checks, and API v0.1 multipart submission.
- Same-origin requests restricted to the browser's `127.0.0.1` HTTP(S) origin; redirects fail rather than forwarding files. No analytics, CDN, external service, prediction endpoint or model call.
- Document/job status, recovery with saved document/job IDs, manually refreshed stored status, and three result levels preserving null/unknown accuracy. Reconnect only reads; writes are never automatically retried. No automatic processing.
- A versioned localStorage recovery handle containing only two opaque IDs. File contents, names, reference text and payloads are not stored there. If storage is unavailable, copy the displayed IDs. Restore them with “Restore an existing document.” Recovery refers to the same installation/origin; it is not a portable document export.
- Explicit unqualified-runtime state and disabled processing. Health v0.1 always reports `runtime_qualified:false`; a future qualified runtime/schema requires an approved contract change.
- Responsive layout, semantic regions, skip link, associated labels/help, visible keyboard focus, minimum 44px controls, live status and alert feedback, native disclosure controls, and text labels independent of color. Accessibility is source-reviewed only, not browser-verified.

The frozen API returns an empty target list and null target/document/model summaries even when document processing is `AVAILABLE`. This UI therefore shows no fabricated passages, answers, model rankings or scores. Numeric or nonempty future result payloads fail closed as incompatible with this version. File type/size checks aid the user; server validation remains authoritative. Accepted upload and completed processing are distinct states. A reference upload never implies trustworthy truth. The interface does not expose raw server/transport error strings.

Safe native PDF preview is not qualified in this source-only release, so there is no PDF embedding, browser parsing, download endpoint or external preview service. The document workspace says preview is unavailable. Multipage viewing, passage selection and release comparison await a separately approved safe viewer and result contract; they are not claimed implemented.

## Tests available without installing anything

With an already installed Node **24 or later** (built-in TypeScript stripping, Fetch/FormData/File):

```sh
cd web
npm test
```

Or from the repository root: `node --test web/tests/contract.test.js`. The tests execute the real `src/api.ts` against complete synthetic API responses and a controlled transport. They cover route/method/multipart shape, optional reference isolation, rejected origins/redirect policy, invalid file/size guards, same-origin status recovery, identity mismatch, runtime 503 and acceptance semantics, no write retries, safe errors, malformed contract/version rejection, all result states/nulls, forbidden scores/truth/targets and recovery ID validation. They require no React install, live HTTP service, private PDFs, model, VM or runtime operations.

Tests do not establish a frontend build, browser rendering, keyboard/screen-reader behavior or end-to-end installation. Those checks remain NOT RUN until the build prerequisite is explicitly authorized and available. `src/main.tsx` is a future bundler entry; source imports use the normal React/TypeScript module resolution pattern. Serve the eventual compiled app and `/api/v1` from the same `127.0.0.1` origin; do not use an unrelated dev-server port or CORS proxy.

## Task acceptance checklist

- [x] Eight authorized source/document/test files only; isolated frontend branch.
- [x] Frozen API v0.1 consumed without route/schema/dependency additions.
- [x] Contract tests written RED before adapter implementation, then GREEN.
- [x] Null scores, unknown truth, unqualified runtime and empty result payloads represented honestly.
- [x] Recovery and refresh never start new work; no automatic POST retry.
- [x] Source layout and accessibility affordances included.
- [ ] Runnable frontend bundle / TSX typecheck (approved dependencies absent).
- [ ] Browser visual, interaction and accessibility testing (no runnable build).
- [ ] Independent exact-candidate QA/security and Research reviews.
- [ ] Owner integration approval, deployment and recipient acceptance.

Implementation and test evidence are recorded in the task's unique frontend handoff. Scientific D03–D06, data approval, PDF runtime qualification, inference, spending, merge and deployment are outside this packet.
