# RL-MVP-002 Correction 02 — fresh independent review

State: REVIEW REQUESTED, not independently verified. Main baseline 80be08a13bcb51177118145fedeff103a5ffce54 / E0015. Routing epoch E0016.
Exact implementation commit: ea930abef319832cf494df5851be1b19d3e2cf1c. Published Backend branch/head: codex/rl-mvp-002-detection-canonicalization @ e5333602c43d304a21980fc96103d19599e2dd27.
Backend handoff: docs/project/handoffs/RL-MVP-002-backend-20261008T151310Z-ea930ab.md on the Backend branch.
Deadline: October 12, 2026 (DEC-020). No QA, scoring, budget, data or merge gate is waived.

QA and Research must independently review this NEW SHA; earlier verdicts on 12698b9 do not transfer. Confirm the branch delta is confined to src/redaction_lab/pdf_detector.py, tests/test_pdf_detector.py and one handoff. Review the full Task 2 scope and Correction 02 packet.

QA focus: sparse/two one-line columns, one-line side column with multi-line main column, legitimate single-line and indented single-column negatives, document/section start/end standalone no-glyph black boxes, remote artwork negatives, prior project ID/overlap fixes, redacted-only/hidden-text leakage, marker identity, parser failure states. Independently run the full suite when feasible; report NOT RUN otherwise, with actual reproducible probes.

Research focus: one physical supported region per target, conservative unsupported behavior, absence of false NO_REDACTIONS, reading-order preservation, project-scoped target IDs and detector v3 provenance, no reference or evaluator content in prediction context. No D03–D06 scientific approval implied.

Each reviewer publishes one unique handoff on its own review branch with exact SHA, PASS/CHANGES_REQUESTED/BLOCKED, actual tests and remaining risks. No code changes, main merge, Task 3, paid calls, restricted data or deployment. Lead reconciles after both reports.
