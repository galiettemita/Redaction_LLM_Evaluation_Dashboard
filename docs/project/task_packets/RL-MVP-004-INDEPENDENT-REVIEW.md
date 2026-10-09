# RL-MVP-004 — Independent QA and Research review

**Status:** READY_FOR_REVIEW; independent verdicts PENDING. **Owner:** Backend/Codex. **Reviewers:** QA and Research separately. **Next receiver:** Lead/Architect.
**Baseline main:** `44f165d801c1c6c5435fb04417462c382b8f422e`, E0034. Review-routing epoch E0035.
**Exact implementation SHA:** `c3a928ce1aaf2039bc778cb91c272b435fb93aa4`.
**Published Backend head:** `de9ad26f7225f5717d2c6ace683e1f21b0fed2fa` on `codex/rl-mvp-004-prediction-worker`.
**Backend handoff:** `docs/project/handoffs/RL-MVP-004-backend-20261009T134815Z-c3a928c.md`.
**Authority:** AGENTS.md; DEC-001/004/008/009/015/017/020/022; approved `docs/project/task_packets/RL-MVP-004-prediction-adapter-durable-worker-PROPOSED.md`; Task 4 of implementation plan. **Deadline:** October 12, 2026; no quality waiver.

## Shared review

Refresh GitHub main HEAD, read AGENTS.md, CURRENT_STATE.md, DECISIONS.md, active AGENT_HANDOFF.md and this packet, then inspect exact candidate and Backend handoff. Verify exact implementation commit changes ONLY `src/redaction_lab/adapters/base.py`, `src/redaction_lab/adapters/ollama.py`, `src/redaction_lab/store.py`, `src/redaction_lab/worker.py`, `tests/test_adapter.py`, `tests/test_worker.py`; publication commit adds only unique Backend handoff. Do not confuse prior main history with candidate delta.

Codex reports 46 focused and 226 full pytest passes, compileall, 21 compatible packages and git diff --check; Lead has NOT independently executed these tests. Reviewers should rerun focused/full suite on exact SHA if possible; otherwise clearly mark NOT RUN and publish independently reproducible probes. Backend self-review is not independent verification.

## QA: adversarial software/security probes

1. **Reference and hidden-text isolation:** no reference PDF/text, ReferenceMapping, target truth, filename, metadata, previous guess or evaluation feedback enters manifest, provider payload, logs or cache key. Test forged CanonicalRedactedDocument text/hash, undeclared/missing/duplicate markers, other targets still masked, unexpected extra fields, wrong project/version and mixed target ordering.
2. **Network isolation:** reject non-loopback endpoints, localhost DNS, userinfo, IPv6, proxies, redirects (including 30x), malformed port/path/query, environment-proxy injection and response size exhaustion. Verify injected transport cannot silently bypass required endpoint validation. No real inference or external calls.
3. **One-shot durability:** duplicate enqueue/claim, concurrent workers/processes, SQLite unique keys and immutable job/attempt rows, crash after intent but before dispatch, crash after dispatch but before response, ambiguous timeout, reconnect, repeated completion and restart. Inspect `next_pending`/claim race and state transitions; no second attempt, no silent retry, no false completed state. Confirm internal IN_DOUBT cannot be confused with a public success/failure.
4. **Attempt/protocol integrity:** deterministic request/response hashes, model/prompt/settings provenance, malformed/refusal/error/timeout handling, output whitespace/punctuation, forged adapter request/config IDs, response-body limits, provider exceptions after claim and resulting durable state. Test the worker's behavior when `adapter.request_hash`, `adapter.predict`, or `store.complete` throws.
5. **Dependencies and scope:** no new dependencies, model downloads, model calls, paid services, private data, Task 5 or deployment. Record exact test commands/results and NOT RUN. Report PASS / CHANGES_REQUESTED / BLOCKED with severity, reproduction and next receiver; do not modify implementation.

## Research: independent protocol checks

1. Validate identical frozen visible-redacted context across targets/models, selected-target independence, other boxes still hidden, no target truth/reference leakage, no prior prediction conditioning and stable prompt/settings/model version provenance.
2. Verify refusal, timeout, malformed/error and ambiguous crash states are NOT scored as factual mistakes or omitted from future denominators. No unsupported claim of exactly-once provider execution or successful real-model inference.
3. Assess UTF-8 byte-budget proxy versus actual tokenizer/context window; identify limits to comparability without inventing model-specific token equivalence. Check experimental condition and any model/provider version evidence.
4. Verify mock tests cannot establish real prediction quality, semantic score validity, D03 scientific approval or availability of a licensed offline model. Report local feasibility as BLOCKED per Backend read-only preflight: Apple M5, 32 GB memory, no discovered runtime/cache/model license. Do not install/download/infer.
5. Publish exact-SHA Research PASS / CHANGES_REQUESTED / BLOCKED with independent tests, assumptions, research limitations and next receiver. No rubric/score weights approval implied.

## Publication and stops

QA and Research each publish one unique scoped handoff on their approved review branches, referencing exact implementation SHA and tests run/not run. No implementation code changes, main merge, Task 5, real inference, model download, external API, paid call, private data or deployment. Any leakage, non-loopback egress, duplicate dispatch or incorrect state/provenance is blocking. Lead reconciles both handoffs before requesting separate owner merge approval. No automatic chat messaging or agent acknowledgment is presumed.
