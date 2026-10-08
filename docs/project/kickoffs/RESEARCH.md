# Research / Evaluation — October 12 kickoff

**Deadline update (DEC-020, 2026-10-08):** first MVP checkpoint is October 12, not October 14. Keep original scope, no-spend rule and review gates. Task 1 is merged; Task 2 Correction 02 is routed, not yet independently verified or merged. Later tasks are not authorized merely by this date change.

Status: PREPARED, NOT YET APPROVED TO IMPLEMENT OR DECLARE VALIDITY.
Owner role: Research / Evaluation. Proposed task: RL-MVP-005.
Read current HEAD, AGENTS.md, DECISIONS.md, RESEARCH_METHOD.md, INTERFACES.md, Oct 12 MVP design and detailed implementation plan.

Prepare a versioned, evidence-based experimental evaluation rubric and synthetic benchmark proposal. Cover short names, paraphrases, actor/action/object reversal, negation, time/quantity/unit mismatches, uncertainty, unsupported additions, incomplete truth, judge disagreement and unknown/null states. Define exact evidence the evaluator should return. Separate scoreability gate, semantic evidence, provisional demo labels and research-verified scores.

Compare local candidate judge feasibility (NLI/MiniCheck-style) but do not claim one is validated or select arbitrary numeric weights/cutoffs. A predicting model cannot solely judge itself. Any provisional numeric mapping must be visibly EXPERIMENTAL and must be reviewed for demo use; scientific accuracy percentages require human-adjudicated calibration and research-human approval.

Permitted initial output after packet approval: docs/project/research_proposals/RL-MVP-005-evaluation-rubric.md and synthetic evaluation fixture proposal/hand-off on your task branch. Do not publish private data or change main. Record research-human approval as NOT OBTAINED until it actually exists. Route results to Lead and Backend Task 6.
