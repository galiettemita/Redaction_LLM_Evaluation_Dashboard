# RL-MVP-006 — Correction 01: trusted evaluation authority and cross-run summaries

**Status: OWNER-APPROVED for bounded synthetic/mock-only implementation (2026-10-11).** Owner: Backend/Codex. Independent reviewers: QA and Research. Lead coordinates integration but merge needs separate owner approval. Publication epoch: E0039. Approval explicitly includes Codex's 2026-10-11 read-only preflight proposed file scope and four additional Lead safeguards. The source preflight was NOT PUBLISHED; this packet is the operative approved scope.

**Integration baseline at approval:** `9d859f4ec531535eafea7bac78d92e4607012fcf`, E0038. Recheck live main/epoch before work and publication. Rejected implementation: `34c08d28c9ec607a89e5dc5bdb48be81e9476ca7`, Backend branch `codex/rl-mvp-006-evaluator-summaries` @ `1e86e52e9007bf043126b3f714f0e5a89f5b8e46`. Independent QA handoff `qa/rl-mvp-006-review-34c08d2` @ `ea6586d2a72fb7a6f9326d49c20aca89e812a955` (FAIL) and Research handoff `review/rl-mvp-006-research-e0038` @ `7bdbfd8161fe67fd97d08b78691df32bb8272ee0` (CHANGES_REQUESTED).

## Objective and non-goals

Correct five independent-review blockers: (1) authentic frozen Task-4 attempt provenance; (2) authoritative stored evaluation evidence (not self-asserted Pydantic trust); (3) summaries bound to exact stored evaluation membership; (4) real cross-document/model-specific runs with explicit protocol compatibility; (5) unvalidated source-fact/mock evidence must stay NEEDS_REVIEW. Preserve DEC-022 byte-pinned synthetic reference eligibility, null numeric scores, reference/predictor separation, immutable attempts and no-retry/IN_DOUBT semantics. No human scientific validation is implied.

**Do not** implement Task 7, live NLI, models, numeric scoring, external/personal data processing, authentication for public API, or deployment.

## Exact authorized file scope

Modify:
- `src/redaction_lab/contracts.py`
- `src/redaction_lab/store.py` (**read-only attempt resolver only**; no change to enqueue/claim/complete behavior)
- `src/redaction_lab/evaluator.py`
- `src/redaction_lab/judges/base.py`
- `src/redaction_lab/summary.py`
- `tests/test_contracts.py`
- `tests/test_worker.py`
- `tests/test_evaluator.py`
- `tests/test_summary.py`

Create:
- `src/redaction_lab/evaluation_store.py`
- `tests/test_evaluation_store.py`
- ONE unique `docs/project/handoffs/RL-MVP-006-backend-<UTC>-<ID>.md` on approved Task-6 implementation branch.

No other files, package/dependency edits, or shared canonical docs. Do not edit prediction adapters, prediction_source.py, reference.py, detector/canonicalizer, fixtures, local_nli.py, API/UI, pyproject.toml or Task-7 files. If another file is essential (including package __init__), STOP and request amendment. Use additive commits on isolated existing Task-6 branch, never force-push or rewrite rejected candidate history.

## Architecture and authority

### 1. Authentic Task-4 attempt resolution
Introduce frozen internal ResolvedAttempt (attempt, job, manifest, run, canonical source) from `RunStore.resolve_attempt(attempt_id, *, project_id)`. Resolve from actual immutable Task-4 SQLite tables; join attempt/job/source/run; recompute/validate stored canonical source, run, manifest, request/response hashes, target/version/model/config/attempt identity, project and state. Preserve TIMEOUT as IN_DOUBT when applicable, ordinary terminal attempts COMPLETE. Legacy/unbound/untrusted rows cannot become authoritative. Resolver performs **zero dispatch, enqueue, retry or mutation**. `evaluate_attempt` in authoritative path must receive this resolved dependency, not merely accept a caller-made ModelAttempt as proof.

### 2. EvaluationStore in same SQLite database
New EvaluationStore owns append-only `source_fact_records`, `evaluations`, `summaries` and `summary_members` with immutable triggers, foreign keys to authentic Task-4 attempts/jobs and authoritative cross-references. Evaluation and summary/member insertion must be **atomic transactional units**; crash/failure may not leave partially authoritative summary or membership. No public `save_evaluation(record)` or `save_summary(snapshot)` accepting self-asserted value objects. Build through authoritative `evaluate_and_store` and `build_summary(request)`, plus project-scoped getters that reload and verify every underlying membership/dependency. A Pydantic instance is a value object, not trust.

**Authorization safeguard:** Internal methods may be used only by a trusted, already-authorized application component. `project_id` is a namespace selector, not proof of caller authorization. Do not claim cross-user authentication, public safety, or solve malicious trusted-process/local-database compromise. Fail closed for mismatched project and foreign-key provenance. If a safe authenticated API is necessary, STOP; Task 7 remains unauthorized.

### 3. Evaluation provenance and deterministic identity
Bind attempt/job/manifest/source/run hashes and IDs, project, redacted PDF SHA, canonical/target versions, model requested/reported/config, experiment condition, prompt/settings/policy/budget/tools/attempt policy, request/response digests, trusted exact mapping/reference evidence, source-fact record and judge/rubric/evaluator identities to immutable authoritative evaluation identity. Extract `condition_id` from frozen RunDefinition, never caller selection. Compute deterministic evaluation ID from normalized dependency+evidence envelope (without timestamps) and a series key over relevant method/source versions. Replay identical dependency+evidence returns identical row or fails on conflict; version changes create new records, old rows remain. Assign creation time on first repository insertion. Byte-reverify DEC-022 synthetic pairing, never promote arbitrary references.

### 4. Explicit unvalidated evidence
Source-fact propositions, completeness and supplied mock judgments have **no scientifically validated semantic authority**. Record explicit `UNVALIDATED_SYNTHETIC` state; do not permit caller-provided `RESEARCH_VALIDATED`. All such cases preserve provisional evidence but `process_status=NEEDS_REVIEW` and qualitative label `UNVALIDATED_MOCK_EVIDENCE` (or an equally explicit non-accuracy label), never `COMPLETE` or `PROVISIONAL_ALL_FACTS_SUPPORTED`, even if every supplied label says SUPPORTED. Numeric score channels remain null, score status NONE, no score scale or validation ID. This safeguard applies to fabricated propositions with correct quote locators and incomplete inventories. No new scientific method approved.

### 5. Real cross-run summaries
Document summaries may be run-local; per-model across-document summaries MUST support distinct legitimate Task-4 run IDs. Replace singular-run matching at MODEL level with immutable `contributing_run_ids` and verified protocol profile derived from actual frozen RunDefinition(s): condition, prompt ID/version, settings fingerprint, attempt policy, context policy/budget and tool permissions. Model provenance includes requested/reported model ID and model_config_id, with explicit limitation that matching names do not establish weights/digest. Require compatible rubric/judge/evaluator/reference provenance. Cross-model comparisons can involve separate model-specific runs and must compare exact common eligible target/reference sets, not artificial same-run IDs. Bind each common eligible entry to project, redacted doc/target versions, mapping/reference versions/hashes/method and DEC-022 trust; deterministic sorted-set identity. No cross-model blended score, weights or numeric means.

### 6. Honest exclusions and counting
Persist requested attempt IDs, included evaluation IDs, explicit exclusions with stable reasons, complete contributing run IDs, eligible provenance sets, compatibility and exact membership. Each requested attempt exactly one included or excluded subject. Unknown truth stays included/unknown rather than disappearing. Maintain orthogonal truth and attempt-outcome partitions; review/disagreement/error are subsets, not additional denominator partitions. Recompute counts/summary identity on read and reject fictional IDs, missing members, changed payloads, scope or version mismatch. Empty eligible denominator => null, never zero. Changed dependencies produce new record identity; determine staleness on read against explicit expected profile, not mutable boolean. No automatic latest selection.

## TDD and review evidence

Add failing tests and regression coverage for:
- authentic persisted Task-4 attempt resolves; caller-forged/altered attempt, job, run, source, target, manifest, request hash/config fails; resolver read-only and TIMEOUT/IN_DOUBT no redispatch;
- directly constructed forged EvaluationRecord or SummarySnapshot has no authoritative storage/summary path; altered source-fact/evaluation/summary/member rows rejected; DB FK and immutability; crash/rollback ensures no partial summary;
- deterministic replay, altered rubric/reference/judge makes distinct evaluation without rewriting prior evidence; correct project authorization boundary and mismatch fail closed;
- mock supplied fact inventory (including invented proposition and omitted material facts) remains NEEDS_REVIEW/UNVALIDATED, never COMPLETE, never numeric;
- two real-shaped document-specific runs for same model can produce MODEL summary; two separate model-specific runs with matching protocol/eligible reference set can compare; changed prompt/settings/condition/context/budget/tools/model-config/rubric/judge/reference fails closed;
- requested vs included/excluded partitions, explicit exclusions, orthogonal truth/attempt status, zero denominator and common eligible set identity;
- all DEC-022 unknown/partial/unregistered reference cases null; no leak to predictor; Tasks 1–4 behavior and tests unchanged.

Use only synthetic fixtures/disposable SQLite databases. Run focused tests, full suite, compileall, dependency integrity, git diff --check, changed-path audit and migration/reopen tests. Document exact commands/results and unrun checks. QA and Research must independently review a new exact corrected SHA. No new dependency, local model, inference, private data, provider API, spending or deployment.

## Publication and stop

Publish one new implementation SHA and one unique Backend handoff on `codex/rl-mvp-006-evaluator-summaries`; record code paths, provenance, tests, compatibility, restrictions and next receivers QA/Research. A passing Backend suite is NOT independent verification or human method approval. Stop for scope expansion, inability to authenticate source dependency, incompatible contract migration, violation of null-scoring, failing regression, changed epoch/hold, or unauthorized model/API use. Recheck live main and decisions before publishing. After independent QA + Research verdicts, Lead reconciles and seeks **separate owner merge approval**. No Task 7 authorized; D03–D06 scientific approvals still open. Deadline is a checkpoint, not permission to waive gates.
