# Agent handoffs and task packets

This file is the Lead-maintained routing/index record. Each specialist writes a separate task-scoped artifact to avoid competing edits to one shared log. The individual record is evidence; this index is a discoverability aid.

## Initial inbox

| Item | Sender -> receiver | State | Next action |
| --- | --- | --- | --- |
| E0001 / RL-OPS-001 coordination baseline | Setup -> all roles | AVAILABLE; no receiver acknowledgment recorded | Read current HEAD and instructions on first active task. |
| E0002 / DEC-007..009 system-design update | Lead -> Research, Backend, Frontend, QA | AVAILABLE; no receiver acknowledgment recorded | At next active task, read the current decisions plus relevant architecture/interfaces; apply automatic target detection and canonical prediction-context rules. |
| E0003 / DEC-010 reference-alignment update | Lead -> Research, Backend, Frontend, QA | AVAILABLE; no receiver acknowledgment recorded | Use text-first global+local anchor alignment; preserve exact revealed spans; treat ambiguous/partial/unreadable mappings as unknown/null; D03 criteria still require research sign-off. |
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
