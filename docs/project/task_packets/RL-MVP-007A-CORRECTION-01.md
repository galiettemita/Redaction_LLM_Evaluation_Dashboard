# RL-MVP-007A Correction 01 — filesystem confinement and authoritative worker composition

**OWNER APPROVED for bounded code implementation; NOT MERGE APPROVED.** Coordination epoch E0048 (scope amendment to E0047). Baseline main ec4e6f45ec903555858a13f507e9d73a572ca2de / E0046. Rejected implementation 87ae7c5d46e72d3f61dcc325e64fab562c9fa00a; Backend published head 90a69fba46ebbb780d4fb3bb85337d6c694ea3f2 on codex/rl-mvp-007a-portable-foundation. Independent QA/security CHANGES_REQUESTED at a6ca3d35c2cb95538c24f1ce4c7a2bbaf334e673; Research scoped PASS at dc2d975b9d427921ecdc62765d684aa83b1b9cc2. This is the controlling correction packet; read E0044–E0046 packets and current AGENTS/decisions.

## Exact approved paths

Modify only:
- src/redaction_lab/application/paths.py
- src/redaction_lab/application/artifact_store.py
- src/redaction_lab/application/isolation.py
- src/redaction_lab/application/document_worker.py
- src/redaction_lab/store.py
- packaging/pdf-worker/README.md
- tests/application/test_paths.py
- tests/application/test_artifact_store.py
- tests/application/test_isolation.py
- tests/application/test_document_worker.py
- tests/test_worker.py
- tests/test_prediction_source.py
- src/redaction_lab/application/migration.py
- tests/application/test_migrations.py

Publish one unique docs/project/handoffs/RL-MVP-007A-backend-<UTC>-correction01-<SHA>.md on the existing Backend branch. No other paths, new dependencies, schema migration, Task 3/6 changes, version changes, runtime-lock activation or force push. Stop for amendment if required.

## Security correction A: filesystem confinement, full lifecycle

Reject explicitly provided or existing symlinked application-home components before normalization loses symlink evidence, including parent directories. Reject relative/empty/root/parent-traversal and unsafe ownership. Verify artifact, temporary, log and backup directories before ANY mutation. On supported macOS use directory-FD-relative, no-follow directory traversal and file operations (O_DIRECTORY, O_NOFOLLOW, dir_fd, fstat, open, mkdir, link/unlink, fsync). Keep descriptors anchored to verified inode directories; never resolve security-sensitive artifact paths anew through a potentially substituted parent. Publish immutable files without overwrite using atomic no-clobber hard-link semantics, verify existing digest/size on EEXIST, and fail closed on different filesystems. Read and recover using verified descriptors, rejecting symlinks, wrong hashes and replacement races. The Lead requires confinement across initial setup, uploads, artifact read and publication, temporary cleanup, orphan recovery and migration backups; do not fix one path and leave backup/deletion susceptible. If the existing migration/backups cannot be secured within the approved exact files, STOP and request added migration paths instead of leaving a known gap. No corrupt-row repair or unsafe fallback.

## Security correction B: production Task 4 authority

The production ingestion operation must own the full verified-runtime -> isolated worker invocation -> nonce/hash/protocol inspection -> strictly validated material -> deterministic source reconstruction -> trusted Task 4 persistence sequence. Do not accept any caller-supplied PdfWorker, runner, policy, verified result, PredictionSource, source material, source-deriver callback, digest or trusted flag as production authority. Remove source_deriver injection from RunStore public constructor; preserve existing RunStore(path), legacy ingest_redacted_pdf trusted/internal semantics and Task 4 deterministic source IDs. Test mocks belong only to a clearly NON-AUTHORITATIVE probe seam with zero ability to insert canonical_sources or mark jobs READY. Only application-owned concrete runtime configuration sourced from a pinned install-owned path may reach production; runtime_verified false must prevent job claim, runtime evidence, Task 4 record creation and processing. No Python capability/hash/Pydantic validity is proof of qualified runtime provenance. Trusted host-process compromise remains explicitly out of threat model; do not claim cryptographic provenance against arbitrary host code.

## TDD and acceptance

Write RED adversarial regressions first: symlinked home/intermediate/artifact/temp/hash prefix/leaf, initial preflight no-mutation, prefix replacement race, descriptor-anchored operations, orphan/temp cleanup and migration backup path confinement; mock worker/runner injection and RunStore callback denied, runtime lock unverified leaves job ACCEPTED and Task 4 unchanged, forged digest insufficient, default Task 4 source identities unchanged, no prediction dispatch. Continue existing artifact, crash/recovery, migration/reopen, immutable Task 6 and DEC-022 tests. Run focused path/artifact/authority suites, application/security suites, full repository pytest, compileall, dependency + offline lock checks, script fail-closed, git diff --check and exact-path audit. Record actual test commands/results, not-run checks, known limitations and final implementation SHA/branch head in one unique Backend handoff. Fresh independent QA/security and Research exact-SHA review mandatory.

## Explicit prohibitions and stop conditions

No Podman installation/execution, OCI image build/download, VM provisioning, private/restricted PDFs, external models/inference/provider APIs, spending, deployment, merge, Task 7B/C/P/D or scientific-method approval. No new permissions implied. Stop if supported macOS cannot guarantee no-follow descriptor-relative operations, if production authority requires a new file/entry point or DB migration, if legacy Task 4 ID contracts change, if backup/cleanup gaps require out-of-scope files, or any required regression fails. Owner approval is required to merge after independent review.

## E0048 owner-approved two-file security amendment

The owner explicitly expands Correction 01 by exactly `src/redaction_lab/application/migration.py` and `tests/application/test_migrations.py`. All other E0047 restrictions remain binding. The migration backup pathway must use securely opened directory descriptors, deny symlink traversal and directory-parent replacement races, avoid unsafe pathname-based SQLite opening/creation/deletion, and safely preserve/verify backups. Cover the entire lifecycle: initialization, backup creation, integrity checking, failure cleanup and reopen. Directory-relative backups must not alter existing Task 4/6 immutable evidence. Write adversarial RED-before-GREEN tests for symlinked backup root/ancestor, symlinked or replaced SQLite database pathname, swapped parent, cleanup after failed integrity check, backup replacement collision, and rollback integrity; add tests for non-disposable backup preservation and normal legacy database migration/reopen. If SQLite connection semantics cannot be made safe with the supported stdlib, stop for a scope amendment rather than relying on check-then-use validation. Re-run focused/full suites and exact fourteen-path scope audit. No other approvals are granted.
