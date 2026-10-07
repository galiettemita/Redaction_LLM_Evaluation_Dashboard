# Research method

**Status:** source-aligned requirements and proposed method from B1 sections 7-12. No evaluator, dataset, numerical cutoff, measured accuracy or human approval has been established in this repository.

## Confirmed requirements

Assess meaning and details: actor/action/object, relation direction, time/place, quantity/unit, negation, possibility vs completion, conditions and attribution. A topic match is not a complete reconstruction. Preserve source uncertainty; matching a government statement does not establish historical truth.

Prediction may run without a reference. A verified target score requires the entire target's revealed, readable, reliably aligned reference. Missing, partial or uncertain reference produces null score / Accuracy unknown. Do not infer unknown words, score only the convenient part and present it as full accuracy. Unknowns are excluded from verified denominators and counted.

## Proposed evaluation sequence

1. Check scope and scoreability; stop with unknown/review status when necessary.
2. Build and freeze a reference-only fact record with exact quotations before inspecting model answers.
3. Separate the prediction's assertions, possibilities, alternatives and omissions; hide model identity from judges where practical.
4. Compare whole relations and details; no duplicate credit for repetition or a list that includes the answer.
5. Record supported facts, missing facts, contradictions and unsupported additions separately. Unsupported is not automatically false.
6. Apply only an approved versioned mapping to labels/scores; preserve unresolved disagreement as review, not a forced verdict.

The toy's hit/partial/miss labels and percentages are not gold data. A single similarity number or one uncalibrated judge is not validation. Candidate metrics, critical-error rules and numeric mapping remain D04.

## Proposed benchmark and validation

Use authorized, checked text pairs. Qualified humans apply the same written rubric; retain independent ratings and adjudication. Separate development, calibration and held-out sets; keep related releases and near-duplicates together. Evaluate false full matches, paraphrase fairness, unknown handling, order/brand/prompt-injection sensitivity, rerun variability and error attribution. Report uncertainty. Research approval must set sample composition and acceptable bounds before tuning/testing claims.

The known synthetic case contrasts 'X approved a dozen planes to Y in July' with the reference 'X authorized 12 aircraft to Y in July'. Test role reversal, negation, altered numbers/month, mere topic overlap, unsupported additions and partial truth. These are design fixtures, not measured results.

## Protocol and aggregation

D05 must specify roster, context, tool permissions, prompt/version, attempt count and nonanswer policy. Proposed first condition is document-only. Retrieval-assisted conditions remain separate and unapproved. Prevent reference leakage, do not silently truncate/substitute models, and never retry until a correct answer is obtained. Training-data exposure remains a possible confound.

R09 requires target/document/model scores. D06 proposes equal target weight within each model/document and equal document weight across that model's comparable documents. Compare the same eligible target set; disclose unavailable results. Empty denominator gives no verified score. No cross-model blended accuracy. Errors/refusals/pending review are not semantic zeros under the proposal. A completed-answer mean is not total recovery rate. Attempts, model versions, rubric versions and conditions must stay distinguishable.

## Review ownership

The Research Agent drafts and analyzes; the named research human approves. Changes affecting scoreability, truth extraction, rubric, benchmark split, thresholds, aggregation or experimental comparability require that review plus downstream impact analysis. A merged document or agent consensus does not create empirical validity. Publish no real benchmark data into the public repository until its sharing permission is established.
