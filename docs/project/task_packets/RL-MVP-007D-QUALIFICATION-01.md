# RL-MVP-007D-QUALIFICATION-01 — portable application qualification

**Status:** OWNER-APPROVED GATE A (read-only feasibility); GATE B NOT APPROVED.
**Owner authorization:** Lead 3 conversation, October 13, 2026 (America/New_York). Authorizes packet publication and read-only QA/security feasibility inspection, runtime/dependency inventory, clean-recipient requirement assessment, proposed Gate B acceptance plan, unique handoffs and independent Research review.
**Baseline:** main `a81c48d9b64cb11fec552639b0c5cf6294011d94`; decision epoch E0063 at authorization. Refresh live main before commencing.
**Task owner:** QA/Security. **Research reviewer:** Research/Evaluation, independently. **Technical read-only support:** Backend/Infrastructure. **Receiver:** Lead/Architect.
**Contracts:** `docs/project/API_CONTRACT_V0_1.md`; existing `RL-MVP-007D-PREP.md`, Task 7A isolation and packaging constraints.
**Requirements:** R01–R03, R05, R08–R11; DEC-001 through DEC-007 and relevant current decisions. The E0043 portable, self-hosted local application direction remains controlling. Proposed architecture and research methods are not institutional/scientific approval.

## Goal and non-goals
Produce a reproducible, independent **read-only** feasibility assessment of qualifying the integrated local application for synthetic PDF processing and clean-compatible-recipient setup. Identify exact blockers and an approvable bounded Gate B execution plan. No live qualification, clean-device trial, or claim of readiness under Gate A.

## Gate A authorized operations — read-only
1. Verify live default branch/HEAD, governing decisions, contract and active handoffs. Inspect repository source, immutable manifests, dependency locks, documentation, current test definitions and published review evidence at pinned revisions. No checkout modification.
2. Inventory the PDF worker's runtime, Podman/container/image and dependency prerequisites, versions, hashes, license evidence, supported OS/architecture, hardware requirements, integrity/signature gaps, and source authority boundary. Missing evidence is BLOCKED/UNVERIFIED, not silently assumed.
3. Inspect loopback/network, worker isolation, prohibition on arbitrary host PDF reparsing, fail-closed runtime behavior, artifact confinement, immutable source/truth separation, error/status semantics, SQLite migration/recovery and duplicate-request controls. Distinguish inspected code from independently executed tests.
4. Specify recipient setup prerequisites, portability risks, reproducibility, local persistence/backup expectations, installation/start procedure and an independent clean-second-device acceptance matrix. Document unsupported platforms explicitly.
5. Map documented and previously reported tests against required tests. State exactly which evidence was previously reported versus independently observed and which tests were NOT RUN here.
6. Prepare **Gate B proposal only**: exact proposed commands and machines, dependencies/downloads, container/image operations, licensing checks, synthetic fixture set, acceptance matrix, success/failure criteria, rollback/cleanup, risk controls, costs, and every permission needed.
7. Research independently inspects the Gate A evidence for leakage of reference-only content, synthetic fixture trust, score-null semantics, prediction claims, and distinction between software acceptance and D03–D06 scientific validation.

## Hard prohibitions for Gate A
No application/test code changes, dependency installs/downloads, runtime or VM/container/PDF-worker operations, executing tests, processing real or synthetic PDFs, private data, external model or paid API calls, model installs/inference, deployment, cloud resources, migrations, spending, public release, Gate B execution or merging implementation. GitHub write permission is restricted to approved **unique task-scoped handoff/report documents on approved review branches**, not product code or canonical main files. No raw source PDFs or private content in public GitHub.

## Deliverables and allowed task-scoped publication
QA branch: unique `qa/rl-mvp-007d-qualification-01-<shortid>` from current main (or an explicitly authorized existing QA branch).
- `docs/project/acceptance/RL-MVP-007D-GATE-A-FEASIBILITY.md` — Gate A findings, evidence links, inventory, risk/register, Gate B proposed commands/permissions and acceptance matrix.
- One unique `docs/project/handoffs/RL-MVP-007D-qa-<UTC>-<shortid>.md` with exact inspection sources, NOT RUN activities, observations, blockers, decision epoch, next receiver.
Research branch: separate `review/rl-mvp-007d-qualification-01-<shortid>` from current main; one unique `docs/project/handoffs/RL-MVP-007D-research-<UTC>-<shortid>.md`, citing the published QA feasibility report (do not copy reports or alter QA branch).
No additional files, canonical edits or production changes. If publishing report requires more scope, stop and ask Lead.

## Acceptance and verdict
QA reports `GATE_A_COMPLETE` only when inventory, evidence gaps, recipient requirements and a precise approval-ready Gate B proposal are all documented; otherwise `BLOCKED` with missing items. Research reports `SCOPED_PASS`, `CHANGES_REQUESTED` or `BLOCKED` on methodology boundaries. These are **not** a PDF-runtime PASS, final Task 7D acceptance, scientific validation, deployment or permission for Gate B.

Lead retrieves both published handoffs, reconciles findings and prepares a single Gate B authorization request for the owner, if warranted. Gate B may include controlled installs/runtime operations only if separately approved. Stop for missing trusted integrity/license evidence, unapproved costs or operations, necessary code edits, reference leakage, source-authority conflict, unsafe egress or changed controlling decision. Recheck main HEAD before delivery.

**Gate A authorization does not approve Task 7D final acceptance, software installation, runtime execution, or any merge/deployment.**
