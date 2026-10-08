# RL-MVP-001 corrected candidate: fresh reviews

State: READY_FOR_REVIEW, not VERIFIED or MERGED.
Canonical baseline: main 44d9b1f3a1b4632bddcdef1f6d76d92ff4fcc294, E0008.
Corrected implementation commit: a1d831153c726db38fc0c403c4d6d80893f657a5.
Published task branch head: c698cd4876af221ba24b85f5ad2d1b2e15c43d04.
Backend handoff: docs/project/handoffs/RL-MVP-001-backend-20261008T024109Z-a1d8311.md on the task branch.

QA: independently inspect the corrected commit and run the full existing suite plus adversarial checks for the previous eight failures, deep immutability, prediction/reference isolation, confirmed/verified prerequisites, denominator validity, and partial-reference PDF. Record actual tests and remaining gaps. Do not carry over the prior verdict.

Research: independently inspect the corrected contracts for reference truth, evaluation process versus score status, scientific scale neutrality, project/version provenance, aggregation, and partial truth. Cross-record validation remains a future transactional requirement, not evidence of verified scoring. Do not carry over the prior verdict.

Both reviewers publish a unique handoff on their own review branch referencing this exact SHA. No feature implementation, main merge, paid calls, external providers or Task 2. Lead reconciles the two reports.
