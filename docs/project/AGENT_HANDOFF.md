# Agent handoffs and task packets

This file is the Lead-maintained routing/index record. Each specialist writes a separate task-scoped artifact to avoid competing edits to one shared log. The individual record is evidence; this index is a discoverability aid.

## Initial inbox

| Item | Sender -> receiver | State | Next action |
| --- | --- | --- | --- |
| E0001 / RL-OPS-001 coordination baseline | Setup -> all roles | AVAILABLE; no receiver acknowledgment recorded | Read current HEAD and instructions on first active task. |
| E0002 / DEC-007..009 system-design update | Lead -> Research, Backend, Frontend, QA | AVAILABLE; no receiver acknowledgment recorded | At next active task, read the current decisions plus relevant architecture/interfaces; apply automatic target detection and canonical prediction-context rules. |
| E0003 / DEC-010 reference-alignment update | Lead -> Research, Backend, Frontend, QA | AVAILABLE; no receiver acknowledgment recorded | Use text-first global+local anchor alignment; preserve exact revealed spans; treat ambiguous/partial/unreadable mappings as unknown/null; D03 criteria still require research sign-off. |
| E0004 / DEC-011..017 owner-approved design directions | Lead -> Research, Backend, Frontend, QA | AVAILABLE; not acknowledged | Read new decisions and role-relevant contracts; do not treat specialized sign-offs as granted; no extra spending. |
| E0005 / RL-MVP-PLAN-001 Oct 14 checkpoint | Lead -> Research, Backend, Frontend, QA | AVAILABLE; NOT ACKNOWLEDGED | Read DEC-018, [proposed MVP design](../../docs/superpowers/specs/2026-10-07-oct14-mvp-design.md), [roadmap](plans/2026-10-07-weekly-implementation-roadmap.md) and relevant packet. Do not code before owner design/plan approval. |
| E0006 / RL-MVP-PLAN-001 detailed plan + role kickoffs | Lead -> Backend, Research, Frontend, QA | AVAILABLE; NOT ACKNOWLEDGED | Read [implementation plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md) and your role kickoff ([Backend](kickoffs/BACKEND.md), [Research](kickoffs/RESEARCH.md), [Frontend](kickoffs/FRONTEND.md), [QA](kickoffs/QA.md)); prepare only, no code until owner plan and packet approval. |
| E0007 / RL-MVP-001 authorization | Lead -> Backend/Codex, Research, QA | APPROVED TASK; NOT ACKNOWLEDGED | Codex may implement only Task 1 after current-HEAD check and preflight; publish branch/commit, tests and unique handoff. Research checks truth/null semantics; QA independently reviews exact candidate. No main merge. |
| E0008 / RL-MVP-001 Backend candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; not independently verified | [Candidate handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/b0282281e72f37c1cd1f7899d09691024991d150/docs/project/handoffs/RL-MVP-001-backend-20261008T015431Z-8fff5f1.md), branch `codex/rl-mvp-001-contracts-fixtures` @ `b0282281e72f37c1cd1f7899d09691024991d150`. QA use [review packet](task_packets/RL-MVP-001-QA-review.md); Research use [contract packet](task_packets/RL-MVP-001-RESEARCH-review.md). No merge. |
| E0009 / RL-MVP-001 corrected QA review | QA -> Lead | PASS for Task 1; not scientific validation | Review `a1d8311`; handoff branch `qa/rl-mvp-001-corrected-a1d8311` at `046c8b3a`; 43 original tests, 11 adversarial passes, 1 deselected. |
| E0009 / RL-MVP-001 corrected Research review | Research -> Lead | PASS for contract semantics; not scientific validation | Review `a1d8311`; handoff branch `review/rl-mvp-001-research-corrected-e0008` at `a597ee23`; 13 independent checks. |
| E0009 / RL-MVP-001 integration gate | Lead -> owner | AWAITING MERGE AUTHORIZATION | Candidate branch `codex/rl-mvp-001-contracts-fixtures` at `c698cd4`; no merge or Task 2 until explicitly authorized. |
| E0010 / RL-MVP-001 integration | Lead -> Backend, Research, Frontend, QA | MERGED; no receiver ACK | Owner-authorized [PR #1](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/1) at `ba60aaa8` integrated reviewed contracts and fixtures. Task 2 not authorized; next roles read current main. |
| E0011 / RL-MVP-002 Codex kickoff | Lead -> Backend, QA, Research | APPROVED TASK; no receiver ACK | [Task packet](task_packets/RL-MVP-002-detection-canonicalization.md): safe vector-PDF text redaction detection and canonicalization, synthetic TDD, new branch and handoff. No merge or Task 3. |
| E0012 / RL-MVP-002 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; NOT VERIFIED | Branch `codex/rl-mvp-002-detection-canonicalization` @ `a6a603f6b11472df5cf36d2acd9eeec215fe81af`, implementation `430467314ca992f36cf3eaab9d49cde45a9805ac`, [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/a6a603f6b11472df5cf36d2acd9eeec215fe81af/docs/project/handoffs/RL-MVP-002-backend-20261008T033731Z-4304673.md). QA use [packet](task_packets/RL-MVP-002-QA-review.md), Research use [packet](task_packets/RL-MVP-002-RESEARCH-review.md). No merge/Task 3. |
| E0013 / RL-MVP-002 QA review | QA -> Lead, Backend | FAIL / CHANGES_REQUESTED | [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/48adf452178e1e7c38896b088f2e7481846bf275/docs/project/handoffs/RL-MVP-002-qa-20261008T123940Z-4304673.md) on `48adf452178e1e7c38896b088f2e7481846bf275`: 3 blockers, focused probes, full candidate suite not rerun. |
| E0013 / RL-MVP-002 Research review | Research -> Lead, Backend | CHANGES_REQUESTED | [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/a0d56b599a5ba284ef036b813fa8167164189847/docs/project/handoffs/RL-MVP-002-research-20261008T121239Z-rsem02.md) on `a0d56b599a5ba284ef036b813fa8167164189847`: 2 blockers, focused probes, no full suite rerun. |
| E0013 / RL-MVP-002 Correction 01 | Lead -> Backend/Codex, QA, Research | CORRECTION ROUTED; no receiver ACK | [Packet](task_packets/RL-MVP-002-CORRECTION-01.md): 4 blocking issues, minimal additive fixes, TDD, new SHA/handoff, fresh QA/Research review. No merge/Task 3. |
| E0014 / RL-MVP-002 corrected candidate | Backend/Codex -> Lead, QA, Research | CORRECTED_READY_FOR_REVIEW; NOT VERIFIED | Implementation `12698b92d883af658266d54a9223b5619dedc7ee`, branch head `c37837669ce9e538a3afa8db0e25ef92cbbdd327`, [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/c37837669ce9e538a3afa8db0e25ef92cbbdd327/docs/project/handoffs/RL-MVP-002-backend-20261008T141115Z-12698b9.md). QA and Research use [fresh review packet](task_packets/RL-MVP-002-CORRECTED-REVIEW.md); no merge/Task 3. |
| E0015 / DEC-020 deadline change | Lead -> all four roles | OWNER-APPROVED; no ACK | First MVP checkpoint **October 12, 2026**, replacing October 14. Read updated [roadmap](plans/2026-10-07-weekly-implementation-roadmap.md) and [implementation plan](../../docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md). Scope, safety, cost and reviews unchanged. |
| E0015 / RL-MVP-002 Correction 02 | Lead -> Backend/Codex, QA, Research | ROUTED; not acknowledged | [Correction packet](task_packets/RL-MVP-002-CORRECTION-02.md) covers sparse side columns and boundary standalone black boxes. Owner says prompt already sent; no new SHA yet. No merge or Task 3. |
| E0016 / RL-MVP-002 Correction 02 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; no independent PASS | Implementation `ea930abef319832cf494df5851be1b19d3e2cf1c`, branch head `e5333602c43d304a21980fc96103d19599e2dd27`, [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/e5333602c43d304a21980fc96103d19599e2dd27/docs/project/handoffs/RL-MVP-002-backend-20261008T151310Z-ea930ab.md). [Fresh QA/Research packet](task_packets/RL-MVP-002-CORRECTION-02-REVIEW.md). No merge/Task 3. |
| E0017 / RL-MVP-002 Correction 02 QA | QA -> Lead, Backend | FAIL | [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/941a9b9b2ff4f1b39aa105122670aad42ad07ef2/docs/project/handoffs/RL-MVP-002-qa-20261008T150000Z-ea930ab.md) on `941a9b9b2ff4f1b39aa105122670aad42ad07ef2`; staggered one-line columns and boundary no-glyph rectangle still unsafe. |
| E0017 / RL-MVP-002 Correction 02 Research | Research -> Lead, Backend | CHANGES_REQUESTED | [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/e1ea57d2cbbedd603637ac79dfffbeda48fe0c5c/docs/project/handoffs/RL-MVP-002-research-20261008T152306Z-correction02.md) on `e1ea57d2cbbedd603637ac79dfffbeda48fe0c5c`; boundary no-glyph issue remains; no scientific score approval. |
| E0017 / RL-MVP-002 Correction 03 | Lead -> Backend/Codex, QA, Research | ROUTED; no receiver ACK | [Packet](task_packets/RL-MVP-002-CORRECTION-03.md) addresses both residual cases with TDD and negative controls. New exact SHA/handoff and fresh reviews required; no merge/Task 3. |
| E0018 / RL-MVP-002 Correction 03 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; no independent PASS | Implementation `dbae9f79d1d4dcee1aba09978713e27d6939f77e`, branch head `821f57348c49845e4d922122cb575e569f22d82c`, [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/821f57348c49845e4d922122cb575e569f22d82c/docs/project/handoffs/RL-MVP-002-backend-20261008T153344Z-dbae9f7.md). [QA/Research review packet](task_packets/RL-MVP-002-CORRECTION-03-REVIEW.md). No merge or Task 3. |
| E0019 / RL-MVP-002 Correction 03 QA | QA -> Lead, Backend | FAIL | [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/b18f947639713b255d2c88adbc1dfbe03832417e/docs/project/handoffs/RL-MVP-002-qa-20261008T150800Z-dbae9f7.md): sparse columns, short boundary boxes, heading false positive. |
| E0019 / RL-MVP-002 Correction 03 Research | Research -> Lead, Backend | CHANGES_REQUESTED | [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/48377ce048b538a7f80bf962177f1d9b61e37483/docs/project/handoffs/RL-MVP-002-research-20261008T154640Z-correction03.md): 16/22 expectations; sparse columns and short boundary boxes. |
| E0019 / RL-MVP-002 Correction 04 | Lead -> Backend/Codex, QA, Research | ROUTED; no ACK | [Packet](task_packets/RL-MVP-002-CORRECTION-04.md): conservative supported-layout boundary, 3 regression classes, new exact SHA and fresh reviews; no merge/Task 3. |
| E0020 / RL-MVP-002 Correction 04 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; not independently verified | Implementation `df20fe074c0bebc7be15971199d3c361469bc6b1`, branch head `6ba3e02af0d13b8ef673ac007f06d08912ff9e38`; [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/6ba3e02af0d13b8ef673ac007f06d08912ff9e38/docs/project/handoffs/RL-MVP-002-backend-20261008T181752Z-df20fe0.md). Review [packet](task_packets/RL-MVP-002-CORRECTION-04-REVIEW.md) on exact SHA. No merge/Task 3. |
| E0021 / RL-MVP-002 Correction 04 review | QA + Research -> Lead | QA FAIL; Research PASS for Task-2 semantics | QA found remote x-aligned non-text artwork false rejection on `df20fe0`; Research PASS does not override QA. |
| E0021 / RL-MVP-002 Correction 05 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; no independent PASS | Implementation `736fa18419340b9fcb8dd5e121e8eebcc24b22f7`, branch head `395d2321012092bd619a34711cb0b4ca4855abf2`; [review packet](task_packets/RL-MVP-002-CORRECTION-05-REVIEW.md). No merge or Task 3. |
| E0022 / RL-MVP-002 Correction 05 QA | QA -> Lead | PASS for scoped software QA | [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/986c525778db7229315940da638d724267a4407b/docs/project/handoffs/RL-MVP-002-qa-20261008T190000Z-736fa18.md) at `986c525778db7229315940da638d724267a4407b`, exact candidate `736fa18419340b9fcb8dd5e121e8eebcc24b22f7`; isolated probes; full repository suite not independently run. |
| E0022 / RL-MVP-002 Correction 05 Research | Research -> Lead | PASS for Task-2 semantics, not scientific validation | [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/38dacef1091a4849fda0acce9444873a87499401/docs/project/handoffs/RL-MVP-002-research-20261008T190900Z-correction05.md) at `38dacef1091a4849fda0acce9444873a87499401`, exact candidate `736fa18419340b9fcb8dd5e121e8eebcc24b22f7`; 22 isolated checks and canonical probe; no scientific score approval. |
| E0022 / RL-MVP-002 integration gate | Lead -> owner | AWAITING MERGE APPROVAL; no ACK | Reviewed Backend branch `codex/rl-mvp-002-detection-canonicalization` @ `395d2321012092bd619a34711cb0b4ca4855abf2`; no merge or Task 3 until separately authorized. |
| E0023 / RL-MVP-002 integration | Lead -> Backend, QA, Research, Frontend | MERGED via owner-approved PR #2; no receiver ACK | Reviewed `736fa18` merged at `35281fb9`; detector/canonicalizer and tests now on main. Task 3 not approved. Consume current main contracts and maintain redacted-only, null-score, no-spend gates. |
| E0024 / RL-MVP-003 Codex kickoff | Lead -> Backend/Codex, QA, Research | OWNER-APPROVED TASK; no receiver ACK | [Task packet](task_packets/RL-MVP-003-text-first-reference-alignment.md) authorizes only new reference.py, test_reference.py and unique Backend handoff. Deterministic word-first global/local alignment; null truth on ambiguity/partial revelation; no merge or Task 4. |
| E0025 / RL-MVP-003 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; no independent PASS | Implementation `931fb1c0012d3b530b837f204d922f0aaa95a602`, branch head `2d79ee6a7d5ba2a06148ff257529faa50dfa06e1`, [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/2d79ee6a7d5ba2a06148ff257529faa50dfa06e1/docs/project/handoffs/RL-MVP-003-backend-20261008T201401Z-931fb1c.md). [QA/Research packet](task_packets/RL-MVP-003-INDEPENDENT-REVIEW.md). No merge/Task 4. |
| E0026 / RL-MVP-003 independent QA | QA -> Lead, Backend | FAIL | [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/007eb0e242a3f43cc01843d0713442a7f02e1e1f/docs/project/handoffs/RL-MVP-003-qa-20261008T202300Z-931fb1c.md): one-sided false confirmation, geometry fallback and lost target-edge whitespace. |
| E0026 / RL-MVP-003 independent Research | Research -> Lead, Backend | CHANGES_REQUESTED | [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/6406a25012801c3850a10e65c4dc8a11036b7c5a/docs/project/handoffs/RL-MVP-003-research-20261008T205700Z-review.md): wrong-release local anchors, one-sided support and exact-span issues; D03 unapproved. |
| E0026 / DEC-021 + RL-MVP-003 Correction 01 | Lead -> Backend/Codex, QA, Research | OWNER-APPROVED; receiver ACK pending | [Task packet](task_packets/RL-MVP-003-CORRECTION-01.md) authorizes only reference.py/test_reference.py and new Backend handoff; trusted DocumentVersion SHA/role/project/version, two-sided support and exact source span or null. New SHA/reviews required. No merge or Task 4. |
| E0027 / RL-MVP-003 trust boundary stop | Backend/Codex -> Lead, owner | BLOCKED; rejected candidate NOT PUBLISHED | Backend reports fabricated DocumentVersion can produce false CONFIRMED and partial punctuation can be omitted. Local rejected `80f9ee1` not pushed; remote Backend branch still `2d79ee6`. |
| E0027 / DEC-022 trust-boundary proposal | Lead -> owner, Backend, Research, QA | PROPOSED; OWNER APPROVAL PENDING | [Proposal](task_packets/RL-MVP-003-TRUST-BOUNDARY-PROPOSAL.md): synthetic-only trusted fixture pairing for October 12, arbitrary uploads unconfirmed; alternative broader authenticated intake. No code/merge/Task 4 until approval. |
| E0028 / DEC-022 synthetic trust correction | Lead -> Backend/Codex, QA, Research, Frontend | OWNER-APPROVED; no receiver ACK | [Task packet](task_packets/RL-MVP-003-TRUSTED-SYNTHETIC-CORRECTION.md): pinned synthetic redacted/reference pair hashes and identity, no caller-created trust, both-side word evidence, exact punctuation or null. Arbitrary uploads unknown; new exact SHA/reviews; no merge/Task 4. |
| E0029 / RL-MVP-003 DEC-022 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; independent verdicts pending | Implementation `8a751d4af27c8daada1071ec6c9c4fce45581d61`, branch head `cd4cbfafbfe0152adc8c8e68a6cf337f20348814`; [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/cd4cbfafbfe0152adc8c8e68a6cf337f20348814/docs/project/handoffs/RL-MVP-003-backend-20261009T010827Z-8a751d4.md). [QA/Research packet](task_packets/RL-MVP-003-DEC022-INDEPENDENT-REVIEW.md). No merge/Task 4. |
| E0031 / RL-MVP-003 Correction 02 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; no new independent verdict | Implementation `97db3615c65b9e31d0f94dca443baab760340c5f`, published head `139921de76f9f3d0a67af19217e0969464f88ffd`; [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/139921de76f9f3d0a67af19217e0969464f88ffd/docs/project/handoffs/RL-MVP-003-backend-20261009T020728Z-97db361.md), [review packet](task_packets/RL-MVP-003-DEC022-CORRECTION-02-REVIEW.md). No merge/Task 4. |
| E0032 / RL-MVP-003 Correction 02 QA | QA -> Lead | PASS for scoped software/provenance | [QA handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/b43682a241bae616b7735c6980553036ff693d5e/docs/project/handoffs/RL-MVP-003-qa-20261009T024200Z-97db361.md) at `b43682a241bae616b7735c6980553036ff693d5e`; exact `97db3615c65b9e31d0f94dca443baab760340c5f`, independent synthetic probes; full repository suite NOT RUN. |
| E0032 / RL-MVP-003 Correction 02 Research | Research -> Lead | PASS for Task-3 trust/truth semantics, not D03 | [Research handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/12ff6e67770f841a4c4dfbf9928cc5e8e32a102b/docs/project/handoffs/RL-MVP-003-research-20261009T025500Z-dec022-correction02.md) at `12ff6e67770f841a4c4dfbf9928cc5e8e32a102b`; exact `97db3615c65b9e31d0f94dca443baab760340c5f`, 20/20 independent probes; full repository suite NOT RUN. |
| E0032 / RL-MVP-003 merge gate | Lead -> owner | AWAITING OWNER MERGE AUTHORIZATION; no ACK | Reviewed Backend branch `codex/rl-mvp-003-text-first-reference-alignment` at `139921de76f9f3d0a67af19217e0969464f88ffd`; no merge or Task 4 until separately approved. |
| E0033 / RL-MVP-003 owner-approved integration | Lead -> Backend, QA, Research, Frontend | MERGED via PR #3; no receiver ACK | Reviewed `97db3615` merged at `733ae0245350439d795f86a7b68d3552cca6a3d2`; reference aligner and synthetic registry/tests now on main. DEC-022 synthetic-only unknown/null for arbitrary references, D03 unapproved. Task 4 not authorized. |
| E0034 / RL-MVP-004 owner authorization | Lead -> Backend/Codex, QA, Research | APPROVED TASK; no receiver ACK | [Packet](task_packets/RL-MVP-004-prediction-adapter-durable-worker-PROPOSED.md): mock-tested redacted-only adapter, durable one-shot worker, read-only local feasibility preflight. No real inference, downloads, additional spend, Task 5+, merge or deployment. |
| E0035 / RL-MVP-004 candidate | Backend/Codex -> Lead, QA, Research | READY_FOR_REVIEW; real model BLOCKED | Implementation `c3a928ce1aaf2039bc778cb91c272b435fb93aa4`, published branch head `de9ad26f7225f5717d2c6ace683e1f21b0fed2fa`; [Backend handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/de9ad26f7225f5717d2c6ace683e1f21b0fed2fa/docs/project/handoffs/RL-MVP-004-backend-20261009T134815Z-c3a928c.md). [Independent review packet](task_packets/RL-MVP-004-INDEPENDENT-REVIEW.md). No merge, inference or Task 5. |
| E0036 / RL-MVP-004 Correction 01 reviews and integration | QA + Research -> Lead -> all roles | MERGED; no receiver ACK | Owner-approved [Correction 01 packet](task_packets/RL-MVP-004-CORRECTION-01.md) scoped ten code/test files. Exact candidate `b9ce8182751f26109fbd857bcb8d909720bafd13`; Backend head `fb4c1f054afc35188ad1a086221bc96dd78d1b18`. QA PASS [handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/8aadbe8259e939a17a4646bbae911b69f83f96b2/docs/project/handoffs/RL-MVP-004-qa-20261009T211127Z-b9ce818.md): independently 102 focused/255 full, 27 selected, 15 probes. Research scoped PASS [handoff](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/blob/3f7c51d45361a8ccea047e58bc9809f1ea374a6f/docs/project/handoffs/RL-MVP-004-research-20261009T180400Z-correction01.md): protocol checks, not D03/D05. Owner-authorized [PR #4](https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard/pull/4) merged `8f4d2f18`. No real inference, Task 5, scientific approval or deployment. |
| E0037 / RL-MVP-005 research-only authorization | Lead -> Research | APPROVED TASK; receiver ACK pending | Owner-approved [Task 5 packet](task_packets/RL-MVP-005-RESEARCH-PROPOSAL.md) now published on main after initial Lead branch `fe7a5031`. Research may create exactly the rubric proposal, synthetic evaluation_cases.json and a unique Research handoff on an isolated branch. No scientific validation, evaluator code, merge, Task 6, inference or costs. |
| Next S1 packet | Lead -> owner / relevant roles | NOT APPROVED | Resolve blocking decisions and propose one narrow packet. |

No review, implementation completion or running agent is implied by these rows.

## Role routing

| Role | Owns proposals/evidence in | Receives changes about |
| --- | --- | --- |
| Lead / Architect | Canonical eight files; integration/sequence | All cross-role changes, holds, approvals, blockers |
| Research / Evaluation | Research method, reference/rubric design, benchmark evidence | Truth, scoring, attempts, denominators, model conditions |
| Backend / Infrastructure | Architecture/contracts and implementation task artifacts | Input/version/state contracts, data policy, provider behavior |
| Frontend / Product | UI/task artifacts and usability evidence | Target IDs/locators, null states, labels, status and API contracts |
| QA / Independent Reviewer | Independent review records only | Exact candidate SHA, acceptance scope, changed contracts and risks |

Roles are logical assignments, not separate credentials or automatically running processes. A reviewer must assess a candidate independently; do not present one agent's self-review as independent review.

## Handoff naming

Use `docs/project/handoffs/<TASK-ID>-<ROLE>-<UTC-TIMESTAMP>-<SHORT-ID>.md` on the approved task branch. ROLE is lead/research/backend/frontend/qa. UTC timestamp format is YYYYMMDDTHHMMSSZ; SHORT-ID prevents a name collision. Create the directory with the first real artifact, not a fake completed task.

Append corrections as a new record that references the old one; do not erase past evidence. The Lead links active records here after authorized integration. A branch-only record is not canonical and cannot be assumed visible to another session. For read-only review, provide a NOT PUBLISHED record in chat when no write scope exists.

## Handoff template (all fields required; explicit not-applicable is valid)

```text
Task ID:
Role / session label:
UTC time:
State: PROPOSED | APPROVED | IN_PROGRESS | BLOCKED | ON_HOLD |
       READY_FOR_REVIEW | CHANGES_REQUESTED | VERIFIED | MERGED | DEPLOYED
Baseline integration SHA / decision epoch:
Candidate branch / exact commit SHA (or no code change):
Source requirements / approved decisions / contract versions:
Authorization reference and permitted file/action scope:
Work performed / artifacts and exact paths:
Tests actually run / command / result / environment:
Tests not run and reason:
Independent review evidence (or not yet reviewed):
Research / data approval evidence (or not approved / not applicable):
Known issues / risks / stale dependencies:
Affected roles / requested next action:
Last freshness check and relevant differences:
Rollback or correction approach:
Publication: PUBLISHED on <branch/ref> | NOT PUBLISHED
```

Do not copy sample commit hashes or test counts as real results. Do not put secrets/raw documents in records. References to external private evidence must not disclose that evidence publicly.

## Acknowledgment

A receiving role records `ACK <decision/epoch or handoff ID> | role | observed SHA | time | affected task | understood impact` in its next handoff. The Lead updates this index. ACK means received/read, not approval or work completion. Unknown acknowledgment is NOT ACKNOWLEDGED; no polling job may fabricate it.

## Task packet template

```text
Task ID / state / single owner:
Objective / non-goals:
Rxx requirements / DEC decisions / unresolved Dxx gates:
Baseline SHA / prerequisites:
Inputs / outputs / exact contract versions:
Allowed files, actions and artifact publication scope:
Tests and acceptance evidence:
Data, provider, cost and runtime limits:
Consumers and expected handoffs:
Independent reviewer / required human approvals:
Rollback / stop conditions:
```

Routine task updates and handoff publication should be authorized in this packet once, not renegotiated every turn. It does not authorize unrelated main-branch writes, merging or deployment.

## State transitions and closure

PROPOSED -> APPROVED requires the relevant owner's authorization. APPROVED -> IN_PROGRESS requires a recorded task owner and fresh baseline. READY_FOR_REVIEW means evidence is submitted, not verified. QA may return CHANGES_REQUESTED. VERIFIED needs independent evidence and applicable human sign-off. MERGED requires a real integration commit and authorization; DEPLOYED requires a verified environment/release record. Any affected active task may become BLOCKED or ON_HOLD. Reopen stale reviews when their candidate or governing decision changes.
