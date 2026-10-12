# RL-MVP-007A Correction 01 Research review

Task ID: RL-MVP-007A Correction 01 — Filesystem Confinement and Trusted Worker Authority
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-12T11:03:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-7A CORRECTION-01 RESEARCH/PROVENANCE SEMANTICS; NOT SCIENTIFIC VALIDATION

Baseline integration SHA / decision epoch: `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595` / E0048
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `aba0a9cfba2e5216a09ce82c12590f063203db53`
Published Backend HEAD: `4ac02c1e3156c572608c499597f70df5623686cb`

Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0048; DECISIONS.md; AGENT_HANDOFF.md; RESEARCH_METHOD.md; INTERFACES.md; owner-approved `docs/project/task_packets/RL-MVP-007A-CORRECTION-01.md`; original QA/security CHANGES_REQUESTED handoff `a6ca3d35c2cb95538c24f1ce4c7a2bbaf334e673`; original Research scoped PASS `dc2d975b9d427921ecdc62765d684aa83b1b9cc2`; Backend Correction-01 handoff.

Authorization reference and permitted file/action scope: exact-SHA independent Research review plus one unique Research handoff only. No implementation edits, merge, Task 7B/C/P/D, Podman installation/execution, image build/download, VM provisioning, private/restricted data, model inference, provider calls, spending, deployment, or scientific-method approval.

## Freshness and scope

- Live GitHub `main` refreshed before review and immediately before publication and remained `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595`, E0048.
- Exact Correction-01 implementation delta from branch reconciliation commit `f6d4a92db897ef5925cd94e1009f914d834e9e91` to `aba0a9c` changes exactly the fourteen E0048-authorized implementation/test paths.
- Exact implementation to published Backend HEAD adds only the unique Backend handoff.
- No Task-3 reference implementation, Task-6 evaluator/evaluation-store/summary implementation, scoring formula, model runtime, or shared scientific method file changed.

## Research findings

### 1. Task-4 source identity remains stable and byte/project derived — PASS

Correction 01 does not change the deterministic source/target identity formulas in `prediction_source.py`.

The default trusted/internal Task-4 path remains:

`RunStore(path).ingest_redacted_pdf(pdf_bytes, project_id=...)`

which continues to call `derive_prediction_source` and therefore preserves the same:
- source ID;
- redacted document version;
- canonical document version;
- target ID/version derivation;
- project scoping;
- PDF-byte SHA binding.

The prior injectable `source_deriver` constructor parameter has been removed from `RunStore`.

Candidate tests explicitly reject:
- `RunStore(..., source_deriver=...)`;
- caller-supplied source arguments to `ingest_redacted_pdf`.

Thus an arbitrary application caller cannot choose a custom derivation callback through the public Task-4 store constructor.

### 2. Production document processing now owns the verified-worker authority path — PASS within the trusted-host boundary

`DocumentWorker` now accepts only:
- ApplicationStore;
- ArtifactStore.

It no longer accepts a caller-supplied PDF worker, runner, policy, result object, source material, or digest.

On each production run, it:
1. constructs `ApplicationPdfWorker`;
2. loads only the install-owned runtime lock;
3. verifies runtime availability before claiming a durable job;
4. invokes the isolated worker;
5. verifies nonce/project/role/hash/protocol bindings;
6. reconstructs a deterministic Task-4 source from the verified worker material plus actual PDF bytes;
7. persists that source through an internal `RunStore._persist_prediction_source` primitive;
8. only then marks the application document job READY.

The source persistence primitive still rechecks:
- exact project;
- exact PDF SHA;
- full `PredictionSource` structural integrity.

This resolves the prior Research caveat that production composition could simply inject a mock worker through the DocumentWorker constructor.

### 3. Mock protocol seams are now explicitly non-authoritative — PASS

Injectable protocol/runner testing remains available as `NonAuthoritativePdfWorkerProbe`.

That probe can test framing, nonce/hash/project/role binding and container-command construction, but it is not accepted by `DocumentWorker` and has no persistence method or application-job transition authority.

The reviewed test demonstrates that attempting:

`DocumentWorker(app_store, artifacts, probe)`

raises `TypeError`, leaving:
- the application job ACCEPTED;
- no Task-4 source;
- no runtime evidence.

This cleanly separates mock protocol evidence from authoritative PDF-derived Task-4 state.

### 4. Unverified runtime fails before job claim or Task-4 persistence — PASS

The checked-in runtime lock remains intentionally unverified.

`ApplicationPdfWorker()` calls `RuntimePolicy.from_lock`, and `DocumentWorker.run_once` also calls `ensure_available()` before `claim_next`.

Therefore a missing/unverified runtime fails before:
- job claim;
- runtime evidence assignment;
- source reconstruction;
- canonical_sources insertion;
- prediction dispatch.

The candidate test confirms the redacted document remains ACCEPTED and Task-4 state remains unchanged when the shipped lock is unverified.

This is important research-wise because synthetic/mock worker behavior cannot be mistaken for a qualified parser execution simply because a document job exists.

### 5. Structural host validation is still not semantic PDF proof — PASS, correctly disclosed

The host still validates:
- actual byte hash;
- project and role;
- nonce;
- protocol version;
- approved parser/canonicalizer versions;
- page/geometry bounds;
- target order and uniqueness;
- canonical text hash/marker structure;
- deterministic Task-4 identities.

The host does **not** independently prove that the isolated parser's canonical text or redaction geometry is semantically correct without reparsing the hostile PDF.

That limitation remains explicitly documented.

Correction 01 improves the authority chain by requiring the production path to originate from the application-owned verified-runtime composition. It does not convert structural verification into a scientific claim about parser correctness.

A compromised trusted Python process/host remains outside the threat model; no cryptographic claim against arbitrary same-process code is made.

### 6. Unsupported PDFs still cannot mint reconstruction targets — PASS

No PDF detector/canonicalizer/reference behavior was widened by this correction.

The production path still depends on the existing isolated worker disposition:
- unsupported;
- failed;
- no redactions;
- processable.

Only a processable REDACTED response with complete bounded material can proceed to Task-4 source reconstruction.

No OCR, raster guessing, inferred redaction text, or unsupported-target fabrication path was introduced.

### 7. Reference isolation and DEC-022 synthetic-only trust remain unchanged — PASS

Correction 01 does not modify:
- Task-3 reference registry/alignment;
- `ReferenceMapping`;
- evaluation truth eligibility;
- DEC-022 registry rules.

Reference uploads remain role-separated from redacted sources and do not create Task-4 prediction sources.

Arbitrary reference uploads or document pairing do not gain trusted-truth status.

Reference content remains outside the prediction-source and PredictionManifest channels.

Therefore DEC-022 remains the sole checkpoint software-trust route for revealed truth.

### 8. Task-4 prediction one-shot semantics remain unchanged — PASS

Correction 01 changes only Task-4 source-ingestion composition.

It does not modify:
- enqueue semantics;
- atomic claim;
- one-shot/no-hidden-retry behavior;
- timeout/IN_DOUBT handling;
- attempt immutability;
- provider/model provenance validation.

The existing Task-4 regression tests remain in scope, and no prediction job is created merely by document validation.

### 9. Task-6 evidence/scoring semantics remain unchanged — PASS by source scope

No Task-6 evaluator, EvaluationStore, summary, or qualitative-evidence contract file changed.

Therefore:
- source-fact segmentation remains unvalidated;
- mock judgments remain NEEDS_REVIEW / `UNVALIDATED_SYNTHETIC`;
- no qualitative mock result becomes research-validated accuracy;
- existing Task-6 evidence remains immutable;
- numeric verified/experimental score channels remain null in the current Task-6 method.

No new score interpretation is introduced by the application foundation.

### 10. Filesystem-confinement correction does not change research identity or truth semantics — PASS

The large filesystem/migration correction is security/integrity plumbing.

From Research scope, I found no path by which these changes:
- rewrite existing Task-4 source identity;
- reinterpret Task-6 evidence;
- confer reference trust;
- create scores;
- alter model-condition semantics.

The new descriptor-anchored storage/backup behavior supports integrity of the bytes and records used by later research layers, but it is not itself scientific validation.

## Independent tests actually run

### Exact repository test execution

Command:

`git ls-remote https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git HEAD`

Result: shell GitHub checkout remains unavailable in this Research environment due DNS/network restriction.

Therefore I did **not** independently execute the exact repository's focused/full pytest suites.

Backend-reported evidence reviewed but not adopted as independent Research execution:
- 29 path/artifact/migration adversarial tests passed;
- 51 isolation/document-worker/Task-4 authority tests passed;
- 55 application tests passed;
- 14 migration tests passed;
- 418 full repository tests passed;
- compileall passed;
- dependency and offline-lock checks passed;
- unverified-runtime scripts failed closed;
- 14-path scope audit passed.

### Independent Research source-level probe

Command:

`python /mnt/data/rl_mvp007a_c01_research_probe.py`

Result:

`PASS assertions=11`

Probe covered:
- deterministic same-PDF/same-project Task-4 source identity;
- changed project changes source identity;
- changed PDF bytes change source identity;
- deterministic target identity;
- changed geometry changes target identity;
- production-shape DocumentWorker rejects a caller worker parameter;
- production-shape ApplicationPdfWorker rejects a caller policy parameter;
- shipped runtime-lock state remains unverified/zero-digest;
- reference association remains untrusted.

Compile:

`python -m compileall -q /mnt/data/rl_mvp007a_c01_research_probe.py`

Result: PASS.

This probe reproduced reviewed identity/composition predicates; it was **not byte-for-byte repository package execution**.

## Tests not run and reason

- exact focused/full repository pytest: NOT RUN independently because local shell GitHub access is unavailable;
- real Podman/VM/image qualification: NOT RUN and prohibited;
- filesystem symlink/race and SQLite cwd/backup adversarial suite: not independently executed by Research; these belong primarily to the separate QA/security review and Backend counts are not inherited;
- real/private/restricted PDFs: NOT RUN and prohibited;
- clean-recipient-device portability: NOT RUN and later 007P/007D gate;
- model/NLI inference, model downloads, provider calls, spending, deployment: NOT RUN and prohibited;
- D03-D06 human/scientific validation: NOT RUN and not approved.

## Residual limitations / risks

1. The application-owned production worker path now removes caller injection, but same-process malicious Python or trusted-host compromise remains explicitly outside the threat model.
2. The actual Podman/runtime/image remains unverified and unusable; no real parser authority exists until later qualification.
3. Host structural verification still cannot independently prove PDF semantic correctness.
4. The migration implementation uses a serialized process-wide `fchdir` section due stdlib SQLite limitations; unrelated host threads using relative paths during startup remain an operational risk for QA/security and later packaging review.
5. Actual clean-device portability, runtime licensing, offline image packaging, institutional/private-data policy and secure production startup remain future gates.
6. DEC-022 remains synthetic-only.
7. D03/D04/D05/D06 remain NOT APPROVED.

## Verdict

**PASS** for RL-MVP-007A Correction 01 Research/provenance semantics on exact implementation `aba0a9cfba2e5216a09ce82c12590f063203db53`.

The correction preserves stable Task-4 identities, prediction/reference separation, DEC-022's synthetic-only trust boundary, unsupported-PDF fail-closed behavior, Task-6 NEEDS_REVIEW semantics and null numeric scoring.

It also removes the prior production mock/source-deriver injection path from the authoritative application composition.

This PASS does **not** validate filesystem security—that requires the separate QA/security verdict—nor does it constitute Podman/runtime qualification, parser semantic validation, D03-D06 approval, merge authorization, or permission to begin Task 7B/C/P/D.

Independent review evidence: fresh Research review of exact SHA `aba0a9cfba2e5216a09ce82c12590f063203db53`; Backend test counts were not treated as independent.
Research/data approval evidence: synthetic/mock-only; no private data or inference; D03-D06 NOT APPROVED.
Known issues / risks: real runtime unqualified; semantic parser correctness unverified; same-process compromise out of scope; migration fchdir operational caveat; future packaging/recipient acceptance still required.
Affected roles / requested next action: Lead / Architect should reconcile this Research PASS with the fresh independent QA/security review of the same exact SHA. Only if all required gates pass should the Lead seek separate owner merge authorization. Do not begin 7B/C/P/D automatically.
Last freshness check: live main remained `353fdc12c8ec04bc05ec7c8664cd699a8d5ad595` / E0048 immediately before publication.
Rollback/correction approach: preserve published history; any new defect requires additive correction and fresh exact-SHA review. No force-push.
Publication: PUBLISHED on `review/rl-mvp-007a-research-correction01-e0048`; not merged.
