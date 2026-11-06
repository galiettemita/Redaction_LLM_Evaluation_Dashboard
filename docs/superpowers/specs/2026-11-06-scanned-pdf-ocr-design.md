# Scanned PDF OCR and Raster Redaction Design

## Intent

Redaction Lab must accept ordinary scanned text PDFs, detect every supported blacked-out text passage automatically, send only redacted-page evidence to the genuine prediction model, and use an optional matching revealed scan only for clearly labeled experimental evaluation. The immediate acceptance case is the owner's two-page redacted/reference pair, but the implementation must be generic, versioned, bounded, and replaceable rather than keyed to those files.

## Goals

- Preserve the existing vector-PDF path and public API v0.3 behavior.
- Add a second, isolated raster/OCR analysis backend for full-page English text scans.
- Detect contiguous near-black rectangular text-redaction regions from redacted pixels alone.
- Produce a reading-order OCR canonical document with exactly one target marker per detected region.
- OCR a reference independently for experimental alignment without allowing reference bytes, text, geometry, or hints into prediction material.
- Preserve detector, OCR engine, canonicalizer, model, and evaluation provenance in every new run.
- Keep historical vector records readable after the new backend ships.
- Fail closed with explicit unsupported/unknown outcomes when image type, OCR quality, layout, target geometry, or resource bounds are uncertain.

## Non-goals and anti-goals

- No reconstruction of photographs, diagrams, tables, signatures, or wholly missing pages.
- No use of the reference to locate targets or improve a prediction prompt.
- No LLM-generated OCR or ground truth.
- No silent acceptance of low-confidence OCR, arbitrary embedded images, handwritten-only pages, or whole-page black regions.
- No Mac-only Vision dependency, paid OCR service, or new external model provider.
- No scientific-validation claim; experimental scores remain labeled and verified scores remain null.

## Constraints

- All untrusted PDF parsing, rendering, OCR, and raster analysis stays in the rootless, network-disabled PDF worker.
- Tesseract OCR 5.5.2 and its English trained-data package run locally inside the worker. Package versions and the dependency-image digest are locked and included in qualification/SBOM evidence.
- pypdfium2 5.14.0 renders pages at a fixed 200 DPI. Processing is page-streamed and bounded by per-page pixels, total raster pixels, page count, OCR output size, target count, subprocess timeout, memory, CPU, and existing worker response limits.
- The existing genuine local Qwen predictor and deterministic experimental evaluator remain unchanged consumers.
- Private PDFs, OCR text, raw model payloads, credentials, and private hostnames never enter Git or test fixtures.

## Approaches considered

1. **Isolated Tesseract backend (selected).** Add a modular raster backend beside the vector backend. It is local, real, deterministic enough to version, available for Alpine arm64, and portable beyond the owner's Mac. It adds a qualified OS dependency and requires bounded OCR/raster tests.
2. **macOS Vision on the host.** Faster to prototype, but it would move untrusted document processing outside the isolated worker and make the product Mac-specific. Rejected for security and portability.
3. **A multimodal LLM for OCR and detection.** This would require a new large model/runtime, blur detection with prediction, weaken deterministic ground truth handling, and complicate cost and provenance. Rejected for this feature.

The owner delegated implementation choices and asked for autonomous completion, so approach 1 is the engineering selection.

## Architecture

### Stable analysis boundary

Create `redaction_lab.document_analysis` as the worker-facing router. It exposes role-specific analysis results and a backend registry. The vector backend remains the first choice for documents it supports. Only explicit raster-eligible vector dispositions (`IMAGE_OR_ANNOTATION_CONTENT`, `NONDEFAULT_PAGE_BOUNDARY`, or `NO_VISIBLE_TEXT`) may fall through to the raster backend. Parser corruption, encryption, unsafe graphics, rotation, and other security dispositions never fall through.

Each result carries its own `detector_version`, `canonicalizer_version`, analysis method, canonical text/hash, bounded target observations, and reason code. Adding another OCR engine later means registering a new versioned backend; it does not require changing API routes, storage tables, prediction adapters, evaluation code, or UI.

### OCR engine boundary

Create `redaction_lab.ocr` with immutable OCR word/page records and an `OcrEngine` protocol. `TesseractOcrEngine` sends a rendered PNG through stdin and parses bounded TSV from stdout using fixed English, segmentation, DPI, timeout, environment, and output limits. It never creates document-bearing temporary files, inherits no network, suppresses stderr, and converts execution/format/quality failures into typed analysis failures.

### Raster backend

Create `redaction_lab.raster_analysis`:

1. Render one page at a time at 200 DPI with pypdfium2.
2. Require a page consistent with a full-page text scan; reject annotations, multiple unrelated image regions, excessive rotation, oversized rasters, insufficient OCR words, poor confidence, or a layout dominated by non-text imagery.
3. Build a near-black mask with a fixed luminance threshold. Find row runs and union vertically overlapping runs into connected components without holding an unbounded pixel graph.
4. Keep components only when rectangularity, width, height, page coverage, margins, and neighboring OCR text-flow evidence are within conservative fixed bounds. White exemption labels inside a black region do not split the component.
5. Treat each connected physical region as one immutable target. Separate horizontal bars remain separate targets, consistent with DEC-007.
6. Remove OCR words intersecting a target and insert one marker at the target's reading-order position. Low-confidence or ambiguous pages fail closed; they never silently omit a target.

The reference role runs the same renderer and OCR engine but never target detection. Its line-preserving OCR text is stored only in the existing reference-source/evaluation channel.

### Provenance and compatibility

Keep the current vector detector/canonicalizer versions. Add raster-specific versions and let `PredictionSourceMaterial` carry the selected pair. Worker target observations gain a strict analysis-method value. Prediction-source identity and validation derive from stored material versions rather than today's global constants, so old vector sources remain valid and new raster sources cannot masquerade as vector evidence.

The internal PDF worker protocol is bumped because its observation schema and qualified runtime change. The public API remains v0.3. Historical attempts and failed jobs remain immutable; the corrected acceptance uses a new project/version.

### Error behavior

- Recoverable, exact pypdf cross-reference repair diagnostics are suppressed and allowed; unknown parser warnings remain fatal.
- OCR executable absence, timeout, malformed TSV, low confidence, raster limits, ambiguous components, and unsupported layouts return specific reason codes.
- A reference failure never blocks genuine prediction; it produces null/unknown evaluation.
- A timeout remains a technical outcome, not a factual error.

## Testing and acceptance

- TDD unit tests for the parser diagnostic allowlist, OCR parsing/bounds, connected-component geometry, text-flow validation, canonical marker invariants, backend routing, provenance, and legacy vector compatibility.
- Synthetic scanned PDFs built from generated text images; no private source files in tests.
- Security tests for no reference channel in prediction material, no OCR stderr/content leakage, subprocess environment/timeout/output bounds, and unchanged container isolation.
- Full Python, Node, typecheck, build, audit, source-integrity, SBOM, and worker qualification suites.
- Real Tesseract qualification inside the exact final worker image.
- Private end-to-end acceptance with the owner-selected pair: authenticated upload, OCR processing, target predictions from genuine Qwen, optional experimental evaluation, result retrieval, browser display, restart/reconnect, and unchanged unauthorized/origin rejection behavior.

## Rollback

The router can disable the raster backend while leaving the vector backend and API intact. Deployment can revert to the prior qualified image and source commit. Stored raster runs retain versioned provenance and are not reinterpreted as vector runs.
