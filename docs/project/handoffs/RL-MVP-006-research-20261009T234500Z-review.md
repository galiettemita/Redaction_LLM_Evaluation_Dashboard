# RL-MVP-006 Research / evaluator-and-summary review

Task ID: RL-MVP-006 — Evaluator Evidence and Three-Level Summaries
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-09T23:45:00Z
State: CHANGES_REQUESTED
Review verdict: CHANGES_REQUESTED FOR TASK-6 RESEARCH/EVALUATION SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: `9d859f4ec531535eafea7bac78d92e4607012fcf` / E0038
Candidate branch / exact commit SHA: `codex/rl-mvp-006-evaluator-summaries` / exact implementation `34c08d28c9ec607a89e5dc5bdb48be81e9476ca7`; Backend publication head `1e86e52e9007bf043126b3f714f0e5a89f5b8e46`.
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0038; DEC-001/003/004/005/011-015/017/020/022; RESEARCH_METHOD.md; INTERFACES.md; owner-approved `docs/project/task_packets/RL-MVP-006-EVALUATOR-SUMMARIES.md`; Task-5 proposed rubric `fact-evidence-rubric-v0.1-proposed` and benchmark `synthetic-adversarial-v0.1-proposed`.
Authorization reference and permitted file/action scope: Exact-SHA independent Research review and one unique Research handoff only. No application-code edits, merge, Task 7, real/model inference, downloads, costs, deployment, private data, or scientific-method approval.

## Freshness / candidate integrity

- Live main refreshed immediately before work and before publication: `9d859f4ec531535eafea7bac78d92e4607012fcf`, E0038.
- Exact implementation changes only the eight authorized source/test files:
  - `src/redaction_lab/contracts.py`
  - `src/redaction_lab/evaluator.py`
  - `src/redaction_lab/judges/base.py`
  - `src/redaction_lab/judges/local_nli.py`
  - `src/redaction_lab/summary.py`
  - `tests/test_contracts.py`
  - `tests/test_evaluator.py`
  - `tests/test_summary.py`
- Publication head differs from implementation only by the Backend handoff.

## Positive findings

1. **Exact truth gate is rechecked from PDF bytes before semantic evidence.**
   - `evaluate_attempt` reruns Task-3 alignment against actual redacted/reference bytes.
   - Changed/unregistered reference bytes route to untrusted/unknown and no judge call.
   - Wrong project, target, target version, mapping ID/version, and stale source-fact records fail closed.

2. **DEC-022 software trust remains separate from numeric scoring.**
   - Semantic evidence is possible only when the re-derived mapping is CONFIRMED/SCOREABLE under the registered synthetic pair.
   - Task-6 records force `score_status=NONE`, `verified_score=None`, `experimental_score=None`.
   - No weights, percentages, rankings, or numeric means are produced.

3. **Prediction/reference separation is preserved.**
   - Frozen `ModelAttempt` is consumed by the evaluator after prediction.
   - No reference/rubric evidence is written back into prediction manifests or attempts.

4. **Attempt outcomes remain orthogonal to semantic evidence.**
   - REFUSED/TIMEOUT/ERROR/MALFORMED produce technical qualitative states and no fact comparisons.
   - Unknown truth does not become zero.
   - Disabled local NLI performs no inference or model download.

5. **Qualitative evidence schema is explicit and provisional.**
   - Typed SUPPORTED/MISSING/CONTRADICTED/NEEDS_REVIEW evidence, unsupported assertions, rationale, quote locators, critical dimensions, judge/rubric/evaluator versions, and immutable IDs are recorded.
   - Actor reversal, negation, quantities/units, dates, modality, alternatives, attribution, repetition, and unsupported additions have mock coverage.

6. **Summary counts preserve separate truth and attempt dimensions.**
   - Truth eligibility, completed attempts, refusal, timeout, malformed, error, needs-review, disagreement, evaluator-error, and unknown counts are explicit.
   - Empty eligible denominator remains null.
   - Duplicate target identities and incompatible model/config/condition/rubric/judge/reference versions are rejected.

## BLOCKING finding 1 — unvalidated source-fact segmentation + mock labels can be emitted as COMPLETE “all facts supported”

The Task-6 packet explicitly states that source-fact segmentation is an unvalidated proposal and that synthetic supplied evidence/mock judges should return NEEDS_REVIEW rather than fabricate semantic certainty.

The exact implementation does not enforce that boundary.

`build_source_fact_record` checks that each `reference_quote` and locator occur in the exact target text, but it does **not** validate that:
- `reference_proposition` is actually entailed by that quote;
- the supplied fact set is complete for the target;
- material target facts were not omitted;
- fact segmentation was independently validated or human-approved.

A caller may therefore supply a syntactically valid record whose quote is correct but whose proposition is fabricated or whose fact set contains only an easy subfact.

Then a mock/supplied judge may return SUPPORTED. `evaluate_attempt` emits:
- `process_status=COMPLETE`
- `qualitative_status=PROVISIONAL_ALL_FACTS_SUPPORTED`

rather than NEEDS_REVIEW.

Independent isolated exact-logic probe reproduced:
- exact target text: `Agent Cedar`
- exact quote/locator: `Agent Cedar` / `chars:0-11` -> accepted
- fabricated proposition: `Agent Birch authorized 99 missiles.` -> not checked by source-fact construction
- supplied mock label: SUPPORTED
- resulting qualitative branch: `PROVISIONAL_ALL_FACTS_SUPPORTED`, with COMPLETE unless judge explicitly flags disagreement/NEEDS_REVIEW.

A completeness variant is also unsafe: for a multi-fact target, a source-fact record can include only one convenient fact; if that one fact is marked SUPPORTED, the implementation can say “ALL_FACTS_SUPPORTED” even though the record itself omitted other material target facts.

This is not a numeric score, but it can still present unvalidated, caller-supplied semantic segmentation and mock labels as a completed qualitative result. That conflicts with the approved packet and with the user-requested distinction between software-trusted synthetic truth and scientifically validated evaluator evidence.

Required correction direction:
- synthetic/mock source-fact records and mock judge labels must remain NEEDS_REVIEW (or an equally explicit unresolved process state) unless a separately approved Research Human validation identity/method establishes the segmentation/judge boundary;
- do not use `COMPLETE` + `PROVISIONAL_ALL_FACTS_SUPPORTED` to imply the supplied fact inventory is complete or independently verified;
- preserve provisional comparisons if useful, but the evaluation process state must clearly communicate unresolved scientific judgment.

## BLOCKING finding 2 — model-level cross-document summaries require one run_id, which is incompatible with valid upstream runs

`summary._validate_common` requires every evaluation in any summary, including MODEL-level summaries, to have the same:
- `run_id`
- model/config
- condition/rubric/evaluator/judge, etc.

But `RunDefinition` binds one run to a single `canonical_document_version_id` / canonical hash. Task 4 also freezes run identity.

Therefore valid evaluations from **different documents** should normally come from different run IDs.

Yet `summarize_model` claims to summarize one model across compatible documents while calling `_validate_common`, which rejects different run IDs.

Independent isolated exact-logic probe:
- model A / document 1 / run-doc-1
- model A / document 2 / run-doc-2
- current common-run check -> `incompatible run_id`.

The existing test `test_model_summary_spans_documents_but_never_models` uses the same synthetic `run-v1` for two different document IDs, which does not reflect the upstream run contract.

This means the required third level — per-model across-document summary — cannot be constructed from normal valid upstream records.

Related consequence: `assert_comparable_summaries` also requires identical singular `run_id` between model summaries, while Task 4 freezes one selected model per run, making cross-model comparison under distinct valid runs overly restrictive.

Required correction direction:
- MODEL-level summaries need a versioned **set of contributing run IDs** or another explicit comparison-series identity, not one singular run ID;
- document-level summaries can remain run-specific;
- cross-model comparison should require compatible condition/prompt/settings/rubric/judge/reference/common eligible set, not artificial same-run identity when upstream runs are model/document specific;
- add tests constructed from valid upstream run semantics.

## Nonblocking Research limitations / cautions

1. `reference_trust="APPROVED_SYNTHETIC_PAIR"` means byte-pinned software trust for one synthetic fixture, not scientifically validated ground truth. Current null numeric channels correctly preserve this distinction.
2. Directly constructed `EvaluationRecord` objects can syntactically self-assert the approved-trust string; summary functions assume records came from the trusted evaluator/application path. Durable authentication/storage of Task-6 records is not implemented. This trust assumption must remain explicit in any future API.
3. The qualitative mock judge tests are examples, not evidence that actor reversal/negation/date/modality detection is scientifically correct.
4. Local NLI is unavailable; no model/judge accuracy has been measured.
5. Task-5 rubric expectations are proposals, not human gold.
6. D03/D04/D05/D06 remain scientifically unapproved.

## Independent tests actually run

Exact repository checkout attempt:

`git clone --no-checkout https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /mnt/data/rl_mvp006_review`

Result: **NOT RUN TO COMPLETION** — review container could not resolve `github.com`. Therefore the exact repository's reported 71 focused / 297 full pytest passes were NOT independently rerun.

Independent isolated semantic/protocol probe:

`python <isolated probe reproducing exact build-source-fact / qualitative-status / summary run-id predicates>`

Observed:
- correct quote/locator can coexist with fabricated `reference_proposition`: reproduced;
- mock SUPPORTED label -> `PROVISIONAL_ALL_FACTS_SUPPORTED`: reproduced;
- no automatic NEEDS_REVIEW from unvalidated segmentation: reproduced;
- model summary with `run-doc-1` + `run-doc-2`: rejected as `incompatible run_id`.

The probe reproduced the exact reviewed predicates; it was **not** byte-for-byte execution of the repository package.

Backend-reported evidence reviewed but not adopted as independent execution:
- 71 focused tests passed;
- 297 full tests passed;
- compileall passed;
- dependency check passed;
- Task-5 fixture parse reported 20 cases;
- diff checks passed.

Tests not run and reason:
- exact repository focused/full pytest: NOT RUN independently because GitHub checkout was unavailable in the review container;
- real NLI/model inference/downloads: NOT RUN and prohibited;
- human annotation/adjudication/calibration/held-out validation: NOT RUN and requires designated Research Human approval;
- private/real data, paid calls, deployment, Task 7: NOT RUN and unauthorized.

## Requested Research checks

- Proposed qualitative rubric represented faithfully: **PARTIAL / CHANGES_REQUESTED** because evidence labels are represented, but unvalidated segmentation/mock labels can advance to COMPLETE/all-facts-supported.
- Exact reference truth before semantic evidence: **PASS** for the byte-reverified DEC-022 synthetic path.
- Actor reversal/negation/quantity/unit/date/modality/unsupported/alternatives/attribution: **represented provisionally**, but mock labels are not independent scientific evidence.
- Unresolved judgments remain NEEDS_REVIEW: **FAIL** for unvalidated segmentation/mock-supported cases.
- Frozen prediction/reference separation: **PASS**.
- Numeric score claims: **PASS — none produced**.
- Target/document reporting: **PASS directionally**.
- Model across-document reporting: **FAIL** under normal upstream run semantics because singular run_id is required.
- Comparable-set integrity: **conservative but overly restrictive**; common eligible sets are deterministic, but same-run requirement blocks valid multi-run comparisons.
- Software-trusted synthetic pair vs scientific ground truth: **correctly distinguished in numeric score channels**, but qualitative COMPLETE/all-facts-supported status currently overstates supplied mock evidence.

## Verdict

**CHANGES_REQUESTED** on exact implementation `34c08d28c9ec607a89e5dc5bdb48be81e9476ca7`.

Blocking corrections:
1. Keep supplied/unvalidated source-fact segmentation and mock judge evidence in an explicit NEEDS_REVIEW/unvalidated process state; do not emit COMPLETE/all-facts-supported as if the fact inventory and labels were independently established.
2. Redesign MODEL-level cross-document summary provenance so valid evaluations from multiple document/run IDs can be summarized and compared without violating upstream frozen-run identity.

No merge and no Task 7.

Independent review evidence: fresh Research review of exact SHA `34c08d28c9ec607a89e5dc5bdb48be81e9476ca7`; Backend self-review/test counts not treated as independent.
Research / data approval evidence: D03/D04/D05/D06 NOT APPROVED; no real judge validation, human benchmark, private data, or scientific score.
Affected roles / requested next action: Lead / Architect -> Backend/Codex for bounded correction; fresh exact-SHA QA and Research review required afterward.
Last freshness check: live main remained `9d859f4ec531535eafea7bac78d92e4607012fcf` / E0038 before publication; no conflicting hold observed.
Rollback or correction approach: branch-only review handoff; implementation correction should be additive and preserve prior evidence; no force-push.
Publication: PUBLISHED on `review/rl-mvp-006-research-e0038`; not merged.
