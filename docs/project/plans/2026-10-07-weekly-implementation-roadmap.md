# Redaction Lab — weekly delivery roadmap

Status: PROPOSED FOR OWNER REVIEW. Created 2026-10-07. See MVP design in docs/superpowers/specs/2026-10-07-oct14-mvp-design.md.
This is a target schedule, not a guarantee of bug-free completion or scientific validity. No extra spending.

## Checkpoint 1 — October 14: first working vertical slice

Two PDF uploads (redacted and reference), automatic detection of all supported text black boxes, canonical text, conservative reference alignment, one real prediction model through a reusable adapter, a different local evaluation model, provisional/unknown results per target, and simple per-document/model summaries in a local UI.

Proposed daily sequence:
- Oct 7: freeze written MVP design, confirm local hardware and license constraints, approve bounded task packets and synthetic fixture contract.
- Oct 8: implement PDF intake, redaction manifest and safe canonical text extraction with leakage tests.
- Oct 9: implement global/local text-anchor reference alignment with null/unknown behavior.
- Oct 10: implement generic prediction adapter, frozen run records and one local model smoke test.
- Oct 11: implement independent local evaluator and a versioned experimental rubric, with Research review.
- Oct 12: connect minimal web upload/viewer, progress and summaries.
- Oct 13: run QA adversarial fixtures, end-to-end test, failure recovery, documentation and fixes.
- Oct 14: controlled local demonstration and checkpoint review. No public deployment implied.

## Later checkpoints (conditional)

- Oct 21: additional provider adapters and fair multi-model comparison, only after vendor/data/cost authorization; keep shared context and versioned attempts.
- Oct 28: human benchmark, score calibration, contradictions/abstention, research-reviewed aggregation and model comparison validity.
- Nov 4: scanned PDF reliability, polished document viewer, accessibility, security, recovery and lab pilot readiness.
- Nov 11 contingency: address validation/deployment blockers and prepare authorized pilot. Month-scale completion is an aspiration; production acceptance depends on evidence.

## Work packets and ownership

RL-MVP-001 Backend: typed records + synthetic fixture/test harness; no external calls.
RL-MVP-002 Backend: PDF ingestion and safe automatic text redaction detection.
RL-MVP-003 Backend: reference text alignment and scoreability gate.
RL-MVP-004 Backend: provider-agnostic prediction adapter + one local real model.
RL-MVP-005 Research: provisional evaluator rubric and benchmark/adversarial cases (no invented research sign-off).
RL-MVP-006 Backend: independent evaluator worker, evidence and summaries.
RL-MVP-007 Frontend: two-upload local UI, target selection, statuses and summaries.
RL-MVP-008 QA: independent security/leakage, alignment, scoring and end-to-end review.
RL-MVP-009 Lead: integration, reproducibility evidence and Oct 14 demo decision.

Backend packets are sequential where they share contracts; Research and Frontend proposals may proceed in parallel after their approved scopes. Specialists publish unique handoffs; Lead alone integrates canonical docs. A task is not approved merely by appearing in this roadmap.

## Gates and stop conditions

Before any product code: owner reviews written MVP design and detailed task plan. Before real model: machine hardware, model license, memory, latency and no-cost access verified. Before numeric score: versioned provisional rubric and explicit experimental labeling; verified scoring requires research-human calibration. Before external APIs/real sensitive documents: institutional authorization. Before deployment: engineering/lab approval. No fake test results, paid calls or silent unsupported fallbacks.
