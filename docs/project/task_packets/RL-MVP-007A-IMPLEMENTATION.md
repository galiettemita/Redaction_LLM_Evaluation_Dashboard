# RL-MVP-007A consolidated implementation authorization

Owner approved Task 7A code and test implementation only. Coordination E0046. Baseline 8376123e5d6eb01e0915a37aa8e022ccf58df16f / E0045.

The existing published E0044 foundation and E0045 PDF-isolation amendment remain binding. This packet consolidates their scope and the accepted isolated-worker interface preflight. Implementation owner: Backend/Codex; mandatory independent QA/security-focused and Research reviews before any separately authorized merge.

Permitted work: synthetic/mock tests and implementation of portable local document upload/storage, five application tables, migration, worker protocol, runtime-inspection abstraction, and the Task 4 trusted worker-derived source interface. No real Podman installation, VM/image operations, model inference, private data, spending, deployment or subsequent Task 7 stages. Runtime absence must fail closed.

Exact new application files: src/redaction_lab/application/__init__.py, config.py, paths.py, artifact_store.py, application_store.py, upload_service.py, document_worker.py, migration.py, migrations/0001.sql, isolation.py, worker_protocol.py.
Exact new tests: tests/application/test_paths.py, test_artifact_store.py, test_application_store.py, test_upload_service.py, test_document_worker.py, test_migrations.py, test_isolation.py, test_worker_protocol.py, tests/security/test_pdf_worker_container.py.
Exact new packaging files: packaging/pdf-worker/Containerfile, containers.conf, runtime.lock, README.md, .containerignore, scripts/build-pdf-worker.sh, scripts/verify-pdf-worker.sh, uv.lock, .python-version.
Exact permitted modifications: src/redaction_lab/store.py, src/redaction_lab/prediction_source.py, tests/test_worker.py, tests/test_prediction_source.py.
One unique Backend handoff under docs/project/handoffs/RL-MVP-007A-backend-<UTC>-<SHA>.md.
No other changes, new dependencies or schema tables without new owner authorization.

Task 4 retains ingest_redacted_pdf as the internal persistence entry point; the default legacy derivation remains compatible, while the new application supplies a strict isolated-worker strategy. Do not reparse arbitrary input PDF on the host or accept a caller-supplied authoritative PredictionSource. Worker observations are bounded and untrusted; host validates input byte SHA, project and role, pinned versions, nonce, permitted geometry, target ordering, markers and deterministic identifiers. Isolated runtime provenance is distinct from proof of PDF semantic correctness. Preserve reference isolation, DEC-022 truth restrictions, immutable Task 4/6 records and null scores.

Document intake is not a guarantee that every PDF is processable. Apply approved 25 MiB/file, 100-page, single-job, 60-second limits. New five tables: documents, document_versions, document_pairs, application_jobs, schema_migrations. Preserve uploaded artifacts through logical keys, safe file publication, crash recovery, transactional migrations and verified backups. Use portable local paths. Only synthetic fixtures during code implementation.

TDD: fail-closed invalid runtime/worker responses and spoofed observations, malformed or oversized files, role separation, deterministic IDs, portable paths, migration/reopen, artifact tamper/recovery, concurrency and Task 1-6 regressions. Run focused and full pytest, compilation, dependency integrity and diff/scope audit. Report exact tests run and NOT RUN. Real isolation/VM and independent recipient-device testing remain later release gates.

Stop for required files outside scope, Task 3/6 modifications, loss of Task 4 authority, any host PDF reparse for arbitrary input, missing runtime integrity, unresolved regressions or forbidden operations. Do not merge, deploy, install/download/run Podman, handle private data, call models or start Task 7B/C/P/D.
