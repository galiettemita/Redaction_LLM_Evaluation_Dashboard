# Frontend / Product — October 12 kickoff

**Deadline update (DEC-020, 2026-10-08):** first MVP checkpoint is October 12, not October 14. Keep original scope, no-spend rule and review gates. Task 1 is merged; Task 2 Correction 02 is routed, not yet independently verified or merged. Later tasks are not authorized merely by this date change.

Status: PREPARED, NOT YET APPROVED TO CODE.
Owner role: Frontend / Product. Proposed task: RL-MVP-007.
Read current HEAD, AGENTS.md, DECISIONS.md, INTERFACES.md, Oct 12 MVP design and detailed plan.

Design a professional, simple local interface for redacted PDF upload and optional reference PDF upload, a Run button, progress, clickable detected text redactions, prediction/revealed text comparison, per-target results and one-model document summary. No technical jargon in primary copy. Accessible labels, keyboard navigation and mobile readability.

Never calculate scores in the browser. Distinguish EXPERIMENTAL score, Accuracy unknown (partial/absent/unreliable reference), model refusal, model failure and pending evaluation. UI must not make reconnect or polling trigger a new model call. Mock synthetic API responses are acceptable for UI tests but never claim a mock prediction as live.

Preparation: draft typed API consumer contract and synthetic-state UI fixtures for Lead/Backend review. Implementation only after plan and RL-MVP-007 packet approval, and after API contract is frozen. Scope to web/ and UI tests; no backend scoring changes. Publish unique handoff with actual tests, accessibility evidence and blockers.
