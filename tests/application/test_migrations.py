from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

import redaction_lab.application.migration as migration_module
from redaction_lab.application.migration import MigrationError, migrate_database
from redaction_lab.application.application_store import ApplicationStore
from redaction_lab.evaluation_store import EvaluationStore
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.store import RunStore


EXPECTED_TABLES = {
    "documents",
    "document_versions",
    "document_pairs",
    "application_jobs",
    "schema_migrations",
}


def _tables(path: Path) -> set[str]:
    with sqlite3.connect(path) as connection:
        return {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }


def test_fresh_migration_creates_exact_five_application_tables(tmp_path: Path) -> None:
    path = tmp_path / "fresh.sqlite3"

    result = migrate_database(path, backup_directory=tmp_path / "backups")

    assert EXPECTED_TABLES <= _tables(path)
    assert result.applied_versions == (1,)
    assert result.backup_path is None


def test_legacy_database_is_backed_up_and_rows_are_byte_equivalent(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE canonical_sources_legacy (payload BLOB NOT NULL)")
        connection.execute("INSERT INTO canonical_sources_legacy VALUES (?)", (b"immutable",))

    result = migrate_database(path, backup_directory=tmp_path / "backups")

    assert result.backup_path is not None and result.backup_path.exists()
    for candidate in (path, result.backup_path):
        with sqlite3.connect(candidate) as connection:
            assert connection.execute("SELECT payload FROM canonical_sources_legacy").fetchone()[0] == b"immutable"


def test_migration_checksum_tampering_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3"
    migrate_database(path, backup_directory=tmp_path / "backups")
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER schema_migrations_no_update")
        connection.execute("UPDATE schema_migrations SET checksum = 'forged'")

    with pytest.raises(MigrationError, match="checksum"):
        migrate_database(path, backup_directory=tmp_path / "backups")


def test_failed_migration_rolls_back_without_partial_tables(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "failed.sqlite3"
    broken = replace(migration_module.MIGRATIONS[0], sql="CREATE TABLE partial(x); INVALID SQL;")
    monkeypatch.setattr(migration_module, "MIGRATIONS", (broken,))

    with pytest.raises(MigrationError):
        migrate_database(path, backup_directory=tmp_path / "backups")

    assert "partial" not in _tables(path)


def test_real_task4_and_task6_database_reopens_without_evidence_rewrite(tmp_path: Path) -> None:
    path = tmp_path / "legacy-real.sqlite3"
    redacted, _ = make_synthetic_pair("two_boxes", tmp_path / "fixture")
    run_store = RunStore(path)
    source_id = run_store.ingest_redacted_pdf(redacted.read_bytes(), project_id="project")
    EvaluationStore(path)
    with sqlite3.connect(path) as connection:
        before = connection.execute(
            "SELECT canonical_json, targets_json FROM canonical_sources WHERE source_id=?",
            (source_id,),
        ).fetchone()

    ApplicationStore(path, backup_directory=tmp_path / "backups")

    with sqlite3.connect(path) as connection:
        after = connection.execute(
            "SELECT canonical_json, targets_json FROM canonical_sources WHERE source_id=?",
            (source_id,),
        ).fetchone()
    assert after == before
    assert RunStore(path).source(source_id) == run_store.source(source_id)
    assert EvaluationStore(path).run_store.source(source_id) == run_store.source(source_id)
    assert len(tuple((tmp_path / "backups").glob("*.bak"))) == 1
