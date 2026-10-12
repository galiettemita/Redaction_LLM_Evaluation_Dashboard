# RL-MVP-007A Research / Evaluation independent review

Task ID: RL-MVP-007A — Portable Application Foundation and Isolated PDF-Worker Interface  
Role / session label: Research / Evaluation independent reviewer  
UTC time: 2026-10-12T10:18:00Z  
State: READY_FOR_REVIEW  
Review verdict: **PASS FOR TASK-7A RESEARCH/PROVENANCE SEMANTICS; NOT SCIENTIFIC VALIDATION**

Baseline integration SHA / decision epoch: `ec4e6f45ec903555858a13f507e9d73a572ca2de` / E0046.  
Candidate branch / exact implementation SHA: `codex/rl-mvp-007a-portable-foundation` / `87ae7c5d46e72d3f61dcc325e64fab562c9fa00a`.  
Published Backend HEAD: `90a69fba46ebbb780d4fb3bb85337d6c694ea3f2`.  
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0046; DECISIONS.md; AGENT_HANDOFF.md; RESEARCH_METHOD.md; INTERFACES.md; E0044 `RL-MVP-007A-PORTABLE-FOUNDATION.md`; E0045 `RL-MVP-007A-PDF-ISOLATION-AMENDMENT.md`; controlling E0046 `RL-MVP-007A-IMPLEMENTATION.md`; Backend handoff `RL-MVP-007A-backend-20261012T042627Z-87ae7c5.md`; Task 4 trusted-source semantics; Task 6 immutable qualitative evidence semantics; DEC-022 synthetic-only truth boundary.

Authorization reference and permitted file/action scope: exact-SHA independent Research review and one unique Research handoff only. No application-code edits, merge, Task 7B/C/P/D, Podman install/build/run, model inference, model download, provider/API calls, private data, spending, deployment or scientific-method approval.

## Freshness and scope

- Live GitHub `main` refreshed before review and immediately before publication: `ec4e6f45ec903555858a13f507e9d73a572ca2de`, E0046.
- Exact implementation comparison from baseline changes **33 paths**, matching the controlling E0046 allowlist.
- Implementation-to-published-Backend-head delta is exactly one handoff file.
- No Task 3 reference-alignment implementation file, Task 6 evaluator/evaluation-store/summary file, API/UI implementation or model-runtime dependency outside the authorized lock/version files was modified.

## Research findings

### 1. Exact redacted-PDF identity and deterministic Task-4 source identity — PASS

The worker-derived bridge does not accept a caller-supplied `PredictionSource` as authority.

For redacted input, the host:
- hashes the actual PDF bytes;
- requires worker material `source_sha256` to equal that actual hash;
- requires approved detector/canonicalizer versions;
- reconstructs the existing deterministic Task-4 source ID, redacted document version and canonical version from project + actual PDF hash + approved versions;
- reconstructs target IDs/versions from project, redacted version, page and geometry under the existing detector version;
- validates target ordering, bounds, duplicate target identities and duplicate detector-evidence IDs;
- validates canonical text SHA and exact TARGET marker order;
- persists through the existing `RunStore.ingest_redacted_pdf` path and revalidates the source before storage.

Candidate tests explicitly require an isolated-worker material representation of the known synthetic PDF to rebuild **the same** Task-4 `PredictionSource` as the legacy derivation path.

Changed PDF bytes or project IDs continue to produce different source/document identities.

This preserves the Task 1–4 deterministic identity model.

### 2. Host PDF parsing is absent from the worker-derived bridge — PASS

`build_prediction_source_from_material` does not invoke `detect_targets` or `canonicalize_redacted`.

The candidate regression test monkeypatches both host parsing functions to raise and verifies the worker-material bridge still reconstructs the source.

Production arbitrary-PDF parsing is therefore intended to occur inside the isolated worker, not silently on the host.

The legacy default `derive_prediction_source` path remains available for existing trusted/internal behavior, preserving Task-4 backwards compatibility; 007A's application worker supplies the isolated source-derivation strategy explicitly.

### 3. Structural worker observations remain distinct from semantic correctness — PASS with important standing limitation

The host verifies structure and provenance bindings:
- exact input hash;
- project;
- role;
- nonce;
- protocol version;
- approved detector/canonicalizer versions;
- canonical hash;
- bounded page/target/text fields;
- target geometry/order/marker consistency;
- runtime image digest returned from the verified isolated-worker path.

It does **not** and cannot cryptographically prove that the worker's target geometry or canonical text is semantically correct without reparsing the hostile PDF on the host.

The code and packaging README explicitly preserve that distinction.

My isolated probe confirmed the exact conceptual boundary: a structurally self-consistent response can satisfy byte/project/protocol bindings while semantic correctness remains dependent on the qualified worker runtime and its tested parser implementation.

This is acceptable for E0046 only because:
- the checked-in runtime lock is intentionally `runtime_verified: false`;
- `RuntimePolicy.from_lock` rejects it;
- build/verify scripts refuse before Podman operations;
- real runtime qualification and second-machine validation remain later authorization gates;
- no real/private PDFs or scientific claims are permitted in 007A.

**Nonblocking trust caveat:** `DocumentWorker` takes an internal dependency-injected `PdfWorker`, and synthetic tests use a mock worker that can return structurally valid material. Such a mock can persist a Task-4 source in the test harness. This is an internal trusted-composition/test seam, not an application-caller authority API. No public/mutating API exists in 007A. Future 007B/007P assembly must ensure production document processing is wired only to the separately qualified `IsolatedPdfWorker`; mock-worker output must never be represented as independently verified PDF semantics.

I found no path in 007A by which an untrusted upload/API caller directly submits a `PredictionSource`, `PredictionSourceMaterial`, source ID, or trusted semantic flag for persistence.

### 4. Unsupported, unreadable or ambiguous PDF material does not fabricate targets — PASS within existing parser profile

Inside the worker:
- strict PDF parsing failures -> FAILED;
- encrypted PDFs -> UNSUPPORTED;
- empty or page-limit violations -> fail closed;
- Task-1 detection NO_REDACTIONS -> NO_REDACTIONS;
- detector UNSUPPORTED -> UNSUPPORTED/FAILED;
- derivation failure -> FAILED;
- PROCESSABLE redacted responses require a nonempty bounded target set and complete canonical material.

Non-processable responses are forbidden from carrying derived canonical/target evidence.

The host does not convert UNSUPPORTED/FAILED/NO_REDACTIONS into Task-4 sources.

This preserves the existing narrower Task-1–4 supported-PDF profile and does not add OCR, guessing or reconstruction of unsupported raster/scanned material.

### 5. Reference uploads remain isolated from prediction authority — PASS

Reference and redacted document versions are role-scoped.

For a PROCESSABLE reference worker response:
- no detector version;
- no canonicalizer version;
- no canonical text/hash;
- no targets

are permitted.

`DocumentWorker` never creates a Task-4 prediction source for a reference role.

Document pairing is explicitly stored as `ASSOCIATED_UNTRUSTED`, and `StoredDocumentPair.truth_trusted` is always false.

Thus arbitrary uploaded reference PDFs:
- may be retained as reference artifacts;
- do not enter Task-4 prediction manifests;
- do not gain DEC-022 trusted-truth status merely by upload, pairing or worker validation.

No Task-3 reference registry/alignment code was changed, so DEC-022 remains the only software-trusted truth route.

### 6. Reference content does not enter prediction source or worker-derived Task-4 source — PASS

The worker request is role-specific and carries only one PDF.

The isolated runtime command has:
- no host volumes;
- no artifact/database mounts;
- no network;
- no reference side channel.

Reference processing returns only validation disposition/page count.

Redacted processing receives only redacted bytes and cannot read a paired reference through the worker protocol.

No reference field was added to `PredictionSource`, `PredictionManifest` or Task-4 run state.

This preserves prediction/reference separation required by DEC-001/008/013.

### 7. Existing Task-4 one-shot and source behavior is preserved — PASS

The `RunStore` change is limited to composition injection of an internal source-deriver function.

Existing default ingestion continues to call the legacy `derive_prediction_source`, preserving existing source identities.

The application path uses the injected worker-material builder only for source creation; `DocumentWorker` does **not** enqueue a Task-4 prediction job.

The candidate regression test verifies that processing a redacted document creates an authoritative canonical source but leaves the Task-4 `jobs` table empty.

No Task-4 prediction retry/claim/attempt logic is modified.

### 8. Task-6 research/evaluation semantics remain unchanged — PASS by scope and source audit

Correction 007A does not modify:
- `evaluator.py`;
- `evaluation_store.py`;
- `summary.py`;
- Task-6 contracts for qualitative evidence.

Therefore:
- source-fact segmentation remains `UNVALIDATED_SYNTHETIC`;
- mock judgments remain `NEEDS_REVIEW` / unvalidated;
- no provisional evidence is converted into scientific accuracy;
- existing Task-6 immutable evaluation and summary records are not rewritten;
- numeric verified/experimental score channels remain null under the existing Task-6 implementation.

007A adds no score computation or score interpretation.

### 9. Runtime absence remains fail-closed — PASS for the code-only qualification state

The committed runtime lock contains zero placeholder digests and `runtime_verified: false`.

`RuntimePolicy.from_lock` rejects such a lock.

Both packaging scripts also refuse immediately with the unverified lock before any Podman action.

Thus this branch cannot silently treat the current developer machine as having a qualified parser runtime.

No real isolation/runtime operation was performed or claimed.

### 10. Portable/local foundation does not alter scientific approval state — PASS

007A is infrastructure and provenance plumbing.

It does not establish:
- D03 automatic reference-truth validity;
- D04 fact/rubric validity;
- D05 model roster/protocol validity;
- D06 aggregation validity;
- actual model reconstruction accuracy;
- parser semantic accuracy on arbitrary PDFs;
- real-document performance;
- clean-recipient-machine portability;
- production isolation.

All remain separate later gates.

## Independent tests actually run

### Exact repository execution attempt

Command:

`git ls-remote https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git HEAD`

Result:

`fatal: unable to access ... Could not resolve host: github.com`

Therefore I could not obtain an exact local checkout and did **not** independently run the repository's focused or full pytest suites.

Backend-reported evidence reviewed but not adopted as independent execution:
- 80 focused application/security/Task-4 bridge tests passed;
- 8 migration/reopen/recovery selection passed;
- 18 adversarial protocol/isolation/source tests passed;
- 398 full tests passed;
- compileall passed;
- dependency integrity passed;
- offline lock check passed;
- shell syntax passed;
- unverified-runtime build/verify scripts exited fail-closed;
- 33-path scope audit passed.

### Independent Research source-level probe

Command:

`python /tmp/rl_mvp007a_research_probe.py`

Result:

`PASS assertions=12`

Probe checks:
- same PDF/project/version tuple -> deterministic same Task-4 source identity;
- different project -> different source identity;
- changed PDF bytes -> different source identity;
- correct protocol nonce/project/role/hash binding accepted;
- forged nonce/project/role/hash/protocol each rejected by the reproduced binding predicate;
- a structurally self-consistent fabricated semantic payload demonstrates the explicit limitation that structural binding alone cannot prove PDF semantic correctness;
- reference association remains `ASSOCIATED_UNTRUSTED` / truth false.

Compile:

`python -m compileall -q /tmp/rl_mvp007a_research_probe.py`

Result: PASS.

This probe reproduced reviewed identity/binding logic conceptually. It was **not byte-for-byte execution of the repository package**.

## Tests not run and reason

- exact repository pytest/full Task 1–7A suite: NOT RUN independently because shell GitHub access remains DNS-blocked;
- real Podman/VM/image build or inspection: NOT RUN and explicitly unauthorized;
- clean second-Mac installation/restart/offline qualification: NOT RUN and belongs to later packaging/recipient acceptance;
- hostile runtime escape/network/filesystem canaries against a real container: NOT RUN and unauthorized in E0046;
- real/private/restricted PDFs: NOT RUN and prohibited;
- model/NLI inference, model downloads, provider/API calls, spending, deployment: NOT RUN and prohibited;
- human/scientific D03–D06 validation: NOT RUN and not approved.

## Scientific and experimental limitations

1. A byte-bound, structurally valid worker response is **not proof of semantic PDF correctness**. Real parser authority depends on later qualification of the pinned isolated runtime/image plus adversarial clean-device testing.
2. The current runtime is intentionally unverified and unusable for real processing.
3. Internal dependency injection allows synthetic/mock workers for tests. That seam must remain unavailable to untrusted application callers and must not be represented as real parsing evidence.
4. DEC-022 remains synthetic-only; arbitrary uploaded references stay untrusted/null.
5. Unsupported/scanned/raster/encrypted/ambiguous PDFs remain outside the current extraction profile; no OCR validity claim exists.
6. Matching Task-4 deterministic source identity proves identity consistency, not historical or semantic truth.
7. Portability is not complete until separately authorized 007P/007D clean-recipient-device testing succeeds.
8. D03/D04/D05/D06 remain NOT APPROVED.

## Verdict

**PASS** for RL-MVP-007A Research/provenance semantics on exact implementation `87ae7c5d46e72d3f61dcc325e64fab562c9fa00a`.

The implementation preserves:
- exact byte/project-based Task-4 identity;
- deterministic target/source provenance;
- existing supported-PDF fail-closed behavior;
- reference isolation and DEC-022 null-truth boundary;
- Task-4 one-shot behavior;
- Task-6 unvalidated/NEEDS_REVIEW semantics and null numeric scores.

The host/worker bridge is **structural/provenance verification, not semantic proof**. The runtime remains intentionally unqualified, so no real-PDF authority, scientific parser validity or portability claim follows from this PASS.

Independent review evidence: fresh Research review of exact SHA `87ae7c5d46e72d3f61dcc325e64fab562c9fa00a`; Backend author test counts were not treated as independent.  
Research/data approval evidence: synthetic/mock-only; no private data or inference; D03–D06 NOT APPROVED.  
Known issues/risks: production composition must not replace the verified isolated worker with a mock/custom worker; actual Podman/macOS isolation, clean-device reproducibility and parser semantic qualification remain future gates.  
Affected roles / requested next action: Lead / Architect should reconcile this Research PASS with the separate independent QA/security review of the same exact SHA. If all gates pass, seek separate owner merge authorization; do not begin 007B/C/P/D automatically.  
Last freshness check: live main remained `ec4e6f45ec903555858a13f507e9d73a572ca2de` / E0046 immediately before publication.  
Rollback/correction approach: preserve history; any later defect requires additive correction and fresh exact-SHA review. No force-push.  
Publication: PUBLISHED on `review/rl-mvp-007a-research-e0046`; not merged.
