# RL-MVP-006 Correction 01 Research review

Task ID: RL-MVP-006 Correction 01 — Trusted Evaluation Authority and Cross-Run Summaries
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-11T23:49:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-6 RESEARCH/EVALUATION SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: `d846f91e0394ef3d6348cfa8a7856746676c5648` / E0039
Candidate branch / exact commit SHA: `codex/rl-mvp-006-evaluator-summaries` / exact corrected implementation `8f2fa74b5c7c988735a572e682c506aed28afe94`; Backend publication head `f220fd7cd06553ad75f952e5ea6e3807a21d9abe`.
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0039; DEC-001/003/004/005/011-015/017/020/022; RESEARCH_METHOD.md; INTERFACES.md; owner-approved `docs/project/task_packets/RL-MVP-006-CORRECTION-01.md`; prior QA FAIL on `34c08d2`; prior Research CHANGES_REQUESTED on `34c08d2`; Task-5 proposed rubric and benchmark.
Authorization reference and permitted file/action scope: exact-SHA independent Research review and one unique Research handoff only. No implementation edits, merge, Task 7, model install/download, real inference, spending, deployment, private data, or scientific-method approval.

## Freshness and candidate integrity

- Live main refreshed before review and before publication: `d846f91e0394ef3d6348cfa8a7856746676c5648`, E0039.
- Read current AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md, Correction-01 packet, prior Task-6 QA and Research findings, corrected Backend handoff, and exact candidate source/tests.
- Backend publication head differs from exact implementation only by the unique Backend handoff.
- Correction code/test changes are within the owner-approved Task-6 Correction-01 scope.

## Research findings

### 1. Authentic frozen Task-4 attempt authority — PASS

The corrected evaluator no longer treats a caller-made `ModelAttempt` as sufficient provenance.

`RunStore.resolve_attempt(attempt_id, project_id=...)` resolves the persisted Task-4 attempt, job, manifest, run, canonical source and frozen model configuration from SQLite and revalidates:
- project;
- job/attempt deterministic identity;
- run/manifest/source binding;
- target/version/model/config;
- request hash;
- terminal COMPLETE vs TIMEOUT/IN_DOUBT state;
- provider model identity where required.

The resolver is read-only and does not enqueue, claim, retry or dispatch. Legacy/unbound attempts cannot resolve as authoritative.

`evaluate_attempt` now requires a `ResolvedAttempt`, and EvaluationStore's authoritative path resolves it internally before producing evidence.

This resolves the prior QA/Research concern that a forged standalone ModelAttempt could be semantically evaluated against trusted truth.

### 2. DEC-022 byte-pinned synthetic truth eligibility — PASS within software-trust scope

The evaluator still byte-verifies the actual redacted PDF against the trusted Task-4 source and recomputes the reference alignment from PDF bytes.

For the scoreable synthetic path it requires the authoritative alignment to reproduce the supplied immutable mapping; changed/unregistered/partial/ambiguous/untrusted reference evidence does not become semantic truth.

The evaluator also bridges the Task-4 target to the Task-3 reference target through physical target evidence before treating the mapping as trusted.

This remains **software trust for the registered synthetic pair only**. It is not D03 scientific validation or real-document ground-truth validation.

### 3. Unvalidated source-fact segmentation and mock judgment — prior blocker RESOLVED

Correction 01 introduces an explicit `EvidenceValidationState.UNVALIDATED_SYNTHETIC`.

`build_source_fact_record` always marks supplied source facts UNVALIDATED_SYNTHETIC.

`evaluate_attempt` accepts only that unvalidated state for Task-6 mock evidence and rejects any attempted synthetic `RESEARCH_VALIDATED`-style escalation.

When source facts and mock judge evidence exist, the record is forced to:
- `process_status=NEEDS_REVIEW`;
- `qualitative_status=UNVALIDATED_MOCK_EVIDENCE`;
- `source_fact_validation_state=UNVALIDATED_SYNTHETIC`;
- `judge_validation_state=UNVALIDATED_SYNTHETIC`;
- `score_status=NONE`;
- `verified_score=None`;
- `experimental_score=None`.

This remains true even if every supplied mock label is SUPPORTED, and it also applies when the proposition segmentation is incomplete or semantically fabricated but mechanically quote-bound.

Therefore provisional evidence can be retained for review without presenting supplied mock segmentation/judgment as completed accuracy.

### 4. Disagreement and unresolved judgment handling — PASS

Mock disagreement remains an orthogonal fact-level signal while the overall process stays NEEDS_REVIEW.

Summary disagreement counts are subsets of successful prediction evaluations and do not create a second denominator partition.

No unresolved mock judgment is promoted to COMPLETE semantic accuracy.

### 5. Authoritative EvaluationRecord storage — PASS for reviewed internal boundary

Correction 01 adds EvaluationStore on the same SQLite database.

The authoritative path is `evaluate_and_store`; there is no public `save_evaluation(record)` that accepts a self-asserted Pydantic value object as authority.

Persisted evaluations are bound by foreign keys to authentic Task-4 attempts/jobs/sources and carry:
- source and source hash;
- run and run digest;
- manifest and manifest digest;
- target/version;
- requested/reported model/config;
- prompt/settings/policy/context provenance;
- request/response hashes;
- mapping/reference provenance;
- rubric/evaluator/judge/source-fact provenance;
- deterministic evaluation-series and evaluation identity.

On read, the repository re-resolves Task-4 authority and verifies deterministic evaluation identity/bindings. Immutable DB triggers prevent normal mutation/deletion.

Directly constructible legacy/value objects therefore remain structurally readable but are not authoritative repository evidence.

### 6. Authoritative summary membership / direct-forgery concern — PASS for reviewed internal boundary

Correction 01 adds an authoritative `EvaluationStore.build_summary(SummaryRequest)` path with exact requested attempt membership.

There is no `save_summary(snapshot)` accepting a caller-built SummarySnapshot as authoritative evidence.

The store:
- resolves each requested attempt through Task-4 authority;
- reloads included evaluations through EvaluationStore authority;
- records explicit exclusions;
- writes summary and summary_members atomically in one transaction;
- binds summary members through SQLite foreign keys;
- reconstructs the summary from stored members/evaluations on read;
- recomputes deterministic summary identity;
- verifies optional expected compatibility profile;
- rejects tampered/missing/cross-project membership.

This addresses the prior QA finding that a standalone forged SummarySnapshot could otherwise look internally self-consistent.

Legacy v1 summary helper/value objects remain available for backward compatibility and must not be treated as repository-authoritative Task-6 v2 evidence.

### 7. Cross-run per-model summaries — prior blocker RESOLVED

The authoritative v2 summary path no longer requires a single run_id for MODEL-level summaries.

MODEL summaries may include multiple legitimate Task-4 runs, and record a deterministic `contributing_run_ids` set.

Document and target summaries remain run-local.

The compatibility profile is derived from frozen run/evaluation provenance and requires consistency in:
- condition;
- prompt ID/version;
- settings fingerprint;
- attempt policy;
- context policy and budget;
- tool permissions;
- requested model/config within one model summary;
- rubric/evaluator/judge;
- mapping method/version.

Independent source inspection and isolated predicate probes confirmed that:
- same model/config + compatible protocol across `run-doc-1` and `run-doc-2` is permitted for MODEL summary;
- the same pair is rejected for DOCUMENT summary as non-run-local.

This resolves the prior Research cross-document summary blocker.

### 8. Cross-model comparisons across separate model-specific runs — PASS

Authoritative model summaries may come from distinct model-specific run IDs.

`assert_comparable_summaries` for v2 requires:
- the same exact common eligible set derived from eligible **reference provenance**, not merely target IDs;
- the same compatibility-profile ID;
- same project and aggregation version.

Model identity/configuration differences are intentionally excluded from the non-model compatibility profile, allowing separate model-specific runs to be compared when their experimental protocol and exact eligible reference set match.

Eligible provenance includes project, document/target identity, mapping/reference versions/method, canonical hashes and reference trust. A changed reference canonical hash therefore changes the common-set identity and blocks comparison.

This is appropriately conservative.

### 9. Unknown truth and technical nonanswers — PASS

Unknown/untrusted reference truth remains included as unknown rather than zero or disappearance.

REFUSED/TIMEOUT/ERROR/MALFORMED remain attempt-outcome categories independent of truth eligibility.

TIMEOUT/IN_DOUBT from Task 4 is not converted into a successful prediction or retried by the evaluator.

No semantic evidence is attached to non-success attempts.

### 10. Null numeric score invariant — PASS

Task-6 v2 EvaluationRecord and SummarySnapshot validators continue to require:
- `score_status=NONE`;
- null verified/experimental score channels;
- no score scale ID;
- no research validation ID.

No mean, percentage, weight, ranking, or numeric semantic accuracy is produced.

### 11. Scientific limitations remain explicit

The corrected implementation does **not** establish:
- D03 truth-confirmation validity on real documents;
- D04 fact segmentation/rubric validity;
- D05 model-trial protocol/roster validity;
- D06 aggregation weights or validated comparison claims;
- semantic correctness of supplied mock labels;
- model-weight identity from matching model names/config strings;
- local NLI accuracy;
- real inference quality.

D03-D06 remain NOT APPROVED.

## Independent tests actually run

Exact repository execution attempt:

`git ls-remote https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git HEAD`

Result:
`fatal: unable to access ... Could not resolve host: github.com`

Therefore the Backend-reported 104 focused / 334 full pytest suites were **NOT independently executed** in this Research environment.

Independent isolated Correction-01 Research probe reproduced the exact reviewed predicates:
- unvalidated supplied evidence -> NEEDS_REVIEW / UNVALIDATED_MOCK_EVIDENCE;
- attempted non-UNVALIDATED synthetic validation escalation -> rejected;
- MODEL summary protocol profile accepts compatible distinct run IDs;
- DOCUMENT summary rejects distinct run IDs;
- exact eligible provenance key changes when reference canonical hash changes;
- common eligible-set identity is deterministic independent of ordering.

Result: **10/10 isolated assertions PASS**.

These were isolated reproductions of reviewed source predicates, **not byte-for-byte execution of the repository package**.

Backend-reported evidence reviewed but not adopted as independent execution:
- 104 focused tests passed;
- 334 full tests passed;
- selected migration/reopen/timeout/direct-authority tests passed;
- compileall passed;
- dependency check passed;
- diff/scope checks passed.

Tests not run and reason:
- exact repository pytest: NOT RUN independently due container DNS/network restriction;
- real local/remote model or NLI inference: NOT RUN and prohibited;
- model downloads/installations: NOT RUN and prohibited;
- human annotation/adjudication/calibration/held-out scientific validation: NOT RUN and requires designated Research Human approval;
- private/real research data, provider calls, Task 7, deployment: NOT RUN and unauthorized.

## Nonblocking limitations / boundaries

1. EvaluationStore and RunStore assume a trusted, already-authorized internal application component. `project_id` is a namespace selector, not caller authentication.
2. Direct malicious control of the trusted Python process or SQLite file is not claimed to be contained.
3. Legacy v1 EvaluationRecord/SummarySnapshot value objects and legacy summary helper functions remain structurally available for backwards compatibility; only repository-built/reverified v2 records are authoritative evidence.
4. Current explicit summary exclusion reason is NO_EVALUATION; incompatible or stale evidence fails closed rather than being silently excluded.
5. Provider/requested model names and model_config_id do not establish an immutable model weights/digest identity.
6. Mock source-fact propositions may still be scientifically wrong or incomplete; that is precisely why their process state remains NEEDS_REVIEW.
7. No authenticated public evaluation API or durable scientific approval workflow exists in this scope.

## Verdict

**PASS** for RL-MVP-006 Correction 01 Research/evaluation semantics on exact implementation `8f2fa74b5c7c988735a572e682c506aed28afe94`.

The two prior Research blockers are resolved:
1. supplied/unvalidated source-fact segmentation and mock judgments no longer become COMPLETE/all-facts-supported; they remain explicit NEEDS_REVIEW/UNVALIDATED_MOCK_EVIDENCE with null numeric scores;
2. authoritative MODEL summaries now support legitimate multi-document, multi-run provenance and separate model-specific runs can be compared on exact compatible eligible reference sets.

The correction also closes the prior trust-chain gap by resolving authentic Task-4 attempts and making EvaluationStore persistence/reverification the authoritative Task-6 path.

This PASS is not scientific validation, D03/D04/D05/D06 approval, model-quality evidence, merge authorization, or Task-7 authorization.

Independent review evidence: fresh Research review of exact corrected SHA `8f2fa74b5c7c988735a572e682c506aed28afe94`; Backend author-reported tests were not treated as independent.
Research/data approval evidence: D03-D06 NOT APPROVED; synthetic/mock-only; no private data or real inference.
Affected roles / requested next action: Lead / Architect should reconcile this Research PASS with the separate fresh QA review of the same exact SHA, then seek separate owner merge authorization if all required gates pass. Do not begin Task 7.
Last freshness check: live main remained `d846f91e0394ef3d6348cfa8a7856746676c5648` / E0039 immediately before publication.
Rollback/correction approach: preserve branch history; if later review finds a defect, publish an additive correction and re-review exact new SHA. No force-push.
Publication: PUBLISHED on `review/rl-mvp-006-research-correction01-e0039`; not merged.
