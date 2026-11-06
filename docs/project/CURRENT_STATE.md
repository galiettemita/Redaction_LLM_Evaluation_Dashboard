# Current state

Updated: 2026-11-05 (America/New_York). Coordination epoch: **E0072**.
Integration branch: `main`. Canonical writer: **Codex Engineering Lead** within standing authority and the owner's bounded completion direction.
Freshness baseline for this record: live GitHub main `67a71ab0ac33e2a2c6bf0210eccc1c9d1add0524`; resolve live HEAD before action.

## Read this first

Stage: **experimental application merged and owner-only authenticated demonstration live**. [DEC-023](DECISIONS.md#dec-023--automatic-experimental-evaluation-and-controlled-demonstration) records the owner's 2026-11-05 direction to finish autonomously with genuine local inference, automatic clearly labeled experimental results before scientific validation, and an owner-only authenticated working link. [Design](../superpowers/specs/2026-11-05-experimental-product-completion-design.md) and [plan/checklist](../superpowers/plans/2026-11-05-experimental-product-completion.md) define the bounded work.

Implementation at baseline: MVP contracts, detector, synthetic aligner, prediction/evaluation infrastructure and portable API/UI through Task 7D, v0.2 frontend (PR #9), PDF runtime qualification (PR #10), model runtime qualification (PR #11) and synthetic workflow (PR #12) are integrated. This replaces stale historical absence/hold statements; their details remain in Git history, [decisions](DECISIONS.md) and task handoffs. The prior Task 10 canary persisted two MALFORMED model outputs; that historical baseline does not describe the new branch acceptance below. [Task 10 handoff](handoffs/RL-E2E-010-lead-20261029T194142Z-851ec58.md) distinguishes host canary evidence from pending independent runtime/recipient qualification.

New branch evidence: Tasks 1–5 passed their scoped independent reviews. Task 6 implementation `1630c31` and final review correction `9e6c01f4eb86503745b1cfc75cb366193283c3f3` adds the authenticated loopback gateway, safe shared runtime root, offline independently qualified v2 image and API mapping identity correction. Final regression: **956 Python / 55 Node passed**, typecheck/build passed, npm audit zero. Genuine exact-reference canary: two SUCCEEDED attempts, experimental target scores **0 / 8.3**, document/model **4.2**, verified scores null. The final image `03db44f` produced 14 fresh SUCCEEDED attempts across exact/negative/marker cases. Historical attempts remain separate: 12 on `954ca79`, two on `f1b8a731`. Prior 14 attempts/evaluations and 28 summaries are unchanged. Negative-reference cases preserve target-level uncertainty. Real mounted Chrome acceptance covered upload/process/results, focus, local files/effect cleanup, errors and same-attempt recovery. This is reference-host synthetic acceptance through a loopback TLS bridge, not external deployment. [Task 6 handoff](handoffs/RL-EXP-015-lead-20261105T220700Z-task6.md) records provenance, limits and remaining actions.

## Active work registry

| Task | State | Owner / scope / next acceptance |
| --- | --- | --- |
| RL-OPS-002 | ACTIVE | Codex Engineering Lead; standing bounded engineering, independent automated review, corrections and normal integration. Nondelegable gates remain. |
| Completion plan Task 1 / DEC-023 | DOCUMENTED; SCOPED REVIEW PASSED | Decision/contracts/checklist through `72bd96e`; branch integration pending. |
| [RL-EXP-015](task_packets/RL-EXP-015-EXPERIMENTAL-EVALUATION.md) | IMPLEMENTED; SCOPED REVIEWS PASSED | Tasks 2–4 through `c82f5fc`; combined v2/genuine evaluation acceptance now recorded. Whole-branch review remains. |
| [RL-UX-016](task_packets/RL-UX-016-EXPERIMENTAL-WORKSPACE.md) | IMPLEMENTED; SCOPED REVIEW PASSED | Task 5 through `a1705f5`; Task 6 completed the deferred mounted Chrome focus/effect/file/error/reconnect evidence. |
| [RL-LINK-017](task_packets/RL-LINK-017-CONTROLLED-DEMO.md) | MERGED; DEPLOYED EXPERIMENTAL DEMO | PR #13 merged at `67a71ab`; owner-only external HTTPS acceptance passed. Temporary host/credentials remain private and the link depends on the reference Mac remaining awake with the owned services running. |

Tasks 2–4 run in dependency order. Task 6's v2 worker rebuild/qualification follows reviewed Task 2 source before the genuine Task 4 canary. Task 5 consumes the frozen v0.3 contract; delivery waits for reviewed application/build. One accountable writer owns each bounded scope; shared-contract/manifest writes remain sequential. No standing scheduler is installed and this table makes no claim that another chat is active.

## Scoring, data and delivery gates

- **Verified/scientific accuracy: unknown.** `verified_score` remains null; verified truth_status remains UNKNOWN. D03–D06 scientific/benchmark validation is open. DEC-023 authorizes only the labeled versioned experimental agreement channel, not validated semantics or a commercial multi-model roster.
- Missing, partial, unreadable, ambiguous, mismatched or unprocessed truth remains null/Accuracy unknown. Reference material is evaluation-only and excluded from prediction inputs. Timeout/refusal/malformed/error are technical outcomes, not factual error.
- No private/institutional data, credentials/raw payloads in this public repository, paid resources, destructive external actions or unrestricted public release. Lab/data authorization is not obtained by an engineering decision.
- **Controlled link: live and owner-authenticated.** External acceptance returned 401 without credentials, 200 for authenticated UI/API/assets, and 403 for a wrong-origin mutation. A synthetic upload completed two genuine Qwen attempts with target scores 1.3/1.5 and document/model score 1.4; verified scores remained null. Repeated GET returned identical attempt IDs and results. The hostname and credentials are delivered privately, not committed. This is not a multi-user/permanent service or clean-recipient qualification.

## Next action and completion evidence

The [final review record](handoffs/RL-EXP-015-final-review-9aea516.md) documents the spaced-sign correction and exact-candidate independent acceptance. [PR #13](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/13) merged the reviewed candidate as `67a71ab`. The [delivery handoff](handoffs/RL-LINK-017-lead-20261106T002131Z-live.md) records the external synthetic acceptance and operating limits. Next work is scientific validation, broader model coverage, and a permanent deployment only after their separate decisions/credentials/cost authority; none is implied by this demo.
