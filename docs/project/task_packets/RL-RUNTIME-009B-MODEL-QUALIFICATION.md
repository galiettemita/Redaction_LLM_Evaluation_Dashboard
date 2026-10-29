# RL-RUNTIME-009B — Local Ollama/model qualification

Status: ACTIVE under RL-OPS-002 standing engineering authority. Decision epoch E0071.
Baseline: `f85204fc142a5a4c2cece30f401b3566d8f45a25`.
Accountable role: Backend / Infrastructure; Engineering Lead integrates after independent exact-candidate review.

## Objective

Qualify one zero-cost application-owned local Ollama runtime and the already frozen `qwen2.5:1.5b-instruct-q4_K_M` operational canary on this Apple Silicon Mac using exact official sources, hashes, licenses and synthetic-only prompts. Preserve literal-loopback ownership, parent-death process supervision, exact model identity before mutation, immutable experiment records, bounded outcomes, null scores and every scientific/data/deployment gate.

This task does not approve a scientific model roster, benchmark, accuracy claim or private/lab-data use.

## Preflight and phased authority

Phase 1 is read-only apart from this task record and its handoff: recheck hardware/disk, inspect existing state, resolve exact official Ollama/model sources, versions, manifests, file sizes, hashes/signatures, licenses, advisories, architecture support, SBOM inputs and estimated peak storage. No executable or model blob runs during Phase 1.

Phase 2 may proceed only if all acquired artifacts are free, officially sourced, immutable/hash-verifiable, license-compatible and leave at least 8 GiB host free space after the complete runtime/model plus rollback inputs are staged. It may install only beneath the application root, run only literal-loopback Ollama under the existing application supervisor, and perform only synthetic prompts. Stop for a credential/password, paid term, missing integrity/license evidence, unsupported host, inadequate reserve, unresolved Critical risk, pre-existing listener, model identity mismatch or unexpected external exposure.

## Authorized paths and actions

Source/package changes are limited to:

- `packaging/model-runtime/runtime.lock`
- `packaging/local/manifest.json`
- `packaging/local/preflight.sh`
- `packaging/local/README.md`
- `src/redaction_lab/application/inference_runtime.py`
- `src/redaction_lab/application/prediction_service.py`
- `src/redaction_lab/adapters/ollama.py`
- `tests/application/test_inference_runtime.py`
- `tests/application/test_prediction_service.py`
- `tests/test_adapter.py`
- `tests/packaging/test_local_preflight.py`

New provenance, integrity, SBOM and license/source artifacts may be added only under `packaging/model-runtime/`. One unique `docs/project/handoffs/RL-RUNTIME-009B-backend-<UTC>-<SHA>.md` is authorized. This task record may be updated with observed evidence.

Host actions are limited to task-specific temporary downloads for verification; application-owned portable Ollama payload/model-store acquisition; literal-loopback supervised runtime start/stop; synthetic-only inference and failure canaries; and exact cleanup of task-created temporary state. No schema, API, PDF-worker, frontend, scoring, evaluator or shared canonical-state change is in scope.

## TDD and acceptance evidence

1. Unverified/missing/substituted locks, executable, model inventory, manifest digest, tag or API identity fail before durable run/intent mutation.
2. Runtime paths resolve beneath the application root and reject symlinks, aliases, unsafe ownership/modes and before/after identity changes.
3. The application owns the literal-loopback process lifecycle; parent/lifetime-pipe death, timeout, malformed/oversized/error outcomes and idempotent cleanup are adversarially covered.
4. Exact Ollama and model source/hash/license inventories and a machine-readable SBOM are published; no credentials, raw private prompts or model output are committed.
5. Actual synthetic inference verifies exact model identity, immutable provenance, deterministic run identity, no reference input, repeat-dispatch behavior and bounded resource measurements without asserting semantic accuracy.
6. Focused/full Python and Node regressions, compilation, lock/file-scope/diff checks and independent exact-candidate security review pass before integration.

## Stop conditions and exclusions

Stop or retain `runtime_verified: false` for inadequate reserve; missing/changed source, digest, signature or license; privileged installation; pre-existing/unowned listener; runtime/model identity mismatch; parent-death/cleanup failure; required regression failure; or need for an out-of-scope contract/schema change.

No private/restricted PDF or reference data, paid provider, commercial credential, benchmark/scientific validation, public deployment/distribution, clean-recipient claim, force push or destructive cleanup is authorized. Qualification on this host is not institutional permission or a release claim.

## Qualification evidence (2026-10-29)

- Official Ollama `v0.40.13` Darwin archive: 186,689,993 bytes, SHA-256 `bae29252232b9e1358cf5801a7d65a07442af18fb5467cb68c7fc3711f59c511`; GitHub-verified release commit `04088e7c9d41cba5d33bafbf788d87a465c79d5b`; valid hardened Developer ID signature from team `3MU9H2V9Y9`; MIT license.
- Exact `qwen2.5:1.5b-instruct-q4_K_M` manifest SHA-256 `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`; 986,048,512-byte model blob SHA-256 `183715c435899236895da3869489cc30ac241476b4971a20285b1a462818a5b4`; Apache-2.0 license.
- Application-owned installed runtime/model footprint: 1,561,744 KiB. Free space after installation: 13,649,200 KiB, above the required 8 GiB reserve. Existing PDF-worker state remained intact.
- Two repeated synthetic dispatches through the supervised application path succeeded with identical deterministic request hashes, exact provider identity and bounded token usage. A separate resource canary observed approximately 1.96 GiB model-runner RSS; its response was safely classified `MALFORMED` rather than persisted as a success.
- Real Ollama parent-death canary reaped both supervisor and runtime and removed the loopback listener within the observed 100 ms polling bound. No listener or model process remained after cleanup.
- Ollama 0.40.13 emits a deterministic 4,143-byte GGUF metadata cache on first tag inspection. It remained byte- and mtime-stable across restart and is included in the exact seven-file model-store lock; arbitrary extra files remain rejected.
- This is reference-host, synthetic-only operational qualification. The package remains non-bundled, recipient acceptance remains not run, and no scientific roster, accuracy, private-data, scoring or distribution approval is implied.

## Independent-review correction

Independent review of exact candidate `3ab23252f948bd86ee0edefcbebf2a8d3491c031` returned `CHANGES_REQUESTED` with no Critical issue and five Important findings: incomplete helper/library attestation, silent model-context truncation risk, descendant cleanup after direct-runtime exit, pathname-based model-store rechecks, and non-wall-clock HTTP deadlines. Two Minor findings covered SBOM depth and an ambiguous inherited-review checklist item.

The grouped correction remains within this packet's authorized paths and preserves architecture. It pins all 45 regular runtime payload files and 10 approved relative symlinks; confines helper discovery to the attested runtime directory; uses descriptor-anchored recursive inventory validation with root/file identity and mode checks; isolates and reaps the whole runtime process group including TERM-resistant descendants; moves API identity and generation I/O into bounded subprocesses with hard parent-enforced deadlines; freezes a raw 32,768-token context, 1,024-token output ceiling, conservative 30,000-byte rendered-prompt limit, and explicit `truncate:false` / `shift:false`; bumps run/service/model-configuration identities; expands native-component SBOM evidence; and distinguishes inherited frontend review from the pending Task 9B correction review.

Correction verification completed with 709 Python tests, 24 Node tests, Python compilation, TypeScript typecheck/build, zero high-level audit findings, exact lock/manifest/inventory checks and truthful non-bundled preflight. A corrected live generation canary used exact model configuration `ollama-0.40.13-qwen2.5-1.5b-q4_K_M-ctx32768-out1024-raw-noshift`, preserved exact provider/manifest identity, bounded the request by a hard subprocess deadline, classified nonconforming output `MALFORMED`, and left no listener or descendant. A separate real abrupt-parent-death canary reaped supervisor/runtime and the listener within the observed 100 ms polling bound. Independent exact-SHA re-review remains required before integration.

Independent re-review of exact candidate `c8bf0584aac9e5052ac01f2fcab40ecc966c7ccf` closed the previous inventory coverage, context/truncation, descendant cleanup, hard-deadline and SBOM findings, then identified two remaining Important races: a single-read subprocess request pipe and a detached nested-directory descriptor that was not reattached to its audited parent/name before acceptance.

The second grouped correction reads the bounded request pipe through EOF, rejects JSON-escaped request bodies above the fixed 131,072-byte transport ceiling, and retains every traversed directory descriptor through a final descriptor/parent/name identity audit. Regular-file and symlink parent/name identities are likewise revalidated after hashing or target capture. Adversarial tests deliver a 28,000-character prompt byte-for-byte through the real subprocess/HTTP path and replace nested directories, regular files and symlinks during verification. A macOS cleanup edge observed during the full gate is also closed: an already-signalled process group that becomes inaccessible during the zero-signal probe no longer crashes its supervisor, while deterministic descendant reaping remains covered.

Final correction verification completed with 715 Python tests and 24 Node tests; 15 repeated direct-runtime-exit cleanup runs; Python compilation; TypeScript typecheck/build; zero npm vulnerabilities; exact 45-file/10-symlink/7-model-file installed inventory validation; lock/manifest hash equality; local preflight; and diff/file-scope checks. A final synthetic live canary preserved exact provider/model-configuration identity, returned bounded status `MALFORMED` with no persistable prediction, and left no loopback listener. Independent exact-SHA re-review of the final correction remains required before integration.
