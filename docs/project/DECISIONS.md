# Decision register

Baseline: [MASTER_SPEC.md](MASTER_SPEC.md), imported 2026-10-06. Epoch E0072.
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

| DEC-020 | The owner advances the **first MVP checkpoint from October 14 to October 12, 2026**. The same previously approved MVP scope, zero-additional-spend rule, independent QA/Research reviews, reference-null protections and human approval gates remain. This is a target date, not guaranteed delivery or blanket permission to code, merge or deploy. | Explicit owner direction on 2026-10-08. Supersedes the **date only** in DEC-018/019 and the prior roadmap. Affects plans, design, state, agent guidance and the next task schedule; no scoring-method decision changed. |

| DEC-021 | Owner approves RL-MVP-003 Correction 01: require both available non-boundary anchor sides to agree with global alignment; do not let geometry override conflicting textual evidence; preserve exact target-edge whitespace or leave truth unknown; refine only the reference-alignment callable interface to accept a **trusted existing DocumentVersion** and verify project, reference role, version ID and SHA-256 against reference PDF bytes. Require conservative document-wide context coherence and trustworthy pairing; if the stateless layer cannot establish them, return unconfirmed, not guessed truth. No contract schema change, numeric threshold, scientific D03 approval, or new task authorization. | Explicit owner approval on 2026-10-08 following independent QA FAIL and Research CHANGES_REQUESTED on Task-3 candidate `931fb1c`. Affects only `reference.py`, `test_reference.py`, Task-3 Backend handoff, and future callers. Existing DocumentVersion remains unchanged; future persistence must authenticate record provenance/pairing. New exact-SHA QA/Research review required; no merge/Task 4. |

Source B1 is identified in MASTER_SPEC. These IDs normalize previously stated requirements; they do not approve new numeric methods.

## Checkpoint-specific decision amendments

| ID | Decision | Status / effects |
| --- | --- | --- |
| DEC-022 | For the October 12 synthetic-only demonstration, permit a trusted test-fixture manifest/registry of immutable redacted/reference pairs and hashes, accessible only through a trusted bootstrap/resolver; require full two-sided text evidence and exact spans or null. Unregistered/user-uploaded references remain NOT_SCOREABLE pending a separately authorized authenticated provenance/pairing system. | **APPROVED by product owner on 2026-10-08 (explicit yes).** [Scoped implementation packet](task_packets/RL-MVP-003-TRUSTED-SYNTHETIC-CORRECTION.md). Only byte-hash-pinned synthetic pairs can pass the checkpoint fixture-pairing gate; arbitrary uploaded references remain unknown/null while prediction remains allowed. This does not approve scientific D03 validation, real-document provenance, extra costs, merge, Task 4 or deployment. |

## DEC-023 — Automatic experimental evaluation and controlled demonstration

**Status:** APPROVED product direction / delegated experimental engineering; not scientific or institutional approval. Effective epoch E0072. Recorded UTC: 2026-11-05T16:14:01Z. Proposer/accountable integrator: Codex Engineering Lead.

**Human authorization evidence:** product-owner clarification in the active completion conversation on 2026-11-05: finish autonomously using genuine models, compute clearly labeled experimental accuracy before formal scientific validation, use independent agents/review and provide a working link. This is the product-safe substance of that direction; no private transcript is published. [Completion design](../superpowers/specs/2026-11-05-experimental-product-completion-design.md) and [plan](../superpowers/plans/2026-11-05-experimental-product-completion.md) record the bounded approach. R01–R12 remain controlling; eventual commercial multi-model and validated semantic-evaluation requirements remain incomplete.

**Old rule:** DEC-022 restricts scoreable reference evidence to pinned synthetic registry pairs; numeric scoring formula/weights remain unapproved under DEC-012/014 and D04/D06; RL-OPS-002 reserves public deployment/distribution to owner approval.

**New bounded rule:** add a separate experimental channel for user-supplied matching reference PDFs processed by the qualified isolated worker. Only unique, complete, readable, reliably aligned exact target spans may produce an experimental number. Provenance is `USER_SUPPLIED_EXPERIMENTAL`; no promotion to verified truth. `score_status = EXPERIMENTAL` may carry `experimental_score`; `verified_score = null` and verified `truth_status = UNKNOWN` remain mandatory. Missing, partial, unreadable, conflicting, ambiguous, mismatched or unprocessed truth stays null / Accuracy unknown. Display `EXPERIMENTAL — NOT SCIENTIFICALLY VALIDATED` and the method/denominators/limitations.

The owner delegates engineering selection/versioning of experimental weights and contradiction caps. Method `experimental-text-agreement-v1`, evidence schema `experimental-text-agreement-evidence-v1`, scale `0–100 text agreement`: token F1 40%, ordered-token agreement 25%, character-trigram F1 20%, critical-detail agreement 15%; normalized exact match returns 100; negation mismatch caps at 35; quantity/date mismatch caps at 60; tighter cap wins; round to one decimal. Report subscores and warnings. Document agreement uses equal scored-target means per exact model/configuration; model agreement uses equal scored-document means over a declared compatible set, with eligible/scored/unknown/excluded/technical counts and null empty denominators. This lexical agreement heuristic is not validated semantic accuracy, a probability, a recovery-rate denominator or proof of historical truth. D03–D06 remain open for verified/scientific claims.

Enable only the installed integrity-pinned `qwen2.5:1.5b-instruct-q4_K_M` for this pass. Genuine provider output must be persisted and technical failures distinguished; rule-based demo output cannot stand in for inference. Preserve redacted-only inputs, one-shot attempts, immutable provenance and side-effect-free GET/reconnect. No new paid model or private-data permission.

The working-link authorization is restricted to an owner-only authenticated temporary HTTPS ngrok demonstration backed by a synthetic-only local workspace and a reviewed loopback gateway. Application/Ollama remain loopback-only; gateway accepts only configured exact Host/HTTPS Origin, enforces authenticated access and preserves upload/framing/security bounds. Disable tunnel inspection; keep credentials/configuration/hostname outside Git. Credentials must not be shared with other researchers. This is not multi-user authorization, general public distribution or permanent hosting; availability depends on the awake Mac and running local services.

**Supersession:** supersedes DEC-022's synthetic-registry-only restriction solely for this explicitly labeled experimental channel; verified synthetic-registry behavior is preserved. Supersedes prior numeric-method prohibitions in DEC-012/014 and historical task/API records solely for these versioned experimental defaults; scientific D03–D06 approvals are not granted. Satisfies RL-OPS-002's owner-deployment gate solely for the described authenticated owner demonstration. All other R01–R12/DEC-001–022 protections, private/institutional data gates, no-paid-resource rule and unrelated deployment/distribution gates remain. Older records describe historical scope, not a competing current authorization.

**Affected consumers/contracts:** Backend, experimental evaluation, Frontend, QA/security and Lead. [API v0.3](API_CONTRACT_V0_3.md); [RL-EXP-015](task_packets/RL-EXP-015-EXPERIMENTAL-EVALUATION.md) (plan Tasks 2–4), [RL-UX-016](task_packets/RL-UX-016-EXPERIMENTAL-WORKSPACE.md) (Task 5), [RL-LINK-017](task_packets/RL-LINK-017-CONTROLLED-DEMO.md) (Task 6, including explicit v2 worker image requalification). Exact-candidate independent engineering/experimental-semantics reviews and genuine/browser acceptance remain required; agents cannot self-approve scientific or institutional gates.

**Compatibility / benchmark effect:** additive migration with pre-migration backup, immutable reference/evaluation identities and original legacy validators. No historical score rewriting, benchmark claim or calibrated threshold. v0.3 browser/server identification changes together; v0.2 persisted data remains readable. A rebuilt `pdf-worker-v2` image must be independently qualified before live v2 work; prior v1 qualification is not inherited.

**Effective revision / rollback:** the commit containing this E0072 record, based on live main `cb0fa4f1242ae8bf12afb084bc9475017040b784`. Revert experimental task commits to disable the new channel; preserve existing immutable predictions/evidence, use verified pre-migration backup recovery when needed, and stop the task-owned tunnel/gateway to remove exposure. No new expenditure, private-data transfer, visibility change or scientific approval is implied.

## E0036 implementation authorization (not scientific approval)

The owner approved RL-MVP-004 Correction 01's scoped expansion and separately authorized integration of exact corrected implementation `b9ce8182751f26109fbd857bcb8d909720bafd13` after independent QA/Research review and reconciliation. PR #4 merged as `8f4d2f18aa2c565e3228d4f3568a2bd8c1714b0f`. This is an implementation/integration authorization, **not** a new DEC-numbered product-method change; DEC-001..022 remain in effect. The trust boundary is internal-only with no authenticated upload API. D03/D05, model/license, data/vendor and deployment approvals remain open. No Task 5, inference, downloads or spending authorized.

## E0037 Task 5 research-only authorization (not scientific approval)

On 2026-10-09, the owner explicitly approved RL-MVP-005 strictly for a research proposal: `docs/project/research_proposals/RL-MVP-005-evaluation-rubric.md`, `tests/fixtures/evaluation_cases.json` (synthetic only), and one unique Research handoff on an isolated branch. The [approved packet](task_packets/RL-MVP-005-RESEARCH-PROPOSAL.md) defines acceptance and stops. No evaluator implementation, merge of Research artifacts, real inference, model downloads, spending, Task 6, deployment or scientific-method approval. D03/D04/D05/D06 remain open. This is a task authorization, not a new DEC-numbered methodological decision.

## E0038 Task 6 implementation authorization (not scientific-method approval)

On 2026-10-09 the owner explicitly approved bounded RL-MVP-006 synthetic/mock-only evaluator evidence and target/document/model summary code: six proposed source/test files, necessary scoped changes in contracts.py and test_contracts.py, and one unique Backend handoff. The owner requires the final [Task 6 packet](task_packets/RL-MVP-006-EVALUATOR-SUMMARIES.md) on main before Codex work and fresh independent QA and Research review. No D03/D04/D05/D06 scientific approval, numeric score formula/weights/thresholds, live model inference, installation/download, new unapproved dependencies, merge, Task 7, spending or deployment. This is task execution authorization, not a DEC-numbered methodological amendment.

## E0045 Task 7A PDF isolation planning amendment

Owner approved documentation publication only of [the 007A security amendment](task_packets/RL-MVP-007A-PDF-ISOLATION-AMENDMENT.md). Accept arbitrary PDFs for validation, propose Podman VM without host shares/network, and require preservation of Task 4 byte-derived source authority without reparsing on host. Extra interface files are proposed but not implementation-authorized. Institutional data permission and all Task 7 code/install/model/deploy gates remain open.

## E0044 Task 7A planning defaults and packet publication (not implementation)

Owner approved publishing [RL-MVP-007A planning packet](task_packets/RL-MVP-007A-PORTABLE-FOUNDATION.md) and proposed macOS Apple Silicon-first local/loopback delivery defaults: 25 MiB per PDF, 100-page limit, one concurrent document job, 60-second parse budget, minimal five-table schema direction, retain uploads/evidence until authorized deletion, 24-hour incomplete-upload cleanup, seven-day content-free logs, and pre-migration backups. This authorizes packet publication only; no code, dependency installs, schema migration on live data, real inference, spend, deployment or Task 7B/C/P/D. D07 and scientific D03–D06 approvals remain open.

## E0043 Task 7 portable local delivery planning decision (not implementation authorization)

Owner selected a **portable, local, recipient-self-hosted web application** for Task 7: a recipient must be able to receive a release/project package, set up and run both frontend and Python backend on their own compatible computer, and access the application from their own browser without relying on the owner's MacBook, machine-specific absolute paths, credentials, filesystem or running server. Require documented supported operating systems and architectures, pinned reproducible dependencies, portable migration/bootstrap and local data isolation, safe setup/start scripts or launcher, all-offline-after-prerequisite-install behavior when feasible, and independent clean-second-device acceptance tests. Model artifacts/runtimes and licenses are independently approved requirements: don't promise real inference on hardware without a compatible authorized model. No public hosting, spending, model download/inference, private data, Task 7 code, deployment, or D03–D06 approval authorized by this decision. Design the smallest viable packaging approach; do not assume Docker, installer technology or support for every OS without an explicit feasibility decision.

## E0042 Task 6 owner-approved integration (not scientific approval)

Owner authorized exact reviewed implementation `0a0ce9e07c48aa04df4981a56d4f9ff47c8696dc` and Backend publication head `fa2669c2dcb4dae3d69d214d4656369cbad0ed31` after QA scoped PASS `effcc0205a54352efb7d75a4a16ebfc99fb53161` and Research scoped PASS `02c34c7b26d7c4e2a7f04ca59954525e19fe14f5`. Lead merged [PR #5](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/5) at `2d825ee34409bfb0f9782969680780d8d9bf2680`. No Task 7, numeric scoring, real inference, download, spending, deployment, or D03–D06 scientific approval. Existing synthetic/mock/unknown/null constraints remain.

## E0041 Task 6 Correction 03 authorization (not scientific approval)

Owner approved [Correction 03](task_packets/RL-MVP-006-CORRECTION-03.md): Backend may change evaluation_store.py and test_evaluation_store.py plus one handoff to enforce canonical member ordinal/subject binding on read, reject corruption without database mutation, TDD and full tests, fresh exact-SHA QA/Research. Correction 02 Research scoped PASS, QA CHANGES_REQUESTED at `8b9ec30`. No merge, Task 7, inference, downloads, spending, deployment or D03–D06 approval.

## E0040 Task 6 Correction 02 authorization (not scientific approval)

Owner approved six-file Task 6 Correction 02 and one Backend handoff: outcome-independent common eligible target/reference truth, truthful all-excluded summaries with v3 conditional nullable evaluation-method provenance, exact TDD/regressions, legacy v2 reopen, and fresh QA/Research. See [owner-approved Correction 02 packet](task_packets/RL-MVP-006-CORRECTION-02.md). No merge, Task 7, model/inference, download, spend, deployment, scientific D03-D06 approvals.

## E0039 Task 6 Correction 01 authorization (not scientific approval)

On 2026-10-11 the owner authorized the expanded bounded Task 6 Correction 01 file scope from Codex's read-only preflight, including new evaluation_store.py/test_evaluation_store.py and scoped Task-4 store.py/test_worker.py, plus four Lead safeguards: atomic persistence, trusted-caller/project authorization limits, explicit unvalidated source-fact provenance, and realistic distinct-run comparability tests. [Correction packet](task_packets/RL-MVP-006-CORRECTION-01.md) is authoritative. No merge, Task 7, inference, downloads, spending, deployment or human D03–D06 approval granted.

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

## E0064 — RL-MVP-007D Gate A read-only feasibility authorization

On 2026-10-13 (America/New_York), the product owner approved publication of [RL-MVP-007D-QUALIFICATION-01](task_packets/RL-MVP-007D-QUALIFICATION-01.md) and Gate A read-only QA/security feasibility inspection, PDF runtime/dependency and license inventory, clean-recipient requirements and proposed Gate B acceptance plan, scoped task handoffs, and independent Research review. **No code changes, dependency installs/downloads, tests, PDF/VM/container runtime operation, private data, model inference, paid calls, spending, deployment, merge or Gate B execution are authorized.** Gate A completion is not scientific validation or final recipient acceptance. Lead must obtain separate owner approval for an exact Gate B execution packet.

## E0065 — owner-authorized emergency experimental real-inference vertical slice

Owner approved on 2026-10-13 (America/New_York) [RL-MVP-007D-EMERGENCY-REAL-INFERENCE](task_packets/RL-MVP-007D-EMERGENCY-REAL-INFERENCE.md) and [API v0.2](API_CONTRACT_V0_2.md) for narrowly scoped isolated-branch code/test implementation, conditional zero-cost pinned Podman/Ollama/model acquisition, PDF-worker qualification and genuine **synthetic-only** local inference **only after** verified sources/full hashes/licenses, hardware compatibility and sufficient disk headroom. No blanket license/data clearance was granted. Previous disk preflight ~3 GiB free is a hard pre-install reassessment gate; no user-file deletion or unapproved workaround. QA/security and Research independently review exact candidate; owner must separately authorize merge. No private PDFs, paid calls, public deployment, scientific score/method changes or Task 3/6/database-schema changes. v0.1 remains unchanged until separately approved v0.2 integration. E0064 Gate A history preserved; Gate A's read-only restriction is superseded **only for this explicitly bounded emergency task**. No claim of actual installation, inference, scientific validation, recipient acceptance or release.

## E0066 — owner-approved code-only emergency amendment
Owner approved [Task 7D Code-Only Amendment 01](task_packets/RL-MVP-007D-EMERGENCY-CODE-ONLY-AMENDMENT-01.md). Permit isolated-branch code changes and mock/synthetic automated tests within existing E0065 file scope, despite failed disk gate. Forbid downloads, installations, Podman/VM execution, real PDF processing, genuine inference, costs, deployment and merge. Maintain original runtime storage/integrity/license gates, null scoring and independent reviews.

## E0067 — owner-approved grouped correction packet publication (execution not yet authorized)

On 2026-10-27, owner approved preparation/publication of [RL-MVP-007D E0066 Correction 01](task_packets/RL-MVP-007D-E0066-CORRECTION-01.md) for four QA findings: crash-safe Ollama ownership, before-mutation model ID verification, oversize-response MALFORMED classification, and complete run ID semantics. This authorization covers the **correction plan only**; Codex must confirm scope feasibility, and out-of-scope files (notably `src/redaction_lab/adapters/ollama.py`), dependencies or helpers require explicit owner amendment before implementation. Existing runtime/download/real PDF/inference/spend/deployment/merge restrictions continue. Research handoff is not yet verified. Candidate `e6669c2` is CHANGES_REQUESTED, not merge-ready.

## E0068 — Owner approves grouped Correction 01 code-only execution

Owner approved [Correction 01 execution and one-file scope amendment](task_packets/RL-MVP-007D-E0066-CORRECTION-01-EXECUTION.md) on 2026-10-27. Exactly `src/redaction_lab/adapters/ollama.py` added; permit only the three named source and three named test files plus unique Backend handoff. Implement four QA defects as one grouped TDD repair with fresh exact-SHA QA/security and Research reviews. No other path/dependency, installs/downloads, PDF processing, real inference, scientific scoring, paid calls, merge or deployment. Runtime 15 GiB gate remains.

## E0069 — Two-fix code-only correction planning approved, not execution

Owner approved preparation/publication of [RL-MVP-007D E0069 Correction 02 plan](task_packets/RL-MVP-007D-E0069-CORRECTION-02-PLAN.md) on 2026-10-29. Proposed changes limited to `src/redaction_lab/application/inference_runtime.py`, `tests/application/test_inference_runtime.py` plus one unique Backend handoff. Address macOS incompatible `/dev/fd` version attestation and lifetime-FD leak for already-exited supervisor. This **does not authorize correction execution**. Require TDD, focused/full permitted regressions and fresh exact-SHA QA/Research reviews after separately approved execution; no download/install, runtime/PDF processing, inference, spending, merge or deployment. Candidate `f244d13` remains QA CHANGES_REQUESTED; Research handoff still unverified.

## E0070 — Standing Codex-led engineering authority

On 2026-10-29 the product owner replaced repeated per-task engineering approvals with [RL-OPS-002](task_packets/RL-OPS-002-AUTONOMOUS-ENGINEERING.md). Codex may create bounded task records and autonomously plan, implement, test, independently review, correct, document, commit and normally integrate work within confirmed product and safety boundaries. This standing authority activates [E0069 Correction 02 execution](task_packets/RL-MVP-007D-E0070-CORRECTION-02-EXECUTION.md) without a separate repair approval.

This is an engineering-process authorization, not a scientific or institutional approval. Paid resources without budget, missing credentials, legal/data permission, destructive external actions, unresolved critical security risk, confirmed product-scope changes, public deployment/distribution, and human scoring/benchmark/release validation remain nondelegable gates. DEC-001 through DEC-022 and UNKNOWN/null, reference-isolation, provenance and immutable-record requirements remain controlling.

## E0071 — Task 7D code integrated; operational qualification remains open

Under RL-OPS-002, independently reviewed Task 7D branch `8f508158f453bae6a4e97a64ea43325de2bbebdb` merged through PR #7 as `9952d84afe1cf987a4626a1ebf980815fbc44a0a`. Exact corrected implementation is `11823200a17d8fca3a45885a2660b7da3d6f88ac`. This establishes only the fail-closed code pathway and API v0.2 source. Frontend v0.2 build/binding, PDF/model runtime qualification, real inference, recipient acceptance, scientific validation, private-data use and deployment/distribution remain separate gates. The dependency order is recorded in [the autonomous completion roadmap](plans/2026-10-29-autonomous-completion-roadmap.md).
