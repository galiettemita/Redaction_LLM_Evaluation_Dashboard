# RL-MVP-002 — Independent Research/Prediction-isolation review

**Status:** REVIEW REQUESTED, NOT STARTED. Read-only research semantics review, unique task handoff on an approved review branch. No implementation, merge, paid calls or Task 3.
**Reviewer:** Research / Evaluation.
**Baseline:** main `0b38e46ec467d9d1c3345b5fe24e03b24e578d0f`, E0011.
**Exact implementation SHA:** `430467314ca992f36cf3eaab9d49cde45a9805ac`; Backend handoff branch head `a6a603f6b11472df5cf36d2acd9eeec215fe81af`.
**Source:** AGENTS.md, DECISIONS.md (DEC-002, 004, 007, 008, 010, 011, 015), INTERFACES.md, RESEARCH_METHOD.md, RL-MVP-002 packet, and candidate Backend handoff.

## Objective

Verify that the canonical document represents only evidence visibly available in the redacted release and that targets correspond to distinct supported physical text-redaction boxes. This is not D03 ground-truth confirmation or scientific score validation.

## Questions

1. Does the detector depend solely on the redacted PDF, never the reference, hints, earlier guesses or evaluator feedback? Are all target markers stable, unique and one-to-one with supported contiguous black boxes?
2. Can the canonicalizer accidentally preserve hidden PDF-layer characters, reorder visible words, collapse or misplace the marker, or erase visible contextual clues? Consider word boundaries, punctuation, same-line multiple targets, document boundaries and line grouping.
3. Are ambiguous layouts and partial/multiple/overlapping occlusions explicitly rejected rather than silently excluded? Is NO_REDACTIONS distinguishable from UNSUPPORTED and supported-with-targets?
4. Are the input hash, project/document IDs, detection/canonicalizer versions and target IDs sufficient for reproducible, frozen prediction context? Are identity and version assumptions clearly documented for downstream Task 3/4?
5. Are the vector-only week-one exclusions correctly represented as a tested MVP limitation, not a claim that the long-term hybrid detection requirement was completed?
6. Which issues, if any, would compromise a later model comparison or truth alignment and must be fixed before integration? Keep future reference alignment and evaluator scoring methods out of Task 2.

## Deliverable

Unique Research handoff referencing the exact candidate SHA with PASS/CHANGES_REQUESTED/BLOCKED for Task 2 semantics, evidence/tests reviewed and downstream risks. Research-human D03–D06 approval remains NOT OBTAINED unless independently documented. No merge or Task 3.
