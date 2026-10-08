# RL-MVP-002 — Automatic text-redaction detection and safe canonicalization

**State:** APPROVED TO IMPLEMENT THIS TASK ONLY (owner's 2026-10-07 direction to continue with Codex after RL-MVP-001 merge).
**Owner:** Backend/Codex. **Reviewers:** QA independent; Research for redacted-only and target semantics. **Receiver:** Lead.
**Baseline:** main d90d673d9cdceeab6a2ce9bdaa3129db9c8d7367, epoch E0010; refresh current main and read AGENTS.md before starting.
**Plan:** Task 2, docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md.

## Objective

Detect all supported visually contiguous near-black rectangular text redactions automatically in the redacted PDF; construct stable immutable RedactionTarget records and a CanonicalRedactedDocument with stable target markers. No user intervention and no access to reference content. Hidden PDF-layer text must never enter the canonical representation, model manifest, logs or errors.

## MVP boundary

Short English digitally born PDFs, selectable visible text, simple filled near-black vector rectangle overlays and ordinary text flow. Scanned-only/OCR, complex clipping/paint order/transparency, images, tables, full-page omissions, rotated/unsupported layout and ambiguous candidates must fail closed or be explicitly UNSUPPORTED. This vector-only week-one subset does not supersede DEC-007's long-term hybrid detector design. No silent omissions or false completeness claims.

## Allowed files

Create src/redaction_lab/pdf_detector.py, src/redaction_lab/canonical.py, tests/test_pdf_detector.py, tests/test_canonical.py. Modify pyproject.toml ONLY if necessary for a verified no-cost PDF parser dependency/license. Add one unique docs/project/handoffs/RL-MVP-002-backend-<UTC>-<ID>.md on a NEW isolated Codex task branch. Do not change existing contracts.py or fixtures.py; stop if a contract change is necessary. No reference alignment, providers, scoring, UI, database, deployment or other task.

## Interfaces

The approved plan sketches detect_targets(pdf_bytes: bytes) -> DetectionResult and canonicalize_redacted(pdf_bytes: bytes, detection: DetectionResult) -> CanonicalRedactedDocument. Because existing immutable contracts require project/document/version IDs, the Task 2 implementation may refine these with explicit keyword-only project_id, redacted_document_version_id and canonical_document_version_id. Define a local frozen DetectionResult with targets and supported/unsupported status; never invent project defaults or alter existing record schemas.

## Safety and behavior

- Parse vector near-black filled rectangles, char geometry and text baselines. Keep adjacent physical boxes distinct; reject non-text black graphics.
- A black rectangle can cover extractable underlying text. Remove any glyph/character potentially occluded before producing canonical text; if clipping, paint order or visibility is uncertain, return UNSUPPORTED instead of exposing text.
- Preserve visible neighboring words and page reading order; insert exactly one stable marker per supported target, keep all other redactions hidden. Derive IDs/hashes deterministically from redacted source version, page geometry and detector/canonicalizer versions.
- Never accept reference bytes, mapping, truth, hints or previous guesses as inputs. Do not include sensitive source strings in errors/logs.
- Report zero detected redactions distinctly from unsupported or untrusted detection coverage.

## Required TDD evidence

First write failing tests and run RED, then implement and run GREEN:
- two boxes; adjacent boxes distinct; stable target IDs/normalized geometry; one marker per target;
- hidden selectable SYNTHETIC_TRAP_TOKEN never appears in canonical text, any prediction serialization, logs or errors;
- visible neighboring words and reading order preserved; no reference dependency;
- black non-text artwork not counted as target; unsupported ambiguous black candidates not silently dropped;
- scan/no visible text, malformed PDF and complex occlusion rejected or explicitly unsupported;
- all existing 43 RL-MVP-001 tests still pass.

Record exact targeted/full pytest commands/results, compileall, git diff --check, parser dependency/version/license, and test limitations. Do not claim a real-world detector recall rate from synthetic fixtures.

## Stop, publish, review

Stop for any leakage, uncertain occlusion assumptions, incompatible contract, paid dependency or scope expansion. Commit allowed files only to a new codex/rl-mvp-002-* branch without force-pushing. Publish exact SHA and task-scoped Backend handoff. QA and Research independently review the exact candidate; Lead reconciles. NO merge, Task 3, paid calls, external providers, restricted data, cloud or deployment. Later tasks require separate authorization.
