# RL-MVP-003 DEC-022 Correction 02 — fresh independent review

**State:** READY_FOR_REVIEW, NOT VERIFIED. **Owner:** Backend/Codex. **Reviewers:** independent QA and Research. **Receiver:** Lead.
**Integration baseline:** main `b23078737c3e493edd0f287810cdf0bac0109f7b` / E0030. Review routing epoch E0031.
**Exact implementation:** `97db3615c65b9e31d0f94dca443baab760340c5f`.
**Published Backend branch head:** `139921de76f9f3d0a67af19217e0969464f88ffd`, `codex/rl-mvp-003-text-first-reference-alignment`.
**Handoff:** `docs/project/handoffs/RL-MVP-003-backend-20261009T020728Z-97db361.md`.
**Authority:** DEC-021/022, `docs/project/task_packets/RL-MVP-003-DEC022-CORRECTION-02.md`, current contracts and research guards. October 12 checkpoint; no waiver.

## Shared review instructions

Refresh main HEAD, AGENTS.md, CURRENT_STATE.md, DECISIONS.md and this packet; inspect exact implementation and Backend handoff. Verify the implementation commit changes only `reference.py`, `reference_registry.py`, `test_reference.py`, `test_reference_registry.py`; the publication commit adds one unique Backend handoff. Branch history also contains inherited main coordination changes; judge the **exact implementation commit**, not the aggregate branch delta.

Codex reports 60 focused and 180 full pytest passes, compileall, 21 dependencies compatible and diff check. Independently rerun exact checkout tests if possible; otherwise mark NOT RUN and report reproducible isolated checks. Old QA FAIL and Research PASS on `8a751d4` do not carry forward.

## QA — independent acceptance

1. Independently regenerate `two_boxes` PDFs and verify both pinned byte hashes plus **literal redacted and reference canonical-version IDs** `redacted-canonical-v1` and `reference-canonical-v1`. No dynamic enrollment.
2. With genuine pinned bytes and otherwise valid records, forge only the redacted `canonical_document_version_id`, then only the `reference_canonical_version_id`. Both must fail closed: NOT_SCOREABLE/null exact text or sanitized typed rejection, never CONFIRMED. Test blank/missing and swapped IDs.
3. For a positive CONFIRMED case, verify the mapping's `redacted_canonical_version_id` and `reference_canonical_version_id` equal registry pins, not caller-controlled values; check stable IDs, canonical hashes and locators.
4. Recheck changed/swapped/unregistered PDF bytes, forged target records, wrong project/document versions, repeated/adjacent targets, one-sided global context, geometry fallback, edge punctuation/whitespace, partial/still-hidden selectable text, reference-to-prediction leakage and malformed inputs.
5. Record actual commands/results, NOT RUN, residual risks and PASS / CHANGES_REQUESTED / BLOCKED. Do not modify implementation or merge.

## Research — independent acceptance

Assess whether the public entry point now prevents caller-forged canonical identities from entering CONFIRMED evidence, and whether canonical provenance is consistent with the synthetic-pair trust boundary. Challenge exact full-target truth, two-sided alignment, reference pairing, partial/unknown/null semantics, source quotation, hidden-text isolation and prediction-manifest separation. Distinguish *synthetic fixture trust* from archival authenticity and scientifically verified accuracy; D03 remains unapproved. Report tests run/not run and an exact-SHA PASS / CHANGES_REQUESTED / BLOCKED handoff.

## Publication and stops

Each reviewer publishes one unique role-specific handoff on its own approved review branch and sends its verdict to Lead through GitHub; no automatic chat messaging is implied. No main merge, Task 4, paid calls, private data, deployment or scientific scoring approval. Any false CONFIRMED, forged provenance or leakage is blocking.
