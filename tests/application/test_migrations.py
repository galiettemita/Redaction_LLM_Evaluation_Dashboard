from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Barrier, Event, Thread

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
    assert not tuple((tmp_path / "backups").glob("*.part"))
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
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    broken = replace(migration_module.MIGRATIONS[0], sql="CREATE TABLE partial(x); INVALID SQL;")
    backup_fd = os.open(backup_directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with sqlite3.connect(path, isolation_level=None) as connection:
            with pytest.raises(MigrationError):
                migration_module._apply_migrations(
                    connection,
                    existed=False,
                    database_name=path.name,
                    backup_fd=backup_fd,
                    migrations=(broken,),
                )
    finally:
        os.close(backup_fd)

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
    real_popen = migration_module.subprocess.Popen
    swapped = False

    def swapping_popen(*args, **kwargs):
        nonlocal swapped
        if not swapped:
            swapped = True
            moved = tmp_path / "application-moved"
            parent.rename(moved)
            parent.symlink_to(outside, target_is_directory=True)
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(migration_module.subprocess, "Popen", swapping_popen)
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
    real_popen = migration_module.subprocess.Popen
    swapped = False

    def swapping_popen(*args, **kwargs):
        nonlocal swapped
        if not swapped:
            swapped = True
            path.rename(original)
            with sqlite3.connect(path) as replacement:
                replacement.execute("CREATE TABLE attacker(value TEXT)")
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(migration_module.subprocess, "Popen", swapping_popen)
    with pytest.raises(MigrationError, match="replaced"):
        migrate_database(path, backup_directory=tmp_path / "backups")

    with sqlite3.connect(original) as connection:
        assert connection.execute("SELECT value FROM immutable").fetchone()[0] == "original"
    assert list((tmp_path / "backups").iterdir()) == []


def test_failed_backup_integrity_removes_only_new_backup(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE legacy(value TEXT)")
    before = path.read_bytes()
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    monkeypatch.setattr(migration_module, "_integrity_check", lambda connection: False)
    backup_fd = os.open(backup_directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with sqlite3.connect(path) as source:
            with pytest.raises(MigrationError, match="backup integrity"):
                migration_module._verified_backup(
                    source,
                    database_name=path.name,
                    backup_fd=backup_fd,
                )
    finally:
        os.close(backup_fd)

    assert path.read_bytes() == before
    assert list(backup_directory.iterdir()) == []


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
    backup_fd = os.open(backup_directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with sqlite3.connect(path) as source:
            with pytest.raises(FileExistsError):
                migration_module._verified_backup(
                    source,
                    database_name=path.name,
                    backup_fd=backup_fd,
                )
    finally:
        os.close(backup_fd)

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
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    backup_fd = os.open(backup_directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with sqlite3.connect(path, isolation_level=None) as connection:
            with pytest.raises(MigrationError, match="migration"):
                migration_module._apply_migrations(
                    connection,
                    existed=True,
                    database_name=path.name,
                    backup_fd=backup_fd,
                    migrations=(broken,),
                )
    finally:
        os.close(backup_fd)

    backups = tuple(backup_directory.glob("*.bak"))
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


def test_parent_process_never_calls_chdir_or_fchdir(
    tmp_path: Path, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("parent process cwd mutation")

    monkeypatch.setattr(migration_module.os, "chdir", forbidden)
    monkeypatch.setattr(migration_module.os, "fchdir", forbidden)

    migrate_database(tmp_path / "database.sqlite3", backup_directory=tmp_path / "backups")


def test_unrelated_thread_relative_io_never_observes_migration_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    original = tmp_path / "original"
    database_directory = tmp_path / "database"
    original.mkdir()
    database_directory.mkdir()
    monkeypatch.chdir(original)
    stop = Event()
    ready = Event()
    observed: set[Path] = set()

    def write_relative() -> None:
        ready.set()
        while not stop.is_set():
            observed.add(Path.cwd())
            with Path("unrelated-thread.txt").open("ab") as handle:
                handle.write(b"x")

    writer = Thread(target=write_relative)
    writer.start()
    assert ready.wait(timeout=1)
    try:
        migrate_database(
            database_directory / "database.sqlite3",
            backup_directory=tmp_path / "backups",
        )
    finally:
        stop.set()
        writer.join(timeout=2)

    assert observed == {original}
    assert (original / "unrelated-thread.txt").exists()
    assert not (database_directory / "unrelated-thread.txt").exists()


def test_helper_invocation_uses_fixed_interpreter_and_only_required_fds(
    tmp_path: Path, monkeypatch
) -> None:
    real_popen = migration_module.subprocess.Popen
    observed: dict[str, object] = {}

    def inspecting_popen(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs.copy()
        return real_popen(command, **kwargs)

    monkeypatch.setattr(migration_module.subprocess, "Popen", inspecting_popen)
    migrate_database(tmp_path / "database.sqlite3", backup_directory=tmp_path / "backups")

    command = observed["command"]
    kwargs = observed["kwargs"]
    assert command[:4] == [sys.executable, "-B", "-m", migration_module.__name__]
    assert command[4] == migration_module._HELPER_ARGUMENT
    assert kwargs["shell"] is False
    assert kwargs["cwd"] is None
    assert kwargs["close_fds"] is True
    assert len(kwargs["pass_fds"]) == 3
    assert len(set(kwargs["pass_fds"])) == 3
    assert "preexec_fn" not in kwargs
    assert kwargs["stdin"] is subprocess.DEVNULL


def test_bounded_helper_output_rejects_overflow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(migration_module, "_MAX_STDOUT_BYTES", 16)
    process = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 17)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    with pytest.raises(MigrationError, match="stdout exceeded limit"):
        migration_module._collect_bounded_output(process)


def test_helper_timeout_terminates_process(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(migration_module, "_HELPER_TIMEOUT_SECONDS", 0.05)
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    with pytest.raises(MigrationError, match="timed out"):
        migration_module._collect_bounded_output(process)

    assert process.poll() is not None


def test_invalid_helper_response_fails_but_restart_reconciles_commit(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "database.sqlite3"
    backup_directory = tmp_path / "backups"
    real_collect = migration_module._collect_bounded_output

    def lose_valid_response(process):
        _, stderr = real_collect(process)
        return b"{invalid", stderr

    with monkeypatch.context() as context:
        context.setattr(migration_module, "_collect_bounded_output", lose_valid_response)
        with pytest.raises(MigrationError, match="invalid JSON"):
            migrate_database(path, backup_directory=backup_directory)

    assert EXPECTED_TABLES <= _tables(path)
    replay = migrate_database(path, backup_directory=backup_directory)
    assert replay.applied_versions == ()
    assert replay.backup_path is None


def test_helper_rejects_replaced_database_descriptor_binding(tmp_path: Path) -> None:
    database_directory = tmp_path / "database"
    backup_directory = tmp_path / "backups"
    database_directory.mkdir()
    backup_directory.mkdir()
    path = database_directory / "database.sqlite3"
    path.touch()
    database_directory_fd = os.open(database_directory, os.O_RDONLY | os.O_DIRECTORY)
    database_fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    backup_fd = os.open(backup_directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        path.rename(database_directory / "original.sqlite3")
        path.touch()
        with pytest.raises(MigrationError, match="replaced"):
            migration_module._require_inherited_descriptors(
                database_directory_fd,
                database_fd,
                backup_fd,
                path.name,
            )
    finally:
        os.close(backup_fd)
        os.close(database_fd)
        os.close(database_directory_fd)


def test_committed_uncheckpointed_wal_records_survive_migration_and_backup(
    tmp_path: Path,
) -> None:
    path = tmp_path / "wal.sqlite3"
    backup_directory = tmp_path / "backups"
    writer = sqlite3.connect(path)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE legacy(value BLOB NOT NULL)")
        writer.execute("INSERT INTO legacy VALUES (?)", (b"committed-wal",))
        writer.commit()
        assert path.with_name(path.name + "-wal").exists()

        result = migrate_database(path, backup_directory=backup_directory)
    finally:
        writer.close()

    assert result.backup_path is not None
    for candidate in (path, result.backup_path):
        with sqlite3.connect(candidate) as connection:
            assert connection.execute("SELECT value FROM legacy").fetchone()[0] == b"committed-wal"


def test_hot_rollback_journal_recovers_before_migration(tmp_path: Path) -> None:
    path = tmp_path / "hot.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("CREATE TABLE legacy(value TEXT NOT NULL)")
        connection.execute("INSERT INTO legacy VALUES ('committed')")
    crash_script = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
connection.execute('PRAGMA journal_mode=DELETE')
connection.execute('PRAGMA synchronous=FULL')
connection.execute('BEGIN IMMEDIATE')
connection.execute("UPDATE legacy SET value='uncommitted'")
os._exit(23)
"""
    crashed = subprocess.run([sys.executable, "-c", crash_script, str(path)], check=False)
    assert crashed.returncode == 23
    assert path.with_name(path.name + "-journal").exists()

    result = migrate_database(path, backup_directory=tmp_path / "backups")

    assert result.applied_versions == (1,)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT value FROM legacy").fetchone()[0] == "committed"


def test_restart_cleans_only_validated_incomplete_backup(tmp_path: Path) -> None:
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    stale = backup_directory / ".database.sqlite3.20261012T010203456789Z.0123456789abcdef.bak.part"
    unrelated = backup_directory / "unrelated.bak.part"
    stale.write_bytes(b"interrupted")
    unrelated.write_bytes(b"preserve")

    migrate_database(
        tmp_path / "database.sqlite3",
        backup_directory=backup_directory,
    )

    assert not stale.exists()
    assert unrelated.read_bytes() == b"preserve"
    assert tuple(candidate.name for candidate in backup_directory.glob("*.part")) == (
        unrelated.name,
    )


def test_helper_failure_cannot_fabricate_success(tmp_path: Path) -> None:
    path = tmp_path / "malformed.sqlite3"
    path.write_bytes(b"not a sqlite database")

    with pytest.raises(MigrationError, match="isolated migration helper failed"):
        migrate_database(path, backup_directory=tmp_path / "backups")

    assert path.read_bytes() == b"not a sqlite database"
    assert not tuple((tmp_path / "backups").glob("*.bak"))


def test_helper_protocol_rejects_duplicate_json_fields() -> None:
    response = (
        b'{"protocol":"redaction-lab-sqlite-migration-v1",'
        b'"protocol":"redaction-lab-sqlite-migration-v1",'
        b'"status":"ok","applied_versions":[],"backup_name":null,'
        b'"database_device":1,"database_inode":2}'
    )

    with pytest.raises(MigrationError, match="duplicate|invalid JSON"):
        migration_module._parse_helper_response(response, b"", 0)


def test_concurrent_initialization_serializes_without_partial_state(tmp_path: Path) -> None:
    path = tmp_path / "database.sqlite3"
    backup_directory = tmp_path / "backups"
    barrier = Barrier(3)
    results: list[object] = []

    def initialize() -> None:
        barrier.wait()
        try:
            results.append(migrate_database(path, backup_directory=backup_directory))
        except Exception as error:
            results.append(error)

    workers = [Thread(target=initialize) for _ in range(2)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join(timeout=5)

    assert all(not isinstance(result, Exception) for result in results)
    assert sorted(result.applied_versions for result in results) == [(), (1,)]
    assert EXPECTED_TABLES <= _tables(path)


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ({"applied_versions": [999]}, "invalid versions"),
        ({"database_inode": -1}, "identity mismatch"),
        ({"backup_name": "../../forged.bak"}, "unsafe backup name"),
    ],
)
def test_parent_rejects_untrusted_helper_result_fields(
    tmp_path: Path, replacement: dict[str, object], message: str
) -> None:
    database = tmp_path / "database.sqlite3"
    database.touch()
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    database_fd = os.open(database, os.O_RDWR | os.O_NOFOLLOW)
    backup_fd = os.open(backup_directory, os.O_RDONLY | os.O_DIRECTORY)
    identity = os.fstat(database_fd)
    payload: dict[str, object] = {
        "protocol": migration_module._HELPER_PROTOCOL,
        "status": "ok",
        "applied_versions": [],
        "backup_name": None,
        "database_device": identity.st_dev,
        "database_inode": identity.st_ino,
    }
    payload.update(replacement)
    try:
        with pytest.raises(MigrationError, match=message):
            migration_module._validate_helper_result(
                payload,
                database_fd=database_fd,
                backup_fd=backup_fd,
                database_name=database.name,
            )
    finally:
        os.close(backup_fd)
        os.close(database_fd)
