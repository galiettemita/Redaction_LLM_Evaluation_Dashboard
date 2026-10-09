# Redaction Lab — weekly delivery roadmap

Status: OWNER-APPROVED ROADMAP, first checkpoint date amended by DEC-020 on 2026-10-08. Created 2026-10-07. See MVP design in docs/superpowers/specs/2026-10-07-oct14-mvp-design.md.
This is a target schedule, not a guarantee of bug-free completion or scientific validity. No extra spending.

## Checkpoint 1 — October 12: first working vertical slice (AT RISK)

Two PDF uploads (redacted and reference), automatic detection of all supported text black boxes, canonical text, conservative reference alignment, one real prediction model through a reusable adapter, a different local evaluation model, provisional/unknown results per target, and simple per-document/model summaries in a local UI.

Revised critical-path sequence (conditional; task-by-task approvals still required):
- **Oct 8:** complete Task 2 Correction 02, publish exact SHA, obtain independent QA/Research review; perform no-cost local model feasibility preflight if available.
- **Oct 9:** after Task 2 approved integration, Task 3 reference alignment; Research rubric proposal and Frontend contract preparation may run in separate approved scopes.
- **Oct 10:** Task 4 one real local predictor/adapter if hardware/license permits; Task 5 versioned provisional rubric review.
- **Oct 11:** Task 6 separate local evaluator and summaries; Task 7 minimal two-upload UI/API, only after stable interfaces and scoped authorizations.
- **Oct 12:** independent end-to-end QA and local demo (Tasks 8/9) if all gates pass; otherwise disclose PARTIAL/BLOCKED and actual tested capabilities.

**Schedule risk:** As of October 8, only Task 1 is merged; Task 2 is under correction and Tasks 3–8 remain unbuilt. No guarantee of a working real-model demo or research-validated scoring by October 12. Do not skip safety, review, or no-spend requirements. Keep the scope unchanged; defer only features already outside the approved first MVP.

**October 8 scope amendment (DEC-022):** for the October 12 demonstration, reference-pair trust and potential exact target matching are limited to pinned synthetic redacted/reference PDF pairs. Arbitrary uploaded references may support predictions from the redacted PDF but cannot yield confirmed truth or verified scores. This is a checkpoint limitation, not a change to the long-term product. Tasks 1–2 merged; Task 3 under approved trust-boundary correction; Tasks 4+ not yet authorized. A working real predictor/evaluator/UI and research validation remain at risk.

## Later checkpoints (conditional; dates not automatically changed by DEC-020)

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
RL-MVP-009 Lead: integration, reproducibility evidence and Oct 12 demo decision.

Backend packets are sequential where they share contracts; Research and Frontend proposals may proceed in parallel after their approved scopes. Specialists publish unique handoffs; Lead alone integrates canonical docs. A task is not approved merely by appearing in this roadmap.

## Gates and stop conditions

Written MVP design and detailed task plan are owner-approved; each subsequent task packet and merge still requires its own authorization. Before real model: machine hardware, model license, memory, latency and no-cost access verified. Before numeric score: versioned provisional rubric and explicit experimental labeling; verified scoring requires research-human calibration. Before external APIs/real sensitive documents: institutional authorization. Before deployment: engineering/lab approval. No fake test results, paid calls or silent unsupported fallbacks.
