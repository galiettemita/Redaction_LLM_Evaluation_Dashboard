# RL-MVP-005 — Proposed Experimental Fact-Level Evaluation Rubric

**Status:** PROPOSED — pending designated Research Human review and validation.  
**Task:** RL-MVP-005 research-only proposal.  
**Rubric version:** `fact-evidence-rubric-v0.1-proposed`.  
**Synthetic benchmark version:** `synthetic-adversarial-v0.1-proposed`.  
**Scientific validation:** NOT APPROVED.  
**Baseline:** `main` `2ceaebacc44e8b1622231683ac0c3ee30c23e7d3`, decision epoch E0037.

This document proposes a transparent fact-comparison method for future evaluator implementation and human validation. It does **not** define an approved numeric accuracy formula, score weight, cutoff, critical-error threshold, model roster, aggregation weight, or verified scientific method.

## 1. Scope and governing constraints

This proposal applies only when evaluating a frozen model prediction for one text-redaction target against the exact target truth that has already passed the project's reference-alignment eligibility rules.

Non-negotiable truth gate:

> A target may enter semantic evaluation only when its **entire exact target truth is fully revealed, readable, unique, and reliably aligned**. Missing, absent, partly revealed, still-hidden, unreadable, ambiguous, conflicting, or otherwise uncertain truth means **null score / Accuracy unknown** for the whole target.

Do not score a convenient known subspan of a partly unknown redaction and present it as target accuracy. Do not infer missing words with an LLM, geometry guess, source familiarity, or the model prediction itself.

Prediction and evaluation remain separate:
- the predictor receives only frozen redacted-only context;
- reference text, reference-derived facts, rubric annotations, judge outputs, prior guesses, and evaluation feedback must never enter prediction input;
- the evaluator consumes a frozen prediction only after the prediction attempt is complete.

Scope remains text reconstruction only. Images, tables, and wholly withheld pages are outside this rubric.

## 2. Intended inputs

A future evaluator should consume immutable, versioned evidence equivalent to:

1. **Target identity**
   - project ID;
   - target ID and target version;
   - redacted document/canonical versions and hashes;
   - experiment condition and run identity.

2. **Prediction attempt**
   - frozen prediction text when status is SUCCEEDED;
   - attempt status;
   - requested model ID;
   - separately recorded provider model identity when available;
   - prompt ID/version;
   - settings;
   - request/response hashes;
   - model configuration provenance.

3. **Reference mapping**
   - mapping ID/version;
   - exact revealed target quotation;
   - source locator;
   - canonical/reference hashes and versions;
   - alignment evidence;
   - scoreability state.

4. **Rubric version**
   - exact rubric identifier;
   - source-fact-record version;
   - evaluator/judge version if automated.

The rubric must not manufacture missing provenance.

## 3. Mandatory pre-evaluation gate

Before facts are compared, check:

- prediction attempt is frozen;
- reference mapping belongs to the exact target/version;
- reference mapping is the approved scoreable state;
- complete revelation is true;
- readability and reliable alignment are established;
- exact target quotation exists;
- target truth is not partial, absent, hidden, ambiguous, conflicting, or unsupported.

If any item fails:
- set target semantic score to null / Accuracy unknown;
- record the reason;
- do not build a partial source-fact record from the uncertain span;
- preserve the prediction outcome independently.

A successful prediction can therefore have unknown accuracy. Conversely, a scoreable reference can exist while a prediction attempt is refusal, timeout, error, or malformed; those attempt states still do not become semantic factual zeros.

## 4. Reference-only source-fact record

For every scoreable target, create and freeze a **reference-only source-fact record before inspecting the model prediction**.

Recommended fact fields:

- `fact_id`: deterministic ID within the target/rubric version;
- `reference_proposition`: concise proposition supported by the exact target quotation;
- `reference_quote_locator`: exact source substring or character/token span;
- `critical_dimensions`: actor, action, object, recipient, direction, negation, date/time, quantity/unit, location, modality, attribution, condition, or other material relation dimensions;
- `dependency`: optional relationship to another fact when one proposition depends on another;
- `notes`: narrowly scoped annotation guidance, not prediction-specific commentary.

The source-fact record should represent propositions, not isolated keyword overlap. A person's name alone is not equivalent to "that person performed action X on object Y."

Facts must not be split so finely that one semantic statement receives duplicate credit for every word. Conversely, materially independent details such as date or quantity may be represented separately when their correctness matters to the target's meaning.

## 5. Proposed fact-level evidence categories

These categories are proposed evidence labels, not numeric scores.

### 5.1 SUPPORTED

A reference fact is **SUPPORTED** when the prediction asserts the same proposition with materially equivalent meaning and no contradiction on a critical dimension.

Examples:
- "authorized 12 aircraft" vs. "approved a dozen planes" when actor, action, object, quantity, recipient, time, and modality remain equivalent;
- syntactic reordering that preserves semantic roles;
- ordinary abbreviation or surface-form variation that does not change identity or meaning.

Lexical overlap is not required, and lexical overlap alone is not sufficient.

### 5.2 MISSING

A reference fact is **MISSING** when the prediction does not assert enough information to establish the proposition and does not directly contradict it.

Examples:
- reference: "Agent Cedar authorized the transfer to Unit Blue";
- prediction: "Agent Cedar."

The name is present, but the action and recipient relation is absent.

A missing fact is an omission/coverage shortfall, not automatically a contradiction.

### 5.3 CONTRADICTED

A reference fact is **CONTRADICTED** when the prediction asserts a materially incompatible proposition.

Dimensions requiring explicit contradiction checks include:
- actor/action/object role reversal;
- recipient/source direction;
- negation;
- changed quantity or unit;
- changed date or time;
- changed location;
- possibility/permission versus completed action;
- attribution or speaker/source changes;
- conditional versus unconditional action.

Examples:
- "Agent Cedar sent the package to Unit Blue" vs. "Unit Blue sent the package to Agent Cedar";
- "may approve" vs. "approved";
- "12 paper stars" vs. "20 paper stars";
- "July 7" vs. "July 8."

A broad topic match does not erase a contradiction.

### 5.4 UNSUPPORTED

An **UNSUPPORTED** assertion is a prediction claim that is not established by the exact target reference.

Example:
- reference: "Agent Cedar delivered the package.";
- prediction: "Agent Cedar delivered the package and received a cash bonus."

The delivery may be supported while the bonus claim is unsupported.

Unsupported does **not** automatically mean historically false. The target reference may simply not establish it. Keep unsupported additions separate from direct contradictions unless the reference actually conflicts with them.

## 6. Hedging, alternatives, repetition, and attribution

### Alternative guesses

A list containing the correct answer among alternatives must not be treated as a clean assertion of the correct fact.

Example:
- reference: "The courier was Agent Cedar.";
- prediction: "The courier was either Agent Cedar or Agent Birch."

Proposed treatment:
- the exact identity fact remains missing/incompletely asserted;
- the alternative claim is tracked separately as unsupported or ambiguous prediction content;
- do not award duplicate or list-based credit merely because one alternative matches.

### Hedging

Preserve meaningful modality. "Probably," "may," "possibly," "reportedly," and similar qualifiers can change the proposition. Human instructions must distinguish harmless linguistic softness from material uncertainty about the target fact.

### Repetition

Repeated restatement of the same claim supports a fact at most once. Repetition must not multiply evidence or compensate for a missing independent fact.

### Attribution

Preserve who said or claimed what.

Reference:
- "Director Vale said the committee approved the request."

Prediction:
- "The committee approved the request."

The prediction omits attribution and changes a reported statement into an unqualified assertion. The attribution-bearing fact is not fully supported.

## 7. Prediction-attempt states are separate from semantic evidence

Future evaluator logic must preserve these distinctions:

| Attempt outcome | Semantic treatment |
| --- | --- |
| SUCCEEDED | Compare only if target truth is scoreable. |
| REFUSED | Nonanswer/refusal; no semantic factual zero. |
| TIMEOUT | Technical/ambiguous execution outcome; no semantic factual zero. |
| ERROR | Technical failure; no semantic factual zero. |
| MALFORMED | Protocol/output failure; no semantic factual zero. |

A refusal or timeout may reduce completion/recovery rates in later reporting, but that is a different channel from semantic agreement.

A failure must not disappear from reporting simply because it lacks a numeric semantic score.

## 8. Recommended evaluator evidence record

This is a recommendation for future Task 6 design, **not an approved contract change**.

Per target/evaluation, record:

- target ID/version;
- attempt ID/status;
- mapping ID/version/status;
- rubric version;
- source-fact-record version;
- evaluator/judge version;
- for each reference fact:
  - fact ID;
  - reference proposition;
  - evidence label: SUPPORTED / MISSING / CONTRADICTED / NEEDS_REVIEW;
  - prediction excerpt when available;
  - rationale/evidence;
- unsupported prediction assertions;
- unresolved judge disagreement;
- process status;
- score status;
- numeric score field only if an independently approved D04 mapping later exists;
- explanation for null/unknown.

Do not force uncertain human or automated judgments into a definitive category; preserve NEEDS_REVIEW/disagreement.

## 9. Qualitative target interpretation before numeric scoring is approved

Until D04 is approved, Task 6 should be able to report evidence without inventing a numeric accuracy score.

Permissible proposed qualitative summaries include:
- all reference facts supported, no material contradiction observed;
- incomplete: one or more reference facts missing;
- contradicted: one or more material reference facts directly contradicted;
- mixed: supported facts plus omissions and/or unsupported additions;
- needs review: evaluator/human disagreement or unresolved semantic ambiguity;
- Accuracy unknown: truth is not fully scoreable;
- technical nonanswer: refusal/timeout/error/malformed.

These are proposed research labels, not gold categories and not approved score bands.

## 10. Aggregation requirements

R09/DEC-003 require eventual target, document, and model-level reporting. D06 has not approved numeric weighting.

### Target level

Report at minimum:
- scoreability/unknown state;
- attempt outcome;
- fact evidence counts or sets;
- contradictions;
- unsupported additions;
- qualitative review state;
- numeric score only if D04 later approves one.

### Per-document per-model level

For each model/document/condition, report separately:
- total targets;
- verified-eligible targets;
- unknown/null truth targets;
- technical nonanswers/failures;
- completed successful predictions;
- targets needing review;
- semantic evidence only over an explicitly declared eligible set.

Do not convert unknown truth to zero.

Do not present a "completed-answer mean" as total recovery performance without also reporting missing/failed attempts.

### Per-model cross-document level

A cross-document model summary must record:
- model identity/version/configuration evidence;
- experiment condition;
- prompt/settings version;
- common eligible target/document set;
- missing outcomes;
- null/unknown counts;
- document inclusion filters;
- rubric/judge versions.

Cross-model comparisons should use a declared **common eligible set** where comparability is claimed.

No cross-model blended accuracy and no hidden model-specific denominator.

### Empty denominator

If the eligible verified denominator is empty, the verified score is null / unavailable.

## 11. Benchmark design in `evaluation_cases.json`

The companion synthetic dataset is deliberately adversarial and proposal-only.

It contains cases for:
- semantic paraphrase;
- name-only versus complete predicate;
- actor/recipient reversal;
- negation;
- altered date;
- altered quantity;
- altered unit;
- possibility versus completed action;
- unsupported additions;
- alternative guesses;
- repeated claims;
- attribution;
- missing quantity/date facts;
- fully hidden reference;
- partly revealed reference;
- misaligned/ambiguous reference;
- refusal;
- timeout;
- malformed response;
- technical error.

Each case declares:
- synthetic reference scenario;
- reference eligibility state;
- attempt outcome and prediction;
- proposed source-fact record;
- proposed expected evidence sets;
- expected qualitative/null state;
- rationale;
- explicit pending-research-validation status.

The file is **not human gold data** and contains no numeric score expectations.

## 12. Human benchmark procedure proposal

### 12.1 Annotation preparation

Before showing predictions to raters:
1. verify the target is scoreable;
2. freeze the exact target reference quotation;
3. create the source-fact record from reference only;
4. assign anonymized target/example IDs;
5. freeze rubric and annotation instructions.

Raters should not know model identity where practical.

### 12.2 Independent rating

Use multiple qualified human raters independently on the same written rubric.

Each rater should mark:
- fact-by-fact SUPPORTED / MISSING / CONTRADICTED / NEEDS_REVIEW;
- unsupported prediction assertions;
- material attribution/modality/quantity/date issues;
- whether the prediction includes unresolved alternatives or hedging;
- whether evaluator evidence is insufficient to judge.

Retain individual ratings rather than replacing them immediately with consensus.

### 12.3 Adjudication

When raters disagree:
- retain the original disagreement;
- use an adjudicator applying the same frozen rubric;
- record the adjudication rationale;
- do not silently rewrite the underlying individual labels;
- distinguish rubric ambiguity from annotator error.

Cases with unresolved disagreement should remain review/uncertain rather than being forced into a gold label.

### 12.4 Development, calibration, and held-out sets

Before any tuning:
- split synthetic/authorized examples into development, calibration, and held-out sets;
- keep near-duplicates and related document/release families together;
- prevent leakage from held-out evaluation into prompt/rubric/judge tuning;
- version the split.

The designated Research Human must approve composition and use before scientific claims.

### 12.5 Validation priorities

Prioritize failure modes that could create false high scores:
- actor/object reversal;
- negation;
- quantity/date errors;
- name-only answers;
- correct answer buried in alternative lists;
- topic overlap without the relation;
- unsupported additions;
- attribution loss;
- partial/unknown truth accidentally scored;
- refusal/timeout accidentally treated as zero;
- evaluator sensitivity to prompt/order/model-brand metadata.

Also measure paraphrase fairness so semantically equivalent wording is not systematically under-scored.

### 12.6 Variability and uncertainty

Validation should measure:
- inter-rater agreement/disagreement;
- adjudication frequency;
- evaluator-versus-human disagreement;
- false-full-match rate;
- false-contradiction rate;
- paraphrase fairness;
- unknown-state handling;
- rerun/order sensitivity where applicable.

No acceptance threshold is approved in this proposal.

## 13. Outstanding research decisions

### D03 — automatic truth confirmation

Still open scientifically.

Questions requiring Research Human approval/validation include:
- what empirical evidence is sufficient to validate automatic truth confirmation beyond the synthetic DEC-022 fixture boundary;
- sample composition and real-document authorization;
- acceptable false-confirmation behavior;
- treatment of OCR/raster or other currently unsupported documents.

Task 3 software behavior and synthetic pairing do not settle D03.

### D04 — evaluator rubric and score mapping

Still open.

Requires approval of:
- final fact decomposition rules;
- final evidence taxonomy;
- contradiction/critical-error rules;
- whether and how unsupported additions affect an overall score;
- any numeric formula;
- any weights, caps, thresholds or qualitative-to-numeric mapping;
- benchmark acceptance criteria;
- evaluator/human agreement requirements.

This proposal intentionally selects none of those numeric decisions.

### D05 — prediction protocol / model roster

Still open.

Requires approval of:
- exact model roster and stable version identity;
- prompt version and settings;
- model configuration/digest evidence;
- context-window comparability;
- tokenizer/budget handling;
- attempt policy;
- nonanswer policy;
- tool/retrieval permissions;
- interpretation of pretraining exposure;
- common-set comparison protocol.

Task 4 mock infrastructure and provider name equality do not establish D05.

### D06 — aggregation and weighting

Still open.

Requires approval of:
- target weighting within documents;
- document weighting across a model;
- treatment of partial completion;
- common-set requirements;
- how to report technical failures alongside semantic evidence;
- uncertainty reporting;
- whether any secondary coverage/recovery metric accompanies semantic agreement.

Until approved, report transparent counts, denominators, filters and qualitative evidence; do not invent weights.

## 14. Incompatibilities with legacy toy grading

Any earlier toy hit/partial/miss labels or percentages are not gold truth and must not be treated as validated scoring.

This rubric differs by:
- requiring complete scoreable truth first;
- evaluating propositions and relation details, not lexical overlap alone;
- separating omissions, contradictions, and unsupported additions;
- separating technical attempt outcomes from semantic evidence;
- preserving disagreement/review;
- refusing to map evidence to an approved numeric score before D04.

## 15. Acceptance boundary for this proposal

This proposal is successful if it gives future evaluator and human-validation work a versioned, auditable set of evidence concepts and adversarial scenarios while preserving all current null/unknown rules.

It does **not** authorize:
- Task 6 evaluator implementation;
- a numerical accuracy formula;
- verified scoring;
- real model inference;
- model downloads;
- private or real research datasets;
- deployment;
- scientific-method approval.

Next receiver: Lead/Architect for scope review and any separately authorized future Research Human validation or Task 6 packet.
