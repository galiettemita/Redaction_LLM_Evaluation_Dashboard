"""Durable SQLite state for immutable one-shot prediction jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from os import PathLike
from pathlib import Path
import sqlite3

from redaction_lab.contracts import ModelAttempt, PredictionManifest


@dataclass(frozen=True)
class StoredJob:
    job_id: str
    state: str
    attempt_policy: str
    manifest: PredictionManifest
    attempt_id: str | None
    request_hash: str | None
    model_config_id: str | None


class RunStore:
    """Small transactional store with conservative no-retry crash semantics."""

    def __init__(self, path: str | PathLike[str]) -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
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
                CREATE TRIGGER IF NOT EXISTS attempts_no_update
                BEFORE UPDATE ON attempts
                BEGIN
                    SELECT RAISE(ABORT, 'attempts are immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS attempts_no_delete
                BEFORE DELETE ON attempts
                BEGIN
                    SELECT RAISE(ABORT, 'attempts are immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS jobs_intent_no_update
                BEFORE UPDATE OF scope_key, project_id, run_id, target_id,
                    target_version, model_id, attempt_policy, manifest_json,
                    created_at ON jobs
                BEGIN
                    SELECT RAISE(ABORT, 'job intent is immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS jobs_no_delete
                BEFORE DELETE ON jobs
                BEGIN
                    SELECT RAISE(ABORT, 'job intent is immutable');
                END;
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
        encoded = json.dumps(values, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def enqueue(self, manifest: PredictionManifest, *, attempt_policy: str) -> str:
        if not attempt_policy.strip():
            raise ValueError("attempt policy must be nonblank")
        scope_key = self._scope_key(manifest, attempt_policy)
        job_id = f"job-{scope_key}"
        manifest_json = manifest.model_dump_json()
        now = datetime.now(UTC).isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    job_id, scope_key, project_id, run_id, target_id,
                    target_version, model_id, attempt_policy, manifest_json,
                    state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
                """,
                (
                    job_id,
                    scope_key,
                    manifest.project_id,
                    manifest.run_id,
                    manifest.target_id,
                    manifest.target_version,
                    manifest.model_id,
                    attempt_policy,
                    manifest_json,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT manifest_json FROM jobs WHERE scope_key = ?", (scope_key,)
            ).fetchone()
            if row is None or row["manifest_json"] != manifest_json:
                raise ValueError("scoped job already has a different frozen manifest")
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
        )

    def job(self, job_id: str) -> StoredJob:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._stored_job(row)

    def next_pending(self) -> StoredJob | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM jobs
                WHERE state = 'PENDING'
                ORDER BY created_at, job_id
                LIMIT 1
                """
            ).fetchone()
        return self._stored_job(row) if row is not None else None

    def claim(
        self, job_id: str, *, request_hash: str, model_config_id: str
    ) -> str | None:
        attempt_seed = json.dumps(
            (job_id, request_hash, model_config_id), separators=(",", ":")
        ).encode("utf-8")
        attempt_id = f"attempt-{sha256(attempt_seed).hexdigest()}"
        now = datetime.now(UTC).isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE jobs
                SET state = 'IN_DOUBT', attempt_id = ?, request_hash = ?,
                    model_config_id = ?, updated_at = ?
                WHERE job_id = ? AND state = 'PENDING'
                """,
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
            row = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise KeyError(job_id)
            manifest = PredictionManifest.model_validate_json(row["manifest_json"])
            expected = (
                row["attempt_id"],
                manifest.project_id,
                manifest.run_id,
                manifest.target_id,
                manifest.target_version,
                manifest.model_id,
                row["model_config_id"],
                row["request_hash"],
            )
            actual = (
                attempt.attempt_id,
                attempt.project_id,
                attempt.run_id,
                attempt.target_id,
                attempt.target_version,
                attempt.model_id,
                attempt.model_config_id,
                attempt.request_hash,
            )
            if row["state"] != "IN_DOUBT" or expected != actual:
                raise ValueError("attempt provenance does not match durable intent")
            connection.execute(
                """
                INSERT INTO attempts (attempt_id, job_id, attempt_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    attempt.attempt_id,
                    job_id,
                    attempt.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            next_state = (
                "IN_DOUBT" if attempt.status.value == "TIMEOUT" else "COMPLETE"
            )
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
        return tuple(
            ModelAttempt.model_validate_json(row["attempt_json"]) for row in rows
        )
