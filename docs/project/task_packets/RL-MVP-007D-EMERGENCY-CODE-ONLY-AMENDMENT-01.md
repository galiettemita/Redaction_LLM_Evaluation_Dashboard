# RL-MVP-007D Emergency Real Inference — Code-Only Amendment 01 (E0066)

**Status:** OWNER APPROVED; code-only execution permitted on the existing authorized isolated task branch. **NOT IMPLEMENTED / NOT REVIEWED / NOT MERGED.**
**Authorization:** project owner in Lead 3 conversation, 2026-10-13 America/New_York: "I approve a narrow E0065 amendment authorizing code-only implementation and mock/synthetic automated tests on the approved isolated branch despite the failed disk-storage gate. No Podman/Ollama installation, downloads, real PDF processing, genuine inference, paid calls, deployment, or merge until the existing prerequisite gates pass. Preserve all PDF isolation, redacted-only prediction, and null-scoring requirements."
**Baseline:** main `e62bf043c3f49ecbc290be4de601cbcd464ee6b0` / E0065 at approval. Recheck live integration HEAD, controlling decisions and handoffs before work.
**Parent:** [E0065 emergency packet](RL-MVP-007D-EMERGENCY-REAL-INFERENCE.md) and [API v0.2](../API_CONTRACT_V0_2.md). Amendment supersedes the parent *only* where its mandatory storage prerequisite would otherwise block **code-only** work and mock/synthetic automated tests; it does not relax any runtime acquisition/qualification or actual inference prerequisites.

## Permitted
1. Create/use the parent packet's isolated branch `codex/rl-mvp-007d-emergency-real-inference`, inspect source and implement API v0.2 PDF-to-prediction orchestration, model/runtime verification logic, immutable one-shot intent/attempt state, durable restart semantics, validated results retrieval and React display within **exactly the source/test paths listed in the parent E0065 packet**. No broader files/modules, new schemas, Task 3/6 changes, detector/canonicalizer changes, or new dependencies.
2. Implement/update fail-closed PDF worker packaging recipes and verifiers **as code only**, using existing approved dependencies and integrity evidence. Missing official hashes/models/VM results remain unverified placeholders; never flip `runtime_verified` or assert real qualification based on mocks.
3. Write/run focused and full **mock/synthetic automated tests** in an existing available environment. Fake/adversarial worker transport, Ollama adapter, runtime responses and redacted-only canonical fixtures are permitted in tests. Running automated tests must not invoke actual PDF parsing/process uploaded or synthetic PDF files through a live worker or start Podman/Ollama, downloads, installations, VM or real model inference. Existing tests that would violate these limits must be skipped with exact NOT RUN explanation.
4. Rebuild Vite assets *only if* the already-installed, approved toolchain is available with no installation/download, and only within authorized frontend/generated-output paths. If unavailable, publish code-only source plus NOT BUILT/NON-DISTRIBUTABLE status; no fake hashes/manual bundle patch.
5. Record actual tests, changed files, limitations and exact implementation SHA; publish one unique Backend handoff on the task branch. Mark implementation `CODE_ONLY_READY_FOR_INDEPENDENT_REVIEW` if evidence supports it. Route exact candidate to independent QA/security and Research review; neither review authorizes merge, runtime or deployment.

## Remain forbidden
- Any Podman/Ollama/model/image/wheel installation or download, image build, VM/container invocation, runtime qualification, actual PDF processing, real inference, external model call, paid service, private data, public deployment/distribution, direct main edit or merge.
- Attempts to bypass the existing 15 GiB physical APFS free-space gate for runtime operations. Last reported free was 6.16 GiB; original required headroom 15 GiB. Recheck at the future separately approved runtime checkpoint; do not delete/move unrelated files.
- Changing truth/reference authority, production/scientific scoring, API v0.1 compatibility, numeric null-score rules, or authority to use a caller-supplied trusted PDF source.
- Fabricating real-model results, treating heuristic guesses as model output, marking unverified runtime locks trusted, or claiming a runnable PDF inference MVP based only on mock tests.

## Acceptance / stop conditions
Tests should cover authentic worker authority being required and failure-closed when unverified; redacted-only one-target-independent model context; immutable deterministic run/attempt IDs; retries/ambiguous outcomes; validated model/version/digest controls; project/target/response provenance; refusal/error/timeouts; inert read-only GET/reconnect; escaped text rendering and UNKNOWN/NONE/null scores; no mock/heuristic substitution for genuine inference. Record NOT RUN for unavailable real-acceptance cases.

Stop and report `AMENDMENT_REQUIRED` if any extra source/test file, dependency install, schema/API contract change, runtime operation, scientific-method change, or unsafe data use is necessary. Do not force push. Before handoff recheck current main and document conflicts.

## Next receiver
Lead retrieves published implementation and handoff, then assigns independent exact-SHA QA/security and Research review. A separate owner decision is required for merge, and runtime/model qualification remains blocked by original resource/security gates until separately authorized.
