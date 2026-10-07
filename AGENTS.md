# Redaction Lab: instructions for every agent

This repository is documentation-first. Read these instructions before project work. They define coordination, not permission to implement the whole product. Higher-priority instructions and the user's actual authorization remain controlling.

## Mandatory freshness check

1. Resolve the current default branch and its HEAD through live GitHub access; `main` is the initial integration branch. Record that SHA as `baseline_sha`. Do not rely on Project memory, an uploaded snapshot, or a stale local branch for current status.
2. At that same SHA, read `docs/project/CURRENT_STATE.md`, `docs/project/DECISIONS.md` and the active portion of `docs/project/AGENT_HANDOFF.md`. Read `docs/project/MASTER_SPEC.md` and `AGENT_OPERATING_GUIDE.md` on first entry, after context loss, and when changed. Then read only the relevant role files and incoming handoff artifacts.
3. If using a local checkout, inspect path, remote, branch, HEAD, working-tree status and worktrees. Fetch the integration ref without resetting or switching another agent's branch. Identify the difference between the code branch and `baseline_sha`.
4. Before a consequential write, provider call or final review, recheck the integration HEAD. If it moved, inspect relevant changes; rebase the plan against them. Stop affected work for a conflicting decision, changed contract or hold. Never claim another running chat has been interrupted or updated.
5. If live access fails, say `SYNC BLOCKED`; do not invent current state or claim synchronization. Previously supplied materials may support explicitly provisional analysis, not consequential writes.

Keep the startup acknowledgment to one line: `Role | task | baseline SHA | decision epoch | relevant blockers`. Do not reread every file on every turn: reuse a confirmed snapshot within a bounded step, then check HEAD at the next checkpoint.

## Authority and scope

- Preserve confirmed requirements R01-R12 and decisions DEC-001 through DEC-006. Proposed architecture, interfaces, scoring and thresholds remain proposed until their designated human approvals are recorded.
- The redacted PDF is required for prediction; the reference file is optional for prediction. Verified scoring additionally requires fully revealed, readable, reliably aligned reference text for that exact target.
- Partial, missing, unreadable or uncertain truth means null score / unknown accuracy, not zero. Text targets only; no image, table or whole-page reconstruction. Ordinary multipage viewing is allowed. Provide redaction, document and model score levels.
- Reference content and hints must not enter prediction inputs. Predictions, mappings and evaluations need versioned provenance. A timeout is not a factual error. Reconnecting must not start a new paid run.
- No stack, API model version, scoring weights or validation threshold has been selected. Do not fill these in silently.

## Task and write protocol

Work only on a task packet with an owner, file scope, acceptance evidence and stop condition. The setup request authorizes documentation initialization only; it is not standing permission for future code, paid calls, migrations, deployments or merges. Routine handoff writing can be included once in each approved task scope to avoid repeat approval requests.

Lead/Architect is the single integration writer for the eight shared project files, under the owner's authorized scope. Specialists propose changes on their task branch or in a unique handoff. They do not independently rewrite canonical state on `main`. An agent role is not a human approval identity.

Use one isolated branch/worktree per writing task. Before publishing, refresh HEAD and reconcile overlap. Use current blob SHAs or an expected-head lease for API writes; use normal non-force Git pushes. A stale-head rejection requires rereading and reconciliation, not a blind retry. Keep a related decision, state and handoff update in one commit where possible. Never force-push or overwrite another writer's work.

At completion, create or extend your task-scoped handoff under `docs/project/handoffs/` using the template in `AGENT_HANDOFF.md`. Include actual artifacts, commit/revision, tests run or not run, decisions used, blockers, affected consumers and next action. If writing is unavailable or unauthorized, provide the exact proposed filename and content, labeled `NOT PUBLISHED`. No handoff is delivered merely because it was written in chat.

Only an independent review of the exact candidate plus required human sign-off can produce `VERIFIED`. `IMPLEMENTED`, `VERIFIED`, `MERGED` and `DEPLOYED` are separate. Do not fabricate test counts, CI status, acknowledgments or background activity.

## Data and communication boundaries

The repository was public at setup. Keep private research data, source PDFs/HTML datasets, credentials, raw model payloads and private conversation exports out of it. Do not change visibility or permissions without authorization.

Project chats exchange durable records, not live messages. These instructions are not a scheduler, enforceable lock or autonomous orchestration service. Consult `AGENT_OPERATING_GUIDE.md` for one-time setup, role prompts and the manual approval boundaries. No cron or runtime is installed.
