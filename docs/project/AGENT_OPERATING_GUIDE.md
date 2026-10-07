# Redaction Lab agent operating guide

Version 1.0 | 2026-10-06 | Coordination setup, not an autonomous runtime.

## 1. The practical setup

Use this GitHub repository as the shared engineering record. Keep five role chats in the same ChatGPT Project and use Codex for approved implementation. Give all chats one persistent startup/update instruction and one role assignment each. Agents read each other's published work directly instead of asking the owner to copy every message.

This does not create five live agents, send messages into existing chats or keep idle sessions running. Instructions reduce reminders; they do not guarantee execution or replace review. An active chat sees a change when it performs its next live read. A currently running task may still use an older snapshot until its next checkpoint.

## 2. One-time owner setup

1. Open the ChatGPT Project's more-options menu, then Project settings. Add the block in [CHATGPT_PROJECT_INSTRUCTIONS.md](CHATGPT_PROJECT_INSTRUCTIONS.md), retaining relevant existing rules. This repository setup cannot change that UI setting for you.
2. Ensure the GitHub connection can access this repository in the Project. Run the startup-only check from that file. A pasted GitHub URL or uploaded PDF alone is not live repository access.
3. Create or reuse the five role chats. Paste the matching role block below once. Attach the master PDF as a baseline if desired, but use live GitHub for changing state.
4. Open the same repository in Codex and perform its startup-only read. Root AGENTS.md carries the work protocol. Old sessions must explicitly reread changed instructions; neither a file commit nor a memory reference proves they have done so.
5. Bring important product feedback to the Lead once. The Lead records the decision, impact, holds and receiving roles. Authorize a narrow task packet; include routine handoff publication in that approval so it need not be requested repeatedly.

The repository was public and empty at inspection. It is initialized with documentation only. Review visibility with the lab before real research uploads; no permission or visibility changes are made by this setup.

## 3. Which file answers which question?

| File | Question | Normal editor |
| --- | --- | --- |
| MASTER_SPEC.md | What product are we building? | Lead after approved changes; source-aligned baseline |
| CURRENT_STATE.md | Where are we now, what is blocked, what next? | Lead |
| DECISIONS.md | What is confirmed, proposed, open or superseded? | Lead with actual approvals |
| ARCHITECTURE.md | What are the system boundaries and constraints? | Lead integrates Backend proposals |
| INTERFACES.md | What data/permission contracts must consumers share? | Lead integrates affected roles' review |
| RESEARCH_METHOD.md | How should truth and scoring be treated? | Lead integrates research-approved changes |
| CHANGELOG.md | What important coordinated changes happened? | Lead |
| AGENT_HANDOFF.md | Who needs which artifact next? | Lead index; individual records by specialists |

A smaller startup packet saves context: read HEAD and the short state, decisions and handoff index first; load the full baseline on first entry or change; read only relevant domain files afterward. Git history is the change history, so no transcript dumps.

## 4. The work loop

**Read:** resolve live integration HEAD; read critical files at that SHA; record baseline and epoch. Read role-specific materials and the exact upstream handoff. If a tool cannot pin a revision, record observed versions and recheck HEAD; retry the read if the snapshot changed.

**Plan:** identify one approved task, one owner, non-goals, contracts and acceptance evidence. A proposed task in CURRENT_STATE is not permission to execute. Use a separate branch/worktree for writes; verify local state and avoid another worker's branch.

**Work:** perform only authorized actions. Recheck relevant state at stage boundaries, before costly/irreversible actions and before delivery. If the epoch or dependencies changed, inspect the impact; stop affected work. An unrelated change does not require rereading the entire repository.

**Publish:** include the scoped implementation/proposal, actual evidence and a unique handoff. Publication is part of the approved task. If write access is unavailable, label the output NOT PUBLISHED and provide exact content/filename; do not imply others can already retrieve it.

**Review/integrate:** independent QA checks the exact candidate; research/product/data humans approve their domains. Lead updates state/decisions/index in one authorized integration change, with a current-head check. Receivers acknowledge at their next task checkpoint. Code merged is not code deployed.

## 5. Last-minute changes and concurrent writers

Example: a new scoring proposal says an actor reversal must prevent a full-match label. The Research Agent does not silently approve a numeric cap. It records a proposal and evidence. The research human approves the rule, the Lead allocates an amendment ID, and the affected evaluation/API/UI/QA tasks are identified. The Lead updates DECISIONS, RESEARCH_METHOD, INTERFACES if needed, CURRENT_STATE and CHANGELOG together. The next active consumer reads that revision and records ACK before continuing.

For urgent contamination or incorrect-score risk, put affected tasks ON_HOLD at once within authorized write scope. A hold is an instruction observed on a read, not an instantaneous broadcast. Review held candidates again after reconciliation; stale approval cannot follow a changed commit.

One Lead integrates canonical files. Specialists write different task artifacts/branches, not the same shared log. Normal non-force Git push or expected-head API updates prevent overwriting an advanced branch; stale writes are reconciled. The single-writer rule is cooperative, not a configured branch protection. No protection policy was installed.

## 6. Evidence and status

Use the packet and handoff formats in [AGENT_HANDOFF.md](AGENT_HANDOFF.md). Each delivered task records baseline/candidate SHAs, decision epoch, changed files, exact commands/results, unrun checks, unresolved issues, required approvals and next consumer. A receiver's ACK only confirms reading. READY_FOR_REVIEW is not VERIFIED; VERIFIED is not MERGED; MERGED is not DEPLOYED. No made-up commit, test count or approval.

Changes in the browser, a local uncommitted file, a proposal branch and merged canonical state are different. Keep them distinct so the owner can understand progress without investigating every tool output.

## 7. Role prompts: paste one per chat

### Lead / Architect

```text
You are the Lead/Architect for Redaction Lab and a Principal Distributed Systems Engineer. Follow this Project's startup protocol and the live repository AGENTS.md. Coordinate the eight docs/project files, resolve cross-role conflicts, propose small task packets, and integrate only within authorized scope. Keep CURRENT_STATE short and evidence-backed. Product, research and institutional approvals remain human; do not self-approve them. Route work through published handoffs and show me only the decisions requiring my input. Begin with a read-only startup check; do not implement or create resources.
```

### Research / Evaluation

```text
You are the Research/Evaluation specialist for Redaction Lab. Follow the live AGENTS.md and startup protocol. Read MASTER_SPEC, DECISIONS, RESEARCH_METHOD and relevant INTERFACES at the current baseline. Own proposals and evidence for truth, semantic scoring, human benchmarks, variability and fair aggregation. Do not invent thresholds or treat toy grades as gold truth. Numeric methods stay proposed until the research human approves. Publish scoped research handoffs on your authorized branch; do not rewrite main or implement application code. Begin with a read-only startup check.
```

### Backend / Infrastructure

```text
You are the Backend/Infrastructure specialist for Redaction Lab. Follow the live AGENTS.md and startup protocol. Read ARCHITECTURE, INTERFACES, decisions and your task packet. Design durable state, failure isolation, versioning, retries, budgets and strict prediction/reference separation. Do not silently select a stack or alter scoring policy. Code only through an approved bounded Codex task, with tests and exact evidence. Publish your handoff; no unapproved main updates, provider calls, migrations or deployment. Begin with a read-only startup check.
```

### Frontend / Product

```text
You are the Frontend/Product specialist for Redaction Lab. Follow the live AGENTS.md and startup protocol. Read MASTER_SPEC, CURRENT_STATE, DECISIONS and relevant INTERFACES. Preserve a professional document-centered workflow, passage selection, release toggle, clear null/unknown and job states, accessibility and optional research details. Never calculate a different score in the UI. Prototype only with synthetic or explicitly permitted examples under approved scope; a design tool does not establish production quality. Publish a scoped handoff. Begin with a read-only startup check; no implementation yet.
```

### QA / Independent Reviewer

```text
You are the independent QA reviewer for Redaction Lab. Follow the live AGENTS.md and startup protocol. Do not implement the feature you review. Read the task's requirements, decisions, exact candidate SHA, diff and submitted evidence; challenge correctness, race conditions, stale mappings, truth leakage, unknown handling, denominators, permissions and regressions. Separate observed defects from untested risks. Report PASS/FAIL/BLOCKED only for reviewed scope; passing software checks is not research approval. Publish review evidence without modifying product code. Begin with a read-only startup check.
```

## 8. Codex handoff and session refresh

```text
Read the repository's AGENTS.md and execute its startup check. Use the current integration revision, not a prior chat's memory. Locate my assigned task packet and verify scope/approvals. If none is approved, propose the next narrow packet and stop. For approved execution, include tests and a task-scoped handoff in the work, recheck latest decisions before delivery, and report the exact candidate SHA. Do not implement the rest of the platform.
```

Official guidance says Codex builds its instruction chain when a run starts. Start a fresh run or explicitly reread changed instructions after a significant policy update. A task-based freshness check is still necessary for CURRENT_STATE and decision changes. [P2]

## 9. Why there is no cron in this setup

The requested alternative chosen here is a durable guide plus persistent instructions. No scheduled job is created. A reminder or digest can notify the owner; it does not itself run these five role chats or update their in-memory context. A timer is not a lock, an approval gate or proof of freshness. Scheduled GitHub checks could later report stale records or missing evidence, but would need a scoped implementation and permissions; they are not installed.

For genuinely autonomous work, use a separately approved orchestrator that starts bounded agent tasks, persists task ownership/results, enforces permissions and budgets, and handles retries/conflicts. That is a different system, not a capability obtained by adding this PDF to a Project. This project does not need that complexity to begin.

## 10. Google Docs and PDFs

A Google Doc can be an optional human-facing intake source for feedback; do not maintain two competing engineering decision logs. Promote accepted changes to GitHub with provenance. OpenAI supports adding Google Drive links as Project sources, but the Drive app is not pre-synced within a Project. Use a live read for new notes. [P1]

The master PDF is a historical product baseline; the operating-guide PDF is an onboarding snapshot. Neither updates itself when main changes. The persistent instructions direct agents to live GitHub. Repository operating files are the maintained copy; update/regenerate exported guides when their rules change.

## 11. Minimal owner workload

Set Project instructions once; assign roles once; give new feedback once to the Lead; approve substantive decisions and bounded task scopes. Agents handle authorized state reads and artifact handoffs. They should not ask you to relay accessible files, reread the unchanged full PDF each turn, or approve routine logging repeatedly. They must still stop for unavailable access, conflicting requirements or actions outside permission.

## 12. Sources and limits

B1: owner-supplied master product PDF, identified in MASTER_SPEC. The coordination workflow is the engineering setup requested on 2026-10-06, not a claim that it was in the product PDF.

P1: OpenAI, [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt), checked 2026-10-06. Used for Project instructions, connected sources and the Drive sync caveat.
P2: OpenAI, [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md), checked 2026-10-06. Used for startup discovery, not a claim of continuous rereading.
P3: OpenAI, [Scheduled tasks](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt), checked 2026-10-06. No scheduled task is activated here.

The GitHub connection was tested for this setup. Other chats' connections, their instruction settings, branch protections and actual future compliance have not been tested. No raw research files or private messages are reproduced.
