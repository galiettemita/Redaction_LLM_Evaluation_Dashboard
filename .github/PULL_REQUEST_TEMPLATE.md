## Task and authority

- Task ID / owner role:
- Requirement IDs and approved decision IDs:
- Baseline integration SHA / decision epoch:
- Authorized scope and non-goals:

## Change

What changed, why, and which producer/consumer interfaces are affected? Distinguish a proposal from an approved behavior change. Link the task-scoped handoff.

## Evidence

- Candidate commit SHA:
- Exact checks run, results and environment:
- Checks not run and why:
- Research benchmark impact and required human approval:
- Data/security implications:
- UI/unknown-state/aggregation effects:
- Rollback:

## Review checklist

- [ ] Current integration HEAD and relevant decisions rechecked; overlap reconciled.
- [ ] No reference leakage; unknown truth remains unscored where relevant.
- [ ] No unapproved scope, stack, provider or scoring changes.
- [ ] No private data, secrets or raw research payloads in this public repository.
- [ ] Relevant tests and regression evidence are attached; unrun checks are explicit.
- [ ] Independent review targets this exact candidate, not an older revision.
- [ ] Necessary human approvals are recorded, not inferred from agent agreement.
- [ ] Handoff/state/decision updates are included or explicitly not applicable.
- [ ] Merge/deploy authority is established separately; no automatic release assumed.

Unchecked boxes are not evidence. This template is a review aid, not an enabled CI gate or branch protection.
