# RL-MVP-002 — Independent QA review

**Status:** REVIEW REQUESTED, NOT STARTED. Read-only review of exact candidate, plus one unique QA handoff on your scoped review branch. No code modifications, merge, paid services or Task 3.
**Reviewer:** QA / Independent Reviewer.
**Baseline:** main `0b38e46ec467d9d1c3345b5fe24e03b24e578d0f`, E0011.
**Candidate implementation:** `430467314ca992f36cf3eaab9d49cde45a9805ac`, branch `codex/rl-mvp-002-detection-canonicalization`; published Backend handoff branch head `a6a603f6b11472df5cf36d2acd9eeec215fe81af`.
**Evidence:** `docs/project/handoffs/RL-MVP-002-backend-20261008T033731Z-4304673.md` on the candidate branch. Approved task packet `docs/project/task_packets/RL-MVP-002-detection-canonicalization.md`.

## Objective

Independently evaluate safety and correctness of PDF detection/canonicalization, not just the 78 Codex-reported tests. Verify the exact source blobs and scope; rerun targeted and full tests if possible. Do not inherit any precursor/self-review verdict.

## Mandatory adversarial checks

1. **Hidden selectable text:** a black overlay covering extractable text must not leak any covered character to canonical text, serialized prediction context, errors or logs. Include partial glyph intersections, punctuation, repeated target markers, adjacent/overlapping boxes, and a black rectangle whose content is text but extraction order differs from paint order.
2. **PDF operators/occlusion:** CMYK and gray near-black, nonblack fills, stroked rectangles, thick lines/curves, text rendering modes, transformations, clipping, transparency, images/annotations, optional/marked content, forms/XObjects, multiple content streams and malformed graphics state. Unsupported cases must fail closed; probe for unsupported operators that the parser might silently ignore.
3. **Scope/classification:** distinguish a black text redaction from black artwork, page borders, text decorations, no-redaction documents and unsupported scans. Adjacent physical rectangles must remain distinct. An ambiguous candidate must not be silently ignored while reporting success.
4. **Canonical text:** preserve surrounding visible words, punctuation, word order, line order, page boundaries and deterministic IDs. Exactly one marker per supported target, no marker collisions with user-visible source text. Test multi-column/positioned text and document boundaries; unsupported layouts should fail closed.
5. **Geometry/identity:** normalize bboxes correctly across PDF coordinate systems, validate page size/zero/negative coordinates, prevent target ID collisions across projects/document versions, and verify that a forged DetectionResult cannot inject reference or target data into canonicalization.
6. **Resource/diagnostic security:** bounded inputs or explicit limitations, decompression bombs, encrypted PDFs, logging of parser errors, process-global stderr redirection and concurrency. Distinguish blockers for the local single-user MVP from production-hardening requirements.
7. **Regression:** verify original 43 tests, new 35 focused tests, dependency/license changes, compilation and no extra spend. Record every test actually run and not run.

## Deliverable

Publish a unique QA handoff on your own review branch with exact reviewed SHA, commands, PASS/CHANGES_REQUESTED/BLOCKED, severity and reproduction steps. If no GitHub write access, say NOT PUBLISHED. Do not implement fixes, merge, or authorize Task 3. Lead reconciles.
