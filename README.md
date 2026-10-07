# Redaction Lab

A document-centered research platform for comparing how well AI models predict text hidden by redactions, using reliably revealed reference text when available.

**Repository status:** documentation-first. This setup does not implement the application, validate a scoring method, approve vendors, or deploy a service.

## Start here

- Agents and Codex: read [AGENTS.md](AGENTS.md).
- Human setup and the five role prompts: [Agent operating guide](docs/project/AGENT_OPERATING_GUIDE.md).
- One-time instructions for all Project chats: [ChatGPT Project instructions](docs/project/CHATGPT_PROJECT_INSTRUCTIONS.md).
- Current work, blockers and decisions needing attention: [CURRENT_STATE.md](docs/project/CURRENT_STATE.md).

## Shared project files

| File | Purpose |
| --- | --- |
| [MASTER_SPEC.md](docs/project/MASTER_SPEC.md) | Source-aligned working digest of the owner-supplied product specification; confirmed versus proposed requirements. |
| [CURRENT_STATE.md](docs/project/CURRENT_STATE.md) | Small current-state snapshot, task registry, holds and next permitted work. |
| [DECISIONS.md](docs/project/DECISIONS.md) | Approved product decisions, open research decisions and change procedure. |
| [ARCHITECTURE.md](docs/project/ARCHITECTURE.md) | Proposed system boundaries and architectural invariants; no selected stack. |
| [INTERFACES.md](docs/project/INTERFACES.md) | Proposed record/permission contracts and compatibility controls. |
| [RESEARCH_METHOD.md](docs/project/RESEARCH_METHOD.md) | Ground truth, evaluation, benchmark and aggregation requirements. |
| [CHANGELOG.md](docs/project/CHANGELOG.md) | Concise coordinated changes with impact and evidence. |
| [AGENT_HANDOFF.md](docs/project/AGENT_HANDOFF.md) | Role routing, independent handoff records, acknowledgments and task packet templates. |

## Product invariants

The redacted PDF is required for prediction. The matching revealed PDF is optional for prediction, but each scored target needs a fully revealed, readable and reliably aligned reference. Missing or partial truth gives **unknown accuracy / null score**, never zero. Reconstruction targets are text passages, not images, tables or entire withheld pages. Scores are required per redaction, per document and per model; formulas and thresholds are not yet approved.

## Coordination, not a background agent runtime

Every active agent checks current GitHub state before work and publishes a scoped handoff afterward. Root instructions do not create agent sessions, send messages to other chats or install a scheduler. No cron, workflow or autonomous merge is installed by this documentation setup. Product and research approvals remain human decisions.

## Public-repository boundary

GitHub reported this repository as public at setup on 2026-10-06. Only the requested planning and operating documentation belongs in this initial commit series. Do not add private Slack exports, source PDFs, the embedded HTML dataset, raw model payloads, API keys or restricted research material. Visibility has not been changed. Resolve data-handling and visibility policy before collecting real uploads or calling providers.
