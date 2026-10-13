# RL-MVP-007CP Assembly — bind reviewed frontend assets
**OWNER APPROVED BOUNDED IMPLEMENTATION, NOT MERGE/DEPLOY/FINAL ACCEPTANCE APPROVED. E0058.**

Baseline: reviewed Frontend implementation 06b240453ee0b361703c48ad833899c64aea70f4; published HEAD 334920de5e885510eaa9cceadd0f33cfd0b8b2eb. Reviewed Packaging implementation 9648f2b86e885bf5fcc554ff71c562b34d5fcc01; published HEAD d0fce23fd96d3781e5559e1bf50616006eaae8a0. Both have exact-SHA independent QA/security and Research scoped PASS. Main E0058 integrates both without claiming combined website acceptance. Recheck live main SHA and canonical documents before work.

## Exact scope
Modify ONLY `packaging/local/manifest.json`, `tests/packaging/test_local_preflight.py`, and `tests/packaging/test_local_static.py`, plus ONE unique Packaging assembly handoff on a new isolated branch. No additional source changes, dependency installs, contract changes or new files.

## Artifact inventory to bind (verify exact committed bytes afresh)
- web/dist/index.html SHA256 ac2bd4d56becd360a2b5082bfd6a407d4af3672cde714c9d5cd83b1fa420263a
- web/dist/assets/index-Jwscaf87.css SHA256 eb4db948b482664a1c92439fc97d44d1f99caad26b9fb0c951d93b5f55a5dcfa
- web/dist/assets/index-my5ZYDMr.js SHA256 2b153239406a0d00b566c61ec2b416eaca206db6d8b1c9b45103025f6480a8e1

Use existing manifest schema and trusted file reader; fill exact SHA256, MIME, byte sizes measured directly from committed assets. Set frontend_available true ONLY if existing preflight/runtime verification actually validates genuine inventory; remain fail-closed if mismatched or missing. Do not edit dist bundle.

## TDD/acceptance
First RED tests against null inventory, then GREEN verified static asset serving and same-origin /api/v1. Run synthetic browser page load, local upload/status, restart persistence, Host/Origin/Transfer-Encoding/Content-Length attacks, symlink/path/missing/tampered assets, truthful runtime-unverified 503 with ACCEPTED job/no source, UNKNOWN truth and null scores. Run full repository regressions, scope check, shell checks and document tests not run. No claim of real PDF processing or independent clean-device acceptance.

Publish exact implementation SHA/branch HEAD/handoff; obtain fresh independent QA/security and Research exact-SHA review. Separate owner approval required before assembly merge.

## Prohibited
No deployment, Podman/VM, image operations, real PDF processing, private/restricted data, inference, paid calls, full scientific scoring, final 7D acceptance or task expansion. Stop if new files or source/API changes are necessary.
