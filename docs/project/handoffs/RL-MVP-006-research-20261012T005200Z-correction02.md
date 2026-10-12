# RL-MVP-006 Correction 02 Research review

Task ID: RL-MVP-006 Correction 02 — Outcome-Independent Reference Eligibility and Exclusion-Only Summaries
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-12T00:52:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-6 CORRECTION-02 RESEARCH/EVALUATION SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: `b81ae54e0326c633a6e43b6cce6d3fe8af117db6` / E0040
Candidate branch / exact commit SHA: `codex/rl-mvp-006-evaluator-summaries` / exact corrected implementation `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`; Backend publication head `7226d23fcd2d83568e3d9c561ea75d3a8289468d`.
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0040; DEC-001/003/004/005/011-015/017/020/022; RESEARCH_METHOD.md; INTERFACES.md; owner-approved `docs/project/task_packets/RL-MVP-006-CORRECTION-02.md`; prior Correction-01 QA CHANGES_REQUESTED `a9614a97188f91e69eb44e94923f6bef94d92b2d`; prior Correction-01 Research PASS `b3ad3902c95d9333543db23eed670cbcddadb55f`; latest Backend handoff `RL-MVP-006-backend-20261012T004501Z-correction02-0ef37c5.md`.
Authorization reference and permitted file/action scope: exact-SHA independent Research review and one unique Research handoff only. No implementation edits, merge, Task 7, inference, model installation/download, spending, deployment, private data, or scientific-method approval.

## Freshness and candidate integrity

- Live GitHub main refreshed before review and before publication: `b81ae54e0326c633a6e43b6cce6d3fe8af117db6`, E0040.
- Read current AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md, Correction-02 packet, Correction-01 QA/Research handoffs, latest Backend handoff and exact corrected source/tests.
- Exact implementation-to-published-head delta is one Backend handoff only.
- Correction-02 implementation changes are confined to the six packet-authorized files after the E0040 branch-baseline reconciliation.

## Research findings

### 1. Reference eligibility is independent of model outcome — PASS

Correction 02 introduces a v3 eligible-reference identity built only from trusted target/reference provenance:

- project;
- redacted document version;
- target ID/version;
- reference target ID/version;
- mapping ID/version/method;
- mapping redacted-canonical version;
- reference document/canonical version;
- redacted/reference canonical hashes;
- DEC-022 trust state.

It excludes:
- attempt status;
- prediction text;
- process/qualitative status;
- run/model identity;
- source-fact record identity/version;
- judge/evaluator outcome.

The truth-eligibility predicate remains based on approved synthetic-pair trust plus CONFIRMED/SCOREABLE mapping state.

Therefore SUCCESS, TIMEOUT, REFUSED, MALFORMED and ERROR evaluations over the same authoritative target/reference mapping produce the same eligible-reference key and the same common eligible-set identity, while their technical outcome counts remain distinct.

This directly resolves the Correction-01 QA blocker.

### 2. Source-fact availability no longer changes truth eligibility — PASS

The v3 eligible-reference key excludes source-fact record ID/version.

A successful prediction with source facts and a technical nonanswer with no source-fact record can therefore remain on the same exact truth set.

Method compatibility remains separate:
- rubric/evaluator/judge/mapping-method compatibility is represented through `evaluation_compatibility_profile_id`;
- conflicting non-null source-fact record versions are still rejected across model comparisons;
- one non-null source-fact version versus a null version from a technical nonanswer is allowed and does not alter truth eligibility.

This is the correct experimental separation: reference truth eligibility is about the target/reference pair, not whether semantic decomposition happened for a particular model outcome.

### 3. Cross-model common reference sets are now scientifically meaningful within the synthetic-only boundary — PASS

For v3 model summaries, `assert_comparable_summaries` requires:
- identical exact eligible-reference key sets / common-set ID;
- same project;
- same prediction-protocol compatibility profile;
- same evaluation-method compatibility profile when evaluations exist;
- same aggregation version;
- no conflicting non-null source-fact-record versions.

Model/run identities are allowed to differ as intended.

A changed target, mapping, mapping method, reference version/hash, canonical hash or DEC-022 trust changes the eligible-reference identity or fails closed.

Thus two models can be compared over the same exact synthetic reference set while preserving their distinct success/refusal/timeout/error counts.

### 4. All-excluded summaries represent no evaluated result, not zero accuracy — PASS

Correction 02 adds `qualitative-summary-evidence-v3` / `qualitative-summary-v3`.

For a nonempty authenticated SummaryRequest where every requested attempt is explicitly `NO_EVALUATION`:
- requested attempts are resolved through Task-4 authority;
- requested_count == excluded_count == N;
- included evaluations = 0;
- eligible evaluations = 0;
- unknown evaluated results = 0;
- completed/refused/timeout/malformed/error evaluated counts = 0;
- review/disagreement/evaluator-error counts = 0;
- eligible reference provenance set is empty;
- the empty common-set identity is deterministic;
- rubric/evaluator/judge/evaluation-method provenance is null rather than fabricated;
- `score_status=NONE`;
- verified/experimental scores are null;
- no score scale or research-validation ID is asserted.

This does not reclassify underlying Task-4 attempt outcomes as evaluated outcomes. It records only that no Task-6 evaluations are included.

The result is therefore “no evaluated results,” not 0% accuracy and not completed semantic evaluation.

### 5. Multiple compatible runs in exclusion-only model summaries — PASS

EvaluationStore derives the summary prediction-protocol profile from resolver-authenticated Task-4 attempts, even when no EvaluationRecord is present.

MODEL-level exclusion-only summaries may span compatible distinct runs and retain the contributing run-ID set.

TARGET/DOCUMENT exclusion-only summaries remain run-local.

Changed prompt/settings/condition/context/budget/tools/model configuration fails the requested-attempt compatibility check before authoritative summary persistence.

### 6. v2/v3 methodology identity remains explicit — PASS

The implementation preserves immutable v2 reconstruction semantics and introduces separate v3 semantics rather than silently reinterpreting old records.

- v2 summary identity retains the legacy outcome-dependent eligible-provenance behavior for historical replay.
- v3 uses corrected outcome-independent eligible-reference identity.
- mixed v2/v3 authoritative comparison fails closed.
- v3 stores a prediction-protocol compatibility profile separately from nullable evaluation-method compatibility.
- all-excluded v3 summaries require evaluation-method fields to be null.
- included v3 summaries require complete evaluation-method provenance.

This version separation is clear enough to prevent a correction in methodology from being presented as if historical v2 results had always used v3 semantics.

### 7. Unvalidated source facts and mock judge evidence remain NEEDS_REVIEW — PASS

Correction 02 does not weaken the Correction-01 research safeguard.

Supplied source-fact segmentation and mock judge evidence remain:
- `UNVALIDATED_SYNTHETIC`;
- `process_status=NEEDS_REVIEW`;
- `qualitative_status=UNVALIDATED_MOCK_EVIDENCE`;
- null numeric score channels.

Even fully SUPPORTED mock labels remain provisional evidence pending designated Research Human validation.

No provisional evidence is promoted to scientifically completed accuracy.

### 8. Unknown/null truth behavior — PASS

DEC-022 remains the only checkpoint trust authority.

Missing, partial, ambiguous, unreadable, conflicting, changed or unregistered reference truth remains untrusted/NOT_SCOREABLE and does not become semantic accuracy.

Unknown truth stays orthogonal to prediction outcome and remains null, never zero.

Reference eligibility is independent of answer quality only **after** the reference itself has passed the synthetic software-trust gate.

### 9. Technical nonanswers and disagreement counting — PASS

REFUSED, TIMEOUT, MALFORMED and ERROR remain separate Task-6 attempt-outcome counts when evaluations exist.

They do not alter the eligible reference set for the same trusted target.

Disagreement remains an orthogonal review subset rather than an additional denominator partition.

No technical nonanswer becomes a factual contradiction or numeric zero.

### 10. Deterministic identity / exact membership semantics — PASS from Research scope

Source inspection shows v3 identity excludes creation timestamps and normalizes eligible/reference and requested-attempt sets.

EvaluationStore persists exact authenticated membership and reconstructs summaries by schema version on reopen.

For v3 all-excluded and included summaries:
- requested membership is exact;
- explicit exclusions are persisted;
- method provenance follows included-evaluation presence;
- summary identity is deterministic under reordered input membership.

The store preserves v2 rows without rewriting them.

These are software-authority properties rather than scientific validation, but they support the research interpretation of the summary evidence.

## Independent tests actually run

Exact repository execution attempt:

`git ls-remote https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git HEAD`

Result:
`fatal: unable to access ... Could not resolve host: github.com`

Therefore Backend-reported 92 focused / 349 full pytest results were **NOT independently executed** in this Research environment.

Independent isolated Research probe:

`python /mnt/data/rl_mvp006_c02_research_probe.py`

Result:
- **PASS assertions=27**
- SUCCESS/TIMEOUT/REFUSED/MALFORMED/ERROR all produced the same synthetic eligible-reference key under identical reference provenance;
- source-fact absent/v1/v2 did not change truth key;
- changed target/mapping/method/reference/hash/trust changed the truth key;
- common-set identity was order-independent;
- one non-null source-fact version plus null was compatible, while conflicting non-null versions were rejected;
- all-excluded semantics had requested=excluded, zero evaluated counts, null method provenance, null scores and score status NONE;
- unvalidated evidence remained NEEDS_REVIEW/UNVALIDATED.

Compile:
`python -m compileall -q /mnt/data/rl_mvp006_c02_research_probe.py`
-> PASS.

Independent comparison/version probe:

`python /mnt/data/rl_mvp006_c02_research_comparison_probe.py`

Result:
- **PASS assertions=9**
- success vs each technical outcome remained comparable on identical v3 reference truth;
- changed evaluation-method identity failed comparison;
- conflicting non-null source-fact versions failed comparison;
- mixed v2/v3 comparison failed;
- changed reference truth failed the exact eligible-set check;
- all-excluded identity was deterministic under reordered attempts/runs.

Compile:
`python -m compileall -q /mnt/data/rl_mvp006_c02_research_comparison_probe.py`
-> PASS.

These probes reproduced exact reviewed v3 predicates and identity logic. They were **isolated reproductions, not byte-for-byte execution of the repository package**.

Backend-reported evidence reviewed but not adopted as independent execution:
- 92 focused tests passed;
- 349 full tests passed;
- 5 selected disposable-DB/reopen/rollback tests passed;
- compileall passed;
- uv dependency integrity passed;
- diff/scope checks passed.

Tests not run and reason:
- exact repository pytest: NOT RUN independently because the review container could not resolve github.com;
- real model/NLI inference: NOT RUN and prohibited;
- model downloads/installations: NOT RUN and prohibited;
- human annotation/adjudication/calibration/held-out scientific validation: NOT RUN and requires designated Research Human approval;
- private/real data, provider calls, deployment, Task 7: NOT RUN and unauthorized.

## Scientific limitations / nonblocking boundaries

1. DEC-022 trust still proves only membership in the registered synthetic byte pair plus software alignment conditions. It does not establish real-document D03 validity.
2. Source-fact segmentation and mock labels remain scientifically unvalidated and must remain NEEDS_REVIEW.
3. A common eligible reference set establishes comparable **reference eligibility**, not equal model weights, tokenizer equivalence, model quality or causal comparability.
4. Matching requested/reported model names and config IDs do not prove immutable weights/digest.
5. D05 still must approve model roster/trial protocol before research claims; D06 still must approve aggregation/weighting.
6. An all-excluded summary documents no evaluated Task-6 result; it must not be surfaced as a performance score.
7. EvaluationStore assumes a trusted already-authorized internal caller; project_id is a namespace selector, not authentication.
8. Legacy v1/v2 value objects and historical records remain readable but do not acquire v3 methodology retroactively.

## Verdict

**PASS** for RL-MVP-006 Correction 02 Research/evaluation semantics on exact implementation `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`.

The two Correction-01 QA blockers are resolved in a way consistent with the approved research boundary:
1. exact eligible-reference identity is now independent of prediction outcome and source-fact availability while method incompatibilities remain separately enforced;
2. authenticated exclusion-only summaries can represent zero evaluated results without inventing method provenance or implying zero accuracy.

D03/D04/D05/D06 remain NOT APPROVED. This PASS is not scientific validation, model-quality evidence, merge authorization or Task-7 authorization.

Independent review evidence: fresh Research review of exact corrected SHA `0ef37c51266d9d6ca333f0f3369ef30e11c208a8`; Backend author-reported test counts were not treated as independent.
Research/data approval evidence: synthetic/mock-only; D03-D06 NOT APPROVED; no private data or real inference.
Affected roles / requested next action: Lead / Architect should reconcile this Research PASS with the separate fresh QA review of the same exact SHA and only then seek separate owner merge authorization if all gates pass. Do not begin Task 7.
Last freshness check: live main remained `b81ae54e0326c633a6e43b6cce6d3fe8af117db6` / E0040 immediately before publication.
Rollback/correction approach: preserve branch history; any later defect requires additive correction and new exact-SHA review. No force-push.
Publication: PUBLISHED on `review/rl-mvp-006-research-correction02-e0040`; not merged.
