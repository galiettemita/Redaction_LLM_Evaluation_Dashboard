# RL-MVP-003 Research / reference-alignment review

Task ID: RL-MVP-003 — Text-First Reference Alignment
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-08T20:57:00Z
State: CHANGES_REQUESTED
Review verdict: CHANGES_REQUESTED FOR TASK-3 TRUTH/ALIGNMENT SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: 7c001af1d25b1dd546d5c4754384a0af71c441b6 / E0025
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-003-text-first-reference-alignment / implementation 931fb1c0012d3b530b837f204d922f0aaa95a602; Backend publication head 2d79ee6a7d5ba2a06148ff257529faa50dfa06e1.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-003-INDEPENDENT-REVIEW.md; RL-MVP-003-text-first-reference-alignment.md; DEC-001, DEC-004, DEC-007, DEC-008, DEC-010, DEC-011, DEC-015, DEC-020; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; merged Task-1/2 contracts/detector/canonicalizer.
Authorization reference and permitted file/action scope: E0025 independent Research review authorizes read-only exact-candidate review, no-cost local probes and one unique Research handoff. No implementation edits, merge, Task 4, provider/model calls, paid services, private data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to 7c001af1d25b1dd546d5c4754384a0af71c441b6 / E0025 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-003-INDEPENDENT-REVIEW.md.
- Read approved Task-3 packet docs/project/task_packets/RL-MVP-003-text-first-reference-alignment.md and the implementation-plan Task 3 section.
- Read Backend handoff docs/project/handoffs/RL-MVP-003-backend-20261008T201401Z-931fb1c.md at publication head 2d79ee6a7d5ba2a06148ff257529faa50dfa06e1.
- Inspected exact implementation src/redaction_lab/reference.py and tests/test_reference.py at 931fb1c0012d3b530b837f204d922f0aaa95a602.
- Confirmed candidate delta from its implementation baseline contains only src/redaction_lab/reference.py and tests/test_reference.py; implementation-to-publication head adds only the unique Backend handoff. Current-main drift from the implementation baseline is coordination/review routing only.

## Positive findings

- Reference parsing is structurally separate from prediction input construction. align_reference receives reference bytes, while PredictionManifest remains redacted-only; no reference field was added to prediction serialization.
- Safe reference parsing reuses detector/canonicalizer protections and builds a separate exact visible-character stream rather than trusting raw extract_text() for covered text.
- Still-hidden/partial markers are explicitly detected; unconfirmed mappings use NOT_SCOREABLE and do not expose exact_revealed_text.
- Reordered confirmed target ranges are invalidated document-wide.
- Candidate mappings carry target/version identity, redacted/reference canonical hashes, token/character locators, mapping/method/global-alignment versions and exact quotation when confirmed.
- Existing candidate tests cover repeated anchors, wholly wrong unrelated documents, reordered target passages, absent/malformed references, still-hidden/partial reference cases, exact internal punctuation/double-space preservation, duplicate-word locator binding, adjacent targets, document boundaries, deterministic IDs and prediction-manifest isolation.
- No numeric scoring or D03 scientific-validation claim is made.

## Blocking finding 1 — one-sided global support can still CONFIRM truth

The exact implementation's _globally_supported() computes left_ok and right_ok but returns:

    left_ok or right_ok

Therefore when both sides of the target exist, one side can conflict with the global monotonic alignment and the candidate can still be treated as globally supported solely because the other side matches. This is explicitly called out as a risk in the E0025 review packet and is not compatible with fail-closed full-target truth.

Independent exact-logic probe:
- redacted token sequence: "same [[TARGET:t]] same same same"
- reference token sequence: "same same same different"
- local left/right anchors identify one candidate;
- SequenceMatcher's monotonic pairs support the left candidate anchor but not the right candidate anchor;
- current _globally_supported result: True; left=True, right=False.
A strict both-sides requirement when both sides exist would be False.

A second independent one-sided geometry-style probe used:
- redacted: "alpha [[TARGET:t]]\nnext context"
- reference: "alpha WRONG\nchanged context"
- candidate bound by left textual evidence only, not a true document boundary;
- current global support returns True from the left side while the later/right document context conflicts.

This means matching one side can still legitimize an otherwise conflicting candidate. CHANGES_REQUESTED.

## Blocking finding 2 — “global” alignment does not reject a wrong document that only preserves local neighbors

Even if finding 1 is changed from OR to AND, current document-global evidence remains too weak for the task's wrong-release requirement. _monotonic_pairs() builds SequenceMatcher blocks for any matching words, but the implementation requires no trusted binary-document identity and no deterministic document-wide coherence condition beyond the target-local anchor pairs and ordering of confirmed target ranges.

Independent exact-logic probe:
- redacted visible tokens: "preamble alpha [[TARGET:t]] beta tail"
- wrong reference: "junk alpha WRONG beta noise"
- local anchors alpha/beta produce a unique candidate;
- global monotonic pairs contain alpha and beta while the rest of the document conflicts;
- both candidate sides are considered globally supported under the current predicate.

The implementation can therefore confirm a target from a wrong document/release that happens to preserve the local surrounding words. Existing wrong-document testing uses a wholly unrelated sentence and does not cover this case.

The function accepts reference_document_version_id as caller metadata but does not receive/verify the immutable DocumentVersion source sha256 against the supplied reference_pdf bytes. The Backend handoff correctly notes that persisted binary provenance is deferred, but this review packet specifically requires wrong-document/integrity scrutiny. Without a trusted document-binding check or another approved deterministic full-document invariant, local neighbor matches cannot establish that the supplied bytes are the matching reference release.

Do not invent a similarity/coverage threshold under D03. Lead/Backend should either bind the supplied bytes to the authorized immutable reference DocumentVersion hash within approved scope, or stop for the contract/scope decision required to make that possible.

## Blocking finding 3 — boundary whitespace is not part of the confirmed exact span

For anchor-derived candidates without geometry-bound source offsets, _confirmed() uses the first matched word token start and last matched word token end as the exact source span. _has_unbound_boundary_punctuation() explicitly tests surrounding gaps using .strip(), so whitespace-only gaps do not make the candidate ambiguous.

Independent exact-logic probe:
- exact visible reference stream: "Left  SECRET  right"
- token candidate is SECRET;
- left and right token gaps each contain two spaces;
- _has_unbound_boundary_punctuation-equivalent result: False;
- confirmed lexical source span is "SECRET", not either surrounding whitespace.

If the physical target box covered boundary spaces, the mapping can therefore claim complete_revelation=True while exact_revealed_text is narrower than the exact revealed target span. Internal double spaces are preserved by an existing test, but leading/trailing target whitespace is not bound. DEC-010 and the task packet require exact revealed span/source evidence; this needs fail-closed handling or exact geometry/source binding, not silent trimming.

## Independent tests actually run

Attempted matching repository checkout:
git clone --no-checkout https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /mnt/data/rl_mvp003_review
Result: NOT RUN TO COMPLETION — container could not resolve github.com. The exact repository 145-test suite was therefore NOT independently executed.

Exact source/tests were read through the live GitHub connector. I then executed isolated probes reproducing the exact reviewed tokenization/anchor/global-support predicates.

Command:
python /mnt/data/rl_mvp003_research_probe.py
Result: PASS as a defect-reproduction probe:
- reproduced unique local candidate with global left=True/right=False while current overall=True;
- reproduced one-sided geometry/global-support acceptance despite conflicting later context;
- reproduced wrong-document local alpha/beta neighbors satisfying both current global anchor checks despite unrelated surrounding document content.

Command:
python /mnt/data/rl_mvp003_whitespace_probe.py
Result: PASS as a defect-reproduction probe:
- whitespace-only left/right gaps are not treated as unbound punctuation;
- exact lexical candidate remains "SECRET" rather than the full whitespace-bounded region.

Command:
python /mnt/data/rl_mvp003_hidden_probe.py
Result: PASS:
- a reference marker with matching surrounding context is detected by the hidden-reference-match path and therefore routes to partial/unconfirmed handling rather than truth exposure.

Compile checks:
python -m compileall -q /mnt/data/rl_mvp003_research_probe.py
python -m compileall -q /mnt/data/rl_mvp003_whitespace_probe.py
python -m compileall -q /mnt/data/rl_mvp003_hidden_probe.py
Result: PASS.

Backend-reported evidence reviewed but not adopted as independent execution: 25 focused tests and 145 full tests passed; compileall/dependency/diff checks reported clean in Backend's Python 3.11 environment.

Tests not run and reason:
- Exact repository 145-test suite: NOT RUN independently because a matching checkout was unavailable due DNS/network restriction.
- Real/private references, OCR/scans, real-world alignment benchmark, hostile-input resource tests, model/provider, scoring, Task 4, API/UI, database, cloud and deployment: outside RL-MVP-003 scope and/or unauthorized.

## Answers to requested review areas

1. Matching revealed words to blacked-out passages: basic exact synthetic cases work by source inspection/tests, but false confirmation remains possible under findings 1/2.
2. Repeated/reordered/wrong/ambiguous: repeated and reordered cases are handled conservatively in existing tests; a wrong document with locally matching neighbors remains a blocker.
3. Partial/still-hidden: PASS in reviewed code path; remains NOT_SCOREABLE with no exposed exact truth.
4. Exact wording/punctuation/whitespace/source/version integrity: internal punctuation/whitespace and locators have good coverage; boundary whitespace and cryptographic binding of reference bytes to the supplied document-version identity remain deficient.
5. Reference leakage into prediction inputs: PASS for the reviewed interfaces/serialization boundary.
6. One-side matching: FAIL — current _globally_supported explicitly accepts left OR right.

## Verdict

CHANGES_REQUESTED on exact implementation 931fb1c0012d3b530b837f204d922f0aaa95a602.

Do not merge or start Task 4. The candidate needs at minimum:
- fail-closed two-sided global support when both sides are available, with explicit boundary rules rather than OR;
- a trustworthy wrong-reference/document binding or approved deterministic full-document coherence rule that does not invent an unvalidated numeric threshold;
- exact-span handling that cannot silently drop target-boundary whitespace while claiming complete revelation.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation 931fb1c0012d3b530b837f204d922f0aaa95a602; no Backend/internal-review verdict inherited.
Research / data approval evidence (or not approved / not applicable): Research-human D03 approval NOT OBTAINED. Passing software tests would not establish scientific validity; D03-D06 remain open as applicable.
Known issues / risks / stale dependencies: Supported reference parsing inherits the conservative Task-2 vector-PDF subset. Persisted cross-record existence/current-version enforcement, OCR/raster support, real-document accuracy, hostile-input isolation and production scale remain unvalidated/deferred. Geometry is still used as secondary/fallback evidence and must not become a substitute for reliable text/document identity.
Affected roles / requested next action: Lead should keep current candidate unmerged and route findings to Backend for bounded correction/scope reconciliation. If trusted reference-byte binding requires a contract change outside the packet, stop and obtain Lead/owner authorization rather than weakening the truth rule. Fresh QA and Research must review the new exact SHA. Do not start Task 4.
Last freshness check and relevant differences: Immediately before publication, live main remained 7c001af1d25b1dd546d5c4754384a0af71c441b6 / E0025. Backend publication head 2d79ee6a7d5ba2a06148ff257529faa50dfa06e1 differs from implementation 931fb1c0012d3b530b837f204d922f0aaa95a602 only by the Backend handoff; no implementation change after the reviewed SHA was identified.
Rollback or correction approach: This Research branch contains only this handoff. If candidate/governing decisions change, this review becomes stale. Backend corrections should be additive on the isolated Task-3 branch; no force-push.
Publication: PUBLISHED on review/rl-mvp-003-research-e0025; not merged to main.
