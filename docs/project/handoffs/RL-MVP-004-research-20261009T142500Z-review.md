# RL-MVP-004 Research / prediction-protocol review

Task ID: RL-MVP-004 — Redacted-Only Prediction Adapter and Durable SQLite Worker
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-09T14:25:00Z
State: CHANGES_REQUESTED
Review verdict: CHANGES_REQUESTED FOR TASK-4 RESEARCH/PREDICTION-PROTOCOL SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: b6fdc226596748a6340c6f85f9e30ae473fd41a8 / E0035
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-004-prediction-worker / implementation c3a928ce1aaf2039bc778cb91c272b435fb93aa4; Backend publication head de9ad26f7225f5717d2c6ace683e1f21b0fed2fa.
Source requirements / approved decisions / contract versions: AGENTS.md; docs/project/task_packets/RL-MVP-004-INDEPENDENT-REVIEW.md; owner-approved docs/project/task_packets/RL-MVP-004-prediction-adapter-durable-worker-PROPOSED.md; DEC-001/004/008/009/015/017/020/022; RESEARCH_METHOD.md; INTERFACES.md; merged RunDefinition, PredictionManifest, ModelAttempt, CanonicalRedactedDocument and JobState contracts.
Authorization reference and permitted file/action scope: E0035 independent review permits read-only exact-candidate inspection, no-cost isolated probes and one unique Research handoff. No implementation edits, merge, Task 5, model download/install, real inference, provider/external calls, paid services, private data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to b6fdc226596748a6340c6f85f9e30ae473fd41a8 / E0035 and read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md, INTERFACES.md and docs/project/task_packets/RL-MVP-004-INDEPENDENT-REVIEW.md.
- Read the owner-approved Task-4 packet and Backend handoff docs/project/handoffs/RL-MVP-004-backend-20261009T134815Z-c3a928c.md at de9ad26f7225f5717d2c6ace683e1f21b0fed2fa.
- Inspected exact implementation c3a928ce1aaf2039bc778cb91c272b435fb93aa4 in:
  - src/redaction_lab/adapters/base.py
  - src/redaction_lab/adapters/ollama.py
  - src/redaction_lab/store.py
  - src/redaction_lab/worker.py
  - tests/test_adapter.py
  - tests/test_worker.py
- Confirmed candidate delta from its implementation baseline is exactly those six approved source/test files; publication head adds only the unique Backend handoff.

## Positive Research findings

1. **One-target-per-request context transformation is structurally correct for a trusted canonical input.**
   - build_prediction_manifest keeps the selected target as [[TARGET:<id>]].
   - Every declared non-selected target marker becomes [[REDACTED:<id>]].
   - The same canonical document text is the starting point for each target-specific render.
   - No previous model guess is written back into the canonical context.

2. **Reference/evaluator fields are structurally absent from PredictionManifest and provider payload construction.**
   - The provider payload is limited to model/options/prompt/stream.
   - The adapter has no reference-PDF, ReferenceMapping, evaluator-feedback or prior-prediction argument.
   - The prompt explicitly tells the model that REDACTED markers are unavailable.

3. **Prompt/model/settings provenance is deterministic at the attempt boundary.**
   - manifest identity includes project/run/target/version, canonical version/hash/text, prompt ID/version, model ID and allow-listed settings.
   - provider request hashing binds the prepared body hash, canonical document hash, model_config_id and prompt ID/version.
   - ModelAttempt persists model_id, model_config_id, request/response hashes and timestamps.

4. **Outcome channels remain distinct.**
   - SUCCEEDED requires a prediction and response hash.
   - REFUSED, TIMEOUT, ERROR and MALFORMED carry no prediction.
   - Direct TimeoutError/socket.timeout is mapped to TIMEOUT.
   - RunStore keeps a TIMEOUT job internally IN_DOUBT rather than treating it as a successful or factual attempt.

5. **At-most-once no-retry intent is directionally conservative.**
   - claim moves PENDING -> IN_DOUBT before adapter.predict.
   - concurrent claims are guarded by an atomic UPDATE ... WHERE state='PENDING'.
   - a worker crash after claim leaves IN_DOUBT and no automatic retry path.
   - duplicate enqueue under the same scope checks the frozen manifest.
   - successful/refused/malformed/error attempts are immutable once written.

6. **Mocked tests do not claim real inference quality.**
   - Backend explicitly reports real local inference BLOCKED after read-only feasibility preflight found no installed runtime/model/cache/license.
   - No model download, inference, paid call or scientific score claim was made.

These positives do not establish real-model quality, semantic accuracy, D03 validation or production readiness.

## Blocking finding 1 — self-consistent forged canonical input can carry hidden/reference truth into the prediction request

The Task-4 packet explicitly stops for forged provenance or reference leakage. build_prediction_manifest validates that canonical_hash matches canonical_text and that the RunDefinition repeats the same canonical version/hash, but it does not authenticate that the supplied CanonicalRedactedDocument was actually produced by the trusted Task-2 canonicalizer from the authorized redacted PDF.

A caller can therefore construct a **self-consistent forged canonical record**, recompute its SHA-256, construct a matching RunDefinition, retain the required target markers, and insert answer-bearing/reference-only text elsewhere in canonical_text. All current builder predicates pass and the injected text is serialized into the provider prompt.

Independent exact-logic probe reproduced:

    canonical_text =
      "Visible REFERENCE_ONLY_SECRET before [[TARGET:t1]]
       between [[TARGET:t2]] after."

with a recomputed canonical hash and a RunDefinition carrying that same hash/version. The builder accepted it and produced:

    "Visible REFERENCE_ONLY_SECRET before [[TARGET:t1]]
     between [[REDACTED:t2]] after."

Thus the current hash check proves only internal self-consistency, not trusted redacted-only provenance.

The same seam also accepts caller-selected positional target_versions because build_prediction_manifest receives only CanonicalRedactedDocument target IDs plus RunDefinition.target_versions; it does not receive trusted RedactionTarget records to bind each ID to its immutable target version.

This is blocking because a forged canonical object can violate the experiment's central redacted-only condition while still satisfying the current API. Existing test_manifest_builder_rejects_forged_canonical_text_hash covers a stale/mismatched hash, not a recomputed self-consistent forgery.

Required direction: bind prediction-manifest construction to a trusted canonical artifact/source record or equivalent authenticated pipeline provenance. If that requires an out-of-scope contract/persistence change, stop for Lead/owner scope rather than treating a self-signed canonical hash as authority.

## Blocking finding 2 — urllib-wrapped network timeout is classified as terminal ERROR instead of ambiguous TIMEOUT/IN_DOUBT

OllamaAdapter.predict distinguishes direct TimeoutError/socket.timeout from other transport exceptions:

- direct TimeoutError/socket.timeout -> AttemptStatus.TIMEOUT
- URLError -> AttemptStatus.ERROR

However urllib commonly represents socket timeouts as URLError(reason=socket.timeout(...)). Under the exact catch ordering, that wrapped timeout becomes ERROR.

RunStore.complete then maps only status TIMEOUT to IN_DOUBT; every other status, including ERROR, becomes COMPLETE.

Independent exact exception-classification probe:

- TimeoutError("timed out") -> TIMEOUT -> IN_DOUBT
- URLError(socket.timeout("timed out")) -> ERROR -> COMPLETE

This converts an ambiguous post-dispatch timeout into a terminal technical ERROR instead of preserving uncertainty. It does not create a successful prediction, but it violates the packet requirement that ambiguous dispatch/timeouts remain explicitly IN_DOUBT/unknown and not be silently finalized as ordinary terminal failures.

Required correction: detect timeout-wrapped URLError (and equivalent timeout wrappers produced by the stdlib transport) and preserve TIMEOUT/IN_DOUBT semantics, without introducing retry.

## Nonblocking Research limitations / cautions

1. **Byte budget is not a tokenizer/context-window guarantee.**
   - build_prediction_manifest gates UTF-8 byte length of the canonical/rendered document.
   - It does not use the eventual model tokenizer and does not prove the complete provider prompt fits a model's context window.
   - The fixed recovery instruction and JSON/provider framing are outside the document-byte check.
   - This can be an explicitly experimental conservative proxy only; direct cross-model context equivalence is not established.

2. **Model configuration is recorded per attempt but not frozen by RunDefinition.**
   - RunDefinition declares model_id/settings but no model_config_id.
   - different target jobs in one run could in principle be claimed by adapters carrying different model_config_id values while sharing the same model_id.
   - each attempt preserves the differing config ID, so the provenance is observable, but later comparisons must not treat such attempts as one common model condition unless D05/run-level configuration binding is added or filtered explicitly.

3. **Real-model feasibility remains BLOCKED.**
   - No installed local runtime/model/cache/license was verified in the approved preflight.
   - Mock response behavior cannot establish prediction quality, latency, token feasibility, model availability or reconstruction accuracy.

4. **No exactly-once provider-execution guarantee is claimed or established.**
   - The conservative state machine aims for no automatic duplicate dispatch after uncertainty.
   - provider-side exactly-once semantics remain unavailable, and this must remain explicit in experiment reporting.

## Independent tests actually run

Exact checkout attempt:

    git clone --no-checkout       https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git       /mnt/data/rl_mvp004_review

Result: NOT RUN TO COMPLETION — container could not resolve github.com. Therefore the exact 46 focused and 226 full repository tests were NOT independently rerun.

Independent adversarial probe:

    python /mnt/data/rl_mvp004_research_probe.py

Result:
- PASS control: selected target remained TARGET; non-selected target became REDACTED.
- BLOCKER reproduced: self-consistent forged canonical text containing REFERENCE_ONLY_SECRET was accepted and serialized.
- BLOCKER reproduced: caller-selected positional target version was accepted without trusted target-record binding.
- PASS control: direct TimeoutError -> TIMEOUT -> IN_DOUBT.
- BLOCKER reproduced: URLError(socket.timeout) -> ERROR -> COMPLETE.

Compile:

    python -m compileall -q /mnt/data/rl_mvp004_research_probe.py

Result: PASS.

The probe reproduced the exact candidate predicates/catch ordering relevant to these findings. It was not a byte-for-byte execution of the repository package.

Backend-reported evidence reviewed but not adopted as independent execution:
- 46 focused tests passed
- 226 full tests passed
- compileall passed
- 21 packages compatible
- git diff check passed
under Backend's Python 3.11.15 environment.

Tests not run and reason:
- exact repository focused/full pytest: NOT RUN independently because checkout was unavailable due DNS/network restriction.
- real inference/model download/install: NOT RUN and explicitly unauthorized; local feasibility is BLOCKED.
- evaluator/scoring, Task 5, private data, external providers, deployment and scientific benchmark: outside scope and/or unauthorized.

## Research answers to the requested protocol checks

1. Frozen redacted-only context: **PASS only for trusted canonical input; FAIL as a trust boundary** because a self-consistent forged canonical record can inject hidden/reference truth.
2. One-target-per-request independence / other targets hidden: **PASS** for the builder transformation and existing declared target set.
3. Reference isolation: **structurally PASS at the manifest schema, but BLOCKED by forged canonical provenance** because answer-bearing text can be smuggled through canonical_text.
4. Prompt/model/settings provenance: **mostly PASS at attempt level**, with model_config_id not frozen at run level as a limitation.
5. Experimental comparability: **not established** beyond byte-identical canonical source/render policy and recorded provenance; tokenizer/model-context equivalence and real-model availability remain unverified.
6. Refusal/timeout semantics: **REFUSED separation PASS; timeout handling CHANGES_REQUESTED** because URLError-wrapped socket timeout becomes terminal ERROR/COMPLETE.
7. Scientific limitations: **correctly non-claimed**. Mock tests establish infrastructure behavior only; they do not validate prediction quality, semantic scores, D03 approval or licensed local-model availability.

## Verdict

CHANGES_REQUESTED on exact implementation c3a928ce1aaf2039bc778cb91c272b435fb93aa4.

Two blocking Research/protocol issues must be resolved before Task-4 integration:
1. prediction-manifest construction must not trust a merely self-consistent caller-forged CanonicalRedactedDocument that can carry hidden/reference truth; and
2. timeout conditions wrapped by urllib must remain TIMEOUT/IN_DOUBT rather than becoming terminal ERROR/COMPLETE.

Do not merge and do not begin Task 5. If canonical provenance cannot be authenticated within current Task-4 files/contracts, escalate for a narrowly scoped contract/persistence decision instead of weakening the redacted-only experiment condition.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation c3a928ce1aaf2039bc778cb91c272b435fb93aa4; Backend self-review/test counts were not treated as independent.
Research / data approval evidence (or not approved / not applicable): D03 scientific validation NOT APPROVED. D05 protocol remains unvalidated by a designated research human. No real inference, model quality, Columbia/private-data authorization or production-readiness claim.
Known issues / risks / stale dependencies: UTF-8 byte budget is not a tokenizer/window guarantee; model_config_id is attempt-level rather than run-frozen; real local model/runtime/license feasibility remains blocked; no exactly-once provider guarantee; future API/UI must preserve IN_DOUBT distinctly from terminal outcomes.
Affected roles / requested next action: Lead -> Backend/Codex for bounded correction/scope reconciliation; fresh QA and Research review on a new exact SHA. Owner merge authorization remains separate. No Task 5.
Last freshness check and relevant differences: Immediately before publication, live main remained b6fdc226596748a6340c6f85f9e30ae473fd41a8 / E0035. Backend publication head de9ad26f7225f5717d2c6ace683e1f21b0fed2fa differs from implementation c3a928ce1aaf2039bc778cb91c272b435fb93aa4 only by the unique Backend handoff.
Rollback or correction approach: This Research branch contains only this handoff. If candidate/governing decisions change, this review becomes stale. Any implementation correction must be additive and separately scoped; never force-push.
Publication: PUBLISHED on review/rl-mvp-004-research-e0035; not merged to main.
