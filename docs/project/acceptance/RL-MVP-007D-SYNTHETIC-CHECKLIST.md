# RL-MVP-007D synthetic acceptance preparation — E0052

Status: **PREPARED, NOT FINAL ACCEPTANCE.** This checklist is scoped to synthetic/local evidence under frozen `docs/project/API_CONTRACT_V0_1.md`. It does not authorize merge, deployment, dependency installation, Podman/VM activity, private data, inference, spending or recipient-machine acceptance.

Baseline: `f3d5235618ead7afc8bd01f13758fcc10bd151c5` / E0052.

## Current gate

The Task-7A foundation is integrated, but the PDF runtime lock remains intentionally unverified. RL-MVP-007B API, RL-MVP-007C frontend and RL-MVP-007P packaging are parallel workstreams and were not present on this baseline. Therefore the end-to-end acceptance items below are **BLOCKED / NOT RUN** until the relevant workstreams publish exact reviewed candidates and Lead integrates or otherwise supplies a reviewable combined build under separate authorization.

Prepared executable acceptance file: `tests/acceptance/test_local_demo.py`.

Future service command, once 7B supplies a genuine loopback service:

`REDACTION_LAB_ACCEPTANCE_URL=http://127.0.0.1:<port> PYTHONPATH=src python -m pytest -q tests/acceptance/test_local_demo.py`

The test refuses non-`127.0.0.1` URLs and skips when no service URL is supplied.

## Acceptance matrix

| Area | Synthetic acceptance evidence | Current E0052 state |
| --- | --- | --- |
| Loopback API | `/api/v1/health` reports API `0.1`, local mode, runtime unqualified, version header | BLOCKED on 7B |
| Bounded upload | synthetic PDF accepted within limit; 25 MiB + 1 byte rejected with 413 | BLOCKED on 7B |
| Reference isolation | upload pair remains `truth_status: UNKNOWN`; reference response has no processing job/source authority | BLOCKED on 7B |
| Honest runtime failure | process request with unverified runtime returns exact 503 contract and leaves job `ACCEPTED`, `source_id:null` | BLOCKED on 7B; runtime is intentionally unverified |
| Null results | pending result has empty targets, all summaries null, `score_status:NONE`, verified/experimental scores null | BLOCKED on 7B |
| No fabricated scores | no percentage/zero substituted for unknown truth | BLOCKED on 7B/7C |
| Unsafe web input | hostile Origin rejected; Host/Content-Type protections to be exercised against integrated 7B | BLOCKED on 7B |
| Durable restart | accepted jobs/documents survive stop/start without re-dispatch or new paid work | BLOCKED on 7P restart/launcher contract |
| Process lock | existing 7A migration lock regressions plus integrated-startup check show one migration owner and preserved Task-4/6 evidence | FOUNDATION EXISTS; integrated 7P startup evidence NOT RUN |
| Frontend honesty | UI shows unknown/null states, no invented scores/targets, and exact API states | BLOCKED on 7C + 7B |
| Clean-device prerequisites | pinned Python/runtime/dependency and launcher prerequisites documented and reproducible without owner's machine | BLOCKED on 7P; final second-device 7D not authorized |

## Required 7D evidence after prerequisites arrive

1. Record exact SHAs/branch heads for the API, frontend and packaging candidates under review. Do not use branch names alone.
2. Start only an authorized local build. Confirm the listener is `127.0.0.1`, not `0.0.0.0`/LAN, before browser/API acceptance.
3. Run `tests/acceptance/test_local_demo.py` against the exact service and retain pass/skip/fail counts. No Backend/Frontend self-test count substitutes for independent QA execution.
4. Re-run the full repository suite and focused Task-4/Task-6/Task-7A security regressions in the combined candidate environment.
5. Exercise reference omission and reference presence separately. Uploading a reference must never make truth trusted outside DEC-022.
6. With the intentionally unverified runtime, confirm process requests fail with the frozen 503 contract and do not claim jobs or create authoritative sources.
7. Confirm result and UI surfaces never fabricate targets, scores or a false `0%`; unknown/unsupported remain explicit states.
8. Once an approved launcher exists, stop and restart the local application and verify document/job IDs and durable state are unchanged. Reconnect/restart must not create a Task-4 prediction attempt.
9. Verify the persistent migration lock path remains safe and startup does not rewrite Task-4/Task-6 immutable evidence.
10. Final clean-recipient-machine acceptance is a separate authorization. Until then, label portability as **not independently accepted**.

## Stop / amendment triggers

Stop and request an owner amendment if any workstream requires a route/schema/header change from API v0.1, a new dependency, a new acceptance-side production hook, private data, runtime installation, model inference, or files outside the assigned role packet. A service that cannot meet the frozen 503/null semantics is not accepted by weakening this checklist.
