# RL-MVP-004 Correction 01 Research review

Task ID: RL-MVP-004 — Correction 01 Trusted Prediction Source and Protocol Integrity
Role / session label: Research / Evaluation independent reviewer
UTC time: 2026-10-09T18:04:00Z
State: READY_FOR_REVIEW
Review verdict: PASS FOR TASK-4 RESEARCH/PREDICTION-PROTOCOL SEMANTICS; NOT SCIENTIFIC VALIDATION
Baseline integration SHA / decision epoch: b6fdc226596748a6340c6f85f9e30ae473fd41a8 / E0035
Candidate branch / exact commit SHA (or no code change): codex/rl-mvp-004-prediction-worker / exact corrected implementation b9ce8182751f26109fbd857bcb8d909720bafd13; Backend publication head fb4c1f054afc35188ad1a086221bc96dd78d1b18.
Source requirements / approved decisions / contract versions: AGENTS.md; current main state/decisions/handoff index; owner-approved docs/project/task_packets/RL-MVP-004-CORRECTION-01.md at eb7e78054eecf4d07b78b00ae60e466e383c0e74; prior QA CHANGES_REQUESTED on c3a928ce; prior Research CHANGES_REQUESTED on c3a928ce; DEC-001/004/008/009/015/017/020/022; current PredictionManifest, ModelAttempt, RunDefinition and CanonicalRedactedDocument contracts.
Authorization reference and permitted file/action scope: user-requested independent Research review plus Correction-01 packet. Read-only exact-code inspection, no-cost isolated probes and one unique Research handoff only. No application-code edits, merge, Task 5, model download/install, real inference, provider/external call, paid service, private data, cloud or deployment.

Work performed / artifacts and exact paths:
- Refreshed live main to b6fdc226596748a6340c6f85f9e30ae473fd41a8 / E0035 and reread AGENTS.md, CURRENT_STATE.md, DECISIONS.md, AGENT_HANDOFF.md, RESEARCH_METHOD.md and INTERFACES.md.
- Read the owner-approved Correction 01 packet at commit eb7e78054eecf4d07b78b00ae60e466e383c0e74.
- Read prior exact-candidate QA and Research handoffs for rejected implementation c3a928ce1aaf2039bc778cb91c272b435fb93aa4.
- Read corrected Backend handoff docs/project/handoffs/RL-MVP-004-backend-20261009T145748Z-b9ce818.md at fb4c1f054afc35188ad1a086221bc96dd78d1b18.
- Inspected exact corrected implementation b9ce8182751f26109fbd857bcb8d909720bafd13, especially:
  - src/redaction_lab/prediction_source.py
  - src/redaction_lab/adapters/base.py
  - src/redaction_lab/adapters/ollama.py
  - src/redaction_lab/store.py
  - src/redaction_lab/worker.py
  - src/redaction_lab/contracts.py
  - tests/test_prediction_source.py
  - tests/test_adapter.py
  - tests/test_worker.py
  - tests/test_contracts.py
- Confirmed the correction stays within the owner-approved file scope; the following Backend publication commit adds only the handoff.

## Findings

### 1. Trusted PDF-derived prediction source — PASS within the approved internal-service boundary

Correction 01 introduces an application-owned PredictionSource derived from actual redacted PDF bytes. Source identity is deterministic and project-scoped over:
- source PDF SHA-256
- project ID
- detector version
- canonicalizer version
- prediction-source version

The source derivation calls the existing fail-closed detector and canonicalizer and stores exact target IDs and target versions. It accepts no reference PDF, ReferenceMapping, truth span, prior prediction or evaluator feedback.

RunStore no longer accepts a caller-created PredictionManifest. enqueue now requires:
- stored source_id
- target_id
- frozen RunDefinition

The store resolves its own immutable source record, requires the run's project/canonical hash/canonical version/target-version order/attempt policy to match the source, builds the manifest internally and revalidates stored source/job integrity before claim.

This resolves the prior Research blocker where a self-consistent forged CanonicalRedactedDocument plus matching forged RunDefinition could directly become a worker payload.

Important limitation: ingest_redacted_pdf is explicitly an internal trusted-service/test-harness boundary. It does NOT authenticate callers itself, and project_id is only a selector. No arbitrary-upload authorization claim is made. Under the Correction-01 packet this is acceptable; any future public/API exposure must add a real authenticated service boundary before treating uploads as authorized.

### 2. Redacted-only context and target independence — PASS

For source-derived manifests:
- the selected target alone remains [[TARGET:<id>]];
- every other registered target becomes [[REDACTED:<id>]];
- all requests start from the same source-derived canonical document;
- exact target version comes from the source's authoritative ordered RedactionTarget records;
- run.target_versions must exactly equal the source target-version tuple;
- previous guesses are not written into later manifests;
- PredictionManifest and provider payload still have no reference/evaluator fields.

The source test surface also verifies hidden selectable text does not enter the stored canonical source.

I found no reference/truth leakage path through the approved RunStore -> worker -> adapter flow.

### 3. Direct untrusted manifest enqueue / legacy jobs — PASS

RunStore.enqueue no longer exposes the old direct-manifest signature. The jobs table has a trusted-insert guard requiring:
- current trust_version;
- non-null source_id;
- non-null run_json;
- source row with matching project and REDACTED role.

next_pending additionally requires a bound source and current trust version, and _validate_bound_job rebuilds the expected manifest from the stored source plus frozen run before claim.

Legacy PENDING rows without source/run trust binding remain readable but are not selected for dispatch. Legacy completed attempts remain readable and immutable.

I found no dispatch path for a caller-created manifest through the approved store/worker interface.

### 4. SQLite immutability / at-most-once intent — PASS for reviewed scope

The correction adds immutable canonical_sources and run_configs tables plus stricter job-state triggers.

Source inspection and isolated trigger probes confirm:
- new untrusted job inserts are rejected;
- normal PENDING -> IN_DOUBT claim is allowed;
- resetting IN_DOUBT/COMPLETE back to PENDING is rejected;
- source/run/manifest/attempt immutable fields cannot be rewritten through the guarded schema;
- run model configuration is frozen on first claim and a later different model_config_id for the same project/run/model cannot dispatch;
- claim remains atomic and only PENDING rows can win;
- restart after claim cannot redispatch IN_DOUBT work.

This is an at-most-once dispatch intent, not provider-level exactly-once execution.

### 5. Wrapped timeout ambiguity — RESOLVED

The adapter now traverses bounded exception reason/cause/context chains and treats:
- TimeoutError;
- errno.ETIMEDOUT OSError;
- URLError.reason wrapping those timeout types

as TIMEOUT.

RunStore preserves TIMEOUT jobs as IN_DOUBT. There is no retry path from IN_DOUBT.

My independent isolated probe reproduced:
- URLError(socket.timeout(...)) -> timeout classification;
- OSError(ETIMEDOUT) in a cause chain -> timeout classification;
- cyclic exception chains terminate safely.

The prior Research blocker where a urllib-wrapped timeout became terminal ERROR/COMPLETE is resolved.

### 6. Production transport boundary — PASS with trusted-process caveat

OllamaAdapter.__init__ no longer accepts an arbitrary transport callable. Production transport is built internally and retains:
- exact numeric IPv4 loopback http://127.0.0.1:<port>;
- no localhost/DNS/IPv6/userinfo/path/query/fragment;
- ProxyHandler({}) to disable environment proxies;
- redirect rejection;
- response-size bound.

Tests monkeypatch the private _stdlib_transport seam only inside the trusted test process.

This does not and should not claim containment against arbitrary already-executing malicious Python in the trusted process. Directly calling OllamaAdapter.predict with a fabricated manifest from arbitrary trusted-process code would bypass the RunStore authority layer; the approved architecture therefore depends on the worker/store being the sole application dispatch path. Because no public/API caller boundary is authorized in this task and the packet explicitly excludes malicious trusted-process containment, I treat this as a documented nonblocking boundary, not a Task-4 defect. It becomes blocking if a future API exposes the adapter directly.

### 7. Requested vs provider-reported model identity — PASS with scientific limitation

ModelAttempt now records optional provider_model_id separately from requested model_id.

For new successful/refused Ollama responses:
- provider top-level model must be present and nonblank;
- provider model must exactly match requested model_id;
- missing identity -> MALFORMED;
- mismatch -> technical ERROR with null prediction and returned provider_model_id retained;
- store completion rejects a SUCCEEDED/REFUSED attempt whose provider_model_id does not equal requested model_id.

This fixes the prior provenance defect.

However, equal provider/requested names establish only name equality. They do NOT prove stable weights, digest, quantization, tokenizer or serving build. The Backend handoff correctly preserves this limitation. D05/model-roster scientific comparability remains unapproved.

### 8. Frozen prompt/settings/model configuration — PASS for infrastructure, not D05 validation

RunDefinition freezes prompt ID/version, model_id, settings, context policy and attempt policy. The trusted store freezes the RunDefinition JSON across target jobs in a run.

model_config_id is not a RunDefinition field, but run_configs freezes the first claimed model configuration for the project/run/model; a later different config is rejected before dispatch.

This prevents silently pooling two model_config_id values within the reviewed store execution. It does not make the protocol scientifically validated; D05 still must specify and approve the model roster/version condition.

### 9. Refusal/error/timeout semantics — PASS

- REFUSED remains distinct from SUCCEEDED and carries no prediction.
- malformed provider output remains MALFORMED.
- deterministic transport/provider failures remain ERROR.
- ambiguous timeout remains TIMEOUT plus internal IN_DOUBT.
- no non-success outcome becomes a factual zero or a successful prediction in this task.

Future evaluation/summary code must continue preserving these distinctions.

## Independent tests actually run

Exact repository checkout attempt:

    git ls-remote https://github.com/galiettemita/Redaction_LLM_Evaluation_Dashboard.git HEAD

Result:
    fatal: Could not resolve host: github.com

Therefore I could not independently execute the exact repository's Backend-reported 102 focused / 255 full pytest suites.

Independent Correction-01 protocol probe:

    python /mnt/data/rl_mvp004_c01_research_probe.py

Result: 11 / 11 PASS.

Checks:
- project-scoped deterministic source identity;
- one-target TARGET / other-target REDACTED rendering for both targets;
- URLError-wrapped timeout classification;
- timeout cause-chain handling;
- cyclic exception-chain bound;
- missing provider model -> MALFORMED predicate;
- provider mismatch -> ERROR predicate;
- exact provider-name match accepted by the name gate;
- direct untrusted job insert rejected by trusted-source trigger;
- valid PENDING -> IN_DOUBT transition;
- IN_DOUBT -> PENDING reset rejected.

Compile:

    python -m compileall -q /mnt/data/rl_mvp004_c01_research_probe.py

Result: PASS.

Independent limitation/config probe:

    python /mnt/data/rl_mvp004_c01_research_limits_probe.py

Result:
- first-claim run model_config_id freeze: PASS
- direct adapter serialization of arbitrary trusted-process manifest text: reproduced as an intentional trust-boundary limitation, not treated as an external-caller-safe path.

Compile:

    python -m compileall -q /mnt/data/rl_mvp004_c01_research_limits_probe.py

Result: PASS.

These probes are isolated reproductions of exact reviewed predicates/schema transitions, not byte-for-byte execution of the repository package.

Backend-reported evidence reviewed but not adopted as independent execution:
- 102 focused tests passed;
- 255 full tests passed;
- migration/restart/wrapped-timeout/direct-insert selection passed;
- compileall passed;
- 21 dependencies compatible;
- git diff checks passed;
all under Backend's Python 3.11.15 environment.

Tests not run and reason:
- exact repository focused/full pytest: NOT RUN independently because container DNS could not resolve github.com;
- real inference/model/runtime/license: NOT RUN and explicitly unauthorized; feasibility remains BLOCKED;
- model downloads/installations: NOT RUN and unauthorized;
- evaluator/scoring/Task 5/private data/external provider/deployment/scientific benchmark: outside scope and/or unauthorized.

## Nonblocking Research limitations

1. The trusted source ingestion method is not an authentication system; it assumes a pre-authenticated internal caller.
2. The adapter itself does not authenticate manifests; protocol safety relies on the store/worker being the only application dispatch route.
3. UTF-8 byte budget is not tokenizer/context-window equivalence and does not prove cross-model context comparability.
4. provider_model_id equality is string equality, not cryptographic model-weight identity.
5. model_config_id is frozen transactionally at first claim rather than declared inside RunDefinition.
6. No provider-level exactly-once guarantee exists.
7. No installed licensed local model/runtime was verified; real inference remains BLOCKED.
8. Mock/synthetic tests do not establish reconstruction quality, real-document performance, semantic accuracy or scientific validity.

## Verdict

PASS for RL-MVP-004 Correction 01 Research/prediction-protocol semantics on exact implementation b9ce8182751f26109fbd857bcb8d909720bafd13.

The two Research blockers from c3a928ce are resolved:
1. the approved worker path now derives prediction context from an application-owned PDF-derived source and no longer accepts direct caller manifests; and
2. wrapped network timeouts remain TIMEOUT/IN_DOUBT with no retry.

The correction also addresses the related QA provenance issues by removing public transport injection and recording/validating provider-reported model identity.

This PASS is limited to the mock-tested internal Task-4 protocol. It is NOT D03 or D05 research-human approval, not proof of tokenizer equivalence, not proof of actual model-weight identity, not real inference evidence, not model-quality evidence, not merge authorization and not Task-5 authorization.

Independent review evidence (or not yet reviewed): Fresh Research/Evaluation review of exact implementation b9ce8182751f26109fbd857bcb8d909720bafd13. Prior verdicts on c3a928ce were not inherited.
Research / data approval evidence (or not approved / not applicable): D03 and D05 remain NOT APPROVED by the designated research human. No real-model, Columbia/private-data or production-readiness approval.
Known issues / risks / stale dependencies: trusted internal caller boundary, adapter direct-call trust assumption, byte-budget/tokenizer mismatch, name-only provider model identity, first-claim config freeze, no provider exactly-once guarantee, no licensed local model/runtime, no real inference.
Affected roles / requested next action: Lead should reconcile this fresh Research PASS with the fresh QA review of the same exact SHA. Separate owner merge authorization remains required. Do not begin Task 5.
Last freshness check and relevant differences: Immediately before publication, live main remained b6fdc226596748a6340c6f85f9e30ae473fd41a8 / E0035. Correction packet is owner-approved on Lead preparation commit eb7e78054eecf4d07b78b00ae60e466e383c0e74. Backend publication head fb4c1f054afc35188ad1a086221bc96dd78d1b18 differs from exact implementation b9ce8182751f26109fbd857bcb8d909720bafd13 only by the unique Backend handoff.
Rollback or correction approach: This Research branch contains only this handoff. If the candidate or governing decisions change, the review becomes stale and must be repeated. No force-push.
Publication: PUBLISHED on review/rl-mvp-004-research-correction01-e0035; not merged to main.
