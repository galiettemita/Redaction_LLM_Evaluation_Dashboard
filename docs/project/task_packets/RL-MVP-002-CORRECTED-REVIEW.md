# RL-MVP-002 Correction 01 — fresh independent review

**Status:** REVIEW REQUESTED, NOT STARTED. **Reviewers:** QA / Independent Reviewer and Research / Evaluation, each independently on a separate approved review branch. **Next receiver:** Lead / Architect.
**Canonical baseline:** main `6036f6fea4f988dddafb6b9b71a21b4660c26b64`, E0013. **Corrected implementation:** `12698b92d883af658266d54a9223b5619dedc7ee`. **Published Backend branch/head:** `codex/rl-mvp-002-detection-canonicalization` @ `c37837669ce9e538a3afa8db0e25ef92cbbdd327`.
**Backend handoff:** `docs/project/handoffs/RL-MVP-002-backend-20261008T141115Z-12698b9.md` on the Backend branch.
**Original QA and Research findings:** [QA](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/48adf452178e1e7c38896b088f2e7481846bf275/docs/project/handoffs/RL-MVP-002-qa-20261008T123940Z-4304673.md) and [Research](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/a0d56b599a5ba284ef036b813fa8167164189847/docs/project/handoffs/RL-MVP-002-research-20261008T121239Z-rsem02.md). **Correction packet:** `docs/project/task_packets/RL-MVP-002-CORRECTION-01.md`.

## Shared requirements

Read AGENTS.md, live main HEAD and current E0014 state before review; inspect exact corrected commit, source and tests, plus Backend handoff. Do not inherit verdicts from `4304673`. The new commit changes `src/redaction_lab/pdf_detector.py` and `tests/test_pdf_detector.py`; the branch head additionally adds one Backend handoff. Confirm no unexpected changes and that detector version v2/target IDs do not silently mismatch prior assumptions.

Review all four originally blocking cases with adversarial variants: (1) distinct projects and delimiter-bearing IDs produce distinct deterministic target IDs, (2) two-column, narrow-gutter and staggered columns fail closed rather than interleave text, (3) overlapping/duplicate black rectangles cannot produce duplicate targets or markers while adjacent separate boxes remain distinct, (4) a standalone redaction-shaped box with no extractable hidden text cannot be silently ignored as remote artwork/NO_REDACTIONS. Probe false positives for legitimate single-column text and remote artwork; test the exact status and reason codes, not only whether an exception occurs.

Maintain redacted-only input isolation and hidden selectable-text suppression; do not accept reference-derived text, previously predicted answers or model/evaluator content. Preserve marker uniqueness, visible context and safe handling of unsupported/malformed PDFs. Do not treat synthetic tests as real-world recall/precision or scientific score validation.

## QA-specific deliverable

Independently run the full 88-test suite when a matching executable checkout is available; if unavailable, state NOT RUN and use reproducible isolated probes without claiming full-suite execution. Test regression behavior, malformed/ambiguous inputs, project-scoped identity, text leakage and failure states. Record commands, actual pass/fail counts, environment, limitations and PASS / CHANGES_REQUESTED / BLOCKED on the **exact SHA**. No code edits.

## Research-specific deliverable

Independently review target identity, one visually contiguous region = one target, redacted-only canonical context, standalone/no-underlying-text ambiguity, false NO_REDACTIONS, version changes and downstream implications for reference alignment/model fairness. Record actual checks and PASS / CHANGES_REQUESTED / BLOCKED for Task 2 semantics only. D03–D06 research-human scoring approval is NOT granted by a contract/detection review.

## Publication / boundaries

Each role publishes a unique handoff on its own review branch referencing `12698b92d883af658266d54a9223b5619dedc7ee` and `c37837669ce9e538a3afa8db0e25ef92cbbdd327`, with exact evidence and next receiver Lead. If write access is unavailable, say NOT PUBLISHED. No implementation fixes, main merge, Task 3, provider/model calls, paid services, private research data, cloud or deployment. Lead reconciles only after both fresh reports.
