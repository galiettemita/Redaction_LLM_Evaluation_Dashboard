from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import os
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


def test_migration_rejects_symlinked_backup_root_without_mutation(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE legacy(payload BLOB)")
        connection.execute("INSERT INTO legacy VALUES (?)", (b"immutable",))
    before = path.read_bytes()
    outside = tmp_path / "outside"
    outside.mkdir()
    backup = tmp_path / "backups"
    backup.symlink_to(outside, target_is_directory=True)

    with pytest.raises(MigrationError, match="symbolic|symlink"):
        migrate_database(path, backup_directory=backup)

    assert path.read_bytes() == before
    assert list(outside.iterdir()) == []


def test_migration_rejects_symlinked_backup_ancestor_without_mutation(tmp_path: Path) -> None:
    parent = tmp_path / "database"
    parent.mkdir()
    path = parent / "application.sqlite3"
    outside = tmp_path / "outside"
    outside.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(MigrationError, match="symbolic|symlink"):
        migrate_database(path, backup_directory=linked_parent / "backups")

    assert not path.exists()
    assert list(outside.iterdir()) == []


def test_migration_rejects_symlinked_database_leaf(tmp_path: Path) -> None:
    target = tmp_path / "target.sqlite3"
    with sqlite3.connect(target) as connection:
        connection.execute("CREATE TABLE protected(value TEXT)")
    before = target.read_bytes()
    link = tmp_path / "application.sqlite3"
    link.symlink_to(target)

    with pytest.raises(MigrationError, match="symbolic|symlink"):
        migrate_database(link, backup_directory=tmp_path / "backups")

    assert target.read_bytes() == before
    assert not (tmp_path / "backups").exists()


def test_parent_replacement_race_stays_anchored_to_original_directory(
    tmp_path: Path, monkeypatch
) -> None:
    parent = tmp_path / "application"
    parent.mkdir()
    path = parent / "database.sqlite3"
    outside = tmp_path / "outside"
    outside.mkdir()
    real_connect = migration_module.sqlite3.connect
    swapped = False

    def swapping_connect(database, *args, **kwargs):
        nonlocal swapped
        if not swapped:
            swapped = True
            moved = tmp_path / "application-moved"
            parent.rename(moved)
            parent.symlink_to(outside, target_is_directory=True)
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(migration_module.sqlite3, "connect", swapping_connect)
    migrate_database(path, backup_directory=tmp_path / "backups")

    assert not (outside / "database.sqlite3").exists()
    assert "schema_migrations" in _tables(tmp_path / "application-moved" / "database.sqlite3")


def test_database_leaf_replacement_during_sqlite_open_is_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "database.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE immutable(value TEXT)")
        connection.execute("INSERT INTO immutable VALUES ('original')")
    original = tmp_path / "original.sqlite3"
    real_connect = migration_module.sqlite3.connect
    swapped = False

    def swapping_connect(database, *args, **kwargs):
        nonlocal swapped
        if database == path.name and not swapped:
            swapped = True
            path.rename(original)
            with real_connect(path) as replacement:
                replacement.execute("CREATE TABLE attacker(value TEXT)")
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(migration_module.sqlite3, "connect", swapping_connect)
    with pytest.raises(MigrationError, match="replaced"):
        migrate_database(path, backup_directory=tmp_path / "backups")

    with real_connect(original) as connection:
        assert connection.execute("SELECT value FROM immutable").fetchone()[0] == "original"
    assert list((tmp_path / "backups").iterdir()) == []


def test_failed_backup_integrity_removes_only_new_backup(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE legacy(value TEXT)")
    before = path.read_bytes()
    monkeypatch.setattr(migration_module, "_integrity_check", lambda connection: False)

    with pytest.raises(MigrationError, match="backup integrity"):
        migrate_database(path, backup_directory=tmp_path / "backups")

    assert path.read_bytes() == before
    assert list((tmp_path / "backups").iterdir()) == []


def test_backup_name_collision_preserves_existing_file_and_database(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE immutable(value TEXT)")
        connection.execute("INSERT INTO immutable VALUES ('original')")
    before = path.read_bytes()
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    fixed = datetime(2026, 10, 12, 1, 2, 3, 456789, tzinfo=UTC)

    class FixedDatetime:
        @classmethod
        def now(cls, timezone):
            assert timezone is UTC
            return fixed

    name = f"{path.name}.{fixed.strftime('%Y%m%dT%H%M%S%fZ')}.bak"
    collision = backup_directory / name
    collision.write_bytes(b"do-not-overwrite")
    monkeypatch.setattr(migration_module, "datetime", FixedDatetime)

    with pytest.raises(FileExistsError):
        migrate_database(path, backup_directory=backup_directory)

    assert path.read_bytes() == before
    assert collision.read_bytes() == b"do-not-overwrite"


def test_failed_legacy_migration_preserves_verified_backup_and_rolls_back(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE immutable(value TEXT)")
        connection.execute("INSERT INTO immutable VALUES ('original')")
    broken = replace(
        migration_module.MIGRATIONS[0],
        sql="CREATE TABLE partial(value TEXT); INVALID SQL;",
    )
    monkeypatch.setattr(migration_module, "MIGRATIONS", (broken,))

    with pytest.raises(MigrationError, match="migration"):
        migrate_database(path, backup_directory=tmp_path / "backups")

    backups = tuple((tmp_path / "backups").glob("*.bak"))
    assert len(backups) == 1
    for candidate in (path, backups[0]):
        with sqlite3.connect(candidate) as connection:
            assert connection.execute("SELECT value FROM immutable").fetchone()[0] == "original"
            assert "partial" not in {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }


def test_migration_restores_process_working_directory(tmp_path: Path) -> None:
    before = os.getcwd()
    migrate_database(tmp_path / "database.sqlite3", backup_directory=tmp_path / "backups")
    assert os.getcwd() == before
