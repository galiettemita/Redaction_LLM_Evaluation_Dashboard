# RL-MVP-007CP Frontend — E0056 transitive dependency preflight BLOCKED

Task ID: RL-MVP-007CP.
Role / session label: Frontend / Team A, E0056 continuation.
UTC time: 2026-10-13T14:59:11Z.
State: BLOCKED before package installation.
Baseline integration SHA / decision epoch: `126772897893218de38cc0e93e196b8e07317d58` / E0056.
Candidate branch: `codex/rl-mvp-007cp-frontend-build`. There is no implementation SHA or runnable bundle.
Authorization: `docs/project/task_packets/RL-MVP-007CP-WEBSITE-BUILD.md`, including the approved direct `vite@7.3.5` amendment. API v0.1 is unchanged.

## Blocking result

The amended direct pins and type pins exist and are mutually compatible: `react@19.2.0`, `react-dom@19.2.0`, `typescript@5.9.3`, `vite@7.3.5`, `@types/react@19.2.2` and `@types/react-dom@19.2.2`. Node `24.21.0` satisfies their declared engines.

A metadata-only `package-lock.json` resolution, generated with `npm install --package-lock-only --ignore-scripts --no-audit --no-fund`, contained 71 exact packages. Every locked package/version endpoint existed; every registry tarball URL and SHA-512 integrity value matched the lock metadata; there were no deprecated packages. Declared licenses were only MIT, ISC, BSD-3-Clause and Apache-2.0. All declared Node engines were compatible with Node 24.21.0. The lifecycle review found `esbuild@0.27.7` postinstall, optional `fsevents@2.3.3` install, and a Rollup source-package prepare script. None ran.

The complete exact-version registry advisory query and `npm audit --package-lock-only --ignore-scripts --audit-level=low --omit=optional` both found one vulnerability:

- `esbuild@0.27.7`, pulled by Vite's `esbuild: ^0.27.0`, is affected by [GHSA-g7r4-m6w7-qqqr](https://github.com/advisories/GHSA-g7r4-m6w7-qqqr), low severity, affected range `>=0.27.3 <0.28.1`. The advisory concerns arbitrary file reading through the esbuild development server on Windows.

The approved build is macOS-only, uses Vite's production build rather than the esbuild development server, and would use `npm ci --ignore-scripts`. Those exposure reductions do not override the packet's explicit requirement to stop for an unsafe transitive package. No package tarball was installed, no lifecycle script ran, no build executable ran and no `node_modules` directory was created.

The unapproved lock, TDD build test and provisional configuration were removed after recording the preflight. The branch contains no product/configuration/dist change from the E0056 baseline.

## Smallest required amendment

Authorize an exact npm `overrides` entry pinning transitive `esbuild` to `0.27.2`, then regenerate rather than hand-edit the lock and repeat the complete graph preflight. Registry metadata confirms `esbuild@0.27.2` exists, is MIT licensed, requires Node `>=18`, has SHA-512 integrity metadata, satisfies Vite's published `^0.27.0` range and is outside the current advisory range. This is only an amendment recommendation, not authorization or proof of the regenerated graph. The existing Frontend path scope is sufficient; no new direct dependency or file is proposed.

## Commands and evidence

- `git fetch origin main`; live `origin/main` remained `126772897893218de38cc0e93e196b8e07317d58`.
- Metadata-only lock resolution: `npm install --package-lock-only --ignore-scripts --no-audit --no-fund` -> exit 0; `node_modules` absent.
- Custom Node registry audit of all 71 exact locked packages -> existence/integrity/tarball/license/engine/lifecycle metadata verified; registry bulk advisory response contained only the esbuild advisory above.
- `npm audit --package-lock-only --ignore-scripts --audit-level=low --omit=optional` -> exit 1, one low-severity vulnerability in esbuild.
- Independent same-session read-only dependency reviewer reproduced the same exact blocker and remediation boundary. This is supporting review only, not independent project approval.
- `node --test web/tests/contract.test.js` -> 19 passed, 0 failed.
- First full pytest invocation without `PYTHONPATH=src` -> collection stopped with 11 import errors because the reused virtual environment's editable package pointed at another worktree. Corrected command: `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -m pytest -p no:cacheprovider` -> 517 passed, 0 failed in 19.22 seconds.
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/rl-mvp-007cp-frontend-pyc ... -m compileall -q src tests` -> compilation completed before the chained environment check failed because that isolated virtual environment has no `pip` module.
- Replacement dependency check: `uv pip check --python /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python` -> 21 packages checked, all compatible.
- `git diff --check` -> clean before this handoff; `web/node_modules` absent.

## Tests not run and limitations

`npm ci`, typecheck, production build, deterministic rebuild, bundle integrity/secrets/CDN/source-map audit, browser smoke, synthetic website workflow and clean-recipient acceptance were NOT RUN because the mandatory transitive vulnerability stop occurred first. There is no genuine `web/dist`, runnable frontend or implementation candidate. No private data, PDF processing, model inference, Podman/VM operation, paid call, deployment or merge occurred. This does not establish Task 7D acceptance, scientific approval or independent QA/Research verification.

Next receiver: Lead/owner for the narrow exact `esbuild@0.27.2` override amendment. After an approved published amendment, Frontend should regenerate the lock, repeat all dependency checks, install only with `npm ci --ignore-scripts`, and resume TDD/build verification on this branch.

Rollback: handoff-only commit; no product rollback is necessary.

ACK E0056 | Frontend | 126772897893218de38cc0e93e196b8e07317d58 | RL-MVP-007CP | BLOCKED by esbuild@0.27.7 GHSA-g7r4-m6w7-qqqr before installation.
