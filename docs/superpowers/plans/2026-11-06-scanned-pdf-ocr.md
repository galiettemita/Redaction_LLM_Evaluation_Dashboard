# Scanned PDF OCR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a qualified, isolated OCR/raster analysis backend so supported scanned text PDFs produce genuine predictions and optional experimental evaluation without regressing vector PDFs.

**Architecture:** A document-analysis router preserves the vector path and falls through only eligible scan dispositions to a bounded pypdfium2/Tesseract backend. Worker material carries backend-specific provenance through a backward-compatible prediction-source layer; the public API, model adapter, evaluator, persistence, and UI remain stable consumers.

**Tech Stack:** Python 3.12, pypdf/pypdfium2, Pillow, Tesseract 5.5.2 English data, Pydantic, pytest, rootless Podman, existing React/TypeScript frontend.

**Spec:** `docs/superpowers/specs/2026-11-06-scanned-pdf-ocr-design.md`

## Global Constraints

- Reference bytes/text/geometry never enter redacted analysis, canonical prediction text, or a model request.
- Unknown truth stays null; `verified_score` stays null; results remain labeled experimental.
- Existing vector behavior and public API v0.3 remain compatible.
- Private documents and content never enter Git, logs, test fixtures, or review artifacts.
- Raster work is isolated, network-disabled at runtime, bounded, versioned, and fail-closed.
- Every behavior change follows RED/GREEN/refactor and is committed in a reviewable unit.

## Review Focus

- A PDF with images plus unsafe vector graphics must not bypass a vector security rejection through OCR fallback; Task 3 adds routing-negative tests.
- Low-confidence or handwritten/image-dominant pages must return unsupported rather than zero targets; Task 2 adds confidence/layout tests.
- White exemption labels must not split one black physical rectangle, while separated bars remain separate targets; Task 2 adds component tests.
- Reference OCR must never affect redacted targets, canonical text, hashes, or prompts; Tasks 3 and 4 add differential leakage tests.
- Historical vector sources must reopen and validate after raster versions ship; Task 4 adds legacy-record tests.

---

### Task 1: OCR engine and qualified dependency boundary

**Files:**
- Create: `src/redaction_lab/ocr.py`
- Create: `tests/test_ocr.py`
- Create: `packaging/pdf-worker/Containerfile.ocr-dependencies`
- Modify: `packaging/pdf-worker/Containerfile`
- Modify: `scripts/build-pdf-worker.sh`
- Modify: worker lock/SBOM/integrity/qualification manifests required by the existing build policy
- Test: `tests/security/test_pdf_worker_container.py`

**Interfaces:**
- Produces: `OcrWord`, `OcrPage`, `OcrFailure`, `OcrEngine.recognize(image) -> OcrPage`, and `TesseractOcrEngine` with fixed bounded subprocess behavior.
- Produces: a digest-pinned dependency image containing Tesseract 5.5.2 and English trained data, followed by offline source-only rebuilds.

- [ ] Write failing tests for valid TSV parsing, malformed/unbounded output, timeout/nonzero exit, confidence data, sanitized errors, and exact dependency/SBOM pins.
- [ ] Run the focused tests and verify failures are due to missing OCR interfaces and image metadata.
- [ ] Implement the immutable OCR records and injectable subprocess runner; keep document bytes on stdin/stdout and suppress stderr.
- [ ] Build the pinned OCR dependency image once, record exact package/image hashes, and restore offline source rebuild behavior.
- [ ] Run OCR/security tests and a real synthetic Tesseract container probe; verify no text appears in logs.
- [ ] Commit the independently testable OCR/runtime boundary.

### Task 2: Bounded raster scan analysis

**Files:**
- Create: `src/redaction_lab/raster_analysis.py`
- Create: `tests/test_raster_analysis.py`

**Interfaces:**
- Consumes: `OcrEngine` from Task 1 and PDF bytes.
- Produces: `RasterTargetObservation`, `RasterRedactedAnalysis`, `RasterReferenceAnalysis`, `analyze_redacted_scan(...)`, and `analyze_reference_scan(...)` with explicit reason codes and raster detector/canonicalizer versions.

- [ ] Write failing tests using generated scan images for component separation/union, text-flow adjacency, marker order, OCR-word removal inside targets, low confidence, image-dominant/whole-page rejection, pixel/page/target limits, deterministic hashes, and reference line text.
- [ ] Run focused tests and verify the missing raster API is the failure.
- [ ] Implement page-streamed pypdfium2 rendering, run-length union components, conservative geometry/text-flow validation, and canonical line reconstruction.
- [ ] Run focused tests; refactor only after all raster tests pass.
- [ ] Commit the raster backend.

### Task 3: Analysis router and worker protocol

**Files:**
- Create: `src/redaction_lab/document_analysis.py`
- Create: `tests/test_document_analysis.py`
- Modify: `src/redaction_lab/application/worker_protocol.py`
- Modify: `tests/application/test_worker_protocol.py`
- Modify: `scripts/verify-pdf-worker.sh`

**Interfaces:**
- Consumes: existing vector detector/canonicalizer and Task 2 raster results.
- Produces: role-specific worker analysis with selected backend versions/method; bump internal worker protocol and add strict target analysis method.

- [ ] Write failing routing tests: vector success never invokes OCR; only the three approved scan dispositions fall through; malformed/encrypted/unsafe graphics do not; reference OCR is independent; raster failures map to explicit dispositions.
- [ ] Run tests and verify expected failures.
- [ ] Implement the registry/router and adapt worker responses without changing public API v0.3.
- [ ] Extend the exact-image qualification script with real synthetic scanned redacted/reference probes and no-reference-leak assertions.
- [ ] Run focused worker/routing tests and commit.

### Task 4: Versioned prediction-source compatibility

**Files:**
- Modify: `src/redaction_lab/prediction_source.py`
- Modify: `tests/test_prediction_source.py`
- Modify: persistence tests only if needed to prove historical reopen behavior

**Interfaces:**
- Consumes: worker material with vector or raster version/method.
- Produces: target/source identities validated against their stored backend versions while preserving existing vector records.

- [ ] Write failing tests for raster material construction, forged method/version combinations, canonical marker binding, and a serialized legacy vector source reopening unchanged.
- [ ] Run tests and verify expected failures.
- [ ] Implement an explicit allowed backend-version registry and version-derived source/target validation.
- [ ] Run focused and application persistence tests; commit.

### Task 5: Cross-product regression and exact-image qualification

**Files:**
- Modify: synthetic E2E and security tests as needed
- Modify: final worker/runtime/package integrity manifests
- Create: task-scoped handoff under `docs/project/handoffs/`
- Modify: project checklist/state only with verified evidence

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: exact candidate, qualified worker digest, regression evidence, deployment and private acceptance receipts.

- [ ] Run focused OCR/raster/router/source tests, then the complete Python suite.
- [ ] Run Node tests, typecheck, production build, and audit; verify the unchanged UI/API consumer path.
- [ ] Rebuild the source image offline from the locked OCR dependency image; update manifests and run full container isolation/qualification.
- [ ] Request independent exact-candidate review and correct any blocking findings with new RED/GREEN cycles.
- [ ] Recheck live integration HEAD, publish/merge normally, stop the tunnel before maintenance, deploy the qualified image/source, then restart the app before the tunnel.
- [ ] Upload the owner-selected pair under a new project identity, process both roles, verify genuine Qwen attempts, experimental/null-safe evaluation, GET stability, browser display, restart/reconnect, 401/403 boundaries, and absence of private content in logs/artifacts.
- [ ] Publish the evidence-only handoff/checklist update, commit, push, and report the working authenticated link and private recovery identifiers.
