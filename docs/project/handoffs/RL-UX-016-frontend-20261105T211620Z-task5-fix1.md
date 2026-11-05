# RL-UX-016 — Task 5 correction round 1

Task ID: RL-UX-016 / Task 5 correction round 1.
Role / session label: Frontend / task5_implementer.
UTC time: 20261105T211620Z.
State: READY_FOR_REVIEW; IMPLEMENTED, not independently VERIFIED, MERGED or DEPLOYED.
Baseline integration SHA / decision epoch: `cb0fa4f1242ae8bf12afb084bc9475017040b784`; integration E0071, completion branch E0072 / DEC-023.
Candidate branch / exact commit SHA: `codex/finish-app` / `1f964db00656fafb364a127dcec6b6ba5f4eed71`.
Source requirements / approved decisions / contract versions: R01–R12, DEC-001..023, API v0.3, RL-UX-016, prior Task 5 handoff `RL-UX-016-frontend-20261105T210652Z-task5.md` and Lead's two Important review findings. ACK E0072 | Frontend | baseline above | 20261105T211620Z | Task 5 correction | exact identity/count binding and mounted-interaction deferral understood.
Authorization reference and permitted file/action scope: Lead's explicit fix round 1/5 instruction within Task 5 source/test/build/manifest scope and prior packaging-test amendments; routine handoff/checklist/report writing included. No subagents or silent scope changes.
Work performed / artifacts and exact paths: detailed correction record below.
Tests actually run / command / result / environment: detailed correction record below; existing Node 24.21.0/npm 11.19.0 and required Python interpreter on macOS.
Tests not run and reason: mounted/full interactive browser workflow, genuine model/PDF processing, controlled HTTPS acceptance deferred to Task 6 by Lead; no runtime qualification or deployment in this correction.
Independent review evidence: two Important findings reproduced and self-reviewed corrections; exact-candidate independent re-review pending.
Research / data approval evidence: synthetic fixtures only; no D03–D06/institutional approval or paid/private-data use. Numeric scores still only originate from API; verified scores null.
Known issues / risks / stale dependencies: mounted-interaction Minor and full qualified runtime acceptance remain Task 6. Unbound opaque summary membership fails closed instead of guessing pending/terminal status. Dependencies remain locally untracked for reviewers.
Affected roles / requested next action: Lead requests exact-candidate re-review of `1f964db00656fafb364a127dcec6b6ba5f4eed71` and coordinates remote publication/integration; Task 6 owns deferred combined acceptance.
Last freshness check and relevant differences: live main unchanged at baseline immediately before correction commit; input FINISH `054585f`, with no conflicting integration move.
Rollback or correction approach: ordinary corrective/revert commit; keep source/bundle/manifest hashes paired and preserve immutable stored evidence.
Publication: PUBLISHED on local `codex/finish-app`; remote publication/integration coordinated by Lead.

## Independent-review correction round 1

State: IMPLEMENTED / READY_FOR_REVIEW; independent re-review pending.
Correction implementation: `1f964db00656fafb364a127dcec6b6ba5f4eed71`; supersedes `9da3065` for exact-candidate review. Input was `054585f89d494877590d22d2025af025b197a296`. Main remained `cb0fa4f1242ae8bf12afb084bc9475017040b784`; no decision/authority change.

Both Important findings addressed. `web/src/api.ts` now derives each target/document summary's technical-failure count from its exact terminal members and validates model counts against those validated document members. Evaluated members bind by immutable evaluation ID. Opaque unevaluated intent IDs must bind through a unique, single-cell target summary's exact target/version/model/configuration: a terminal row (including IN_DOUBT) contributes its actual technical outcome; no terminal row denotes pending/running only within the reported progress bound. Unknown, duplicate, contradictory or unbound intent membership fails closed. Target truth/scored counts also derive from these same resolved cells. Pending intents are never assumed to be technical failures, and unevaluated terminal failures cannot masquerade as pending.

Shared `(target_id, target_version)` now requires exactly identical zero-based page index and normalized bounding box across every model attempt. Nested evaluations accept only their frozen v0.3 field set; unsupported identity/provenance fields are rejected rather than silently contradicting their enclosing attempt/target/model. No source contract/backend scope expansion, score formula or UI interaction change.

TDD evidence: `node --test web/tests/contract.test.js` first RED **6 failed / 27 passed** for the precise TIMEOUT/zero-summary counterexample, independent summary levels over REFUSED/TIMEOUT/MALFORMED/ERROR, mixed success/timeout, pending+IN_DOUBT, page 1 versus page 51/bbox mismatch and contradictory nested identities. Focused GREEN **33 passed**. Self-review added an adversarial extra-attempt-field probe for collision with internal binding metadata: RED **1 failed / 33 passed**; member resolution then became explicit, final focused GREEN **34 passed**. Final `npm test --prefix web`: **55 passed**. `npm run typecheck --prefix web`, `npm run build --prefix web`: pass. Repeated unchanged production build matches every manifest digest and size. `npm audit --prefix web --json`: **0 vulnerabilities**, dependency/lock files unchanged. `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /Users/galiettemita/Downloads/IARPA/Redaction_LLM_Evaluation_Dashboard-RUNTIME009B/.venv/bin/python -m pytest tests/packaging -q`: **100 passed in 16.06s**, including Chrome startup. Same interpreter full `-m pytest -q`: **865 passed in 52.32s**. Diff checks pass.

Exact correction assets under `web/dist`:
- `assets/index-BfjntY5Y.js`: 225482 bytes; `text/javascript; charset=utf-8`; SHA-256 `b51e9a86ebf73cfd45eb5db3c5324652872550b333b144a495394070c97cf533`.
- `assets/index-DOfTYw_4.css`: 7483 bytes; `text/css; charset=utf-8`; SHA-256 `93b1e6178c23c09e35b4b9a84888a4c32f5a1c92cabe6b80611ec792ecd6d1e4`.
- `index.html`: 567 bytes; `text/html; charset=utf-8`; SHA-256 `95ef232ffb8ecc6cef2a6e44ea438dab2811d01bf72b2daecce2cf46180ece7e`.

Only production source changed: `web/src/api.ts`. Regression: `web/tests/contract.test.js`. Generated bundle, `packaging/local/manifest.json`, `tests/packaging/test_local_static.py` and `tests/packaging/test_local_preflight.py` rebound to exact assets under prior scope. The deferred mounted-interaction Minor remains Task 6; no live PDF/model/tunnel/browser workflow or independent re-review claim. No dependencies, paid calls, private data, new scientific validation or deployment. Node dependencies remain untracked locally for review.

Logs: `/tmp/rl-task5-r1-red.log`, `/tmp/rl-task5-r1-red-binding.log`, `/tmp/rl-task5-r1-green-contract.log`, `/tmp/rl-task5-r1-node.log`, `/tmp/rl-task5-r1-build.log`, `/tmp/rl-task5-r1-repeat-build.log`, `/tmp/rl-task5-r1-audit.json`, `/tmp/rl-task5-r1-packaging.log`, `/tmp/rl-task5-r1-python.log`.
