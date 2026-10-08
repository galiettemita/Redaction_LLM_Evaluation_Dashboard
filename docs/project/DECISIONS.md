# Decision register

Baseline: [MASTER_SPEC.md](MASTER_SPEC.md), imported 2026-10-06. Epoch E0013.
Product decision IDs `DEC-...` are distinct from the source PDF's open-decision IDs `D01`-`D10`.

## Authority

The product owner approves scope and user experience; the designated research human approves methodology; the designated lab/data authority approves data/vendor use. Lead/Architect reconciles and integrates records but cannot manufacture those approvals. A specialist recommendation or two agreeing agents is not approval.

A new user instruction can authorize work within its scope, but a chat statement not yet recorded in GitHub is not broadcast to other sessions. Record its product-safe substance, source/date and affected tasks before dependent work. Do not publish a private chat transcript as evidence in this public repository.

## Confirmed product decisions

| ID | Decision | Evidence / impact |
| --- | --- | --- |
| DEC-001 | Redacted input is required for prediction; a matching revealed reference is optional for prediction. Scoring needs fully revealed, readable, reliably aligned truth for the exact target. Uploading a reference alone is not sufficient. | B1 sections 4/7; owner's optional-input clarification. Intake, workers, evaluator, viewer. |
| DEC-002 | Text passage reconstruction only; no images, tables or wholly withheld/missing pages. Multipage display/navigation remain included. | B1 R03 and section 2; owner's explicit exclusion. Detection, fixtures, UI. |
| DEC-003 | Show scores per redaction, per document and per model. Per-document results remain model-specific. | B1 R09 and section 11; owner's three-level approval. Aggregation, UI, exports. |
| DEC-004 | Missing, partially revealed, unreadable or uncertain truth yields null score / Accuracy unknown, not zero; disclose exclusions. No full-target score from partial truth. | B1 R08 and section 7; owner's unknown-truth rule. Every scoring and display path. |
| DEC-005 | Assess meaning and important factual detail, including actor/action/object, not mere lexical overlap or a broad topic match. | B1 R07 and sections 9/10; owner's accuracy priority. Rubric, benchmark, evaluator. |
| DEC-006 | User-friendly professional viewer, release toggles, passage-linked answers and automatic on-demand results. | B1 R04/R06/R10 and sections 4/5/15. UX, orchestration. |
| DEC-007 | One visually contiguous blacked-out region that covers text is one immutable redaction target. Target discovery is automatic: users do not draw, approve or correct boxes in the normal workflow. Use independent vector-PDF and rendered-image detection, fuse candidates, validate that the region lies in text flow, and exclude images/tables/whole-page omissions. If the system cannot reliably establish supported text targets, fail processing rather than ask the user to mark them. | Product-owner approval during system design, 2026-10-06. Document processor, target identity, fixtures, UX. |
| DEC-008 | Primary comparative prediction condition uses one target per model request and the same frozen canonical redacted-document representation for every participating model. The target is specially marked; all other redactions remain hidden; prior guesses are never written back into later prompts. Baseline prediction gets no reference, evaluator feedback, web or retrieval tools. Full-document context is preferred when it fits the common approved context budget; the initial comparative baseline does not silently give different context subsets to different models. | Product-owner approval during system design, 2026-10-06. Run definition, canonical input manifest, adapters, benchmark comparability. Research sign-off under D05 is still required before comparative claims. |
| DEC-009 | Models may use knowledge already present from pretraining/parametric memory. The baseline research claim is therefore “can the model reconstruct this redaction when given this redacted document under the declared protocol,” not “is the answer logically derivable only from evidence inside the uploaded document.” Training exposure remains a confound to record, not something the system claims to eliminate. | Product-owner approval during system design, 2026-10-06. Research protocol, result interpretation, UI/reports. Research sign-off under D05 remains required. |
| DEC-010 | Reference alignment is text-first and anchor-based. Canonicalize both redacted and reference documents into token streams; globally align stable matching text, then locally use surrounding left/right token anchors around each immutable redaction target to isolate the exact newly revealed span. Page number and geometry are secondary validation evidence only. Mapping must preserve the exact revealed text and algorithm/version evidence. If the span is not unique, complete, readable and reliably aligned—or remains partly redacted—truth is unknown and score is null. No LLM may invent or repair ground truth. | Product-owner approval during system design, 2026-10-06. Document processor, ReferenceMapping, evaluation eligibility, QA fixtures. Exact automatic-confirmation thresholds and research sign-off remain under D03. |

| DEC-011 | Owner approves conservative automatic reference confirmation: only unique, complete, readable, reliably aligned exact revealed text is scoreable; repeated/ambiguous/partly hidden/conflicting mappings are null. Acceptance thresholds and research validation still pending. | Product-owner direction approved 2026-10-07; D03 specialized approval/validation pending. |
| DEC-012 | Owner approves reference-grounded fact-by-fact evaluator direction: coverage, support, contradictions, deterministic entity/date/quantity/negation checks and semantic relation/paraphrase matching. Predictor cannot solely judge itself. MiniCheck/NLI are candidates only; score formula, weights, caps, thresholds and human benchmark remain unapproved. | Product-owner direction approved 2026-10-07; D04 specialized approval/validation pending. |
| DEC-013 | Owner approves one frozen independent prediction attempt per target/model with common canonical redacted input, declared prompt/settings, no reference/web/retrieval/evaluator feedback, and pretrained knowledge allowed. Refusal, timeout and malformed answers differ from factual error. Exact model roster and protocol verification pending. | Product-owner direction approved 2026-10-07; D05 specialized approval/validation pending. |
| DEC-014 | Owner approves reporting target, document and model results with semantic agreement separate from coverage/completion and technical failures. Unknown/uncertain truth stays null and excluded from verified denominators; comparisons use declared common eligible sets. Weighting choices need research sign-off. | Product-owner direction approved 2026-10-07; D06 specialized approval/validation pending. |
| DEC-015 | Owner approves safe initial local/synthetic or explicitly authorized public-data MVP direction, no private raw documents/secrets in public repo and no external commercial-provider transfer without lab authorization. This is not Columbia data/vendor permission. | Product-owner direction approved 2026-10-07; D02 specialized approval/validation pending. |
| DEC-016 | Owner approves pragmatic modular local MVP direction: Python document/evaluation modules, lightweight API/workers, durable local persistence, simple UI; FastAPI/React/SQLite are candidate tools, not a final production stack. Engineering/lab approval still required for hosting, auth, operations. | Product-owner direction approved 2026-10-07; D07 specialized approval/validation pending. |
| DEC-017 | Owner approves a seven-day evaluation-focused working MVP with zero additional spending beyond existing subscriptions. Codex plan does not imply third-party model API credits or cloud services. No paid calls or resource provisioning authorized. | Product-owner direction approved 2026-10-07; D08 specialized approval/validation pending. |

| DEC-018 | Owner sets October 14, 2026 first checkpoint: a locally runnable smallest end-to-end version accepting a redacted and matching reference PDF, automatically handling every supported text redaction, using one real prediction model via an extensible adapter and a separate evaluation model, and displaying per-target plus document/model results. The long-term reference-optional prediction rule remains. A seven-day demo is a target, not a validated-score or zero-bug guarantee; no extra spend. | Product-owner milestone request on 2026-10-07. Proposed written MVP design and weekly roadmap are linked in CURRENT_STATE. This milestone does not approve exact model IDs, numerical rubric, code task packets, external calls or deployment. |

| DEC-019 | Owner explicitly approved the written October 14 MVP design on 2026-10-07 and requested a detailed Codex implementation plan and role-specific implementation preparation. This approves the scoped design direction only: the detailed plan still requires owner review, each coding task requires a packet, and research/data/engineering approvals remain separate. | Owner approval in Lead conversation, 2026-10-07. MVP design: docs/superpowers/specs/2026-10-07-oct14-mvp-design.md. Implementation plan: docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md (READY FOR OWNER REVIEW). |

Source B1 is identified in MASTER_SPEC. These IDs normalize previously stated requirements; they do not approve new numeric methods.

## Installed coordination rules (not research approvals)

**OPS-001:** GitHub integration-branch records are the shared operational source. PDFs and Project memory are background snapshots. A Google Doc is optional intake, not a competing technical authority.

**OPS-002:** read latest HEAD, read critical records at one snapshot, work within one task, recheck before consequential actions and delivery. No unconditional 'always in sync' claim.

**OPS-003:** one Lead integration writer; separate specialist branches and per-task handoffs; stale writes must be reconciled. Approval scope does not expand through a document.

**OPS-004:** publish observed evidence, explicit unrun tests and required acknowledgments. No fabricated tests, approvals or completed work. These rules are the operating setup requested by the owner on 2026-10-06, not automated enforcement.

## Open specialized approvals and deferred decisions

| ID | Decision | Human review role | Blocks |
| --- | --- | --- | --- |
| D01 | PDF baseline; scanned/OCR reliability, language and size limits need testing; other formats deferred | Product + engineering | S1 intake commitment |
| D02 | DEC-015 owner direction approved; institutional data/vendor permission pending | Lab / engineering | Not a completed specialist approval |
| D03 | DEC-011 owner direction approved; auto-confirmation acceptance/validation pending | Research / product as applicable | Not a completed specialist approval |
| D04 | DEC-012 owner direction approved; rubric, judge, formula and calibration pending | Research / product as applicable | Not a completed specialist approval |
| D05 | DEC-013 owner direction approved; exact roster and protocol validation pending | Research / product as applicable | Not a completed specialist approval |
| D06 | DEC-014 owner direction approved; weighting and fairness validation pending | Research / product as applicable | Not a completed specialist approval |
| D07 | DEC-016 owner direction approved; final stack, hosting, auth and operations pending | Lab / engineering | Not a completed specialist approval |
| D08 | DEC-017 zero-extra-spend rule approved; paid calls remain unauthorized | Research / product as applicable | Not a completed specialist approval |
| D09 | Simple professional UI direction approved; final styling/branding/tool deferred | Research / product as applicable | Not a completed specialist approval |
| D10 | Text-only scope approved; administrative text and retrieval/extra formats deferred | Research / product as applicable | Not a completed specialist approval |

Role holders are not yet named in this register. Do not assign responsibilities to people merely mentioned in prior messages. The owner's choice of this repository resolves its address, not all of D07.

## New decision / amendment procedure

Use `PROPOSED -> APPROVED -> SUPERSEDED` (or `REJECTED`). Give each new change a unique ID; the Lead allocates the next `DEC-...` ID during integration. Never reuse or delete an old decision.

Record: title; UTC timestamp; proposer; human approval evidence/reference and date (or 'not approved'); source requirement IDs; old rule; new rule; rationale; affected modules/contracts/tasks/tests; compatibility and benchmark effects; migration/rollback; effective revision; required consumer roles; supersedes.

Approved amendments override conflicting baseline clauses only within their recorded scope. Proposed alternatives do not override anything. Conflicting approved records require Lead reconciliation and human clarification where needed.

A critical correction first places affected work on hold in CURRENT_STATE, then receives impact review. The accepted update changes this register and the affected canonical files in one integration commit. Receivers acknowledge the new epoch in their next task handoff before resuming. An absent acknowledgment is `NOT ACKNOWLEDGED`, never presumed consent.
