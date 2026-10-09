# RL-MVP-005 — Research rubric and synthetic adversarial benchmark

**Status: OWNER-APPROVED, research-only proposal task (2026-10-09).** Owner: Research / Evaluation. Lead publishes this routing packet; Research authors proposed artifacts and a unique handoff on its own isolated task branch. This approval is **not** scientific-method approval, evaluator implementation, model inference, merge or deployment authority.

**Planning baseline:** `main` at `563cada90d9e350c1fe71acaceca9fd34ff9cbe4`, coordination epoch E0036. Refresh live default branch, HEAD, AGENTS.md, CURRENT_STATE.md, DECISIONS.md and active AGENT_HANDOFF.md before beginning and again before publication. The 2026-10-12 checkpoint remains at risk.

## Sources, prerequisites and constraints

- Owner-approved October 12 MVP implementation plan, Task 5; confirmed requirements R07–R09/R11–R12; DEC-001/003/004/005/011–014/015/017/020/022.
- Read `docs/project/MASTER_SPEC.md`, `RESEARCH_METHOD.md`, `INTERFACES.md` and Task-3/Task-4 boundaries as needed.
- RL-MVP-001 through 004 merged; Task-3 scoring truth for the October 12 demonstration is synthetic-pair-registry-only. Unregistered reference uploads remain unknown/null. No scientific D03/D04/D05/D06 approval exists.
- A reference may be absent during prediction. Verified scoring requires fully revealed, readable, uniquely/reliably aligned exact target truth; absent, partial, unreadable, ambiguous or conflicting target truth must remain **null / Accuracy unknown**.
- Scope is text targets only: no image, table or whole-page reconstruction; all three score levels remain required for eventual product implementation.
- The reference, reference-derived facts and proposed rubric must never enter the predictor's input or earlier frozen prediction.

## Objective

Produce a clearly labeled **PROPOSED** versioned experimental fact-comparison rubric and a **synthetic-only** adversarial test dataset to guide future independent evaluator design and human-method validation. The goal is transparent evidence and defensible unknown/abstention semantics—not an approved numeric accuracy formula or implementation of Task 6.

## Exact authorized output paths

1. Create `docs/project/research_proposals/RL-MVP-005-evaluation-rubric.md`.
2. Create `tests/fixtures/evaluation_cases.json` containing only original, synthetic textual examples with declared expected evidence and null/unknown statuses, not private data.
3. Create ONE unique `docs/project/handoffs/RL-MVP-005-research-<UTC>-<SHORT-ID>.md` on the same approved Research task branch.

No edits to application code, tests other than the single synthetic fixture JSON, existing contracts or canonical shared files; no dependencies, evaluator, API, UI, cloud/runtime/model setup, private/restricted datasets, commercial provider calls, costs, deployment or Task 6. If the file scope is insufficient, stop for authorization. Research branch publication is not permission to merge into `main`.

## Rubric proposal requirements

Document rubric version/proposal status, its inputs, output evidence schema recommendation (not an approved contract), traceability to complete exact target-reference quotations, rationale and incompatibilities with legacy demo grading. Propose a source-fact record frozen independently of model predictions and distinguish:
- supported reference facts and legitimately equivalent paraphrases;
- omissions/coverage shortfalls;
- direct contradictions in actor/action/object or relation direction, negation, quantities/units, dates/time, location, modality/possibility versus completed action and attribution;
- extra unsupported prediction assertions (not automatically historic falsehoods);
- hedging, lists of alternatives and refusal/nonanswers; prevent duplicate credit for repetition.
- facts that cannot be verified due to reference uncertainty or unreliable alignment, with **no target-level score**; do not score only a convenient known subspan of a partially unknown redaction.
- no semantic factual zero for timeout/refusal/error/malformed; preserve independent prediction and evaluation states.

Include an explicit separation of target-level evidence, per-document per-model aggregation requirements and per-model cross-document summary requirements. Report counts/eligible denominators and compatibility filters; propose comparable common eligible target sets and distinguish technical failure/completion from semantic agreement. Empty verified denominator => null/no verified score; no assumed weighting approval.

## Synthetic adversarial fixture requirements

Provide machine-parseable JSON with explicit version and documented top-level shape. At least one case each for: correct paraphrase, name-only versus complete predicate, reversed actor/recipient, negated action, altered date, altered quantity/unit, possibly versus actually, unsupported additional assertion, ambiguous alternative guesses, repeated claim, fully hidden reference, partly revealed reference, misaligned reference, refusal, timeout and malformed/error; add distinct contextual/attribution case where helpful.

Each synthetic case must identify source text/target scenario, proposed model prediction or technical outcome, availability/eligibility state, expected fact-level evidence (supported/missing/contradicted/unsupported), expected null or provisional review/label, and rationale. Avoid invented numerical scores, pseudo-verified percentages or leaking source-private content. Make dataset comprehensive enough to challenge relation direction and central meaning, while clearly marking expectations as **proposals pending research validation**, not human gold.

## Human validation and unresolved decisions

Propose written human annotation instructions; independent blinded raters, adjudication and disagreement retention; development/calibration/held-out split with family/near-duplicate grouping; false-full-match, paraphrase fairness, unknown-state and denominator checks; measured uncertainty and approval gates. List unresolved human research decisions D03 (truth confirmation), D04 (rubric/score formula/critical-error rules), D05 (model trial protocol/roster), and D06 (aggregation/weighting). Do not select score cutoffs or numeric weights as though approved.

## Verification and acceptance

Research must validate JSON parse/schema consistency using existing local tools where feasible, explicitly record command/output and counts; manually inspect all scenario coverage, nonleakage and null score expectations. Publish only the three authorized paths on its isolated task branch. Give baseline SHA/epoch, exact files, findings, tests run/not run, known limits, required scientific approval, next receiver (Lead) and publication commit. Do not fabricate human annotation, scientific outcomes or tests.

Lead will retrieve and review the published Research proposal and decide whether to request a revision or separately seek authorization for a future task. The October 12 deadline does not waive scientific or data/security gates.

**Stop:** no evaluator implementation, merge, Task 6, real inference, model downloads/installation, paid/API calls, new cloud resources, deployment, private data or scientific-method approval. No automatic agent messaging.
