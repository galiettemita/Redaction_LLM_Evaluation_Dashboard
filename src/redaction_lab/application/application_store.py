"""Durable local application records, separate from Task 4/6 evidence tables."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from redaction_lab.application.migration import migrate_database
from redaction_lab.contracts import DocumentRole
from redaction_lab.application.worker_protocol import (
    WORKER_PROTOCOL_VERSION,
    WorkerResponse,
    WorkerStatus,
)


class ProcessingStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    NO_REDACTIONS = "NO_REDACTIONS"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RegisteredUpload:
    document_id: str
    version_id: str
    job_id: str
    project_id: str
    role: DocumentRole
    artifact_key: str
    sha256: str
    byte_size: int


@dataclass(frozen=True)
class StoredDocumentVersion:
    version_id: str
    document_id: str
    project_id: str
    role: DocumentRole
    artifact_key: str
    sha256: str
    byte_size: int
    page_count: int | None
    processing_state: ProcessingStatus
    source_id: str | None
    created_at: datetime


@dataclass(frozen=True)
class StoredApplicationJob:
    job_id: str
    project_id: str
    version_id: str
    role: DocumentRole
    input_sha256: str
    status: ProcessingStatus
    owner: str | None
    request_nonce: str | None
    protocol_version: str | None
    image_digest: str | None
    page_count: int | None
    source_id: str | None
    reason_code: str | None
    updated_at: datetime


@dataclass(frozen=True)
class StoredDocumentPair:
    pair_id: str
    project_id: str
    redacted_version_id: str
    reference_version_id: str | None
    pairing_status: str = "ASSOCIATED_UNTRUSTED"

    @property
    def truth_trusted(self) -> bool:
        return False


@dataclass(frozen=True)
class StoredReferenceSource:
    source_id: str
    version_id: str
    job_id: str
    project_id: str
    input_sha256: str
    canonical_text: str
    canonical_hash: str
    canonicalizer_version: str
    page_count: int
    request_nonce: str
    protocol_version: str
    image_digest: str
    provenance: str = "USER_SUPPLIED_EXPERIMENTAL"

    @property
    def reference_document_version_id(self) -> str:
        return self.version_id

    @property
    def canonical_document_version_id(self) -> str:
        return self.source_id


def _identity(prefix: str, values: object) -> str:
    encoded = json.dumps(
        values, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"{prefix}-{sha256(encoded).hexdigest()}"


class ApplicationStore:
    def __init__(self, path: Path, *, backup_directory: Path) -> None:
        self.path = Path(path)
        self.backup_directory = Path(backup_directory)
        migrate_database(self.path, backup_directory=self.backup_directory)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @staticmethod
    def _job(row: sqlite3.Row) -> StoredApplicationJob:
        return StoredApplicationJob(
            job_id=row["job_id"], project_id=row["project_id"],
            version_id=row["document_version_id"], role=DocumentRole(row["role"]),
            input_sha256=row["input_sha256"], status=ProcessingStatus(row["status"]),
            owner=row["owner"], request_nonce=row["request_nonce"],
            protocol_version=row["protocol_version"], image_digest=row["image_digest"],
            page_count=row["page_count"], source_id=row["source_id"],
            reason_code=row["reason_code"], updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def register_upload(
        self,
        *,
        project_id: str,
        role: DocumentRole,
        artifact_key: str,
        sha256: str,
        byte_size: int,
    ) -> RegisteredUpload:
        project_id = project_id.strip()
        if not project_id:
            raise ValueError("project context must be nonblank")
        document_id = _identity("document", [project_id, role.value, sha256])
        version_id = _identity("document-version", [document_id, sha256, role.value])
        request_digest = _identity("ingestion-request", [project_id, role.value, sha256])
        job_id = _identity("application-job", request_digest)
        now = datetime.now(UTC).isoformat()
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT OR IGNORE INTO documents VALUES (?, ?, ?, 'ACCEPTED', ?)",
                (document_id, project_id, role.value, now),
            )
            connection.execute(
                """INSERT OR IGNORE INTO document_versions (
                    version_id, document_id, project_id, role, artifact_key, sha256,
                    byte_size, media_type, page_count, processing_state, source_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'application/pdf', NULL, 'ACCEPTED', NULL, ?)""",
                (version_id, document_id, project_id, role.value, artifact_key, sha256, byte_size, now),
            )
            connection.execute(
                """INSERT OR IGNORE INTO application_jobs (
                    job_id, request_digest, project_id, document_version_id, role,
                    input_sha256, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'ACCEPTED', ?, ?)""",
                (job_id, request_digest, project_id, version_id, role.value, sha256, now, now),
            )
            row = connection.execute(
                """SELECT d.document_id, v.*, j.job_id
                   FROM document_versions v
                   JOIN documents d ON d.document_id = v.document_id
                   JOIN application_jobs j ON j.document_version_id = v.version_id
                   WHERE j.request_digest = ?""",
                (request_digest,),
            ).fetchone()
            if row is None or tuple(row[key] for key in (
                "document_id", "version_id", "job_id", "project_id", "role",
                "artifact_key", "sha256", "byte_size",
            )) != (
                document_id, version_id, job_id, project_id, role.value,
                artifact_key, sha256, byte_size,
            ):
                raise ValueError("upload identity already has different content")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return RegisteredUpload(
            document_id, version_id, job_id, project_id, role, artifact_key, sha256, byte_size
        )

    def create_pair(
        self,
        *,
        project_id: str,
        redacted_version_id: str,
        reference_version_id: str | None,
    ) -> StoredDocumentPair:
        pair_id = _identity(
            "document-pair", [project_id, redacted_version_id, reference_version_id]
        )
        now = datetime.now(UTC).isoformat()
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT version_id, project_id, role FROM document_versions WHERE version_id IN (?, ?)",
                (redacted_version_id, reference_version_id or ""),
            ).fetchall()
            by_id = {row["version_id"]: row for row in rows}
            redacted = by_id.get(redacted_version_id)
            reference = by_id.get(reference_version_id) if reference_version_id else None
            if redacted is None or redacted["project_id"] != project_id or redacted["role"] != "REDACTED":
                raise ValueError("invalid redacted document version")
            if reference_version_id and (
                reference is None or reference["project_id"] != project_id or reference["role"] != "REFERENCE"
            ):
                raise ValueError("invalid reference document version")
            connection.execute(
                """INSERT OR IGNORE INTO document_pairs
                   VALUES (?, ?, ?, ?, 'ASSOCIATED_UNTRUSTED', ?)""",
                (pair_id, project_id, redacted_version_id, reference_version_id, now),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return StoredDocumentPair(pair_id, project_id, redacted_version_id, reference_version_id)

    def get_pair(self, pair_id: str) -> StoredDocumentPair:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM document_pairs WHERE pair_id=?", (pair_id,)).fetchone()
        if row is None:
            raise KeyError(pair_id)
        return StoredDocumentPair(**{key: row[key] for key in StoredDocumentPair.__dataclass_fields__})

    def pairs_for_redacted(self, version_id: str) -> tuple[StoredDocumentPair, ...]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM document_pairs WHERE redacted_version_id=? ORDER BY pair_id", (version_id,)
            ).fetchall()
        return tuple(StoredDocumentPair(**{key: row[key] for key in StoredDocumentPair.__dataclass_fields__})
                     for row in rows)

    @staticmethod
    def _reference_source(connection: sqlite3.Connection, version_id: str) -> StoredReferenceSource | None:
        row = connection.execute("SELECT * FROM reference_sources WHERE version_id=?", (version_id,)).fetchone()
        if row is None:
            return None
        source = StoredReferenceSource(**dict(row))
        values = asdict(source)
        values.pop("source_id")
        if source.source_id != _identity("reference-source", values) or source.provenance != "USER_SUPPLIED_EXPERIMENTAL":
            raise ValueError("reference source identity mismatch")
        # Validate hashes, bounds and schema again on every read, including after reopen.
        WorkerResponse(
            protocol_version=source.protocol_version, request_nonce=source.request_nonce,
            project_id=source.project_id, role=DocumentRole.REFERENCE, input_sha256=source.input_sha256,
            status=WorkerStatus.PROCESSABLE, page_count=source.page_count,
            reference_text=source.canonical_text, reference_hash=source.canonical_hash,
            reference_canonicalizer_version=source.canonicalizer_version,
        )
        bound = connection.execute(
            """SELECT 1 FROM application_jobs j JOIN document_versions v ON v.version_id=j.document_version_id
               WHERE j.job_id=? AND v.version_id=? AND j.role='REFERENCE' AND v.role='REFERENCE'
               AND j.project_id=? AND v.project_id=? AND j.input_sha256=? AND v.sha256=?
               AND j.request_nonce=? AND j.protocol_version=? AND j.image_digest=? AND j.page_count=?""",
            (source.job_id, source.version_id, source.project_id, source.project_id,
             source.input_sha256, source.input_sha256, source.request_nonce, source.protocol_version,
             source.image_digest, source.page_count),
        ).fetchone()
        if bound is None:
            raise ValueError("reference source binding mismatch")
        return source

    def reference_source(self, version_id: str) -> StoredReferenceSource | None:
        with self.connect() as connection:
            return self._reference_source(connection, version_id)

    def record_reference_source(
        self, job_id: str, *, owner: str, response: WorkerResponse
    ) -> StoredReferenceSource:
        # Revalidate even model_copy-created instances before persisting any evidence.
        response = WorkerResponse.model_validate(response.model_dump())
        if response.role is not DocumentRole.REFERENCE or response.status is not WorkerStatus.PROCESSABLE:
            raise ValueError("reference source requires processable reference evidence")
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            job = connection.execute("SELECT * FROM application_jobs WHERE job_id=?", (job_id,)).fetchone()
            if job is None or job["owner"] != owner or job["status"] != 'PROCESSING' or any((
                job["role"] != response.role.value, job["project_id"] != response.project_id,
                job["input_sha256"] != response.input_sha256, job["request_nonce"] != response.request_nonce,
                job["protocol_version"] != response.protocol_version, job["page_count"] != response.page_count,
                not job["image_digest"],
            )):
                raise ValueError("reference source runtime binding mismatch")
            values = dict(
                version_id=job["document_version_id"], job_id=job_id, project_id=response.project_id,
                input_sha256=response.input_sha256, canonical_text=response.reference_text,
                canonical_hash=response.reference_hash, canonicalizer_version=response.reference_canonicalizer_version,
                page_count=response.page_count, request_nonce=response.request_nonce,
                protocol_version=response.protocol_version, image_digest=job["image_digest"],
                provenance="USER_SUPPLIED_EXPERIMENTAL",
            )
            source = StoredReferenceSource(source_id=_identity("reference-source", values), **values)
            existing = self._reference_source(connection, source.version_id)
            if existing is not None and existing != source:
                raise ValueError("immutable reference source already differs")
            if existing is None:
                connection.execute("INSERT INTO reference_sources VALUES (" + ",".join("?" for _ in asdict(source)) + ")",
                                   tuple(asdict(source).values()))
            connection.commit()
            return source
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_job(self, job_id: str) -> StoredApplicationJob:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM application_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._job(row)

    def get_version(self, version_id: str) -> StoredDocumentVersion:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM document_versions WHERE version_id = ?", (version_id,)
            ).fetchone()
        if row is None:
            raise KeyError(version_id)
        return StoredDocumentVersion(
            version_id=row["version_id"], document_id=row["document_id"],
            project_id=row["project_id"], role=DocumentRole(row["role"]),
            artifact_key=row["artifact_key"], sha256=row["sha256"], byte_size=row["byte_size"],
            page_count=row["page_count"], processing_state=ProcessingStatus(row["processing_state"]),
            source_id=row["source_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def claim_next(
        self,
        *,
        owner: str,
        now: datetime,
        expected_job_id: str | None = None,
    ) -> StoredApplicationJob | None:
        if not owner.strip():
            raise ValueError("worker owner must be nonblank")
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute(
                "SELECT 1 FROM application_jobs WHERE status = 'PROCESSING'"
            ).fetchone():
                connection.commit()
                return None
            row = connection.execute(
                "SELECT job_id FROM application_jobs WHERE status = 'ACCEPTED' "
                "ORDER BY CASE role WHEN 'REDACTED' THEN 0 ELSE 1 END, "
                "created_at, job_id LIMIT 1"
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            if expected_job_id is not None and row["job_id"] != expected_job_id:
                connection.commit()
                return None
            connection.execute(
                "UPDATE application_jobs SET status='PROCESSING', owner=?, updated_at=? WHERE job_id=?",
                (owner, now.isoformat(), row["job_id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM application_jobs WHERE job_id=?", (row["job_id"],)
            ).fetchone()
            connection.commit()
            return self._job(claimed)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def record_runtime(
        self,
        job_id: str,
        *,
        owner: str,
        request_nonce: str,
        protocol_version: str,
        image_digest: str,
        page_count: int,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self.connect() as connection:
            cursor = connection.execute(
                """UPDATE application_jobs SET request_nonce=?, protocol_version=?,
                   image_digest=?, page_count=?, updated_at=?
                   WHERE job_id=? AND status='PROCESSING' AND owner=?""",
                (
                    request_nonce,
                    protocol_version,
                    image_digest,
                    page_count or None,
                    now,
                    job_id,
                    owner,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("application job is not owned processing work")

    def complete_job(
        self,
        job_id: str,
        *,
        owner: str,
        status: ProcessingStatus,
        page_count: int | None,
        source_id: str | None,
        reason_code: str | None,
    ) -> None:
        if status not in {
            ProcessingStatus.READY,
            ProcessingStatus.NO_REDACTIONS,
            ProcessingStatus.UNSUPPORTED,
            ProcessingStatus.FAILED,
        }:
            raise ValueError("job completion requires a terminal status")
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT document_version_id, role, project_id, input_sha256, protocol_version
                   FROM application_jobs
                   WHERE job_id=? AND status='PROCESSING' AND owner=?""",
                (job_id, owner),
            ).fetchone()
            if row is None:
                raise ValueError("application job is not owned processing work")
            if row["role"] == "REFERENCE" and source_id is not None:
                raise ValueError("reference jobs cannot bind Task-4 sources")
            if (
                row["role"] == "REFERENCE" and status is ProcessingStatus.READY
                and row["protocol_version"] == WORKER_PROTOCOL_VERSION
            ):
                reference = self._reference_source(connection, row["document_version_id"])
                if reference is None or reference.page_count != page_count:
                    raise ValueError("READY reference job requires an immutable reference source")
            if row["role"] == "REDACTED" and status is ProcessingStatus.READY:
                has_sources = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='canonical_sources'"
                ).fetchone()
                source = (
                    connection.execute(
                        """SELECT 1 FROM canonical_sources
                           WHERE source_id=? AND project_id=? AND source_sha256=?
                             AND role='REDACTED'""",
                        (source_id, row["project_id"], row["input_sha256"]),
                    ).fetchone()
                    if has_sources is not None and source_id is not None
                    else None
                )
                if source is None:
                    raise ValueError("READY redacted job requires an authentic Task-4 source")
            connection.execute(
                """UPDATE document_versions SET page_count=?, processing_state=?, source_id=?
                   WHERE version_id=?""",
                (page_count, status.value, source_id, row["document_version_id"]),
            )
            connection.execute(
                """UPDATE application_jobs SET status=?, page_count=?, source_id=?,
                   reason_code=?, updated_at=? WHERE job_id=?""",
                (status.value, page_count, source_id, reason_code, datetime.now(UTC).isoformat(), job_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def recover_interrupted(self, *, now: datetime) -> tuple[str, ...]:
        connection = self.connect()
        recovered: list[str] = []
        try:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """SELECT job_id, document_version_id, owner, project_id, role,
                          input_sha256, page_count, request_nonce, protocol_version,
                          image_digest
                   FROM application_jobs WHERE status='PROCESSING'"""
            ).fetchall()
            has_sources = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='canonical_sources'"
            ).fetchone() is not None
            for row in rows:
                source = None
                if (
                    has_sources
                    and row["role"] == "REDACTED"
                    and row["page_count"] is not None
                    and row["request_nonce"] is not None
                    and row["protocol_version"] is not None
                    and row["image_digest"] is not None
                ):
                    source = connection.execute(
                        """SELECT source_id FROM canonical_sources
                           WHERE project_id=? AND source_sha256=? AND role='REDACTED'""",
                        (row["project_id"], row["input_sha256"]),
                    ).fetchone()
                if row["role"] == "REFERENCE":
                    try:
                        reference = self._reference_source(connection, row["document_version_id"])
                    except ValueError:
                        reference = None
                    if reference is not None:
                        source = {"source_id": None}
                if source is not None:
                    connection.execute(
                        """UPDATE document_versions SET page_count=?, processing_state='READY',
                           source_id=? WHERE version_id=?""",
                        (row["page_count"], source["source_id"], row["document_version_id"]),
                    )
                    connection.execute(
                        """UPDATE application_jobs SET status='READY', source_id=?,
                           reason_code=NULL, updated_at=? WHERE job_id=?""",
                        (source["source_id"], now.isoformat(), row["job_id"]),
                    )
                    recovered.append(row["job_id"])
                    continue
                connection.execute(
                    "UPDATE document_versions SET processing_state='FAILED' WHERE version_id=?",
                    (row["document_version_id"],),
                )
                connection.execute(
                    """UPDATE application_jobs SET status='FAILED', reason_code='INTERRUPTED',
                       updated_at=? WHERE job_id=?""",
                    (now.isoformat(), row["job_id"]),
                )
                recovered.append(row["job_id"])
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return tuple(recovered)

    def referenced_artifact_keys(self) -> set[str]:
        with self.connect() as connection:
            return {
                str(row[0])
                for row in connection.execute("SELECT artifact_key FROM document_versions")
            }
