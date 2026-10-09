"""Durable SQLite state for immutable, trusted-source prediction jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from os import PathLike
from pathlib import Path
import sqlite3

from redaction_lab.adapters.base import build_prediction_manifest
from redaction_lab.contracts import (
    AttemptStatus,
    CanonicalRedactedDocument,
    DocumentRole,
    ModelAttempt,
    PredictionManifest,
    RedactionTarget,
    RunDefinition,
)
from redaction_lab.prediction_source import (
    PredictionSource,
    derive_prediction_source,
    validate_prediction_source,
)


TRUST_VERSION = "canonical-source-binding-v1"


@dataclass(frozen=True)
class StoredJob:
    job_id: str
    state: str
    attempt_policy: str
    manifest: PredictionManifest
    attempt_id: str | None
    request_hash: str | None
    model_config_id: str | None
    source_id: str | None = None


class RunStore:
    """Transactional internal store with conservative no-retry semantics.

    ``ingest_redacted_pdf`` is for an authenticated trusted service/test harness.
    This component does not expose or claim an arbitrary-upload authorization API.
    """

    def __init__(self, path: str | PathLike[str]) -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @staticmethod
    def _add_column_if_missing(
        connection: sqlite3.Connection, table: str, column: str, definition: str
    ) -> None:
        names = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in names:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS canonical_sources (
                    source_id TEXT PRIMARY KEY,
                    source_version TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role = 'REDACTED'),
                    redacted_document_version_id TEXT NOT NULL,
                    detector_version TEXT NOT NULL,
                    canonicalizer_version TEXT NOT NULL,
                    canonical_document_version_id TEXT NOT NULL,
                    canonical_hash TEXT NOT NULL,
                    canonical_json TEXT NOT NULL,
                    targets_json TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    UNIQUE (project_id, source_sha256, detector_version, canonicalizer_version)
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    scope_key TEXT NOT NULL UNIQUE,
                    project_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    target_version TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    attempt_policy TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    source_id TEXT REFERENCES canonical_sources(source_id),
                    run_json TEXT,
                    trust_version TEXT,
                    state TEXT NOT NULL CHECK (state IN ('PENDING', 'IN_DOUBT', 'COMPLETE')),
                    attempt_id TEXT,
                    request_hash TEXT,
                    model_config_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL UNIQUE REFERENCES jobs(job_id),
                    attempt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run_configs (
                    project_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    model_config_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (project_id, run_id, model_id)
                );
                """
            )
            self._add_column_if_missing(connection, "jobs", "source_id", "TEXT")
            self._add_column_if_missing(connection, "jobs", "run_json", "TEXT")
            self._add_column_if_missing(connection, "jobs", "trust_version", "TEXT")
            connection.executescript(
                """
                BEGIN IMMEDIATE;
                DROP TRIGGER IF EXISTS attempts_no_update;
                DROP TRIGGER IF EXISTS attempts_no_delete;
                DROP TRIGGER IF EXISTS jobs_intent_no_update;
                DROP TRIGGER IF EXISTS jobs_trusted_insert;
                DROP TRIGGER IF EXISTS jobs_state_guard;
                DROP TRIGGER IF EXISTS jobs_no_delete;
                DROP TRIGGER IF EXISTS canonical_sources_no_update;
                DROP TRIGGER IF EXISTS canonical_sources_no_delete;
                DROP TRIGGER IF EXISTS run_configs_no_update;
                DROP TRIGGER IF EXISTS run_configs_no_delete;

                CREATE TRIGGER attempts_no_update BEFORE UPDATE ON attempts
                BEGIN SELECT RAISE(ABORT, 'attempts are immutable'); END;
                CREATE TRIGGER attempts_no_delete BEFORE DELETE ON attempts
                BEGIN SELECT RAISE(ABORT, 'attempts are immutable'); END;
                CREATE TRIGGER canonical_sources_no_update BEFORE UPDATE ON canonical_sources
                BEGIN SELECT RAISE(ABORT, 'canonical sources are immutable'); END;
                CREATE TRIGGER canonical_sources_no_delete BEFORE DELETE ON canonical_sources
                BEGIN SELECT RAISE(ABORT, 'canonical sources are immutable'); END;
                CREATE TRIGGER run_configs_no_update BEFORE UPDATE ON run_configs
                BEGIN SELECT RAISE(ABORT, 'run configuration is immutable'); END;
                CREATE TRIGGER run_configs_no_delete BEFORE DELETE ON run_configs
                BEGIN SELECT RAISE(ABORT, 'run configuration is immutable'); END;
                CREATE TRIGGER jobs_intent_no_update
                BEFORE UPDATE OF scope_key, project_id, run_id, target_id,
                    target_version, model_id, attempt_policy, manifest_json,
                    source_id, run_json, trust_version, created_at ON jobs
                BEGIN SELECT RAISE(ABORT, 'job intent is immutable'); END;
                CREATE TRIGGER jobs_trusted_insert BEFORE INSERT ON jobs
                WHEN NEW.trust_version IS NOT 'canonical-source-binding-v1'
                  OR NEW.source_id IS NULL
                  OR NEW.run_json IS NULL
                  OR NOT EXISTS (
                      SELECT 1 FROM canonical_sources
                      WHERE source_id = NEW.source_id
                        AND project_id = NEW.project_id
                        AND role = 'REDACTED'
                  )
                BEGIN SELECT RAISE(ABORT, 'job requires trusted source binding'); END;
                CREATE TRIGGER jobs_state_guard
                BEFORE UPDATE OF state, attempt_id, request_hash, model_config_id ON jobs
                WHEN NOT (
                    (OLD.state = 'PENDING' AND NEW.state = 'IN_DOUBT'
                     AND OLD.attempt_id IS NULL AND OLD.request_hash IS NULL
                     AND OLD.model_config_id IS NULL AND NEW.attempt_id IS NOT NULL
                     AND NEW.request_hash IS NOT NULL AND NEW.model_config_id IS NOT NULL)
                    OR
                    (OLD.state = 'IN_DOUBT' AND NEW.state IN ('IN_DOUBT', 'COMPLETE')
                     AND NEW.attempt_id = OLD.attempt_id
                     AND NEW.request_hash = OLD.request_hash
                     AND NEW.model_config_id = OLD.model_config_id)
                )
                BEGIN SELECT RAISE(ABORT, 'invalid job state transition'); END;
                CREATE TRIGGER jobs_no_delete BEFORE DELETE ON jobs
                BEGIN SELECT RAISE(ABORT, 'job intent is immutable'); END;
                COMMIT;
                """
            )

    @staticmethod
    def _scope_key(manifest: PredictionManifest, attempt_policy: str) -> str:
        values = (
            manifest.project_id,
            manifest.run_id,
            manifest.target_id,
            manifest.target_version,
            manifest.model_id,
            attempt_policy,
        )
        return sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _source_from_row(row: sqlite3.Row) -> PredictionSource:
        canonical = CanonicalRedactedDocument.model_validate_json(row["canonical_json"])
        source = PredictionSource(
            source_id=row["source_id"],
            source_version=row["source_version"],
            project_id=row["project_id"],
            source_sha256=row["source_sha256"],
            role=DocumentRole(row["role"]),
            redacted_document_version_id=row["redacted_document_version_id"],
            detector_version=row["detector_version"],
            canonicalizer_version=row["canonicalizer_version"],
            canonical_document=canonical,
            targets=tuple(
                RedactionTarget.model_validate(item)
                for item in json.loads(row["targets_json"])
            ),
            provenance=row["provenance"],
        )
        validate_prediction_source(source)
        if (
            row["canonical_document_version_id"] != canonical.canonical_document_version_id
            or row["canonical_hash"] != canonical.canonical_hash
        ):
            raise ValueError("stored prediction source canonical identity failure")
        return source

    def ingest_redacted_pdf(self, pdf_bytes: bytes, *, project_id: str) -> str:
        """Persist a byte-derived source for a pre-authenticated internal caller."""

        source = derive_prediction_source(pdf_bytes, project_id=project_id)
        canonical_json = source.canonical_document.model_dump_json()
        targets_json = json.dumps(
            [target.model_dump(mode="json") for target in source.targets],
            sort_keys=True,
            separators=(",", ":"),
        )
        values = (
            source.source_id,
            source.source_version,
            source.project_id,
            source.source_sha256,
            source.role.value,
            source.redacted_document_version_id,
            source.detector_version,
            source.canonicalizer_version,
            source.canonical_document.canonical_document_version_id,
            source.canonical_document.canonical_hash,
            canonical_json,
            targets_json,
            datetime.now(UTC).isoformat(),
            source.provenance,
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT OR IGNORE INTO canonical_sources (
                    source_id, source_version, project_id, source_sha256, role,
                    redacted_document_version_id, detector_version,
                    canonicalizer_version, canonical_document_version_id,
                    canonical_hash, canonical_json, targets_json, ingested_at, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values,
            )
            row = connection.execute(
                "SELECT * FROM canonical_sources WHERE source_id = ?", (source.source_id,)
            ).fetchone()
            if row is None or self._source_from_row(row) != source:
                raise ValueError("source ID already identifies different content")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return source.source_id

    def source(self, source_id: str) -> PredictionSource:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM canonical_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
        if row is None:
            raise KeyError(source_id)
        return self._source_from_row(row)

    @staticmethod
    def _validate_run(source: PredictionSource, run: RunDefinition) -> None:
        canonical = source.canonical_document
        if (
            source.role is not DocumentRole.REDACTED
            or run.project_id != source.project_id
            or run.canonical_document_version_id != canonical.canonical_document_version_id
            or run.canonical_document_hash != canonical.canonical_hash
            or run.target_versions != source.target_versions
            or run.attempt_policy != "one-frozen-attempt"
        ):
            raise ValueError("run does not match trusted prediction source")

    def enqueue(self, source_id: str, target_id: str, run: RunDefinition) -> str:
        source = self.source(source_id)
        self._validate_run(source, run)
        target_ids = tuple(target.target_id for target in source.targets)
        if target_id not in target_ids:
            raise ValueError("target is not registered in prediction source")
        manifest = build_prediction_manifest(source.canonical_document, target_id, run)
        if manifest.target_version != source.targets[target_ids.index(target_id)].target_version:
            raise ValueError("target version does not match prediction source")

        scope_key = self._scope_key(manifest, run.attempt_policy)
        job_id = f"job-{scope_key}"
        manifest_json = manifest.model_dump_json()
        run_json = run.model_dump_json()
        now = datetime.now(UTC).isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing_run = connection.execute(
                """SELECT source_id, run_json FROM jobs
                   WHERE project_id = ? AND run_id = ? AND trust_version = ? LIMIT 1""",
                (run.project_id, run.run_id, TRUST_VERSION),
            ).fetchone()
            if existing_run is not None and (
                existing_run["source_id"] != source_id or existing_run["run_json"] != run_json
            ):
                raise ValueError("run identity is already frozen to different intent")
            connection.execute(
                """INSERT OR IGNORE INTO jobs (
                    job_id, scope_key, project_id, run_id, target_id, target_version,
                    model_id, attempt_policy, manifest_json, source_id, run_json,
                    trust_version, state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)""",
                (
                    job_id, scope_key, manifest.project_id, manifest.run_id,
                    manifest.target_id, manifest.target_version, manifest.model_id,
                    run.attempt_policy, manifest_json, source_id, run_json,
                    TRUST_VERSION, now, now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM jobs WHERE scope_key = ?", (scope_key,)
            ).fetchone()
            if row is None or (
                row["manifest_json"] != manifest_json
                or row["source_id"] != source_id
                or row["run_json"] != run_json
                or row["trust_version"] != TRUST_VERSION
            ):
                raise ValueError("scoped job already has different frozen intent")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return job_id

    @staticmethod
    def _stored_job(row: sqlite3.Row) -> StoredJob:
        return StoredJob(
            job_id=row["job_id"],
            state=row["state"],
            attempt_policy=row["attempt_policy"],
            manifest=PredictionManifest.model_validate_json(row["manifest_json"]),
            attempt_id=row["attempt_id"],
            request_hash=row["request_hash"],
            model_config_id=row["model_config_id"],
            source_id=row["source_id"],
        )

    def job(self, job_id: str) -> StoredJob:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._stored_job(row)

    def next_pending(self) -> StoredJob | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT jobs.* FROM jobs
                   JOIN canonical_sources ON canonical_sources.source_id = jobs.source_id
                   WHERE jobs.state = 'PENDING' AND jobs.trust_version = ?
                     AND jobs.run_json IS NOT NULL
                   ORDER BY jobs.created_at, jobs.job_id LIMIT 1""",
                (TRUST_VERSION,),
            ).fetchone()
            if row is not None:
                self._validate_bound_job(connection, row)
        return self._stored_job(row) if row is not None else None

    def _validate_bound_job(
        self, connection: sqlite3.Connection, row: sqlite3.Row
    ) -> tuple[PredictionManifest, RunDefinition]:
        if row["trust_version"] != TRUST_VERSION or row["source_id"] is None or row["run_json"] is None:
            raise ValueError("job lacks trusted prediction source binding")
        source_row = connection.execute(
            "SELECT * FROM canonical_sources WHERE source_id = ?", (row["source_id"],)
        ).fetchone()
        if source_row is None:
            raise ValueError("job prediction source is missing")
        source = self._source_from_row(source_row)
        run = RunDefinition.model_validate_json(row["run_json"])
        self._validate_run(source, run)
        expected = build_prediction_manifest(source.canonical_document, row["target_id"], run)
        stored = PredictionManifest.model_validate_json(row["manifest_json"])
        if expected != stored or (
            row["project_id"], row["run_id"], row["target_id"], row["target_version"],
            row["model_id"], row["attempt_policy"],
        ) != (
            expected.project_id, expected.run_id, expected.target_id,
            expected.target_version, expected.model_id, run.attempt_policy,
        ):
            raise ValueError("job intent does not match trusted prediction source")
        return stored, run

    def claim(self, job_id: str, *, request_hash: str, model_config_id: str) -> str | None:
        attempt_seed = json.dumps(
            (job_id, request_hash, model_config_id), separators=(",", ":")
        ).encode()
        attempt_id = f"attempt-{sha256(attempt_seed).hexdigest()}"
        now = datetime.now(UTC).isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            if row["state"] != "PENDING":
                connection.commit()
                return None
            manifest, _ = self._validate_bound_job(connection, row)
            connection.execute(
                """INSERT OR IGNORE INTO run_configs (
                    project_id, run_id, model_id, model_config_id, created_at
                ) VALUES (?, ?, ?, ?, ?)""",
                (manifest.project_id, manifest.run_id, manifest.model_id, model_config_id, now),
            )
            config = connection.execute(
                """SELECT model_config_id FROM run_configs
                   WHERE project_id = ? AND run_id = ? AND model_id = ?""",
                (manifest.project_id, manifest.run_id, manifest.model_id),
            ).fetchone()
            if config is None or config["model_config_id"] != model_config_id:
                raise ValueError("run is frozen to a different model configuration")
            cursor = connection.execute(
                """UPDATE jobs SET state = 'IN_DOUBT', attempt_id = ?, request_hash = ?,
                   model_config_id = ?, updated_at = ?
                   WHERE job_id = ? AND state = 'PENDING'""",
                (attempt_id, request_hash, model_config_id, now, job_id),
            )
            connection.commit()
            return attempt_id if cursor.rowcount == 1 else None
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def complete(self, job_id: str, attempt: ModelAttempt) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            manifest, _ = self._validate_bound_job(connection, row)
            expected = (
                row["attempt_id"], manifest.project_id, manifest.run_id,
                manifest.target_id, manifest.target_version, manifest.model_id,
                row["model_config_id"], row["request_hash"],
            )
            actual = (
                attempt.attempt_id, attempt.project_id, attempt.run_id,
                attempt.target_id, attempt.target_version, attempt.model_id,
                attempt.model_config_id, attempt.request_hash,
            )
            if row["state"] != "IN_DOUBT" or expected != actual:
                raise ValueError("attempt provenance does not match durable intent")
            if (
                attempt.status in (AttemptStatus.SUCCEEDED, AttemptStatus.REFUSED)
                and attempt.provider_model_id != attempt.model_id
            ):
                raise ValueError("provider model identity is not verified")
            connection.execute(
                "INSERT INTO attempts (attempt_id, job_id, attempt_json, created_at) VALUES (?, ?, ?, ?)",
                (attempt.attempt_id, job_id, attempt.model_dump_json(), datetime.now(UTC).isoformat()),
            )
            next_state = "IN_DOUBT" if attempt.status is AttemptStatus.TIMEOUT else "COMPLETE"
            connection.execute(
                "UPDATE jobs SET state = ?, updated_at = ? WHERE job_id = ?",
                (next_state, datetime.now(UTC).isoformat(), job_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def attempts(self) -> tuple[ModelAttempt, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT attempt_json FROM attempts ORDER BY created_at, attempt_id"
            ).fetchall()
        return tuple(ModelAttempt.model_validate_json(row["attempt_json"]) for row in rows)
