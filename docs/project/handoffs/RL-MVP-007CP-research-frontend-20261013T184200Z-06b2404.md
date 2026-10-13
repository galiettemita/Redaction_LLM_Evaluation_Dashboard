# RL-MVP-007CP Frontend Build — Research / Evaluation independent review

Task ID: RL-MVP-007CP — website build / Frontend build
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-13T18:42:00Z
State: READY_FOR_REVIEW
Review verdict: **PASS FOR RESEARCH/PROVENANCE AND BUILT-UI PRESENTATION SEMANTICS; NOT SCIENTIFIC VALIDATION; COMBINED WEBSITE/RECIPIENT ACCEPTANCE NOT ESTABLISHED**

Baseline integration SHA / decision epoch: `82b70faf6fa5669e2b335bb5b93c9d20047ed97b` / E0057.
Exact implementation SHA reviewed: `06b240453ee0b361703c48ad833899c64aea70f4`.
Published Frontend HEAD: `334920de5e885510eaa9cceadd0f33cfd0b8b2eb`.
Source requirements: AGENTS.md; CURRENT_STATE.md E0057; DECISIONS.md; AGENT_HANDOFF.md; frozen `API_CONTRACT_V0_1.md`; owner-approved `RL-MVP-007CP-WEBSITE-BUILD.md`, including Vite 7.3.5 and esbuild 0.27.2 override.
Authorization: exact-SHA independent Research review plus one unique Research handoff only. No code edits, merge, deployment, runtime/model operations, private data, spending or final 7D acceptance.

## Findings

### Truth / score semantics — PASS

The unchanged React source and produced bundle preserve the frozen v0.1 semantics:
- upload/reference truth remains `UNKNOWN`;
- `score_status` remains `NONE`;
- verified and experimental scores remain null;
- target list remains empty under v0.1;
- target/document/model summaries remain null;
- `NEEDS_REVIEW` remains unresolved and is rendered as “Needs review” with predictions/scores unavailable;
- `FAILED` is explicitly not treated as an incorrect prediction;
- `AVAILABLE` is presented as document-processing completion only, with no passage prediction/evaluation claim.

The built JavaScript contains the same unknown/null/NEEDS_REVIEW presentation invariants. I found no browser-side score calculation, reference-trust promotion or model ranking.

### Reference isolation / DEC-022 — PASS

The UI continues to state that adding a reference does not establish trustworthy revealed text or verified accuracy. The adapter accepts upload state only when `truth_status === "UNKNOWN"`.

No Task-3 trust enrollment, reference mapping, evaluator or scoring route is introduced by the build. DEC-022 remains synthetic-only and unchanged.

### Task-4 / Task-6 boundaries — PASS

The frontend still has no prediction-authority path. Refresh/recovery remains read-only and does not replay process/upload actions. No Task-4 retry or new model attempt is created by the build.

Task-6 semantics are presentation-only here; null scoring and NEEDS_REVIEW are preserved, not reinterpreted.

### Build artifact correctness relevant to Research — PASS

The committed production build is local and references only hashed local JS/CSS assets. No source maps are present. Source-level and built-bundle checks show the user-facing unknown/null messages and same-origin API behavior are retained.

The approved frontend pins are exact and the build handoff reports deterministic identical artifact hashes. I did not independently reproduce npm install/build, so those hashes and dependency-audit counts remain implementer evidence.

### Acceptance distinction

- **Source/build research semantics:** PASS.
- **Standalone built artifact static smoke:** implementer evidence only, not independently rerun here.
- **Combined same-origin website/browser workflow with Packaging candidate:** NOT independently established by this review.
- **Clean-recipient acceptance / final 7D:** NOT RUN and not authorized.

## Independent tests actually run

Exact repository shell checkout/tests: **NOT RUN** in this review environment; direct shell GitHub access remains unavailable. Frontend-reported typecheck/build/22 Node tests/517 pytest and Chrome smoke are not claimed as independent evidence.

Independent exact-source/bundle inspection through GitHub at `06b2404...`:
1. source truth UNKNOWN invariant;
2. source null-score invariants;
3. source NEEDS_REVIEW presentation;
4. reference trust warning;
5. READY/AVAILABLE caveat;
6. built bundle contains truth-status UNKNOWN handling;
7. built bundle contains null score channels;
8. built bundle contains “Accuracy unknown”;
9. built bundle retains same-origin/redirect-error transport behavior.

Result: **9/9 Research checks PASS**.

## Tests not run / limitations

Not independently run: npm audit, npm ci, TypeScript compiler, Vite build, reproducibility rebuild, browser accessibility/keyboard/screen-reader, combined 7CP launcher website, clean recipient machine, private/real PDFs, inference, Podman/VM, D03-D06 scientific validation.

The branch history also contains earlier blocked task handoffs from E0055/E0056; this Research review applies to exact implementation `06b2404...`, not to branch-history publication hygiene. Lead should reconcile exact integration scope separately.

## Verdict

**PASS** for RL-MVP-007CP Frontend build Research/provenance semantics on exact SHA `06b240453ee0b361703c48ad833899c64aea70f4`.

No reference-trust promotion, invented prediction, numerical accuracy or READY-as-accuracy misuse was found. D03-D06 remain **NOT APPROVED**.

Next receiver: **Lead / Architect**, to reconcile this Research PASS with independent QA/security on the same exact SHA and with separate Packaging review before any merge/combined acceptance.
Rollback/correction: preserve history; any demonstrated defect requires additive correction and fresh exact-SHA review.
Publication: PUBLISHED on `review/rl-mvp-007cp-frontend-research-e0057`; not merged.
