# QA / Independent Reviewer — October 12 kickoff

**Deadline update (DEC-020, 2026-10-08):** first MVP checkpoint is October 12, not October 14. Keep original scope, no-spend rule and review gates. Task 1 is merged; Task 2 Correction 02 is routed, not yet independently verified or merged. Later tasks are not authorized merely by this date change.

Status: PREPARED. Independent review begins only on an exact candidate SHA.
Owner role: QA / Independent Reviewer. Immediate review when the new SHA arrives: RL-MVP-002 Correction 02; later proposed task: RL-MVP-008.
Read current HEAD, AGENTS.md, DECISIONS.md, Oct 12 design, implementation plan and the specific candidate task packet/commit before reviewing.

Prepare adversarial synthetic cases for: hidden selectable text beneath black overlay; black rectangles not covering text; adjacent targets; repeated anchors; wrong/unrelated reference; partly still-redacted truth; reversed actor/action, negation and wrong dates/numbers; missing/null denominators; refusal/timeout; duplicate dispatch, restart/reconnect, malformed PDFs, cross-project/reference leakage, and no-cost local-only boundary.

Review exact commits independently. Do not implement features being reviewed. Separate observed failures from untested risks and missing research approvals. No passing unit tests may be presented as proof that evaluation scores are scientifically accurate.

After approved QA scope and candidate publication: run tests, document commands and results, PASS/FAIL/BLOCKED with reasons, and publish unique QA handoff to Lead. Escalate any reference leak, false verified score, or hidden paid provider call as a stop condition.
