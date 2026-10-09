# RL-MVP-005 Research proposal handoff

Task ID: RL-MVP-005 — Research rubric and synthetic adversarial benchmark
Role / session label: Research / Evaluation
UTC time: 2026-10-09T21:32:00Z
State: READY_FOR_REVIEW
Baseline integration SHA / decision epoch: `2ceaebacc44e8b1622231683ac0c3ee30c23e7d3` / E0037
Candidate branch / exact commit SHA (or no code change): `research/rl-mvp-005-rubric-e0037`; proposal artifact commits `d0c4173a8d7445da23d61a01b8caa7a0317748d4` and `c85e20805893da2dd6ab09f01fe2384197a24982`; no application-code change.
Source requirements / approved decisions / contract versions: AGENTS.md; CURRENT_STATE.md E0037; DEC-001/003/004/005/011/012/013/014/015/017/020/022; MASTER_SPEC.md; RESEARCH_METHOD.md; INTERFACES.md; owner-approved October 12 implementation plan Task 5; approved `docs/project/task_packets/RL-MVP-005-RESEARCH-PROPOSAL.md`.
Authorization reference and permitted file/action scope: Owner-approved research-only Task 5 packet published on main. Authorized outputs are exactly one rubric proposal, one synthetic JSON benchmark fixture and one unique Research handoff on an isolated Research branch. No evaluator/application code, merge, Task 6, inference, downloads, costs, private data, deployment or scientific-method approval.

Work performed / artifacts and exact paths:
1. Created `docs/project/research_proposals/RL-MVP-005-evaluation-rubric.md`.
   - Rubric ID: `fact-evidence-rubric-v0.1-proposed`.
   - Clearly labeled PROPOSED / scientifically unapproved.
   - Preserves the full-target truth gate: absent, partial, hidden, unreadable, ambiguous, conflicting or unreliable truth => null / Accuracy unknown.
   - Proposes a reference-only source-fact record frozen before prediction inspection.
   - Distinguishes SUPPORTED, MISSING, CONTRADICTED and UNSUPPORTED evidence without assigning numeric weights.
   - Covers actor/action/object roles, relation direction, negation, quantity/unit, date/time, modality, attribution, alternatives, hedging, repetition and unsupported additions.
   - Separates technical attempt outcomes from semantic evidence.
   - Proposes target/document/model reporting requirements, common-set compatibility and empty-denominator null behavior without approving aggregation weights.
   - Proposes blinded independent human annotation, adjudication, disagreement retention, grouped dev/calibration/held-out splits, false-high-score checks, paraphrase fairness and uncertainty reporting.
   - Lists D03/D04/D05/D06 as unresolved and does not choose numeric thresholds or score mappings.

2. Created `tests/fixtures/evaluation_cases.json`.
   - Dataset ID: `rl-mvp-005-synthetic-adversarial`.
   - Version: `synthetic-adversarial-v0.1-proposed`.
   - Synthetic only; explicitly not human gold.
   - 20 adversarial cases.
   - Includes correct paraphrase, name-only/incomplete predicate, actor reversal, negation, altered date, altered quantity, altered unit, modality/completion, unsupported addition, alternative guesses, repeated claim, attribution, missing facts, fully hidden reference, partial reference, misaligned reference, refusal, timeout, malformed response and technical error.
   - Each case records synthetic reference state, attempt outcome, source-fact record, expected supported/missing/contradicted/unsupported evidence, proposed qualitative/null state and rationale.
   - Contains no numeric score, weight, threshold or percentage expectation.

Tests actually run / command / result / environment:
- Live GitHub content validation via repository connector and JavaScript JSON parser:
  - `JSON.parse(tests/fixtures/evaluation_cases.json)` -> PASS.
  - case count -> 20.
  - required scenario-tag coverage -> none missing for paraphrase, name-only, actor reversal, negation, date, quantity, unit, modality, unsupported addition, alternatives, repetition, fully hidden reference, partial reference, misaligned reference, refusal, timeout, malformed and error.
  - unknown/null rule check -> 0 violations.
  - technical nonanswer rule check for REFUSED/TIMEOUT/ERROR/MALFORMED -> 0 violations.
  - numeric score/weight/threshold/percentage field scan -> none.
  - rubric references D03/D04/D05/D06 -> all present.
  - rubric proposal/scientific-nonapproval labeling -> present.
- GitHub branch diff audit before handoff:
  - branch was exactly two commits ahead of main before this handoff;
  - changed paths were exactly the two authorized proposal artifacts.

Tests not run and reason:
- pytest/application test suite: NOT RUN; no application code or executable evaluator was modified by this research-only task, and the packet asks for proposal/fixture validation rather than Task 6 implementation.
- human inter-rater benchmark, adjudication study, calibration, held-out evaluation and scientific acceptance tests: NOT RUN; these require future designated Research Human authorization/validation and approved study materials.
- model inference, evaluator inference, model downloads, provider/API calls, private/real data, deployment: NOT RUN and explicitly unauthorized.

Independent review evidence (or not yet reviewed): This is the Research-authored proposal, not independent scientific review. No designated Research Human approval has been obtained. Lead review is next.
Research / data approval evidence (or not approved / not applicable): D03/D04/D05/D06 remain NOT APPROVED. Synthetic-only examples; no private or restricted data used.
Known issues / risks / stale dependencies:
- D03: real-world automatic truth-confirmation validity remains unestablished beyond the current synthetic fixture trust boundary.
- D04: final fact-decomposition rules, critical-error rules, numeric formula, weights, thresholds and evaluator/human agreement criteria remain open.
- D05: final model roster, stable model/version identity, tokenizer/context comparability, prompt/settings and nonanswer protocol remain open.
- D06: target/document weighting, partial-completion treatment, common-set aggregation and uncertainty reporting remain open.
- Proposed evidence labels and fixture expectations are not human gold until independently annotated/adjudicated.
- Synthetic cases cannot establish real-document evaluator accuracy or production validity.
Affected roles / requested next action: Lead/Architect should review the scoped proposal and decide whether to request revision or separately seek Research Human validation / a future Task 6 implementation packet. No automatic merge or Task 6 follows from this handoff.
Last freshness check and relevant differences: Immediately before handoff publication, live main remained `2ceaebacc44e8b1622231683ac0c3ee30c23e7d3` / E0037. No conflicting hold or decision change was found. The Research branch contained only the two authorized proposal artifacts at that checkpoint.
Rollback or correction approach: Branch-only proposal. Revise additively on this Research branch if requested; do not overwrite prior evidence or force-push. If governing decisions change, re-read main and issue a new scoped handoff.
Publication: PUBLISHED on `research/rl-mvp-005-rubric-e0037`; not merged to main.
