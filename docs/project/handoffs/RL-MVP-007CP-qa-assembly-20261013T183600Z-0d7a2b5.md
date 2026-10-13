# RL-MVP-007CP Assembly — independent QA / security review

Task ID: RL-MVP-007CP Assembly — bind reviewed frontend assets  
Role / session label: QA / Independent Reviewer  
UTC time: 2026-10-13T18:36:00Z  
State: READY_FOR_REVIEW  
Verdict: **PASS for the exact reviewed assembly scope. Combined local website functionality is materially assembled; clean-recipient/final Task-7D acceptance remains NOT ESTABLISHED.**

Baseline integration SHA / decision epoch: `29cf5cc6a569643d906616ad3937711ff5397aec` / E0058.  
Exact implementation SHA reviewed: `0d7a2b56fabd13bb6a2471247b8dcc266ccab093`.  
Published branch HEAD: `91808b75896e7f9fc41d1f23e53b05fbddf46542`.  
Candidate branch: `codex/rl-mvp-007cp-assembly`.  
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0058; DECISIONS.md; AGENT_HANDOFF.md; MASTER_SPEC.md; AGENT_OPERATING_GUIDE.md; frozen `docs/project/API_CONTRACT_V0_1.md`; owner-approved `docs/project/task_packets/RL-MVP-007CP-ASSEMBLY.md`; already reviewed Frontend `06b240453ee0b361703c48ad833899c64aea70f4`; already reviewed Packaging `9648f2b86e885bf5fcc554ff71c562b34d5fcc01`; DEC-022; Task-4 one-shot/immutable behavior; Task-6 null-score/NEEDS_REVIEW semantics.  
Authorization reference and permitted scope: exact-SHA independent QA/security review plus one unique QA handoff only. No implementation edits, merge, deployment, Podman/VM, private data, real PDF processing, inference, spending or final Task-7D acceptance.

## Freshness and scope

Live GitHub `main` was refreshed before review and immediately before publication and remained `29cf5cc6a569643d906616ad3937711ff5397aec`, E0058.

Exact implementation `0d7a2b5...` changes exactly the three assembly-authorized files:
- `packaging/local/manifest.json`
- `tests/packaging/test_local_preflight.py`
- `tests/packaging/test_local_static.py`

Implementation-to-published-head delta is exactly the unique assembly handoff.

No static-server source, API source, frontend dist bytes, Task-3/4/6 source, runtime lock, dependency file or schema changed in this assembly commit.

## Independent evidence actually run

### Exact repository execution

Direct shell GitHub remains unavailable in this QA execution environment.

Command:
`git ls-remote https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git HEAD`

Result:
`Could not resolve host: github.com`

Therefore the Packaging handoff's **98 focused / 594 full pytest passes**, 22 Node tests and Chrome/browser evidence are implementer evidence only and were **not** inherited as independent QA execution.

GitHub Actions and commit-status lookup for exact SHA `0d7a2b5...` returned no runs/status checks.

### Independent exact-byte manifest binding verification

Using GitHub content pinned to the exact assembly SHA, I independently re-encoded the committed UTF-8 asset bytes and recomputed SHA-256 for all three reviewed frontend artifacts.

Observed:

- `web/dist/index.html`
  - bytes: **567**
  - SHA-256: `ac2bd4d56becd360a2b5082bfd6a407d4af3672cde714c9d5cd83b1fa420263a`
  - manifest size/hash: exact match
  - MIME: `text/html; charset=utf-8`

- `web/dist/assets/index-Jwscaf87.css`
  - bytes: **5,353**
  - SHA-256: `eb4db948b482664a1c92439fc97d44d1f99caad26b9fb0c951d93b5f55a5dcfa`
  - manifest size/hash: exact match
  - MIME: `text/css; charset=utf-8`

- `web/dist/assets/index-my5ZYDMr.js`
  - bytes: **211,223**
  - SHA-256: `2b153239406a0d00b566c61ec2b416eaca206db6d8b1c9b45103025f6480a8e1`
  - manifest size/hash: exact match
  - MIME: `text/javascript; charset=utf-8`

Result: **PASS, 3/3 exact asset bindings independently verified.**

### Independent exact-diff / scope audit

I inspected the exact implementation diff.

Production behavior change is limited to:
- replacing `frontend.assets:null` with the exact reviewed three-file inventory;
- changing `delivery_status.frontend_available` from `false` to `true`.

All other changes are test-only assembly coverage. No unreviewed production/source path was introduced.

Result: **PASS**.

## QA / security findings

### Exact reviewed frontend binding — PASS

The manifest binds only the three previously reviewed production artifacts and no additional asset.

The independently recomputed SHA-256, byte sizes and MIME types exactly match both:
- the E0058 packet;
- the candidate manifest.

No dist artifact was modified by the assembly commit.

### Hash / size / MIME enforcement — PASS by unchanged reviewed hosting boundary

The assembly does not alter `src/redaction_lab/api/static.py`.

The previously reviewed static loader still:
- validates exact manifest schema;
- caps asset count/per-file/aggregate bytes;
- permits only index plus constrained JS/CSS names;
- requires exact MIME;
- checks declared byte size;
- computes and checks SHA-256 before accepting an asset;
- verifies exact directory inventory.

The assembly simply supplies a real, independently verified inventory to that already reviewed boundary.

### No-follow / symlink / immutable snapshot defenses — PASS, unchanged

No static-host source changed.

Existing reviewed behavior remains:
- descriptor-relative `O_NOFOLLOW` traversal;
- regular-file and same-owner checks;
- no group/world writable entries;
- single hard-link leaves;
- exact directory inventories;
- before/after identity checks;
- verified asset bytes retained in memory, so request-time serving does not reopen redirected paths.

The assembly tests extend genuine-bundle coverage but do not weaken the settled boundary.

### Same-origin routing / 127.0.0.1 / Host-Origin-framing — PASS, unchanged

The assembly modifies no launcher/router source.

The reviewed static/server layer still:
- binds literal `127.0.0.1`;
- delegates `/api/v1` unchanged to the reviewed API;
- requires safe Host/Origin;
- rejects duplicate Host/Origin/Content-Length/Content-Type before WSGI normalization;
- rejects any Transfer-Encoding;
- rejects raw/decoded static target ambiguity, traversal, query confusion and request bodies on static routes.

The candidate's assembly tests switch those checks from synthetic placeholder assets to the genuine reviewed bundle.

### Browser-safe loading — PASS for the bound artifacts; independent browser run NOT performed

The exact bound HTML references only the exact local hashed JS/CSS files.

The earlier independent Frontend review found no external runtime fetch/CDN/eval/source-map/private-secret issue in these exact reviewed artifacts.

The assembly handoff reports a real existing-Chrome headless same-origin render showing:
- the expected page/title;
- degraded unverified-runtime UI;
- null-score message.

That Chrome execution is implementer evidence; QA did not independently rerun a browser in this environment.

### Synthetic upload / status / restart persistence — PASS by assembly logic; exact execution not independently rerun

The assembly production change does not touch API/store/runtime logic.

The candidate tests now exercise the genuine website bundle together with:
- synthetic upload;
- exact static GET/HEAD bytes;
- API health;
- status/result reads;
- restart persistence;
- persisted ACCEPTED job with source null.

This is relevant coverage, but the reported passing execution remains implementer evidence.

No code path in the assembly can create a prediction attempt or mutate Task-4/Task-6 evidence.

### Runtime-unverified 503 — PASS, unchanged

The assembly does not alter the worker/runtime boundary.

The reviewed API still fails unverified processing before durable work claim/source authority with:
- HTTP 503;
- `RUNTIME_UNVERIFIED`;
- job `ACCEPTED`;
- `source_id:null`.

Setting `frontend_available:true` means only that the exact reviewed browser bundle passed static verification. It does not qualify the PDF runtime.

### Fail-closed tamper semantics — PASS

If a bound asset is missing, extra, symlinked, writable, hard-linked, replaced, wrong-size, wrong-MIME or hash-mismatched, the unchanged static verifier makes `frontend_available=False` and static root fails closed rather than serving substitute bytes.

The API diagnostic remains separately available; no fake website-ready state is inferred from presence alone.

## Residual limitations / acceptance boundaries

1. Exact repository focused/full pytest was **NOT RUN independently** because shell GitHub access remains DNS-blocked.
2. Backend/Packaging reported 594 full tests and Chrome evidence were not inherited as independent QA results.
3. Browser rendering was not independently rerun by QA.
4. Manual keyboard, screen-reader and visual accessibility acceptance was not run.
5. Clean recipient-machine installation/offline prerequisite acceptance remains unrun.
6. Real PDF runtime remains intentionally unqualified and fail-closed.
7. No real/private PDFs, model inference, deployment or scientific validation were run.
8. Final Task-7D acceptance remains separately prohibited/unapproved.

## Verdict

**PASS** for RL-MVP-007CP Assembly QA/security scope on exact implementation `0d7a2b56fabd13bb6a2471247b8dcc266ccab093`.

The assembly correctly binds exactly the three independently reviewed frontend artifacts to the already reviewed static-hosting verifier. No demonstrated regression was found in hash/size/MIME validation, no-follow confinement, same-origin routing, loopback binding, framing defenses, API delegation, runtime-unverified behavior or durable state semantics.

This PASS establishes **assembly code/security correctness**, not clean-recipient acceptance, deployment readiness, scientific validation or final Task 7D acceptance.

Tests not run and reason: exact repository pytest/browser execution not independently runnable due shell GitHub DNS failure; no private/real data, runtime/model operation, Podman/VM, deployment or final acceptance run.

Independent review evidence: fresh exact-SHA diff/source review and independent re-hashing of all three exact committed frontend assets; implementer test/browser counts were not treated as independent.

Research/data approval evidence: QA grants none. Separate exact-SHA Research review must be reconciled by Lead.

Known residual risks: browser/accessibility and recipient-device execution are still acceptance gates; runtime/model/scientific validity remains absent.

Affected roles / next receiver: **Lead / Architect**.

Last freshness check: live `main` remained `29cf5cc6a569643d906616ad3937711ff5397aec`, E0058, immediately before publication.

Rollback/correction: preserve history; any later demonstrated defect requires additive correction and fresh exact-SHA review. No immutable evidence rewrite.

Publication: PUBLISHED on `qa/rl-mvp-007cp-assembly-review-0d7a2b5`; no implementation code modified, no merge, no deployment, no runtime/model operation.
