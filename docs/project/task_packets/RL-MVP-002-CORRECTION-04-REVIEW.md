# RL-MVP-002 Correction 04 — independent review packet

**State:** REVIEW REQUESTED, not verified. **Reviewers:** QA and Research independently, each on their own scoped review branch.
**Integration baseline:** main `2d23efa3f4f3ae55ffa1717e506ef90f14c5248c`, E0019. Routing epoch E0020.
**Exact implementation:** `df20fe074c0bebc7be15971199d3c361469bc6b1`. **Published branch head:** `6ba3e02af0d13b8ef673ac007f06d08912ff9e38`, `codex/rl-mvp-002-detection-canonicalization`.
**Backend handoff:** `docs/project/handoffs/RL-MVP-002-backend-20261008T181752Z-df20fe0.md` at the branch head.
**Source:** approved RL-MVP-002 Correction 04 packet and owner-approved conservative supported-layout boundary with two safeguards. **Deadline:** October 12, 2026 (DEC-020); no waived gates.

## Independent review requirements

Read live main HEAD, AGENTS.md, current epoch, Correction 04 packet, Backend handoff and exact implementation SHA. Confirm the branch delta since `821f5734` is limited to detector, detector tests and the unique handoff. Previous FAIL verdicts on `dbae9f79` do not automatically become PASS.

QA: independently probe the entire approved positive/negative matrix: staggered disjoint columns at 40/49/52/60/80 pt; one-line secondary columns; normal single-column text and modest indents; short centered heading with two aligned body lines and insufficient one-line body evidence; 18/20/30/120 pt no-glyph boundary rectangles, moderately offset boxes, remote square/wide artwork and remote text-sized decorative rectangles. Check that a box is not silently dropped as NO_REDACTIONS, that UNSUPPORTED reasons are deterministic and non-sensitive, and that no hidden selectable text reaches canonical/prediction serialization, errors or logs. Recheck target IDs, overlaps, marker uniqueness, malformed PDFs and v5 provenance. Run focused/full suite if an executable checkout is available; otherwise report NOT RUN and precise isolated probes.

Research: independently verify one supported physical region per target, redacted-only context, preservation of visible reading order, conservative refusal on uncertain layout, short-box/remote-artwork ambiguity, and heading exception requiring affirmative single-column flow evidence. Consider whether the new broad rejection of remote text-height black artwork is a documented MVP limitation rather than an incorrect claim of complete detection. Evaluate downstream alignment implications, not numeric scoring or D03–D06 research-human validity.

Both reviewers: publish unique role-specific handoffs with reviewed SHA, actual commands/results, PASS / CHANGES_REQUESTED / BLOCKED, unresolved risks and next receiver Lead. No code changes, merge, Task 3, paid services, private data or deployment. If a blocker remains, reproduce it and distinguish a supported-input defect from an explicitly rejected unsupported layout.
