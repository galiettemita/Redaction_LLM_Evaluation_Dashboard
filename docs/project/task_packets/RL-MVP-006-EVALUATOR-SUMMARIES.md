# RL-MVP-006 — Independent evaluator evidence and three-level summaries

**Status: OWNER-APPROVED for bounded synthetic/mock-only implementation (2026-10-09).** Backend/Codex is the single implementation owner. QA and Research must independently review the exact candidate before a separately authorized merge. **No scientifically verified numeric scoring, model downloads, real inference, new dependency without approval, merge, Task 7, deployment or additional spend is authorized.**

**Baseline:** main `2ceaebacc44e8b1622231683ac0c3ee30c23e7d3`, coordination epoch E0037 at approval; publication routing epoch E0038. Refresh live default branch, HEAD, AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md and incoming handoffs before work and publication. October 12 remains a checkpoint target, not a quality waiver.

## Authority and inputs

Owner explicitly approved the proposed six Task-6 source/test files, necessary scoped changes to `contracts.py`/`test_contracts.py`, and one unique Backend handoff. Sources: approved October 12 implementation plan Task 6, R05/R07/R08/R09/R11/R12, DEC-001/003/004/005/011–014/015/017/020/022, `docs/project/INTERFACES.md`, `docs/project/RESEARCH_METHOD.md`, and Task-5 Research proposal (branch `research/rl-mvp-005-rubric-e0037` at `aa52cd3300c5cb5c81ade03194fcabd80a2d467f`; rubric `fact-evidence-rubric-v0.1-proposed`; dataset `synthetic-adversarial-v0.1-proposed`, 20 synthetic cases). Those artifacts remain proposals, are not human gold, and are not approved scoring methodology.

## Objective / non-goals

Build independently testable, immutable, versioned **qualitative fact evidence** and target/document/model count-and-coverage summaries for frozen model attempts and approved reference mappings. Hard separation: evaluator may read reference truth and frozen predictions, but must never modify predictions or supply reference-derived hints to predictor. **No numeric semantic scores, rankings, thresholds, weights, percentages, or verified accuracy claims**, even as experimental outputs in this task. Both `verified_score` and `experimental_score` must be null, `score_status=NONE`, and no score scale/validation IDs asserted.

## Exact authorized paths

Create:
- `src/redaction_lab/judges/base.py`
- `src/redaction_lab/judges/local_nli.py` (disabled/availability-gated interface only; no installed model, weights, downloads or real inference)
- `src/redaction_lab/evaluator.py`
- `src/redaction_lab/summary.py`
- `tests/test_evaluator.py`
- `tests/test_summary.py`

Modify **only if needed for scoped compatibility**:
- `src/redaction_lab/contracts.py`
- `tests/test_contracts.py`

Publish exactly one unique `docs/project/handoffs/RL-MVP-006-backend-<UTC>-<SHORT-ID>.md` on the implementation task branch. If creating `judges/__init__.py`, touching fixtures, dependencies, existing Task 1–4 modules/tests, `pyproject.toml`, API/UI, shared canonical docs, or any additional files is required, STOP and seek explicit expanded scope. No unauthorized import-time side effects.

## Required contract and trust semantics

- `evaluate_attempt` must bind project, exact target ID/version, frozen attempt ID/status, reference mapping ID/version, redacted-document identity where available, rubric/evaluator version and mapping trust. `ModelAttempt` currently lacks direct target context beyond target_id/version and run identity, while `ReferenceMapping` has redacted-document version; do not invent a binding. If a trusted caller/resolver cannot establish this dependency with the approved contract scope, fail closed or stop for narrow clarification.
- A `ReferenceMapping` marked CONFIRMED/SCOREABLE is **not by itself** evidence of authentic source: Task 3's October 12 DEC-022 registry only admits pinned synthetic pairs. Do not allow caller-constructed mappings to become scientifically verified truth. For synthetic tests, use trusted fixture-pair source evidence/resolver, or treat evidence as clearly fixture/provisional with all numeric scores null; no general user-upload provenance claim.
- Eligibility: only completely revealed, readable, unique, reliably aligned exact target truth may enter fact evidence. Missing, absent, partly hidden, unreadable, ambiguous, conflicting, mismatched or untrusted truth: no partial full-target judgment, no fact comparisons, and null accuracy. Reject stale/mismatched identities rather than silently scoring another target.
- Technical outcomes SUCCEEDED, REFUSED, TIMEOUT, ERROR, MALFORMED are distinct. Only a successful frozen prediction with eligible truth can be considered for semantic evidence. Nonanswers must not become factual zero, completed matches or vanish from completion counts. Internal worker IN_DOUBT must not be represented as terminal success.
- Reference-only fact decomposition must be generated/frozen before examining a prediction; no self-judging predictor, lexical overlap alone, repeated/list-of-alternatives credit, or fabricated exact source quotation. Version and provenance all proposed fact evidence; distinguish SUPPORTED, MISSING, CONTRADICTED, UNSUPPORTED and NEEDS_REVIEW. Source-fact segmentation is still an unvalidated design proposal; use deterministic synthetic supplied evidence/mock judges and return NEEDS_REVIEW rather than fabricate semantic certainty.
- `FactJudge.assess(reference,prediction)` and `JudgeEvidence` must not silently claim NLI semantic accuracy. `local_nli.py` is an explicit disabled/unavailable adapter with safe errors until separately approved hardware/license/model and implementation scope. Do not install `transformers` or fetch weights.
- Prefer existing immutable `EvaluationRecord`, `FactComparison`, `SummarySnapshot` contracts, and make only narrowly justified additive adjustments in authorized files; document schema/consumer impact and backwards compatibility. No rewrite of prediction, reference or job contracts. Preserve attempt/reference/rubric/evaluator versions, exact immutable evidence, contradictions and unsupported additions. If existing contracts cannot represent a necessary evidence dimension safely, STOP rather than overload ambiguous string fields.

## Three-level summary contract

Produce target, per-document-per-model and per-model-across-document records. Include exact evaluation IDs, versioned scope/model/condition/rubric/aggregation identity and immutable counts, exclusions, unknown truth, refusals/timeouts/errors/malformed, pending review and disagreements. Explicitly define eligible versus included sets, avoid double-counting overlapping categories, require identical eligible target sets for comparisons, and keep incompatible model/settings/prompt/rubric/judge/reference versions separate. A document summary must remain model-specific. No pooling of unrelated conditions or comparing model-dependent subsets as like-for-like. Empty eligible verified denominator yields null, never 0. **Do not calculate numeric mean, weight, percentage or score in Task 6.** If `SummarySnapshot` requires `common_eligible_set_id`, use a declared deterministic identity backed by the actual set rather than an arbitrary caller string.

## Required TDD checks

- Missing, partial, still-hidden, unreadable, ambiguous, conflicting, misaligned, unregistered synthetic reference => null/unknown, no source facts or numeric scores.
- Wrong project/target/version, forged mapping, stale reference/rubric and wrong attempt binding fail closed.
- Correct equivalent paraphrase, actor/object reversal, negation, quantities/units, dates, attribution, modality, unsupported additions, multiple alternatives and repeated claims produce only supported/provisional fact evidence or NEEDS_REVIEW as justified; no unvalidated full-match claims.
- Distinct SUCCEEDED/REFUSED/TIMEOUT/ERROR/MALFORMED handling and internal uncertainty; no zero score or hidden loss from counts.
- Exact target/document/model summaries, comparable-set IDs, empty denominator null, mismatch rejection, no cross-model aggregate, version separation, absence of guessed weights, inclusive counts/partition reconciliation.
- Immutable EvaluationRecord/SummarySnapshot, deterministic IDs/version binding, replay with changed reference/rubric produces new record without changing frozen prediction.
- No reference/rubric/answer leakage into prediction manifests; no live model calls under mock tests; all relevant prior Task 1–4 tests preserved.

Run focused pytest (including relevant Task 5 fixture checks if usable), full pytest, compileall, dependency integrity and `git diff --check`; report commands, numbers, failing/NOT RUN checks, exact file audit and research limitations. QA independently reviews software/state/security on exact SHA; Research independently reviews truth/fact/scoring protocol on same SHA. Author tests never substitute for independent checks or human D03–D06 approval.

## Publishing / stops / rollback

Use one isolated Task-6 branch/worktree based on fresh main. Publish implementation exact SHA and a unique Backend handoff. No direct main edits by specialist; no unapproved merge. Stop for unrepresentable trusted reference authority, necessary out-of-scope files/dependencies, unauthorized model calls, proposed scores presented as verified, change to Task 1–4 contracts, private data, additional spend, real inference or deployment. Roll back with ordinary additive revert/no force push. After fresh QA/Research PASS, Lead reconciles and requests separate owner merge authorization. Task 7 remains unapproved.
