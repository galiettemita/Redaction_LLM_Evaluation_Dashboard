# Master product specification: working repository digest

**Source baseline:** owner-supplied `Redaction_Lab_Master_Product_Spec_v1.0.pdf`, 24 pages, document date 2026-10-05. **Repository import:** 2026-10-06. **Status:** planning baseline; application and evaluator not validated.

This is a source-aligned, condensed working representation, not a verbatim replacement PDF or a new research approval. Section numbers below follow the source's 22 sections. The source PDF governs unamended details; approved changes are recorded in [DECISIONS.md](DECISIONS.md). Report discrepancies rather than silently resolving them. The PDF and embedded research HTML are not published in this public repository.

Source PDF SHA-256: `17eec51971ac7020e1c383702daf53e8869736bf7e4eb868f7e82b2808c82a6d`.

`Confirmed` means the owner stated the requirement. `Proposed` means a recommended design, not an empirically validated method or selected technology. `Open` requires the relevant approval before its blocking stage. A passing software test does not establish research validity or institutional approval.

## 01. Product charter (source page 3)

**Confirmed.** Build an easy-to-use, professional, document-centered research platform that compares commercial AI predictions of hidden text with later-revealed reference text when available. Keep the main workflow understandable to a middle-school or high-school reader; this does not authorize use by minors or public access. Optional research details expose provenance and method choices.

Compare recovered meaning: actor, action, object and important details. A topic match is not complete recovery. A plausible guess is not a verified answer. The platform predicts text; it does not remove redactions, determine classification, authorize release or establish historical truth. When trustworthy evaluation conflicts with speed, preserve uncertainty.

## 02. Scope and requirement register (source page 4)

| ID | Confirmed requirement |
| --- | --- |
| R01 | Accept an uploaded redacted PDF; do not restrict users to the toy's documents. |
| R02 | Allow an optional matching unredacted or less-redacted version. |
| R03 | Reconstruct text passages only; exclude images, tables and wholly missing/withheld pages. |
| R04 | Run multiple commercial models automatically on demand; show arriving results. |
| R05 | Link each prediction to the exact target and correct reference when available. |
| R06 | Provide Redacted / Unredacted views, passage selection and model comparison. |
| R07 | Evaluate meaning and factual detail, not just matching words. |
| R08 | Unknown accuracy when truth is still hidden or not trustworthy. |
| R09 | Scores per redaction, per model and per document with counts/exclusions. |
| R10 | Professional, jargon-light interface with optional research detail. |
| R11 | Provenance, versioned evaluation, regression tests and staged readiness reviews. |
| R12 | Narrowly scoped, reviewed Codex engineering. |

Multipage PDF viewing, rendering pages for display and cross-release alignment remain in scope. Documents may contain excluded material, but that material cannot become a reconstruction target. PDF is the baseline; scanned-text support, DOCX, handwriting, languages and limits are Open (D01).

## 03. Supplied prototype (source page 5)

**Source observations, not validated research.** The toy embeds document data, page images, predictions and grades. Keep its document-centered viewer, release toggle, navigation and comparison pattern. Do not represent its stored results as fresh inference.

Its legacy document calculation is `100 * (hits + 0.5 * partials) / (hits + partials + misses)`, rounded. Do not adopt it as the new semantic metric. The source warns of imperfect page mapping, different judges/rubrics across columns and unverified AI-generated grades. Neither legacy rankings nor labels are human gold data. Historical model labels are not a current API roster.

## 04. User journey (source page 6)

Upload redacted PDF -> optionally add reference -> check uncertain passages -> choose approved models/start -> observe progress -> select a passage and inspect answers -> compare summaries.

**Proposed checkpoints.** Validate files and permissions, preserve originals, align the pair, exclude unsupported targets, freeze input/settings and cost scope, then dispatch. Redacted-only runs show predictions with unknown accuracy. Adding a reference later may evaluate existing frozen predictions without generating them again. Human intervention is for uncertain cases, not routine manual grading of every run.

## 05. Results workspace (source page 7)

Large document view and clear answer panel; preserve the selected target across release toggles, navigation and responsive layout. Click/tap pins a target; hover is optional and keyboard access is required. Do not assume identical page numbers. Disable unavailable reference viewing and explain why.

**Proposed copy:** Matches the meaning; Partly correct; Does not match; Accuracy unknown; Needs review; No answer / run failed. Distinguish reference availability, prediction outcome and evaluation status. Show each model consistently, with a short explanation and optional research details. No raw technical logs, hidden thinking traces or unsupported leaderboard claims in the primary view.

## 06. Processing and alignment (source page 8)

**Proposed contract.** Detect targets from the redacted artifact alone; give them stable IDs and versioned page coordinates. Exclude non-redactions, graphics, tables and whole-page omissions. Administrative-text inclusion is Open (D10).

Verify that releases represent the same underlying document. Account for changed pagination, inserted covers, rotation, scan size and line wrapping. Preserve exact revealed quotations and locators, not AI summaries as truth. Prefer extraction that reflects only visible content; use a separately validated transcription path only if approved.

Hidden text layers, annotations, filenames, reference-derived questions or other hints must not leak answers. Corrections create new versions; determine affected predictions/evaluations instead of overwriting history or recomputing everything.

## 07. Reference truth and unknowns (source page 9)

A target is scoreable only when fully revealed, readable and reliably aligned. Partial reference, absent reference, still-hidden text, unreadable text and uncertain mapping yield **null score / Accuracy unknown**. Conflicting references require review; unsupported targets are excluded.

Even when part of a target is known, the full target stays unknown. Separately scoring a known subspan is not enabled by this baseline. Unknown means unavailable in the supplied source, not necessarily still classified today. It is excluded from verified-score denominators and counted visibly.

Adding or correcting a reference creates a new reference/evaluation version; retain the original prediction and its date. Agreement with source content does not prove the historical account itself is correct.

## 08. Models and experimental protocol (source page 10)

**Confirmed breadth:** commercial model families, including smaller and more capable options. **Open:** exact providers/models, versions, capabilities, prices and attempts (D05).

Freeze targets, context, inputs, prompts, output shape, tools and attempt policy before comparative runs. Record provider-specific mappings. No silent truncation, model substitution or selection of the best answer after seeing truth. Distinguish refusal, blank answer, malformed response and provider error.

**Proposed first condition:** document-only, no reference or evaluator feedback in prediction context. Retrieval-assisted work is a separate, later opt-in with a versioned corpus/time cutoff; it is not authorized by a legacy '+ corpus' label. Preventing prompt leakage does not prove the model never saw the document during training. Repeated attempts must follow a declared protocol, not retry-until-correct.

## 09. Meaning-based evaluation (source page 11)

**Proposed, unvalidated sequence:** check scoreability; freeze reference-only facts with quotations; parse assertions and alternatives in the prediction; compare relations and details without duplicate credit; distinguish missing, contradicted and unsupported claims; apply an approved, versioned rubric or preserve review status.

Check actor/action/object direction; dates, places, quantities and units; negation, possibility, intention, conditions and causation; attribution and allegations. Keep model identity hidden from judges where practical. Unsupported does not automatically mean historically false. No weights, caps, thresholds or numeric score mapping are approved.

## 10. Acceptance examples (source page 12)

For the synthetic reference 'General X authorized the transfer of 12 aircraft to Country Y in July,' 'X approved sending a dozen planes to Y during July' preserves meaning. Merely discussing a possible transfer does not. Swapping sender/recipient, changing 12 to 20 or July to August, or adding negation must be detected. A topic summary or list of many possible answers is not full recovery. Added unsupported claims receive no credit. Partial truth stays unknown.

Test equivalent paraphrases, ordering, repeated sentences, brand masking and instructions embedded in an answer. These are design examples, not observed performance results.

## 11. Three score levels (source page 13)

**Confirmed:** target, document and model summaries. Numeric scores represent agreement with known content under a named method, not probability of truth, byte recovery or sensitivity. Until validation, do not present precise percentages as trusted scores.

**Proposed aggregation (D06):** equal target weight within each model/document; equal document weight within each model's selected comparable document set. Display models separately rather than one cross-model accuracy number. Comparisons use the same eligible target set, disclose incomplete/shared subsets and show counts. Empty denominator means no verified score, not zero.

Unknown, refusal, no answer, timeout, error and pending review are distinct. Completed-answer averages are not recovery rates over all requested targets. Repeat-run summaries declare attempt counts/variability; never pool incompatible model versions, conditions or scoring versions.

## 12. Validation gate (source page 14)

**Proposed process:** authorized, checked text pairs; qualified human reviewers using a common rubric; retained independent ratings and adjudication; separate development/calibration/held-out sets, keeping related releases and near-duplicates together.

Report false full matches, paraphrase errors, unknown-state handling, judge consistency, end-to-end component errors and aggregation validity with uncertainty. Research approval must define dataset composition, error bounds, score mapping and uncertainty before trusted scoring. No study or approved thresholds exist in this baseline.

## 13. Architecture (source page 15)

**Proposed:** small modular application plus durable workers, not early microservice proliferation. Responsibilities: web UI, application API, document processor, prediction workers, evaluation workers, summary logic, metadata store, protected artifacts and job coordination.

Prediction gets redacted-only input and target location, not reference access. Evaluation reads frozen predictions plus approved truth. Viewing the reference must never change prediction inputs. Stack, repository governance, hosting, authentication and infrastructure selection remain Open (D07); creating this documentation repository does not settle them.

## 14. Contracts and provenance (source page 16)

Preserve project-scoped document versions, targets, mappings, run definitions, model attempts, evaluations, summaries and review/audit events. Each has stable identity and versioned dependencies. Completed attempts/evaluations are immutable; corrections supersede them. Reference edits do not mutate unaffected predictions. Replayable method records do not guarantee identical future external-model outputs. See [INTERFACES.md](INTERFACES.md).

## 15. On-demand jobs (source page 17)

On demand with incremental results, not zero latency. Persist tasks before dispatch. Bound concurrency, retries, timeouts and spending; isolate provider failure. Refresh/reconnect restores stored state, not paid work. Do not claim exactly-once billing when remote outcomes are uncertain. Cancellation stops undispatched work; accepted requests may finish. Evaluation is independent of prediction and can be unknown or awaiting review. Stale mappings/scores must not appear current.

## 16. Security and governance (source page 18)

No institutional approval is implied. D02 requires permitted-data, vendor, storage, retention and sharing decisions. Prediction and evaluation providers may need separate permissions. Protect secrets server-side; authorize each action/project; validate and isolate parsing; treat source/prediction text as untrusted data; safely render outputs. Cover derivatives, caches, exports and backups in deletion policy. Preserve contributor attribution. UI prototypes use synthetic or explicitly authorized examples. Named human approvers are not assigned by this digest.

## 17. Verification (source page 19)

Cover scope/intake, incorrect pairing, partial truth, prediction isolation, semantic contradictions, null states, zero denominators, incompatible model sets, timeout/retry/reconnect/cancel, accessibility, cross-project access and regression. Use unit, contract, mocked integration, approved live smoke, end-to-end and frozen benchmark tests as applicable. Independent review examines evidence. Tests are future obligations, not completed results.

## 18. Staged roadmap (source page 20)

S0 baseline -> S1 reference foundations -> S2 evaluation benchmark -> S3 one-model vertical slice -> S4 evaluator validation -> S5 multi-model comparison -> S6 friendly workspace -> S7 controlled lab pilot. Each stage needs a scoped component specification and approved task plan. UI exploration with synthetic data can run earlier without settling scoring or enabling providers. No dates or universal-support promises.

## 19. Codex working agreement (source page 21)

One accountable implementer per work package; inspect actual repository state and consumers first. Define requirements, non-goals, contracts, authorized files, tests, cost/data bounds, review, rollback and stop conditions. Avoid unrelated refactoring. Compare against current integration state; independently review and rerun affected tests. Changes to truth, scoring and aggregates require research review. Merges, paid calls, migrations and deployment need approved scope. Stop for contamination, unexplained score changes or scope conflict.

## 20. Production-ready (source page 22)

Requires product usability, research validation, engineering recovery/security evidence, data governance and authorized pilot acceptance. No passing code test substitutes for semantic validity. New models, scoring rules, formats or audiences trigger the corresponding review before enabling them.

## 21. Decisions (source page 23)

D01 input support; D02 data handling; D03 reference review; D04 scoring contract; D05 trial protocol; D06 aggregation; D07 architecture/access; D08 time/budget; D09 UI production path; D10 target taxonomy. See [DECISIONS.md](DECISIONS.md) for owners-by-role and blocking gates. Unresolved choices remain unresolved. Accepted amendments record reason, impact and approval rather than rewriting history.

## 22. Handoff and source limits (source page 24)

The next product task is read-only planning: inspect the workspace, restate scope, identify relevant blockers and propose one narrow task. No application implementation is authorized by the PDF itself. Current documentation initialization is separately authorized by the owner's GitHub setup request.

**B1:** the source PDF described above. **U1/U2 in B1:** owner's product vision and text-only/three-score clarification. **H1 in B1:** supplied IARPA.html observations, not a validated benchmark. The original source date is preserved; this import is dated separately. This digest publishes no private messages, raw inputs or new empirical results.
