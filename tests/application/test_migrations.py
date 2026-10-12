from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Barrier, Event, Thread
import time

import pytest

import redaction_lab.application.migration as migration_module
from redaction_lab.application.migration import MigrationError, migrate_database
from redaction_lab.application.application_store import ApplicationStore
from redaction_lab.evaluation_store import EvaluationStore
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.judges.base import SourceFact, SourceFactRecord
from redaction_lab.store import RunStore


EXPECTED_TABLES = {
    "documents",
    "document_versions",
    "document_pairs",
    "application_jobs",
    "schema_migrations",
}


def _subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _start_migration_process(path: Path, backup_directory: Path) -> subprocess.Popen[str]:
    script = """
import json, sys
from pathlib import Path
from redaction_lab.application.migration import migrate_database
print("READY", flush=True)
sys.stdin.buffer.read(1)
result = migrate_database(Path(sys.argv[1]), backup_directory=Path(sys.argv[2]))
print(json.dumps({"applied": result.applied_versions, "backup": str(result.backup_path) if result.backup_path else None}), flush=True)
"""
    return subprocess.Popen(
        [sys.executable, "-B", "-c", script, str(path), str(backup_directory)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_subprocess_environment(),
    )


def _tables(path: Path) -> set[str]:
    with sqlite3.connect(path) as connection:
        return {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }


def _seed_task4_task6_evidence(path: Path, fixture_directory: Path):
    redacted, _ = make_synthetic_pair("two_boxes", fixture_directory)
    run_store = RunStore(path)
    source_id = run_store.ingest_redacted_pdf(
        redacted.read_bytes(), project_id="project"
    )
    source = run_store.source(source_id)
    evaluation_store = EvaluationStore(path)
    provisional = SourceFactRecord(
        source_fact_record_id="pending-identity",
        source_fact_record_version="source-facts-v1",
        project_id=source.project_id,
        target_id=source.targets[0].target_id,
        target_version=source.targets[0].target_version,
        mapping_id="synthetic-mapping-v1",
        mapping_version="mapping-v1",
        rubric_version="fact-evidence-rubric-v0.1-proposed",
        facts=(
            SourceFact(
                fact_id="synthetic-fact",
                reference_proposition="Agent Cedar",
                reference_quote="Agent Cedar",
                reference_quote_locator="chars:0-11",
                critical_dimensions=("identity",),
            ),
        ),
    )
    record = provisional.model_copy(
        update={
            "source_fact_record_id": evaluation_store._source_fact_identity(provisional)
        }
    )
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO source_fact_records (
                   source_fact_record_id, project_id, mapping_id, mapping_version,
                   rubric_version, validation_state, payload_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                record.source_fact_record_id,
                record.project_id,
                record.mapping_id,
                record.mapping_version,
                record.rubric_version,
                record.validation_state.value,
                record.model_dump_json(),
            ),
        )
        source_row = connection.execute(
            "SELECT * FROM canonical_sources WHERE source_id=?", (source_id,)
        ).fetchone()
        fact_row = connection.execute(
            "SELECT * FROM source_fact_records WHERE source_fact_record_id=?",
            (record.source_fact_record_id,),
        ).fetchone()
    return run_store, evaluation_store, source, record, source_row, fact_row


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
    assert len(kwargs["pass_fds"]) == 4
    assert len(set(kwargs["pass_fds"])) == 4
    assert tuple(int(value) for value in command[5:9]) == kwargs["pass_fds"]
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
    lock_fd = migration_module._open_migration_lock(database_directory_fd, path.name)
    try:
        path.rename(database_directory / "original.sqlite3")
        path.touch()
        with pytest.raises(MigrationError, match="replaced"):
            migration_module._require_inherited_descriptors(
                database_directory_fd,
                database_fd,
                backup_fd,
                lock_fd,
                path.name,
            )
    finally:
        os.close(lock_fd)
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


def test_two_independent_processes_serialize_legacy_migration(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    backup_directory = tmp_path / "backups"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE immutable(value BLOB NOT NULL)")
        connection.execute("INSERT INTO immutable VALUES (?)", (b"preserved",))
    workers = [
        _start_migration_process(path, backup_directory),
        _start_migration_process(path, backup_directory),
    ]
    for worker in workers:
        assert worker.stdin is not None and worker.stdout is not None
        assert worker.stdout.readline().strip() == "READY"
    for worker in workers:
        assert worker.stdin is not None
        worker.stdin.write("x")
        worker.stdin.close()

    results: list[dict[str, object]] = []
    for worker in workers:
        worker.wait(timeout=10)
        assert worker.stdout is not None and worker.stderr is not None
        stderr = worker.stderr.read()
        assert worker.returncode == 0, stderr
        results.append(json.loads(worker.stdout.read()))

    assert sorted(tuple(result["applied"]) for result in results) == [(), (1,)]
    assert len(tuple(backup_directory.glob("*.bak"))) == 1
    assert not tuple(backup_directory.glob("*.part"))
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1
        assert connection.execute("SELECT value FROM immutable").fetchone()[0] == b"preserved"


def test_two_process_migration_preserves_task4_and_task6_evidence_on_reopen(
    tmp_path: Path,
) -> None:
    path = tmp_path / "evidence.sqlite3"
    backup_directory = tmp_path / "backups"
    run_store, evaluation_store, source, record, source_before, fact_before = (
        _seed_task4_task6_evidence(path, tmp_path / "fixture")
    )
    workers = [
        _start_migration_process(path, backup_directory),
        _start_migration_process(path, backup_directory),
    ]
    for worker in workers:
        assert worker.stdin is not None and worker.stdout is not None
        assert worker.stdout.readline().strip() == "READY"
    for worker in workers:
        assert worker.stdin is not None
        worker.stdin.write("x")
        worker.stdin.close()

    results: list[dict[str, object]] = []
    for worker in workers:
        worker.wait(timeout=10)
        assert worker.stdout is not None and worker.stderr is not None
        assert worker.returncode == 0, worker.stderr.read()
        results.append(json.loads(worker.stdout.read()))

    third = _start_migration_process(path, backup_directory)
    assert third.stdin is not None and third.stdout is not None
    assert third.stdout.readline().strip() == "READY"
    third.stdin.write("x")
    third.stdin.close()
    third.wait(timeout=10)
    assert third.stdout is not None and third.stderr is not None
    assert third.returncode == 0, third.stderr.read()
    third_result = json.loads(third.stdout.read())

    assert sorted(tuple(result["applied"]) for result in results) == [(), (1,)]
    assert tuple(third_result["applied"]) == ()
    assert len(tuple(backup_directory.glob("*.bak"))) == 1
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT count(*) FROM schema_migrations WHERE version=1"
        ).fetchone()[0] == 1
        source_after = connection.execute(
            "SELECT * FROM canonical_sources WHERE source_id=?", (source.source_id,)
        ).fetchone()
        fact_after = connection.execute(
            "SELECT * FROM source_fact_records WHERE source_fact_record_id=?",
            (record.source_fact_record_id,),
        ).fetchone()
    assert source_after == source_before
    assert fact_after == fact_before
    assert RunStore(path).source(source.source_id) == run_store.source(source.source_id)
    assert evaluation_store._get_source_fact_record(
        record.source_fact_record_id, project_id=source.project_id
    ) == record


def test_contender_does_not_remove_live_holders_part_backup(tmp_path: Path) -> None:
    path = tmp_path / "database.sqlite3"
    backup_directory = tmp_path / "backups"
    backup_directory.mkdir()
    part_name = ".database.sqlite3.20261012T010203456789Z.0123456789abcdef.bak.part"
    holder_script = """
import os, sys
from pathlib import Path
from redaction_lab.application import migration
database = Path(sys.argv[1])
backup = Path(sys.argv[2])
database_directory_fd = os.open(database.parent, os.O_RDONLY | os.O_DIRECTORY)
try:
    with migration._exclusive_migration_lock(database_directory_fd, database.name, timeout_seconds=2):
        part = backup / sys.argv[3]
        part.write_bytes(b"live")
        print("READY", flush=True)
        sys.stdin.buffer.read(1)
finally:
    os.close(database_directory_fd)
"""
    holder = subprocess.Popen(
        [sys.executable, "-B", "-c", holder_script, str(path), str(backup_directory), part_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_subprocess_environment(),
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "READY"
    contender_script = """
import sys
from pathlib import Path
from redaction_lab.application import migration
migration._MIGRATION_LOCK_TIMEOUT_SECONDS = 0.05
try:
    migration.migrate_database(Path(sys.argv[1]), backup_directory=Path(sys.argv[2]))
except migration.MigrationError as error:
    print(str(error), flush=True)
else:
    raise SystemExit("unexpected migration success")
"""
    contender = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            contender_script,
            str(path),
            str(backup_directory),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        env=_subprocess_environment(),
        check=False,
    )
    assert contender.returncode == 0, contender.stderr
    assert "another Redaction Lab process is migrating" in contender.stdout
    assert (backup_directory / part_name).read_bytes() == b"live"

    assert holder.stdin is not None
    holder.stdin.write("x")
    holder.stdin.close()
    holder.wait(timeout=5)
    assert holder.returncode == 0

    restart = _start_migration_process(path, backup_directory)
    assert restart.stdin is not None and restart.stdout is not None
    assert restart.stdout.readline().strip() == "READY"
    restart.stdin.write("x")
    restart.stdin.close()
    restart.wait(timeout=5)
    assert restart.stderr is not None
    assert restart.returncode == 0, restart.stderr.read()
    assert not (backup_directory / part_name).exists()


def test_lock_timeout_precedes_database_or_backup_mutation(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE immutable(value BLOB NOT NULL)")
        connection.execute("INSERT INTO immutable VALUES (?)", (b"original",))
    before = path.read_bytes()
    holder_script = """
import os, sys
from pathlib import Path
from redaction_lab.application import migration
database = Path(sys.argv[1])
directory_fd = os.open(database.parent, os.O_RDONLY | os.O_DIRECTORY)
try:
    with migration._exclusive_migration_lock(directory_fd, database.name, timeout_seconds=2):
        print("READY", flush=True)
        sys.stdin.buffer.read(1)
finally:
    os.close(directory_fd)
"""
    holder = subprocess.Popen(
        [sys.executable, "-B", "-c", holder_script, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_subprocess_environment(),
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "READY"
    contender_script = """
import sys
from pathlib import Path
from redaction_lab.application import migration
migration._MIGRATION_LOCK_TIMEOUT_SECONDS = 0.05
try:
    migration.migrate_database(Path(sys.argv[1]), backup_directory=Path(sys.argv[2]))
except migration.MigrationError as error:
    print(str(error), flush=True)
else:
    raise SystemExit("unexpected migration success")
"""
    contender = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            contender_script,
            str(path),
            str(tmp_path / "backups"),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        env=_subprocess_environment(),
        check=False,
    )
    assert holder.stdin is not None
    holder.stdin.write("x")
    holder.stdin.close()
    holder.wait(timeout=5)

    assert contender.returncode == 0, contender.stderr
    assert "another Redaction Lab process is migrating" in contender.stdout
    assert path.read_bytes() == before
    assert not (tmp_path / "backups").exists()


def test_abrupt_holder_exit_releases_persistent_lock(tmp_path: Path) -> None:
    path = tmp_path / "database.sqlite3"
    holder_script = """
import os, sys
from pathlib import Path
from redaction_lab.application import migration
database = Path(sys.argv[1])
directory_fd = os.open(database.parent, os.O_RDONLY | os.O_DIRECTORY)
with migration._exclusive_migration_lock(directory_fd, database.name, timeout_seconds=2):
    print("READY", flush=True)
    sys.stdin.buffer.read(1)
"""
    holder = subprocess.Popen(
        [sys.executable, "-B", "-c", holder_script, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_subprocess_environment(),
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "READY"
    holder.kill()
    holder.wait(timeout=5)

    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        lock_name = migration_module._migration_lock_name(path.name)
        with migration_module._exclusive_migration_lock(
            directory_fd, path.name, timeout_seconds=0.2
        ):
            assert (tmp_path / lock_name).exists()
    finally:
        os.close(directory_fd)


def test_inherited_lock_survives_parent_exit_until_child_exits(tmp_path: Path) -> None:
    path = tmp_path / "database.sqlite3"
    release = tmp_path / "release-child"
    child_ready = tmp_path / "child-ready"
    child_done = tmp_path / "child-done"
    parent_script = """
import os, subprocess, sys, time
from pathlib import Path
from redaction_lab.application import migration
database, release, ready, done = map(Path, sys.argv[1:5])
directory_fd = os.open(database.parent, os.O_RDONLY | os.O_DIRECTORY)
child_code = '''
import os, sys, time
from pathlib import Path
lock_fd = int(sys.argv[1]); release = Path(sys.argv[2]); ready = Path(sys.argv[3]); done = Path(sys.argv[4])
os.fstat(lock_fd); ready.touch()
while not release.exists(): time.sleep(0.01)
done.touch()
'''
with migration._exclusive_migration_lock(directory_fd, database.name, timeout_seconds=2) as lock_fd:
    subprocess.Popen([sys.executable, '-B', '-c', child_code, str(lock_fd), str(release), str(ready), str(done)], pass_fds=(lock_fd,), close_fds=True)
    while not ready.exists(): time.sleep(0.01)
    print("READY", flush=True)
    os._exit(23)
"""
    parent = subprocess.Popen(
        [
            sys.executable,
            "-B",
            "-c",
            parent_script,
            str(path),
            str(release),
            str(child_ready),
            str(child_done),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_subprocess_environment(),
    )
    assert parent.stdout is not None
    assert parent.stdout.readline().strip() == "READY"
    assert parent.wait(timeout=5) == 23
    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(MigrationError, match="another Redaction Lab process"):
            with migration_module._exclusive_migration_lock(
                directory_fd, path.name, timeout_seconds=0.05
            ):
                pass
        release.touch()
        deadline = time.monotonic() + 2
        while not child_done.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert child_done.exists()
        with migration_module._exclusive_migration_lock(
            directory_fd, path.name, timeout_seconds=0.5
        ):
            pass
    finally:
        os.close(directory_fd)


@pytest.mark.parametrize(
    "unsafe_kind", ["symlink", "directory", "hardlink", "wrong-mode"]
)
def test_unsafe_migration_lock_leaf_fails_before_database_mutation(
    tmp_path: Path, unsafe_kind: str
) -> None:
    path = tmp_path / "database.sqlite3"
    backup_directory = tmp_path / "backups"
    lock_path = tmp_path / migration_module._migration_lock_name(path.name)
    outside = tmp_path / "outside"
    if unsafe_kind == "symlink":
        outside.write_bytes(b"outside")
        lock_path.symlink_to(outside)
    elif unsafe_kind == "directory":
        lock_path.mkdir()
    else:
        outside.write_bytes(b"outside")
        os.chmod(outside, 0o600)
        if unsafe_kind == "hardlink":
            os.link(outside, lock_path)
        else:
            lock_path.write_bytes(b"")
            os.chmod(lock_path, 0o644)

    with pytest.raises(MigrationError, match="migration lock"):
        migrate_database(path, backup_directory=backup_directory)

    assert not path.exists()
    assert not backup_directory.exists()
    if outside.is_file():
        assert outside.read_bytes() == b"outside"


def test_migration_lock_inode_replacement_fails_closed(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "database.sqlite3"
    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    lock_name = migration_module._migration_lock_name(path.name)
    real_flock = migration_module.fcntl.flock
    replaced = False

    def replacing_flock(descriptor, operation):
        nonlocal replaced
        result = real_flock(descriptor, operation)
        if operation & migration_module.fcntl.LOCK_EX and not replaced:
            replaced = True
            os.unlink(lock_name, dir_fd=directory_fd)
            replacement = os.open(
                lock_name,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_fd,
            )
            os.close(replacement)
        return result

    monkeypatch.setattr(migration_module.fcntl, "flock", replacing_flock)
    try:
        with pytest.raises(MigrationError, match="replaced migration lock"):
            with migration_module._exclusive_migration_lock(
                directory_fd, path.name, timeout_seconds=0.1
            ):
                pass
    finally:
        os.close(directory_fd)


def test_migration_lock_wrong_owner_fails_closed(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "database.sqlite3"
    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    lock_fd = migration_module._open_migration_lock(directory_fd, path.name)
    real_fstat = migration_module.os.fstat

    def wrong_owner_fstat(descriptor: int):
        metadata = real_fstat(descriptor)
        if descriptor != lock_fd:
            return metadata
        values = list(metadata)
        values[4] = os.getuid() + 1
        return os.stat_result(values)

    monkeypatch.setattr(migration_module.os, "fstat", wrong_owner_fstat)
    try:
        with pytest.raises(MigrationError, match="migration lock"):
            migration_module._validate_migration_lock(
                directory_fd, lock_fd, path.name
            )
    finally:
        os.close(lock_fd)
        os.close(directory_fd)


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
