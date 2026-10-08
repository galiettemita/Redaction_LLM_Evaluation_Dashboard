# RL-MVP-001 corrected Research semantics review

Task ID: RL-MVP-001
Role / session label: Research / Evaluation corrected-candidate reviewer
UTC time: 2026-10-08T02:53:15Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR RL-MVP-001 CONTRACT SEMANTICS; NOT SCIENTIFICALLY VERIFIED
Baseline integration SHA / decision epoch: e2460ca2c931ca387e75274f498316884ba4dd3f / E0008
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-001-contracts-fixtures / corrected implementation commit a1d831153c726db38fc0c403c4d6d80893f657a5; published Backend handoff at branch head c698cd4876af221ba24b85f5ad2d1b2e15c43d04.
Source requirements / approved decisions / contract versions: R01-R12 as applicable; DEC-001..019, especially DEC-001, DEC-004, DEC-005, DEC-008, DEC-010..014; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; RL-MVP-001 implementation packet; corrected-review packet docs/project/task_packets/RL-MVP-001-CORRECTED-REVIEW.md; prior Research review 12795b2a79a4eb0581c6699882b01c32a6e604e4.
Authorization reference and permitted file/action scope: Corrected-review packet authorizes independent Research review of exact implementation commit a1d831153c726db38fc0c403c4d6d80893f657a5 and publication of a unique role-specific handoff. No implementation-code edits, merge, Task 2, paid calls, provider access, or scientific-validity claim.

Work performed / artifacts and exact paths:
- Refreshed live main and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, and docs/project/task_packets/RL-MVP-001-CORRECTED-REVIEW.md.
- Inspected exact candidate source at a1d831153c726db38fc0c403c4d6d80893f657a5: src/redaction_lab/contracts.py, src/redaction_lab/fixtures.py, tests/test_contracts.py, tests/test_fixtures.py, pyproject.toml.
- Read corrected Backend handoff docs/project/handoffs/RL-MVP-001-backend-20261008T024109Z-a1d8311.md at branch head c698cd4876af221ba24b85f5ad2d1b2e15c43d04.
- Compared prior implementation 8fff5f11cd9ce0c1e2ca7943aab7d02f629eff58 to corrected a1d831153c726db38fc0c403c4d6d80893f657a5 and verified the branch-head delta after a1d8311 is handoff-only.

## Resolution of prior Research findings

1. RESOLVED — CONFIRMED truth prerequisites. ReferenceMapping now requires nonblank project/document/version identity, exact revealed text, token locator, redacted/reference canonical version+hash bindings, global alignment version, left/right anchor evidence or explicit document-boundary evidence, and candidate_unique/complete_revelation/readable/reliably_aligned=true before CONFIRMED can be SCOREABLE.
2. RESOLVED AT TASK-1 CONTRACT LEVEL — VERIFIED prerequisites. EvaluationRecord now requires COMPLETE process state, SUCCEEDED attempt snapshot, complete mapping identity snapshot, CONFIRMED + SCOREABLE mapping snapshot, score_scale_id, verified_score, and research_validation_id. This does not prove those referenced records/approvals actually exist; cross-record existence/same-project/current-version validation remains a future transactional requirement as the corrected-review packet states.
3. RESOLVED — evaluation process versus score validity are separate axes: EvaluationProcessStatus {COMPLETE, NEEDS_REVIEW, DISAGREEMENT, ERROR} and ScoreStatus {NONE, EXPERIMENTAL, VERIFIED}. Non-complete process states cannot carry a score channel.
4. RESOLVED — prediction settings escape hatch. PredictionSettings is an allow-listed frozen model containing only temperature; extra/nested reference, evaluator, retrieval, or web fields are rejected in PredictionManifest and RunDefinition settings.
5. RESOLVED — deep immutability of the previously mutable nested evidence/config objects. DetectionEvidence, PredictionSettings, TokenUsage and FactComparison are frozen typed value objects held through immutable tuples where applicable.
6. RESOLVED — no arbitrary 0..1 research scale is imposed. Numeric fields use FiniteFloat without a range constraint and any numeric score requires a versioned score_scale_id. EXPERIMENTAL cannot claim research_validation_id; VERIFIED requires one. No weight, cutoff, formula, or scientific interpretation is created by this contract.
7. RESOLVED FOR TASK-1 CONTRACT SCOPE — SummarySnapshot now carries summary_level, scope identity/version, exact included and eligible evaluation IDs, common_eligible_set_id, aggregation_version, explicit outcome counts, denominator consistency checks, separate verified/experimental channels, and zero-eligible => null-score validation. Verification that referenced records belong to the same actual common set remains future transactional/service work.
8. RESOLVED FOR TASK-1 CONTRACT SCOPE — project_id is present on all relationship-bearing records reviewed. Same-project equality, referential existence, supersession/current-version checks remain intentionally deferred to the future persistence/evaluation boundary and are not proof of validated scoring.
9. RESOLVED — missing partial-truth fixture. partially_revealed_reference now represents one contiguous target fully hidden in the redacted release while the reference reveals ORCHARD and keeps SEVEN visually hidden; the underlying text layer remains extractable, preserving an adversarial trap for later visibility-aware processing.

## Independent tests performed

Direct network git clone was unavailable in the review environment (DNS resolution failure), so I did not claim a byte-for-byte checkout execution of the repository's reported 43-test suite. I inspected the exact candidate files through the live GitHub connector and reproduced the candidate contracts/fixture logic in an isolated local harness for independent adversarial behavior checks.

Command:
- cd /mnt/data/rl_corrected && PYTHONPATH=. pytest -q
Result:
- 13 passed in 0.22s

Independent checks covered:
- confirmed mapping missing required evidence and false uniqueness/completeness/readability/reliability flags;
- explicit document-boundary alternative to missing anchors;
- non-confirmed truth cannot be SCOREABLE or expose exact full truth;
- nested/top-level answer-bearing prediction settings rejection;
- deep immutability of detector evidence, run/manifest settings, usage and fact evidence;
- evaluator workflow/score-channel independence;
- VERIFIED prerequisites including successful attempt, confirmed scoreable mapping, scale identity and research-validation identity;
- scale neutrality using negative and >100 EXPERIMENTAL values with versioned scales;
- summary level/common-set/eligible membership, duplicate IDs, partition counts and zero-denominator null behavior;
- project scope on relationship records;
- partial-reference fixture generation and retained hidden text-layer trap;
- partial truth cannot produce a numeric evaluation;
- all-or-none mapping snapshot fields;
- exactly-one target marker invariant.

Additional command:
- python -m compileall -q redaction_lab test_research_review.py
Result:
- PASS

Backend-reported evidence reviewed but not independently adopted as my own: focused/full suite 43 passed at candidate preparation. I did not rerun the exact repository test files because a network checkout was unavailable.

## Remaining gaps / non-blocking cautions

- Cross-record existence, same-project equality, immutable-version currentness/supersession, and resolution of research_validation_id to a real human-approved validation release are not established by standalone Pydantic records. They must be enforced transactionally by the later persistence/evaluation boundary before any verified score is accepted.
- ScoreStatus.VERIFIED and a nonblank research_validation_id are representational capability only. They are not evidence that D03-D06 or scientific validation has occurred.
- PARTIAL mappings correctly remain non-scoreable and cannot populate exact_revealed_text. If later UI/research requirements need structured preservation of visibly known fragments from a partial reference, add a separate non-scoreable observed-fragment field rather than reusing the full-truth field. This is not required to clear the current RL-MVP-001 acceptance packet.
- Model/tool protocol enforcement, evaluator semantics, score mapping, aggregation method selection and human benchmark calibration remain later tasks/approvals; this review does not authorize them.

Tests not run and reason: exact repository 43-test suite not independently executed because direct GitHub clone/network checkout was unavailable; no model/provider/API/UI/worker/reference-aligner/evaluator-service/persistence/deployment tests are in this Research review scope.
Independent review evidence (or not yet reviewed): This handoff is a fresh Research/Evaluation review of exact corrected implementation commit a1d831153c726db38fc0c403c4d6d80893f657a5. Prior CHANGES_REQUESTED verdict was not carried over.
Research / data approval evidence (or not approved / not applicable): Research-human approval NOT OBTAINED. D03-D06 remain open. Synthetic-only review; no institutional data approval claimed.
Known issues / risks / stale dependencies: No blocking Research contract-semantics defect remains from my prior review within RL-MVP-001 scope. The transactional gaps above must remain explicit and cannot be presented as solved by these schemas.
Affected roles / requested next action: Lead should reconcile this Research PASS with fresh QA review of the same exact corrected SHA. Do not merge or start Task 2 based on this Research handoff alone; separate owner/Lead authorization and QA evidence remain required.
Last freshness check and relevant differences: Live main rechecked immediately before publication at e2460ca2c931ca387e75274f498316884ba4dd3f, epoch E0008. Corrected implementation SHA remains a1d831153c726db38fc0c403c4d6d80893f657a5; branch head c698cd4876af221ba24b85f5ad2d1b2e15c43d04 differs from implementation only by the Backend handoff commit.
Rollback or correction approach: This review branch contains only this role-specific handoff. If candidate or governing decisions change, treat this review as stale and publish a new review against the new exact SHA.
Publication: PUBLISHED on review/rl-mvp-001-research-corrected-e0008; not merged to main.
