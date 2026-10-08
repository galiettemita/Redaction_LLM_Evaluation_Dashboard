# Codex — how to start the October 14 MVP

## Read-only startup you may do immediately

Open the existing GitHub repository in Codex: galiettemita/Redaction_LLM_Evaluation_Dashboard.
Read root AGENTS.md and live main HEAD; at that SHA read CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, the Oct 14 MVP design and the detailed implementation plan. Report role, baseline SHA, epoch, blockers and local hardware/model feasibility. Do not modify code, install models, call paid APIs, provision services, or deploy. Do not claim the other ChatGPT chats were notified.

## First coding task — only after owner approves detailed plan and packet

Create a separate task branch/worktree. Read docs/project/task_packets/RL-MVP-001-contracts-and-synthetic-fixtures.md and Task 1 of docs/superpowers/plans/2026-10-07-oct14-mvp-implementation.md. Implement ONLY typed records, synthetic PDF fixtures and their tests using TDD. No providers, evaluation weights, UI, cloud, restricted data or extra spend.

At end, provide exact branch and commit, paths, tests run/not run, risks, and publish a task-scoped handoff. Stop for missing approval, changed epoch/HEAD, hidden reference leakage, model license/cost issue or scope conflict. Do not merge to main without authorization.

## Copyable first prompt

Run a read-only Redaction Lab startup/preflight. Follow AGENTS.md at live main HEAD. Read the October 14 design, detailed implementation plan and RL-MVP-001 packet. Inspect the available Codex machine (OS, RAM, GPU, local model runtime, disk) and identify whether one real local predictor and a distinct local evaluator can run without additional spending; check licenses and availability. Report exact HEAD, epoch, feasibility, blockers and recommended first scoped coding action. Do not edit files, install/download models, call external paid services or start implementation yet.
