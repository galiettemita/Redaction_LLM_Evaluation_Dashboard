# QA / Independent Reviewer — October 14 kickoff

Status: PREPARED. Independent review begins only on an exact candidate SHA.
Owner role: QA / Independent Reviewer. Proposed task: RL-MVP-008.
Read current HEAD, AGENTS.md, DECISIONS.md, Oct 14 design, implementation plan and the specific candidate task packet/commit before reviewing.

Prepare adversarial synthetic cases for: hidden selectable text beneath black overlay; black rectangles not covering text; adjacent targets; repeated anchors; wrong/unrelated reference; partly still-redacted truth; reversed actor/action, negation and wrong dates/numbers; missing/null denominators; refusal/timeout; duplicate dispatch, restart/reconnect, malformed PDFs, cross-project/reference leakage, and no-cost local-only boundary.

Review exact commits independently. Do not implement features being reviewed. Separate observed failures from untested risks and missing research approvals. No passing unit tests may be presented as proof that evaluation scores are scientifically accurate.

After approved QA scope and candidate publication: run tests, document commands and results, PASS/FAIL/BLOCKED with reasons, and publish unique QA handoff to Lead. Escalate any reference leak, false verified score, or hidden paid provider call as a stop condition.
