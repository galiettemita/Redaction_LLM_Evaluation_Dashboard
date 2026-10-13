# RL-MVP-007CP Frontend — dependency preflight BLOCKED

Task ID: RL-MVP-007CP.
Role / session label: Frontend / Team A.
UTC time: 2026-10-13T13:53:04Z.
State: BLOCKED.
Baseline integration SHA / decision epoch: `6d1b3176bf6b912e69b112b59e281549462ee6eb` / E0055.
Candidate branch / exact commit SHA: `codex/rl-mvp-007cp-frontend-build`; **no implementation commit or runnable bundle**. This branch contains this task-scoped evidence record only; its documentation revision is discoverable from Git history.
Source requirements / approved decisions / contract versions: R01–R12, DEC-001–022, E0055 bounded authorization, frozen API v0.1 unchanged.
Authorization reference and permitted file/action scope: [approved 007CP packet](../task_packets/RL-MVP-007CP-WEBSITE-BUILD.md), Frontend branch file list and one unique Frontend handoff. Stop condition: an unsafe specified package or changed upstream version requires Lead amendment before installation. No source files, package configuration, lock or dist were changed.

## Work performed and stop evidence

Resolved live GitHub default branch `main` and HEAD, fetched `origin/main`, inspected checkout/remote/status/worktrees, and created isolated `/private/tmp/rl-mvp-007cp-frontend-build` from baseline. Original checkout was at `f9599eb23bbf9239aaf27d646196ac1e550a5ee4`, with an unrelated untracked `.DS_Store`; it was not switched or reset. Read AGENTS.md, current state/decisions/handoff index, master specification, operating guide, frontend kickoff, interfaces, frozen API contract and complete approved 007CP packet from the baseline worktree.

Read-only registry metadata and security queries used installed Node `v24.21.0` and npm `11.19.0`. No package tarballs were downloaded, no dependency installation or lifecycle script was run, and no lock/bundle was generated. Registry integrity strings below are **published metadata**, not checksums verified against downloaded tarballs.

All six examined direct pins exist at their version endpoints and provide HTTPS registry tarball URLs and SHA-512 integrity metadata:

| Package | Version | License | Node engine | Relevant script / dependency metadata |
| --- | --- | --- | --- | --- |
| react | 19.2.0 | MIT | >=0.10.0 | No scripts or dependencies |
| react-dom | 19.2.0 | MIT | Not declared | `start: node server.js` only; scheduler ^0.27.0; peer react ^19.2.0 |
| typescript | 5.9.3 | Apache-2.0 | >=14.17 | Development/build/test scripts; no install/prepare/postinstall hooks or runtime dependencies |
| vite | 7.1.12 | MIT | ^20.19.0 or >=22.12.0 | Development/build scripts, no install/prepare/postinstall hooks; dependencies fdir ^6.5.0, rollup ^4.43.0, esbuild ^0.25.0, postcss ^8.5.6, picomatch ^4.0.3, tinyglobby ^0.2.15; optional fsevents ~2.3.3 |
| @types/react | 19.2.2 | MIT | Not declared | No scripts; csstype ^3.0.2 |
| @types/react-dom | 19.2.2 | MIT | Not declared | No scripts; peer @types/react ^19.2.0 |

The examined type versions satisfy the React 19.2 peer ranges. They are proposed exact build pins; compilation and full graph compatibility have not been established because the preflight stopped before installation.

Published integrity values:

```text
react@19.2.0 sha512-tmbWg6W31tQLeB5cdIBOicJDJRR2KzXsV7uSK9iNfLWQ5bIZfxuPEHp7M8wiHyHnn0DD1i7w3Zmin0FtkrwoCQ==
react-dom@19.2.0 sha512-UlbRu4cAiGaIewkPyiRGJk0imDN2T3JjieT6spoL2UeSf5od4n5LB/mQ4ejmxhCFT1tYe8IvaFulzynWovsEFQ==
typescript@5.9.3 sha512-jl1vZzPDinLr9eUt3J/t7V6FgNEw9QjvBPdysz9KfQDD41fQrC2Y4vKQdiaUpFT4bXlb1RHhLpp8wtm6M5TgSw==
vite@7.1.12 sha512-ZWyE8YXEXqJrrSLvYgrRP7p62OziLW7xI5HYGWFzOvupfAlrLvURSzv/FyGyy0eidogEM3ujU+kUG1zuHgb6Ug==
@types/react@19.2.2 sha512-6mDvHUFSjyT2B2yeNx2nUgMxh9LtOWvkhIU3uePn2I2oyNymUAX1NIsdgviM4CH+JSrp2D2hsMvJOkxY+0wNRA==
@types/react-dom@19.2.2 sha512-9KQPoO6mZCi7jcIStSnlOWn2nEF3mNmyr3rIAsGnAbQKYbRLyqmeSc39EVgtxXVia+LMT8j3knZLAZAh+xLmrw==
```

POST `https://registry.npmjs.org/-/npm/v1/security/advisories/bulk` with exact direct versions returned HTTP 200 and **five advisories for vite@7.1.12**; no advisories were returned for the other five direct pins. GitHub advisory metadata independently confirmed every affected range and first patched version:

| Advisory | Severity (npm) | Affected Vite 7 range | First patched Vite 7 |
| --- | --- | --- | --- |
| [GHSA-v6wh-96g9-6wx3](https://github.com/advisories/GHSA-v6wh-96g9-6wx3): NTLMv2 disclosure through UNC handling | moderate | >=7.0.0 <=7.3.4 | 7.3.5 |
| [GHSA-4w7w-66w2-5vf9](https://github.com/advisories/GHSA-4w7w-66w2-5vf9): optimized dependency map traversal | moderate | >=7.0.0 <=7.3.1 | 7.3.2 |
| [GHSA-v2wj-q39q-566r](https://github.com/advisories/GHSA-v2wj-q39q-566r): query-based server.fs.deny bypass | high | >=7.1.0 <=7.3.1 | 7.3.2 |
| [GHSA-p9ff-h696-f583](https://github.com/advisories/GHSA-p9ff-h696-f583): arbitrary file read through dev-server WebSocket | high | >=7.0.0 <=7.3.1 | 7.3.2 |
| [GHSA-fx2h-pf6j-xcff](https://github.com/advisories/GHSA-fx2h-pf6j-xcff): alternate Windows path deny bypass | high | >=7.0.0 <=7.3.4 | 7.3.5 |

These advisories involve development-server/platform surfaces; this packet intends production static serving. That does not waive its explicit unsafe-package stop condition. No vulnerable Vite executable was installed or started.

## Smallest exact amendment recommendation — proposed, not authorized

`vite@7.3.5` is the smallest higher Vite 7 version outside all five observed affected ranges. `https://registry.npmjs.org/vite/7.3.5` returned HTTP 200, MIT license, Node `^20.19.0 || >=22.12.0`, and:

```text
sha512-KuOaNhcnGFN2zIPGA7wRmzF+lJA1sea7rHq17aiJ++9lzY1WWG6Jpwqwe1KNbRVPIqHmr8GLYx7jbrQcN/7/ww==
https://registry.npmjs.org/vite/-/vite-7.3.5.tgz
```

Node 24.21.0 satisfies this unchanged engine requirement. Vite declares no React/TypeScript peer constraint; its @types/node peer is optional. Its ordinary dependency names remain the same, with esbuild changing from ^0.25.0 to ^0.27.0. Full transitive integrity/license/lifecycle/vulnerability preflight remains required. A metadata-only audit of `{"vite":["7.3.5","7.3.6"]}` returned HTTP 200 `{}`. This establishes no currently reported direct Vite advisory for these exact versions; it does not establish a safe full dependency tree.

Proposed exact amendment wording:

> In RL-MVP-007CP Frontend dependency pins, replace only `vite 7.1.12` with exact `vite 7.3.5`, the first Vite 7 release patched for all five advisories recorded in this handoff. Retain `react 19.2.0`, `react-dom 19.2.0`, `typescript 5.9.3` and exact compatible type pins established by preflight. This permits only Vite's required transitive graph after fresh registry existence, integrity, license, engine, lifecycle and vulnerability preflight. No new direct packages/plugins or executed install hooks. Existing allowed files, zero-cost limit, `npm ci --ignore-scripts`, deterministic production build, source-map/secrets/network audit, tests, independent reviews and separate merge/deployment gates remain unchanged.

## Reproducible read-only commands and actual results

Startup commands: `gh api repos/galiettemita/Redaction_LLM_Evaluation_Dashboard --jq .default_branch` -> `main`; `gh api repos/galiettemita/Redaction_LLM_Evaluation_Dashboard/commits/main --jq .sha` -> baseline; `git fetch origin main` -> success. `git worktree add -b codex/rl-mvp-007cp-frontend-build /private/tmp/rl-mvp-007cp-frontend-build origin/main` -> success at baseline.

The effective metadata/advisory queries ran via `node --input-type=module` with Fetch; equivalent executable command:

```sh
node --input-type=module <<'JS'
const pins = {react:'19.2.0','react-dom':'19.2.0',typescript:'5.9.3',vite:'7.1.12','@types/react':'19.2.2','@types/react-dom':'19.2.2'};
for (const [name, version] of Object.entries(pins)) {
  const r = await fetch(`https://registry.npmjs.org/${encodeURIComponent(name)}/${version}`);
  const p = await r.json();
  console.log(r.status, JSON.stringify({name,version:p.version,license:p.license,engines:p.engines,dist:p.dist,scripts:p.scripts,dependencies:p.dependencies,optionalDependencies:p.optionalDependencies,peerDependencies:p.peerDependencies}));
}
const r = await fetch('https://registry.npmjs.org/-/npm/v1/security/advisories/bulk', {
  method:'POST', headers:{'Content-Type':'application/json'},
  body:JSON.stringify(Object.fromEntries(Object.entries(pins).map(([n,v])=>[n,[v]])))
});
console.log(r.status, JSON.stringify(await r.json()));
JS
```

Independent advisory metadata: GET `https://api.github.com/advisories/<GHSA-ID>` for each of the five IDs above, using `Accept: application/vnd.github+json`; all HTTP 200. Fields inspected: `vulnerabilities`, `first_patched_version`, `severity`, `published_at`, `updated_at`, `references`. Candidate registry GETs for Vite 7.3.5/7.3.6 were HTTP 200; candidate bulk POST was HTTP 200 `{}`.

Tests actually run / command / result / environment: `node --test web/tests/contract.test.js` -> **19 passed, 0 failed**, Node 24.21.0, original unchanged baseline source. `git status --short` and `git diff --name-only origin/main` were empty before this handoff was added.
Tests not run and reason: TDD build tests, full pytest, compileall, npm ci, full transitive audit, typecheck, production build, deterministic rebuild comparison, bundle audit, browser smoke and clean-recipient acceptance **NOT RUN**. Mandatory direct-dependency stop occurred before implementation/install. No new implementation exists to validate. System pytest is 9.0.2 under Python 3.10, below the repository's >=3.11 requirement; no Python tool installation was attempted.
Independent review evidence: Not yet reviewed; BLOCKED preflight record only, no build candidate for QA/Research.
Research / data approval evidence: No scientific D03–D06/data authorization; not needed for read-only public-package metadata and unchanged synthetic contract tests. No private documents, runtime, inference or paid service calls.
Known issues / risks / stale dependencies: Approved Vite 7.1.12 is vulnerable by current public advisory metadata. Full transitive dependency safety and production compilation remain unestablished. Packaging cannot pin a genuine final dist allowlist until Frontend is unblocked and produces the deterministic bundle.
Affected roles / requested next action: Lead/owner review narrow Vite amendment; Packaging may continue static-host work but must not claim website-ready or invent a bundle manifest. Frontend resumes only after the amendment is approved and published, then repeats preflight for the complete exact graph.
Last freshness check and relevant differences: Live GitHub main rechecked 2026-10-13T13:53:04Z, still baseline `6d1b3176bf6b912e69b112b59e281549462ee6eb`; no governing changes observed.
Rollback or correction approach: Evidence-only branch; no product files or dependencies changed. Correct the approved pin via Lead packet amendment and continue on isolated branch; do not force-push or overwrite canonical records.
Publication: PUBLISHED on `codex/rl-mvp-007cp-frontend-build` after normal push; documentation SHA is discoverable in branch history.

ACK E0055 | Frontend | 6d1b3176bf6b912e69b112b59e281549462ee6eb | 2026-10-13T13:53:04Z | RL-MVP-007CP | Bounded build authorized only after safe dependency preflight; unsafe approved pin requires amendment.

## Task acceptance checklist

- [x] Live baseline, coordination snapshot and isolated frontend branch established.
- [x] Direct registry metadata, license/engine/lifecycle metadata and current advisory evidence inspected before install.
- [x] Mandatory unsafe-pin stop observed; smallest patched exact candidate identified without installation.
- [x] Existing frontend contract regression: 19 passed.
- [x] One unique task-scoped BLOCKED evidence handoff published.
- [ ] Owner-approved safe Vite amendment recorded.
- [ ] Complete transitive preflight and integrity-hashed exact lock.
- [ ] TDD build contract, typecheck, deterministic production bundle and output audit.
- [ ] Full regressions and approved synthetic browser checks.
- [ ] Exact bundle allowlist delivered to Packaging.
- [ ] Independent exact-candidate QA/security and Research review.
- [ ] Separate owner merge approval and recipient acceptance.
