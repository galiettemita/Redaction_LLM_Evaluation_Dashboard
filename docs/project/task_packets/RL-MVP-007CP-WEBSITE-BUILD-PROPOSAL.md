# RL-MVP-007CP — runnable local website build and same-origin serving
**STATUS: PROPOSED FOR OWNER REVIEW ONLY — NOT APPROVED FOR IMPLEMENTATION, INSTALLATION, DOWNLOAD, BUILD OR MERGE.** Epoch E0054.

## Objective
Turn the independently reviewed Task-7C React/TSX source and Task-7P local API diagnostic launcher into a reproducibly built, securely same-origin served macOS Apple Silicon local website. Deadline pressure does not override approval gates. Frozen API v0.1 and Task 4/6 truth/null scoring remain unchanged.

## Proposed bounded workstreams (approval required)
Frontend: source/manifest changes only in web/package.json and web/README.md; proposed new web/tsconfig.json, web/vite.config.ts, web/package-lock.json, web/dist/** generated deterministic build outputs (whether build assets are tracked to be decided), scoped frontend build/security tests and one new unique handoff. Pin exact React, React DOM, TypeScript and Vite versions and transitive lock integrity; audit dependency licenses and build output for external networking, credentials or embedded secrets before approval. Build must not require CDN or remote runtime assets.
Packaging: changes only packaging/local/launch.sh, preflight.sh, manifest.json, README.md; proposed new same-origin static-serving module/path and narrowly scoped tests (exact location to be approved), and one unique handoff. Serve only immutable built assets under literal 127.0.0.1 and same port as /api/v1; reject traversal, dotfiles, symlinks, unknown MIME or unsafe extension, oversized/static route ambiguity, SPA fallback outside expected page; no public bind. Preserve strict HTTP framing, Origin/Host, API security controls, no telemetry and degraded/unverified runtime behavior. Avoid injecting uploaded PDF bytes into asset paths.
Acceptance: separate QA/browser/manual accessibility and clean independent recipient-machine verification is NOT approved by this proposal. Only permitted existing synthetic checks can continue under E0052 7D-prep.

## Decisions owner must approve before implementation
1. Precise package versions/lockfile and whether networked package download/install is authorized, with explicit cost cap zero and acceptable license/security audit.
2. Exact static server source path, generated artifact ownership, allowed changed files and whether compiled dist is committed or independently reproducibly built.
3. Whether build/testing permitted on existing local machine and how offline recipient prerequisites are obtained; do not claim a standalone installer or clean-device success without evidence.
4. Separate branch owners, parallel work, exact-SHA independent QA/security and Research reviews; distinct owner merge authorization.

## Stop conditions
No unapproved dependency, no new schema/API contract, no new Task 3/4/6 authority, no Podman/VM/images, private data, real models/inference, paid calls, deployment or scientific acceptance. Missing prerequisites are explicit BLOCKED, never synthetic runtime success.
