# Frontend / Product — October 14 kickoff

Status: PREPARED, NOT YET APPROVED TO CODE.
Owner role: Frontend / Product. Proposed task: RL-MVP-007.
Read current HEAD, AGENTS.md, DECISIONS.md, INTERFACES.md, Oct 14 MVP design and detailed plan.

Design a professional, simple local interface for redacted PDF upload and optional reference PDF upload, a Run button, progress, clickable detected text redactions, prediction/revealed text comparison, per-target results and one-model document summary. No technical jargon in primary copy. Accessible labels, keyboard navigation and mobile readability.

Never calculate scores in the browser. Distinguish EXPERIMENTAL score, Accuracy unknown (partial/absent/unreliable reference), model refusal, model failure and pending evaluation. UI must not make reconnect or polling trigger a new model call. Mock synthetic API responses are acceptable for UI tests but never claim a mock prediction as live.

Preparation: draft typed API consumer contract and synthetic-state UI fixtures for Lead/Backend review. Implementation only after plan and RL-MVP-007 packet approval, and after API contract is frozen. Scope to web/ and UI tests; no backend scoring changes. Publish unique handoff with actual tests, accessibility evidence and blockers.
