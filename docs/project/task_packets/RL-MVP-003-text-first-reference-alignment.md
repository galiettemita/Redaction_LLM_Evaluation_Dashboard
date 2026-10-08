# RL-MVP-003 — Text-first, fail-closed reference alignment

**State:** OWNER-APPROVED TO IMPLEMENT TASK 3 ONLY. Owner replied "yes" after RL-MVP-002 merge, 2026-10-08.
**Owner:** Backend/Codex. **Reviewers:** independent QA and Research. **Next receiver:** Lead.
**Baseline:** main 31cde9e982c847b730fcfa90efd0ab9b4008dd6d, epoch E0023; refresh HEAD and current epoch before work.
**Sources:** AGENTS.md; DEC-001,004,007,008,010,011,015,020; Task 3 of docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md; current contracts.py, canonical.py, pdf_detector.py, INTERFACES.md, RESEARCH_METHOD.md.
**Deadline:** October 12, 2026; no reduction of correctness gates.

## Objective

Given a frozen CanonicalRedactedDocument and an optional reference PDF, produce one immutable ReferenceMapping per detected text target. Canonicalize the reference safely, globally align normalized word tokens monotonically, then use unique left/right word anchors around each target to extract its **exact revealed text** with source offsets and versioned evidence. Page numbers/geometry are secondary checks, not primary matching. No LLM may infer truth.

CONFIRMED requires unique, complete, readable, reliably aligned full-target truth. Repeated, partial, still-hidden, wrong-release, unreadable, unsupported and absent references must be NOT_SCOREABLE with exact_revealed_text=None and downstream null score. D03 scientific validation is not granted by this task.

## File and authority boundary

Create ONLY src/redaction_lab/reference.py and tests/test_reference.py, plus one unique docs/project/handoffs/RL-MVP-003-backend-<UTC>-<ID>.md on a NEW isolated codex/rl-mvp-003-* branch. Synthetic PDFs can be constructed inside the new test file with existing ReportLab. Do not modify contracts.py, fixtures.py, canonical.py, detector, existing tests, dependencies or canonical shared docs. Stop and ask Lead if a contract change is necessary. No paid APIs, private research data, cloud, scoring, UI, DB, deployment, or Task 4.

## Interface

The plan sketches align_reference(redacted: CanonicalRedactedDocument, reference_pdf: bytes) -> list[ReferenceMapping]. Existing strict contracts require more identity fields. Refine using **required keyword-only** metadata: actual RedactionTarget records, reference_document_version_id, reference_canonical_version_id and mapping_version; allow reference_pdf=None for ABSENT. No fabricated project/version defaults.

Validate redacted canonical hash and exactly one [[TARGET:<id>]] marker per expected target; ensure target IDs/versions belong to the same project and redacted document, with no duplicates or unexpected markers. Do not claim this proves persisted cross-record existence; later transactional checks remain necessary.

For reference parsing, use existing safe PDF detector/canonicalizer protections to suppress still-hidden selectable text under black overlays; never trust raw extract_text() to reveal visually hidden words. Keep a normalized matching token stream separately from the exact visible source text/character locators. Preserve original readable quotation (including meaningful whitespace), deterministic hashes, algorithm version and boundary evidence. If canonicalizer output cannot preserve exact source quotation, fail closed rather than fabricate it.

Perform global monotonic token matching before local left/right anchors. Widen anchors as needed; repeated plausible candidates, rewritten context or insufficient uniqueness -> AMBIGUOUS/CONFLICTING and null truth, never first-match. For reference boxes covering part of a target, return PARTIAL or other unconfirmed state with NO exposed candidate truth. Sanitize logs/exceptions; reference text must never enter prediction manifests, previous guesses or public handoffs.

Only existing ReferenceStatus values may be used. Unsupported reference parsing may return an explicit safe unconfirmed outcome or sanitized typed error; never masquerade as CONFIRMED. Confirmed mappings must satisfy all ReferenceMapping evidence/scoreability validators. A schema SCOREABLE state is NOT research-human scientific verification.

## TDD acceptance

Write failing tests first (RED), then minimal implementation and GREEN:
- exact span between anchors, including exact quotation/locator/provenance and multiple targets;
- repeated anchors unknown, wrong release unknown, still-hidden and partially revealed reference unknown with no truth exposure;
- reflow/punctuation/page-number changes only when unique/reliable, adjacent targets independent, true document-boundary anchors;
- no-reference ABSENT, mismatched project/version rejected, tampered hash/marker rejected, deterministic IDs/hashes;
- malformed/unsupported reference fail closed, hidden selectable reference text never leaked to output/errors/logs/prediction manifest;
- all existing 120 Task-1/2 tests still pass.

Run focused/full pytest, compileall, git diff --check, dependency check; record exact commands, RED/GREEN counts, tests not run and limitations. Do not claim real-world accuracy or D03 research validation.

## Publish and review

Commit and push only authorized files to a new task branch; publish exact implementation SHA, branch/handoff SHA, changed paths, tests, risks and next receiver. QA and Research independently review the NEW exact SHA. No main merge, Task 4, paid services, external models, private data or deployment. Stop for uncertain/partial truth confirmation, reference leakage, changed epoch/hold, or required out-of-scope changes.
