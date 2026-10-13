# RL-MVP-007CP Assembly Packaging handoff

Task ID: RL-MVP-007CP Assembly.
Role / session label: Packaging / frontend-bundle assembly.
UTC time: 2026-10-13T19:22:16Z.
State: READY_FOR_REVIEW; not independently verified, merged, deployed or final-accepted.
Baseline integration SHA / decision epoch: `29cf5cc6a569643d906616ad3937711ff5397aec` / E0058.
Candidate branch / exact commit SHA: `codex/rl-mvp-007cp-assembly` / implementation `0d7a2b56fabd13bb6a2471247b8dcc266ccab093`.
Source requirements / approved decisions / contract versions: R01-R12; DEC-001..019 and DEC-022; frozen local API v0.1; reviewed Frontend `06b240453ee0b361703c48ad833899c64aea70f4`; reviewed Packaging `9648f2b86e885bf5fcc554ff71c562b34d5fcc01`; E0058 assembly authorization. Reference isolation, one-shot Task 4 authority, immutable Task 6 evidence, unknown truth and null verified/experimental score channels remain unchanged.
Authorization reference and permitted file/action scope: `docs/project/task_packets/RL-MVP-007CP-ASSEMBLY.md`; exactly `packaging/local/manifest.json`, `tests/packaging/test_local_preflight.py`, `tests/packaging/test_local_static.py`, and this one unique Packaging handoff on a new isolated branch. No source/API/dist edits, dependencies, merge, deployment, Podman/VM operation, private data, PDF processing, inference or spending.

Work performed / artifacts and exact paths:

- Re-hashed the committed build bytes and bound the existing manifest inventory to `web/dist/index.html` (567 bytes, SHA-256 `ac2bd4d56becd360a2b5082bfd6a407d4af3672cde714c9d5cd83b1fa420263a`, `text/html; charset=utf-8`), `web/dist/assets/index-Jwscaf87.css` (5,353 bytes, `eb4db948b482664a1c92439fc97d44d1f99caad26b9fb0c951d93b5f55a5dcfa`, `text/css; charset=utf-8`) and `web/dist/assets/index-my5ZYDMr.js` (211,223 bytes, `2b153239406a0d00b566c61ec2b416eaca206db6d8b1c9b45103025f6480a8e1`, `text/javascript; charset=utf-8`).
- Set manifest `delivery_status.frontend_available` true. Existing preflight and launcher independently verify the exact complete inventory before serving it and remain API-only/degraded on any missing, extra, replaced, symlinked or mismatched asset.
- Added byte-for-byte committed-inventory tests and genuine-package preflight evidence. The copied-package launcher test now serves the actual reviewed build, exercises exact static bytes and the same-origin API upload/status/result/restart flow, and retains Host/Origin/raw-target/framing attacks.
- Added a real existing-Google-Chrome headless render test through the local launcher. It verifies React execution, reviewed page content, explicit unverified-processing UI and the null-score message. The HTTP flow separately proves upload, document state, `RUNTIME_UNVERIFIED` 503, persisted `ACCEPTED` state with no source, `UNKNOWN` truth, empty targets and null score channels before and after restart.

Tests actually run / command / result / environment:

- TDD RED against the null manifest inventory: genuine static serving, genuine preflight and real launcher flow each failed closed; the Chrome probe rendered `FRONTEND_UNAVAILABLE`. No source behavior was changed to obtain RED.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -p no:cacheprovider tests/packaging/test_local_preflight.py tests/packaging/test_local_static.py -q`: **98 passed, 0 failed in 17.88s** on the final candidate. An implementer run independently reported the same 98 passes in 18.24s.
- Same command with ten explicit genuine/static/security/HTTP/Chrome nodes: supporting review expanded parametrization to **50 passed, 0 failed in 5.27s**.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -B -m pytest -p no:cacheprovider -q`: **594 passed, 0 failed in 34.20s**.
- `node --test web/tests/contract.test.js web/tests/build.test.js`: **22 passed, 0 failed**.
- `PYTHONPYCACHEPREFIX=<fresh temporary directory> /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python -m compileall -q src tests`: exit 0; temporary bytecode removed.
- `uv pip check --python /private/tmp/rl-mvp-006-evaluator-summaries/.venv/bin/python`: 21 packages checked, all compatible.
- `sh -n packaging/local/launch.sh packaging/local/preflight.sh`; Python 3.12 `-m json.tool packaging/local/manifest.json`; `git diff --check`; exact changed-path audit: all passed.
- Fresh SHA-256 and byte-size measurements matched all three E0058 packet values. Fresh `git ls-remote origin refs/heads/main` remained `29cf5cc6a569643d906616ad3937711ff5397aec` before commit.
- One diagnostic command used the host's older system Python for `compileall` and failed on pre-existing Python-3.12-only f-string syntax in `src/redaction_lab/store.py`; the required project Python 3.12.14 compile above passed. One dependency command initially addressed a nonexistent venv-local `uv` executable; the corrected explicit `uv --python` command above passed. Neither diagnostic changed files or indicates a candidate regression.

Tests not run and reason: no npm install/build/typecheck in this assembly task because dependencies were intentionally absent and installation was prohibited; reviewed deterministic build evidence is inherited from the integrated Frontend candidate and the committed bundle was independently hashed/tested here. No manual keyboard/screen-reader review, clean-recipient-machine acceptance, qualified isolated PDF runtime, real/private PDF, model inference, scientific scoring, deployment or Task 7D acceptance; all are outside this packet. The automated Chrome test covers render and degraded-state UI; HTTP integration covers upload/status/restart because no new browser-automation dependency was authorized.

Independent review evidence: fresh independent QA/security and Research exact-SHA review is pending. Same-session subagents provided implementation assistance and a read-only supporting audit only; that audit is not independent approval. Supporting audit found no packet gap and passed 50 adversarial cases on the candidate content.
Research / data approval evidence: no new research-method, data-use, model/runtime or scientific-validity approval. DEC-022 synthetic-only reference authority and null scoring are preserved; arbitrary PDF processing remains runtime-unverified and fails closed.
Known issues / risks / stale dependencies: frontend availability proves integrity of this reviewed local bundle, not a qualified PDF worker or clean-device installation. Chrome smoke depends on an already-present macOS Google Chrome executable; it passed here but remains explicitly skippable where Chrome is absent. The standard-library local server is bounded loopback infrastructure, not a deployment target. No genuine model/PDF result can be produced while the runtime lock is unverified.
Affected roles / requested next action: QA/security and Research should independently review exact implementation `0d7a2b56fabd13bb6a2471247b8dcc266ccab093`; Lead then evaluates their exact-SHA handoffs for a separate owner merge decision. Do not infer Task 7D acceptance.
Last freshness check and relevant differences: live default branch `main` remained at approved `29cf5cc6a569643d906616ad3937711ff5397aec` / E0058 immediately before implementation commit. The isolated branch differs only by the three authorized implementation files plus this handoff. ACK E0058 / Assembly packet at the stated baseline; no acknowledgment by another session is claimed.
Rollback or correction approach: revert the isolated implementation and handoff commits, or discard the unmerged branch. The integrated API-only launcher remains fail-closed when the genuine inventory is absent or invalid; no database migration or persistent evidence rewrite occurred.
Publication: PUBLISHED on `codex/rl-mvp-007cp-assembly` after normal non-force push containing this handoff; no merge or deployment.

Completion checklist:

- [x] Fresh E0058 baseline, isolated branch and exact-scope checks.
- [x] Exact committed artifact hashes, sizes and MIME types bound in manifest.
- [x] Fail-closed genuine static serving and same-origin API preserved.
- [x] Browser render plus upload/status/runtime-unavailable/null/restart evidence.
- [x] Host/Origin/framing/traversal/symlink/tamper adversarial coverage.
- [x] Focused, full, frontend, compile, dependency, shell and diff checks.
- [x] Implementation commit and unique Packaging handoff prepared for publication.
- [ ] Fresh independent QA/security and Research exact-SHA reviews.
- [ ] Owner merge authorization and final Task 7D/clean-device acceptance.
