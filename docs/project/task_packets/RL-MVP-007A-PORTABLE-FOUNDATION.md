# RL-MVP-007A — Portable local application foundation (planning packet)

**Status: OWNER-APPROVED FOR PACKET PUBLICATION ONLY; IMPLEMENTATION NOT AUTHORIZED.** Owner planning decision: 2026-10-11. Lead planning epoch E0044. Baseline main at drafting: `33dc165956568d90480d33afceeb910e2cf14a49` / E0043. Recheck live HEAD, AGENTS.md, CURRENT_STATE.md, DECISIONS.md and AGENT_HANDOFF.md before future approval or writes. This packet is a proposed execution boundary for subsequent *separate* implementation authorization, not an instruction to run code, install dependencies, migrate a live database or deploy.

## Objective and delivery boundary

Build the 007A internal foundation for a **portable, local, loopback-only** Redaction Lab web application initially verified on **macOS Apple Silicon**. Another compatible computer must eventually be able to install and run its own independent backend, frontend and data without access to the original author's MacBook. Windows and Linux remain planned but unclaimed until clean-device verified. Local/synthetic-only for this stage; no real-model operation, private/restricted research PDFs, public hosting or additional expenditure authorized.

Task 7 sequence remains 007A (foundation) -> 007B (API/orchestration) -> 007C (UI) -> 007P (reproducible packaging/launcher) -> 007D (recipient-machine acceptance). 007A must be path-independent from its first tests; 007P cannot retroactively cure Mac-specific paths.

## Confirmed planning defaults approved by owner

- PDF intake bound: **25 MiB per file** (use explicit byte comparison, 25 * 1024 * 1024); at most **100 pages** per PDF; pair may contain two files (maximum 50 MiB combined).
- At most **one concurrent document-processing job** per local application instance; **60 seconds** processing time budget per PDF, with enforceable termination of an isolated parsing process, not only a cooperative Python timer. Resource and decompression limits must be tested; no assertion that every 100-page PDF is supported.
- Listen on **127.0.0.1 only** when any later API starts; no remote/public binding, public identity provider or reverse proxy.
- Keep successfully uploaded PDFs and immutable evidence until an explicitly approved deletion operation. No general deletion endpoint in 007A. Clean incomplete upload temporaries after **24 h**, without deleting a committed/referenced artifact. Operational logs have **seven-day** retention and contain no PDF content, extracted text, prompts, reference text, predictions, tokens, secrets or identifying filenames.
- Before any schema migration on a non-disposable database, take and verify a recoverable backup; never rewrite Task 4/6 immutable rows. No migration on a real user database under this packet-publication approval.
- Strictly local, synthetic or otherwise explicitly approved non-private test material only. DEC-022 byte-pinned registered synthetic reference pairing is the sole currently software-trusted pair; arbitrary uploaded references are untrusted/NOT_SCOREABLE, with null numeric scores.

## Minimum five-table schema direction

Create only five **new application tables**, separate from existing Task 4 `canonical_sources`, `jobs`, `attempts`, `run_configs` and Task 6 evidence/summary tables:

1. `documents`: opaque document ID, one local owner/project namespace, redacted document designation, created time and lifecycle state. Never use caller-supplied project ID as authentication.
2. `document_versions`: immutable version identity, owning document, role (redacted/reference), logical opaque artifact key, original byte SHA-256 and byte size, format/page/processing state; version-binding constraints and unique immutable digests. Reference versions do not confer truth.
3. `document_pairs`: project-scoped exact redacted/reference version relation (reference optional) and processing/mapping status. This association is not itself evidence of DEC-022 trust and must never be used as a substitute for byte-derived authoritative Task 3 reference validation.
4. `application_jobs`: one durable document ingestion/processing job per accepted command, idempotent input/version scope, status, safe diagnostics/retry policy and restart/recovery timestamps; explicit terminal UNSUPPORTED/NO_REDACTIONS/FAILED/READY and in-progress state. This is *not* a Task 4 prediction job; no prediction enqueue or inference in 007A.
5. `schema_migrations`: applied migration version, checksum, timestamp; additive and transactional, with legacy Task 4/6 table detection and no reinterpretation of existing records.

No `project_members`, `projects`, `artifact_metadata`, `application_job_events`, `idempotency_records` table in the initial packet absent a demonstrated correctness need. Logical artifact metadata belongs in document_versions; a carefully defined unique job request digest can support ingestion idempotency within application_jobs. If tests reveal legitimate need for more schema, STOP for explicit owner amendment rather than stretching these five tables.

The single-local-owner trust boundary must be explicit and loopback-limited. Loopback is not authentication: cross-origin and CSRF/security threats are not solved by a project string. No public API is provided by 007A; 007B must design session/origin/authorization before exposing mutating endpoints. Application data stored outside repo/web root at platform-resolved paths, not inside source checkout or at developer-specific absolute paths.

## Proposed exact future implementation file scope — subject to separate owner implementation approval

Create only:
- `src/redaction_lab/application/__init__.py`
- `src/redaction_lab/application/config.py`
- `src/redaction_lab/application/paths.py`
- `src/redaction_lab/application/artifact_store.py`
- `src/redaction_lab/application/application_store.py`
- `src/redaction_lab/application/upload_service.py`
- `src/redaction_lab/application/document_worker.py`
- `src/redaction_lab/application/migration.py`
- `src/redaction_lab/application/migrations/0001.sql`
- `tests/application/test_paths.py`
- `tests/application/test_artifact_store.py`
- `tests/application/test_application_store.py`
- `tests/application/test_upload_service.py`
- `tests/application/test_document_worker.py`
- `tests/application/test_migrations.py`
- one unique Backend task handoff `docs/project/handoffs/RL-MVP-007A-backend-<UTC>-<SHA>.md`

No wildcard paths. No changes to `pyproject.toml` or new third-party dependencies initially; existing Python >=3.11, pdfplumber and existing detector/source interfaces should be reused. Any required dependency, init-module, schema, API or worker changes beyond this list require a scope amendment.

## Existing authoritative interfaces to reuse and protect

- `derive_prediction_source(pdf_bytes, *, project_id)` in prediction_source.py: Task 4 redacted-input canonical source boundary. Its supported PDF profile is narrower than arbitrary upload acceptance; unsupported input receives explicit status, not guessed redactions.
- `RunStore.ingest_redacted_pdf(pdf_bytes, *, project_id)` and immutable `canonical_sources`: do not construct forged source identity or import caller hash as authority. Document ingestion may invoke this only after validated processing; do not enqueue or dispatch any Task 4 prediction.
- `RunStore.source`, `RunStore.resolve_attempt`: existing trusted source and attempt authority remain unchanged.
- `EvaluationStore` and immutable evaluation/summary membership are not modified/exposed in 007A.
- `pdf_detector.detect_targets`, Task 1–3 canonical/reference procedures and DEC-022 registry remain the only approved extraction/trust behavior. Unsupported raster/scanned/encrypted/rotated/ambiguous PDFs must fail closed without OCR or interpretation upgrades.
- Persistent artifacts must preserve exact byte hashes and distinguish original redacted/reference bytes; reference blob keys and access channels must be outside any future prediction worker interface. Never store reference bytes in a PredictionManifest.

## Persistence, file security and recovery

Use bounded streaming to a private temporary file, verify exact byte size, format signature plus parser validation in isolated worker, calculate SHA-256 over real bytes and publish by atomic rename to content-addressed opaque storage outside repository and web root. Never trust filenames, paths, MIME headers or supplied digest as authority. Defend against symlink traversal, replaced files, hash collisions, zip/polyglot and oversized/decompression-bomb behavior. Enforce restrictive permissions and no logs of content. Metadata and filesystem writes are not naturally atomic; detect/reconcile orphan temporary/completed blobs after crashes without deleting referenced content. Idempotent retries must not create duplicate document/jobs.

Existing Task-4/6 SQLite rows stay untouched by migrations. New tables and indexes added in transactional migration; checksum/reopen checks and a pre-migration recoverable backup gate for any non-disposable DB. Crash interruption and startup recovery must be deterministic; do not silently reprocess a completed immutable source or convert an indeterminate Task 4 job into a new dispatch. No PDF parser given unrestricted filesystem/network privileges; if safe process/resource isolation unavailable in minimal scope, STOP and propose explicit safeguard amendment.

## Test-first acceptance required for any subsequent authorized implementation

- Clean macOS Apple Silicon user-profile / temporary `REDACTION_LAB_HOME` initialization works without owner's paths or existing virtual environment; never writes artifacts into repo or web root.
- PDF 25 MiB/100-page boundary: exact cutoff, one-over, pair limit, malformed/encrypted/unsupported/raster-only; parse worker time/resource/concurrency limits and rejection states; no unsupported targets fabricated.
- Valid redacted PDF ingestion produces authoritative immutable Task 4 canonical source with correct project/hash/version; unregistered reference can be uploaded/viewed later but remains NOT_SCOREABLE and never influences prediction manifest/prompt.
- Redacted/reference bytes and roles correctly separated; artifact digest checked on all reads; changed bytes, symlink/path traversal and wrong logical key fail.
- Duplicate/replayed requests idempotent; interrupted temp writes, orphan blobs and metadata crash consistency; one concurrent job; clean shutdown/restart/reopen.
- Fresh and legacy Task 4/6 DB migration/reopen, backup/rollback and immutable-row byte-equivalence; schema checksum tampering rejected.
- No public API/authentication claim in 007A; local loopback-only future binding and cross-origin concern explicitly tracked for 007B.
- Full Task 1–6 pytest regressions, focused tests, compileall, dependency integrity, diff check and exact changed-file audit. No inference, model download, provider call, private data or paid operation.
- Document packaging assumptions clearly recorded; eventual independent 007P/007D second-machine install/launch required before claiming portability complete.

## Open implementation gates, blockers and rollback

Owner has approved planning defaults and **publication of this packet only**, not execution. No Task 7A code, dependency installation, model inference, paid call, migration, production deployment or Task 7B/C/P/D implementation is authorized. D07 security/operations production approval and D03–D06 scoring/methodology remain outstanding.

Before implementation approval, resolve whether the 60-second processing timeout can be enforced using the allowed standard library on the proposed macOS-first isolation target, whether the selected path/schema boundaries suffice under cross-process concurrency, and verify 007A's no-new-dependency feasibility. If not, propose a scope amendment, not a silent workaround. Local-owner/session security and recipient distribution require later explicit 007B/007P approvals.

When implementation eventually authorized, Backend works on a unique isolated branch with one unique handoff; fresh QA/security and Research reviews on exact code are required. Lead integrates only after separate owner merge approval. Rollback is additive code revert and tested application-table recovery; never delete/edit existing Task 4/6 immutable evidence. Keep private research materials and secrets outside public GitHub.
