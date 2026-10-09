# RL-MVP-003 DEC-022 Correction 02 Research review

Task ID: RL-MVP-003 DEC-022 Correction 02 — canonical-version provenance
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-09T02:55:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR DEC-022 TASK-3 TRUST/TRUTH SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: 0c3462291676be7b7b6e101a6cb2910a094a5cbd / E0031
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-003-text-first-reference-alignment / implementation 97db3615c65b9e31d0f94dca443baab760340c5f; Backend publication head 139921de76f9f3d0a67af19217e0969464f88ffd.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-003-DEC022-CORRECTION-02-REVIEW.md; RL-MVP-003-DEC022-CORRECTION-02.md; DEC-001, DEC-004, DEC-010, DEC-011, DEC-020, DEC-021, DEC-022; RESEARCH_METHOD.md; INTERFACES.md contract-draft-0.1; prior DEC-022 implementation 8a751d4 and fresh Correction-02 packet.
Authorization reference and permitted file/action scope: E0031 independent Research review authorizes read-only exact-SHA review, no-cost local probes and one unique Research handoff. No implementation edits, merge, Task 4, provider/model calls, paid services, private data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to 0c3462291676be7b7b6e101a6cb2910a094a5cbd / E0031 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-003-DEC022-CORRECTION-02-REVIEW.md.
- Read docs/project/task_packets/RL-MVP-003-DEC022-CORRECTION-02.md and Backend handoff docs/project/handoffs/RL-MVP-003-backend-20261009T020728Z-97db361.md at publication head 139921de76f9f3d0a67af19217e0969464f88ffd.
- Inspected exact implementation 97db3615c65b9e31d0f94dca443baab760340c5f, including src/redaction_lab/reference.py, src/redaction_lab/reference_registry.py, tests/test_reference.py and tests/test_reference_registry.py.
- Confirmed the implementation commit's product-code/test changes are limited to the four authorized Task-3 reference/registry paths; the publication head adds only the unique Backend handoff.

## Findings

### 1. Canonical-version provenance defect is resolved

The registry now pins literal canonical-version identities:
- redacted canonical: redacted-canonical-v1
- reference canonical: reference-canonical-v1

Public align_reference no longer accepts caller canonical labels as sufficient evidence. After byte-pair resolution it requires:
- redacted.canonical_document_version_id == trusted_pair.redacted_canonical_version_id
- supplied reference_canonical_version_id == trusted_pair.reference_canonical_version_id

It rebuilds the redacted detector/canonical records from the pinned redacted PDF bytes using the trusted registry project, redacted document-version ID and pinned redacted canonical-version ID, then requires exact rebuilt CanonicalRedactedDocument equality and exact target tuple equality.

Confirmed mappings are invoked with the registry-pinned reference document-version and reference canonical-version IDs. Thus a successful mapping carries the approved canonical identities rather than caller-selected ones.

### 2. Forged, blank, missing and swapped canonical identities fail closed

Independent exact-condition probes confirmed:
- forged redacted canonical ID -> rejected
- blank redacted canonical ID -> rejected
- swapped redacted/reference canonical IDs -> rejected
- forged reference canonical ID -> rejected
- blank reference canonical ID -> rejected

The candidate tests additionally assert that untrusted canonical identities produce CONFLICTING, NOT_SCOREABLE mappings with exact_revealed_text=None and with canonical provenance withheld on the failed mapping.

No false-CONFIRMED path was found through the public DEC-022 entry point for these identity attacks.

### 3. Byte-pinned fixture trust remains intact

I independently regenerated the deterministic two_boxes fixture using the repository fixture algorithm under ReportLab 4.4.9 and reproduced the same literal pins:
- redacted SHA-256 2ce777d994b52281fe51f15194f4beecf47e1feb6332dfdc6873114dfe37faa2
- reference SHA-256 8316ae58f9a6e86c42764f3c47cb37a7e284e546eceba84dcfb3934bc5908eb4

Independent trust-gate probes confirmed modified redacted bytes, modified reference bytes, swapped PDFs, wrong project, wrong redacted document version and wrong reference document version all fail the gate.

This remains fixture provenance only; it is not archival authenticity or real-document validation.

### 4. Confirmed provenance is internally consistent for the registered pair

For a positive registered-pair path, source inspection and candidate tests show confirmed mappings carry:
- redacted_canonical_version_id = redacted-canonical-v1
- reference_canonical_version_id = reference-canonical-v1
- pinned document-version identities
- deterministic canonical/reference hashes and source locators from the content layer

The exact two registered revealed phrases remain Agent Cedar and 12 paper stars.

### 5. Prior truth/null protections remain intact

Correction 02 does not weaken the earlier DEC-021/022 content rules:
- _globally_supported still requires left_ok AND right_ok;
- true document boundary evidence substitutes only for the physically absent side;
- geometry fallback requires both available sides;
- unmatched document context prevents confirmation;
- repeated anchors, reordered passages and adjacent targets remain fail-closed under existing exact-candidate tests;
- anchor-only spans without exact physical source bounds remain AMBIGUOUS/null;
- partial/still-hidden reference content is not exposed as exact truth;
- unregistered or altered reference bytes cannot reach authoritative confirmation.

Independent probe truth table confirmed left-only and right-only non-boundary support are rejected while both-side support and a true boundary plus the available side are accepted.

### 6. Reference isolation and unknown/null semantics remain correct

PredictionManifest still exposes only redacted canonical input, target markers and prediction metadata; it has no reference/truth/evaluator field.

For failed trust/provenance conditions, mappings are NOT_SCOREABLE and exact_revealed_text remains null. Arbitrary user uploads remain outside the one registered DEC-022 pair and therefore cannot become trusted checkpoint truth.

No scoring-validity or D03 claim follows from a SCOREABLE synthetic mapping.

## Independent tests actually run

Attempted exact repository checkout:
git clone --no-checkout https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git /mnt/data/rl_mvp003_c02_repo

Result: NOT RUN TO COMPLETION — review container could not resolve github.com. The exact repository focused/full pytest suites were therefore NOT independently executed.

Independent synthetic provenance/trust probe:
python /mnt/data/rl_mvp003_dec022_c02_research_probe.py

Result: 20 / 20 passed.

Checks included:
- literal redacted/reference SHA pins
- correct registry + canonical provenance
- forged/blank/swapped canonical IDs
- wrong project/document-version claims
- modified redacted/reference bytes
- swapped PDF roles
- exact registered reference phrases
- left-only/right-only/both-side/boundary global-support semantics

Compile:
python -m compileall -q /mnt/data/rl_mvp003_dec022_c02_research_probe.py
Result: PASS.

Probe environment:
- Python review container
- ReportLab 4.4.9
- pypdf 5.9.0
- pdfplumber 0.11.9

Backend-reported evidence reviewed but not adopted as independent execution:
- 60 focused tests passed
- 180 full tests passed
- compileall passed
- 21 dependencies compatible
- git diff checks passed
under Backend's macOS/Python 3.11.15 environment.

Tests not run and reason:
- Exact repository 60-test focused and 180-test full suites: NOT RUN independently because a matching checkout could not be obtained due DNS/network restriction.
- Real/private reference documents, OCR/scans, hostile resource-exhaustion corpus, scientific benchmark, provider/model, scoring, Task 4, API/UI, persistence, cloud and deployment: outside this correction/review scope and/or unauthorized.

## Necessary-versus-sufficient research boundary

The correction now makes canonical provenance trustworthy inside the approved DEC-022 checkpoint mechanism, but this is only a synthetic fixture trust result.

A registered fixture pair plus pinned canonical versions is necessary for checkpoint confirmation. It is not sufficient for scientific validity: the content still must be complete, uniquely aligned, readable and exact, and D03 human scientific validation remains separately required.

No result here supports real-document automatic-confirmation accuracy, government-document provenance, archival authenticity or verified model reconstruction accuracy.

## Verdict

PASS for RL-MVP-003 DEC-022 Correction 02 Research trust/truth semantics on exact implementation 97db3615c65b9e31d0f94dca443baab760340c5f.

I found no false-CONFIRMED path in the reviewed public checkpoint interface from forged canonical-version identities, altered bytes, incorrect pair/version claims or one-sided textual evidence. Confirmed synthetic mappings now carry the pinned canonical identities and continue to require full content evidence.

This PASS is not D03 scientific validation, not research-human approval of real-document auto-confirmation, not merge authorization and not Task 4 authorization.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation 97db3615c65b9e31d0f94dca443baab760340c5f; no prior verdict was inherited.
Research / data approval evidence (or not approved / not applicable): D03 scientific validation NOT APPROVED. Synthetic-only checkpoint evidence; no Columbia/private-data authorization, real-document accuracy or production-readiness claim.
Known issues / risks / stale dependencies: Only deterministic two_boxes is registered. Literal PDF pins are intentionally environment-sensitive and fail closed on byte drift. Real authenticated persistence/provenance, archival identity, OCR/raster support, hostile-input isolation, real-document alignment calibration and production scale remain deferred/unvalidated. The private _align_reference_content seam remains test-only and must not become an application trust path.
Affected roles / requested next action: Lead should reconcile this fresh Research PASS with fresh QA review of the same exact SHA. Do not merge or begin Task 4 from this handoff alone; separate owner merge authorization and all required gates remain.
Last freshness check and relevant differences: Immediately before publication, live main remained 0c3462291676be7b7b6e101a6cb2910a094a5cbd / E0031. Backend publication head 139921de76f9f3d0a67af19217e0969464f88ffd differs from implementation 97db3615c65b9e31d0f94dca443baab760340c5f only by the Backend handoff.
Rollback or correction approach: This Research branch contains only this handoff. If candidate/governing decisions change, this review becomes stale and a new exact-SHA review is required.
Publication: PUBLISHED on review/rl-mvp-003-research-dec022-correction02-e0031; not merged to main.
