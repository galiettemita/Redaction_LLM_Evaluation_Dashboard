# October 12 MVP Implementation Plan (DEC-020; historical filename)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Status:** OWNER APPROVED 2026-10-07; first-checkpoint date amended to October 12, 2026 (DEC-020, 2026-10-08). Tasks 1–3 merged; Task 4 approved for mock-tested adapter/worker and read-only local preflight only; Task 5+ NOT APPROVED. No real inference, model downloads, extra spend, automatic merge or deployment. No paid calls, external data transfer, automatic merge or deployment.
**Goal:** By October 12, demonstrate two PDF uploads, automatic supported text-redaction detection, exact reference alignment, one REAL prediction model, a DIFFERENT evaluation model, and per-target/document/model results.
**Architecture:** Local modular Python backend; redacted-only manifests feed a provider-neutral prediction adapter, while reference truth is isolated in a separate evaluator. Frozen attempts, versioned mappings, durable SQLite job state and a thin web UI allow later additional models without changing core contracts.
**Tech Stack:** Proposed Python 3.11+, Pydantic v2, pytest, pdfplumber/pdfminer.six, ReportLab synthetic fixtures, FastAPI, SQLite, HTTPX, local Ollama-compatible predictor, local NLI judge via Transformers, React/Vite/TypeScript. Verify licenses, hardware and exact versions in Task 0. No production stack approved.
**Spec:** docs/superpowers/specs/2026-10-07-oct14-mvp-design.md
**Baseline:** main @ 21dca206ffbebf8a8c37eb20d31f31c78078d1a9, epoch E0005; refresh before every task.

## Global Constraints

- Zero additional spend; synthetic/explicitly authorized public data only. No external model APIs, cloud provisioning, deployment or restricted document processing.
- Prediction receives only visible redacted text. No reference, hidden PDF text layers, filenames, metadata, evaluation feedback or earlier guesses.
- One contiguous physical black text box = one immutable target; every supported target receives one independent model attempt.
- Week-one scope: short English digitally born PDFs with selectable visible text and simple rectangular black text boxes. Explicitly reject unsupported scans, tables, images, missing pages and ambiguous layouts.
- Ground truth requires complete readable unique alignment; otherwise score null. Provisional demo results must say EXPERIMENTAL; verified_score stays null until human research validation.
- Distinct local prediction and evaluation models; mocks are test-only. No model/version chosen before a measured hardware and license preflight.
- Freeze hashes, prompts, settings, model versions, attempts, judge versions and mappings. A retry/reconnect must not start another paid or real attempt.
- Task branches and handoffs; independent QA; no specialist direct main edits.

## File map

pyproject.toml (deps/tests); src/redaction_lab/contracts.py (typed records and redacted-only manifest); fixtures.py (synthetic PDFs); pdf_detector.py (vector boxes and scope); canonical.py (visible text); reference.py (text alignment); adapters/base.py and adapters/ollama.py (model interface); store.py and worker.py (durable jobs); judges/base.py and judges/local_nli.py (separate judge); evaluator.py (fact checks); summary.py (aggregation); api.py (local endpoints); web/src/App.tsx, web/src/api.ts, web/src/components/DocumentPanel.tsx and ResultPanel.tsx (UI); tests/ (unit, contract, integration, adversarial).

## Review Focus — high-risk cases

- A black overlay hiding selectable text must never leak the hidden text to the predictor (Task 2).
- Repeated context phrases, wrong release or partially hidden reference must return unknown, not guessed truth (Task 3).
- Reversed actor/action, negation or wrong quantity must not earn an unqualified full match (Task 6).
- Duplicate dispatch, restart or browser reconnect must not create new attempts (Tasks 4 and 7).
- Unknown truth, refusal and timeout must not become semantic zero or disappear from denominators (Task 6).

---

### Task 0 — Environment feasibility (read-only)

**Files:** Task-scoped Backend handoff only.
**Produces:** exact OS/RAM/GPU/disk, Python/Node availability, local runtime, candidate predictor and judge IDs/licenses, context and measured latency, or BLOCKED.

- [ ] Inspect machine and installed model runtimes without spending or provisioning.
- [ ] Verify licenses, model availability and whether TWO distinct models can run locally.
- [ ] Smoke-test existing authorized local assets only; record commands, times and outputs, or NOT RUN.
- [ ] Report PASS/BLOCKED. If blocked, mocks remain tests, not a claimed live-model demo.

### Task 1 — Contracts and synthetic fixtures (RL-MVP-001)

**Files:** Create pyproject.toml; src/redaction_lab/contracts.py, fixtures.py; tests/test_contracts.py, test_fixtures.py.
**Produces:** DocumentVersion, RedactionTarget, ReferenceMapping, CanonicalRedactedDocument, RunDefinition, PredictionManifest, ModelAttempt, EvaluationRecord, SummarySnapshot, JobState; function make_synthetic_pair(case: str, output_dir: Path) -> tuple[Path, Path].

- [ ] Write failing tests: test_unknown_truth_is_null, test_prediction_manifest_has_no_reference_fields, test_distinct_attempt_statuses, test_synthetic_fixture_is_reproducible.
- [ ] Run python -m pytest tests/test_contracts.py tests/test_fixtures.py -q; expect FAIL before implementation.
- [ ] Implement Pydantic models with explicit enums: CONFIRMED/ABSENT/PARTIAL/AMBIGUOUS/UNREADABLE/CONFLICTING; SUCCEEDED/REFUSED/TIMEOUT/ERROR/MALFORMED; VERIFIED/EXPERIMENTAL/UNKNOWN. Keep verified_score: float | None and experimental_score: float | None separate.
- [ ] Implement synthetic cases: two boxes, adjacent boxes, repeated anchors, still-hidden reference, and a black overlay covering extractable text.
- [ ] Re-run targeted tests, then commit only scoped files and publish Backend handoff.

### Task 2 — Detect and safely canonicalize redacted text (RL-MVP-002)

**Files:** Create src/redaction_lab/pdf_detector.py, canonical.py; tests/test_pdf_detector.py, test_canonical.py.
**Interfaces:** detect_targets(pdf_bytes: bytes) -> DetectionResult; canonicalize_redacted(pdf_bytes: bytes, detection: DetectionResult) -> CanonicalRedactedDocument.

- [ ] Write failing tests: test_detects_two_distinct_black_text_boxes, test_adjacent_boxes_not_merged, test_hidden_overlay_text_never_in_manifest, test_non_text_black_art_excluded, test_unsupported_scan_is_explicit.
- [ ] Run targeted pytest; expect FAIL.
- [ ] Parse near-black vector rectangles and per-character text boxes; classify text-flow scope, suppress any text intersecting occluding black regions, insert stable target markers, preserve original source hash/geometry. Fail closed if paint order/occlusion cannot be established; no raster/OCR support claimed this week.
- [ ] Re-run tests and verify no secret token appears in canonical text, prompt serialization or logs; commit and handoff.

### Task 3 — Text-first reference alignment (RL-MVP-003)

**Files:** Create src/redaction_lab/reference.py; tests/test_reference.py.
**Interface:** align_reference(redacted: CanonicalRedactedDocument, reference_pdf: bytes) -> list[ReferenceMapping].

- [ ] Write failing tests: test_extracts_exact_span_between_anchors, test_repeated_anchors_unknown, test_wrong_release_unknown, test_partial_reference_unknown, test_reflow_or_punctuation_does_not_shift_target, test_adjacent_targets_independent.
- [ ] Run targeted pytest; expect FAIL.
- [ ] Canonicalize reference separately; perform global monotonic token matching, then local unique left/right-anchor search; store exact quoted span and evidence. Do not infer words or use page number as primary key. Ambiguity -> null.
- [ ] Re-run tests, commit, publish handoff.

### Task 4 — Model adapter and durable one-shot run (RL-MVP-004)

**Files:** Create src/redaction_lab/adapters/base.py, adapters/ollama.py, store.py, worker.py; tests/test_adapter.py, test_worker.py.
**Interfaces:** PredictionAdapter.predict(manifest: PredictionManifest) -> PredictionResponse (async); build_prediction_manifest(doc: CanonicalRedactedDocument, target_id: str, run: RunDefinition) -> PredictionManifest; run_pending_once(store: RunStore, adapter: PredictionAdapter) -> bool.

- [ ] Write failing tests: test_reference_cannot_serialize_into_request, test_each_target_starts_from_frozen_context, test_duplicate_job_one_attempt, test_restart_keeps_attempt, test_refusal_timeout_distinct, test_remote_endpoint_rejected.
- [ ] Run targeted pytest; expect FAIL.
- [ ] Add local-only HTTP adapter, strict response parser, persisted immutable attempts and transactional claim/complete; no hidden retry after ambiguous outcome. Record exact model/prompt/input hashes and timestamps.
- [ ] Run mocked tests; if Task 0 PASS, run one authorized real local prediction and record latency/model ID; commit and handoff.

### Task 5 — Research rubric and adversarial benchmark (RL-MVP-005, parallel proposal)

**Files:** Create docs/project/research_proposals/RL-MVP-005-evaluation-rubric.md and tests/fixtures/evaluation_cases.json (synthetic only).
**Produces:** versioned experimental fact rubric, null/abstention rules, adversarial cases, human-validation gap.

- [ ] Draft exact test cases for paraphrase, name-only targets, wrong actor/object, negation, dates, quantities, unsupported additions and partial truth.
- [ ] Separate source-supported facts, missing facts, contradictions and unsupported claims. No arbitrary numeric weight/cutoff claimed as research approved.
- [ ] Research Agent publishes proposed rubric and human-review requirements. No experimental score may be labeled verified.

### Task 6 — Independent evaluator and summaries (RL-MVP-006)

**Files:** Create src/redaction_lab/judges/base.py, judges/local_nli.py, evaluator.py, summary.py; tests/test_evaluator.py, test_summary.py.
**Interfaces:** FactJudge.assess(reference: str, prediction: str) -> JudgeEvidence; evaluate_attempt(attempt: ModelAttempt, mapping: ReferenceMapping, judge: FactJudge, rubric: Rubric) -> EvaluationRecord; build_summary(records: list[EvaluationRecord]) -> SummarySnapshot.

- [ ] Write failing tests: test_unknown_truth_null, test_role_reversal_not_full, test_negation_not_full, test_valid_paraphrase_supported, test_refusal_not_zero, test_empty_denominator_null, test_model_and_document_counts.
- [ ] Run targeted pytest; expect FAIL.
- [ ] Implement separate local NLI/semantic judge adapter plus deterministic entity/date/quantity/negation checks and auditable evidence. Use a versioned experimental rubric ONLY if Research has reviewed the demo mapping; otherwise return evidence/uncertainty without inventing numeric accuracy.
- [ ] Compute summaries from eligible frozen records, preserving unknown/failed counts and model/condition IDs; run tests, real local judge smoke if Task 0 PASS, commit and handoff.

### Task 7 — Minimal local API and accessible UI (RL-MVP-007)

**Files:** Create src/redaction_lab/api.py; tests/test_api.py; web/package.json, web/src/App.tsx, web/src/api.ts, web/src/components/DocumentPanel.tsx, web/src/components/ResultPanel.tsx, web/src/App.test.tsx.
**Interfaces:** POST /api/runs (redacted_pdf, reference_pdf optional) -> {run_id}; GET /api/runs/{run_id} -> persisted status/targets/evaluations/summaries; GET /api/health -> status.

- [ ] Write failing API tests: test_two_pdf_upload, test_invalid_pdf_rejected, test_refresh_does_not_rerun, test_reference_absent_unknown, test_rejects_oversized_or_unsupported_pdf. Write UI tests for accessible upload, target selection, experimental/unknown label.
- [ ] Run targeted Python and frontend tests; expect FAIL.
- [ ] Implement local-only API, bounded uploads, persisted run creation and read-only result polling. Build document-centered viewer with selected target, model prediction, exact reference when known, separate score status and counts. UI never computes scores.
- [ ] Re-run tests, commit and handoff. No public hosting or production authentication claim.

### Task 8 — Independent QA and checkpoint evidence (RL-MVP-008/009)

**Files:** tests/test_end_to_end.py; docs/project/handoffs/<task>-qa-<UTC>-<ID>.md; docs/project/demo/2026-10-12-checkpoint.md.
**Consumes:** exact candidate commit, approved design, plan, fixtures and rubric.

- [ ] QA independently tests overlay leakage, duplicate jobs, repeated anchors, missing truth, wrong actor/negation, refusals, malformed PDFs, restart and no extra spend.
- [ ] Run python -m pytest -q and frontend tests/build; record exact commands and outcomes, not invented passes.
- [ ] Execute one REAL local predictor and distinct evaluator end-to-end on synthetic multi-redaction pair; save reproducible environment/model/version evidence, without publishing private artifacts.
- [ ] If any gate fails, label checkpoint PARTIAL/BLOCKED with reason. Lead integrates only after authorized review; no automatic deploy.

## Execution order and schedule — revised October 8

**First MVP checkpoint: October 12, 2026 (DEC-020). Status: AT RISK.** The same acceptance criteria apply. This accelerated sequence is a conditional critical path, not authorization for later tasks or a guarantee of completion.

- **Oct 8:** RL-MVP-002 Correction 02 is in progress on its existing branch; wait for exact-SHA QA/Research review and owner-authorized merge. Read-only no-cost machine/model/license feasibility may be checked separately. No Task 3 while Task 2 is held.
- **Oct 9:** *If* Task 2 is approved and merged, propose/authorize Task 3 text-first reference alignment, with null/unknown tests and independent review. Research may prepare the Task 5 experimental-rubric proposal, and Frontend may prepare a synthetic API/UI contract, only within approved scopes.
- **Oct 10:** *If prerequisites and packets are approved*, implement Task 4 provider-neutral one-shot adapter and a real no-cost local predictor; evaluate separate local judge feasibility. Start Task 5 research rubric review without claiming human scientific approval.
- **Oct 11:** *If Task 3/4 contracts and local hardware are verified*, implement Task 6 independent evaluator and summaries; implement Task 7 minimal local two-upload API/viewer only against stable interfaces and approved packets. Independent QA reviews exact candidate commits; no unreviewed merges.
- **Oct 12:** Task 8/9 integrated local synthetic-PDF demo, regression/QA and reproducibility evidence **only if all required gates pass**. If the real models, safe alignment, independent evaluator, UI or reviews are not ready, report PARTIAL/BLOCKED with exact missing components instead of a fabricated successful demo.

**Sequencing rule:** Codex remains the implementation engine, but a completed branch is not automatically merged or allowed to start the next task. Backend and Frontend may work on separate approved branches only when interfaces are stable. QA and Research cannot be replaced by Codex self-review. No paid inference, cloud, private data, lowered truth requirements or scientifically unvalidated accuracy claims.

## Self-review and hard gates

All spec flows have tasks. Exact dependency names are declared once above; downstream implementers must keep signatures compatible. No extra providers, OCR, DOCX, multi-model ranking or deployment this week. Hardware/licensing, exact local model IDs, validated numeric scoring and lab data permissions remain explicit gates. The owner approved the MVP design and detailed plan; DEC-020 changes the checkpoint date only. Task 1 is merged and Task 2 remains under correction. Tasks 3+ require separate authorization; plan publication does not implement code.
