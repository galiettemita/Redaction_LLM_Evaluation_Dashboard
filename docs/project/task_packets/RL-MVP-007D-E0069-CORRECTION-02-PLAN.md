# RL-MVP-007D — E0069 Correction 02 planning packet: macOS version execution and lifetime-FD cleanup

**State:** OWNER-APPROVED FOR PACKET PREPARATION/PUBLICATION ONLY. **IMPLEMENTATION NOT AUTHORIZED BY THIS PACKET.**  
**Date:** 2026-10-29; **coordination epoch:** E0069.  
**Baseline main at planning:** `dfaf9ed0a27cde2fc7d64f2789f5ac7e826da0c4` / E0068. Refresh current HEAD and check holds before subsequent work.  
**Candidate exact SHA under review:** `f244d1337e51dd188cd2253f3845c5a3d243e144`; published Backend head `e109bd386367b68c962d3ff62b157be6488ff604` on `codex/rl-mvp-007d-emergency-real-inference`.
**QA evidence:** Independent QA `CHANGES_REQUESTED` at `0f89572278ba23894bcab0bd196c205d69969a82`, handoff `docs/project/handoffs/RL-MVP-007D-qa-20261029T150500Z-f244d13-correction01.md` on `qa/rl-mvp-007d-e0068-correction01-f244d13`. The original four E0068 fixes were found corrected at source level; these two residual defects block PASS. **Research handoff/verdict not verified; must not be inferred.**
**Authority:** Owner specifically approved preparing/publishing this narrow packet, not execution, in Lead 3 chat on 2026-10-29. E0065-E0068 requirements, API v0.2, reference-truth isolation, one-shot attempt semantics and unknown/null scoring remain binding.
**Proposed implementer:** Backend/Codex, only after separate explicit implementation approval. **Reviewers:** independent QA/security and Research. **Next receiver:** Lead/Architect.

## Objective and strict prospective change scope

Resolve two QA findings together with test-driven **code-only** changes; maintain the existing supported macOS arm64 local trust boundary, supervisor semantics and provenance. Proposed implementation changes are restricted to these existing files:

1. `src/redaction_lab/application/inference_runtime.py`
2. `tests/application/test_inference_runtime.py`

Plus one uniquely named Backend handoff under `docs/project/handoffs/` after authorized execution. No other code/test file, helper, dependency, schema, API, canonical document or bundled asset modification.

### Finding A — Important: macOS-incompatible version attestation

Current `InferenceRuntime.verified()` still uses `subprocess.run([f"/dev/fd/{executable_fd}", "--version"], ...)`, whereas published implementation evidence says that Mach-O execution via `/dev/fd` fails on macOS. It may reject legitimate pinned executables on the only supported target.

**Proposed correction:** retain an already-verified open executable file descriptor as identity anchor, verify its identity against the audited absolute pathname immediately before `--version` spawn, run the audited pathname (not `/dev/fd`), immediately compare pathname identity again and revalidate the retained descriptor/hash. Maintain existing ownership, path safety, version attestation, no-proxy/loopback, unknown-listener refusal and fail-closed conditions. Do not claim atomic FD execution. A malicious same-user replace/restore race remains a documented trust-boundary limitation accepted by QA for the currently scoped local environment, subject to future security review.

**Proposed tests:** exercise actual command construction with a harmless executable/test double where permitted, assert audited pathname and before/after retained-FD checks, rejection on mismatched inode/hash/version, cleanup on exceptions, and no remaining `/dev/fd/<fd>` Mach-O execution path for the version check. No real Ollama invocation.

### Finding B — Medium: already-exited supervisor lifetime writer leak

Current `_terminate_process(process)` returns early if `process.poll() is not None`, while `_SupervisedProcess` closes its lifetime write descriptor only from `terminate()`. Therefore child/supervisor early exit may leave an FD open in the persistent API process.

**Proposed correction:** ensure supervised lifetime-pipe close is unconditional and idempotent even for an already-exited supervisor. Preserve bounded graceful termination, kill/reap fallback, parent-death cleanup and rejection of unknown processes. Avoid closing unrelated descriptors or double-close races.

**Proposed tests:** `poll() == 0` before cleanup closes writer; repeated startup failure/child exit causes no FD growth; normal, abrupt-parent-death and noncooperative child behavior remain intact using harmless subprocesses only.

## Work sequence after future execution authorization

1. Refresh current main, candidate branch and latest QA/Research handoffs. Assess exact file scope and notify Lead if outside-path changes are required.
2. Write failing focused regression tests for both defects, then make the minimal corrections in the two authorized files.
3. Run focused and full permitted Python/mock/synthetic tests, existing Node tests if available, compilation, lock validation and diff/scope audit. Mark any missing-tool or prohibited runtime checks `NOT RUN`; do not install/download.
4. Publish corrected implementation SHA, branch HEAD and one unique Backend handoff. Independent QA/security and Research must review the exact corrected SHA. Report both completed and unrun checks.
5. Lead reconciles reviews and, if passing, requests **separate** owner merge authorization. Runtime/model qualification, actual PDF processing, genuine inference, deployment and scientific scoring remain separate gates.

## Hard stops

No software or dependency installation/download, Podman/Ollama/model execution, real PDF processing, genuine inference, money, private data, deployment, merge, new helper/module, database schema changes, Task 3/6/scientific changes, or public API contract changes. No force push or rewrite of published immutable records. The runtime storage/integrity/license gates remain intact. If implementation requires anything outside the two specified paths plus handoff, STOP for explicit owner amendment.

**Publication status:** Packet published to main; code execution and tests under this packet are NOT YET AUTHORIZED and were NOT RUN during planning.
