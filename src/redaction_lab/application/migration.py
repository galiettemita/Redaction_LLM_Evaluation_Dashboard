"""Additive migrations with descriptor-confined SQLite access and backups."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import os
from pathlib import Path
import sqlite3
import stat
from threading import RLock

from redaction_lab.application.paths import open_verified_directory, preflight_directories


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Migration:
    version: int
    sql: str

    @property
    def checksum(self) -> str:
        return sha256(self.sql.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MigrationResult:
    applied_versions: tuple[int, ...]
    backup_path: Path | None


_MIGRATION_PATH = Path(__file__).with_name("migrations") / "0001.sql"
MIGRATIONS = (Migration(1, _MIGRATION_PATH.read_text(encoding="utf-8")),)
_CWD_LOCK = RLock()
_FILE_FLAGS = os.O_RDWR | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _integrity_check(connection: sqlite3.Connection) -> bool:
    return connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@contextmanager
def _anchored_working_directory(directory_fd: int):
    """Temporarily anchor SQLite relative paths to an already-verified inode.

    Migration runs synchronously during store construction. The process-wide
    lock prevents two Redaction Lab migrations from changing cwd concurrently,
    and the original cwd descriptor is restored on every exit path.
    """

    with _CWD_LOCK:
        previous = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fchdir(directory_fd)
            yield
        finally:
            os.fchdir(previous)
            os.close(previous)


def _open_database_leaf(directory_fd: int, name: str) -> tuple[int, bool]:
    try:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        descriptor = os.open(
            name,
            _FILE_FLAGS | os.O_CREAT | os.O_EXCL,
            0o600,
            dir_fd=directory_fd,
        )
        return descriptor, False
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise MigrationError("database path must not be a symbolic link")
    descriptor = os.open(name, _FILE_FLAGS, dir_fd=directory_fd)
    return descriptor, metadata.st_size > 0


def _validate_database_leaf(directory_fd: int, name: str) -> None:
    """Reject an unsafe existing leaf before creating any managed directory."""

    try:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise MigrationError("database path must not be a symbolic link")


def _connect_anchored(name: str, expected_fd: int) -> sqlite3.Connection:
    connection = sqlite3.connect(name, isolation_level=None)
    current = os.stat(name, follow_symlinks=False)
    expected = os.fstat(expected_fd)
    if (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino):
        connection.close()
        raise MigrationError("database pathname was replaced during open")
    return connection


def _verified_backup(
    source: sqlite3.Connection,
    *,
    database_name: str,
    backup_directory: Path,
    backup_fd: int,
) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    name = f"{database_name}.{stamp}.bak"
    descriptor = os.open(
        name,
        _FILE_FLAGS | os.O_CREAT | os.O_EXCL,
        0o600,
        dir_fd=backup_fd,
    )
    destination: sqlite3.Connection | None = None
    try:
        destination = sqlite3.connect(f"/dev/fd/{descriptor}", isolation_level=None)
        destination.execute("PRAGMA journal_mode=OFF")
        source.backup(destination)
        destination.close()
        destination = None
        os.fsync(descriptor)
        verifier = sqlite3.connect(
            f"file:/dev/fd/{descriptor}?mode=ro&immutable=1",
            uri=True,
        )
        try:
            if not _integrity_check(verifier):
                raise MigrationError("pre-migration backup integrity check failed")
        finally:
            verifier.close()
        os.fchmod(descriptor, 0o600)
        os.fsync(backup_fd)
        return backup_directory / name
    except Exception:
        if destination is not None:
            destination.close()
        os.close(descriptor)
        descriptor = -1
        try:
            os.unlink(name, dir_fd=backup_fd)
            os.fsync(backup_fd)
        except FileNotFoundError:
            pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def migrate_database(path: Path, *, backup_directory: Path) -> MigrationResult:
    path = Path(path)
    backup_directory = Path(backup_directory)
    if not path.is_absolute() or not backup_directory.is_absolute():
        raise MigrationError("database and backup paths must be absolute")
    try:
        preflight_directories((path.parent, backup_directory))
        database_directory_fd = open_verified_directory(path.parent, create=True)
    except ValueError as error:
        raise MigrationError(str(error)) from error

    database_fd = -1
    backup_fd = -1
    connection: sqlite3.Connection | None = None
    backup_path: Path | None = None
    applied: list[int] = []
    try:
        _validate_database_leaf(database_directory_fd, path.name)
        backup_fd = open_verified_directory(backup_directory, create=True)
        database_fd, existed = _open_database_leaf(database_directory_fd, path.name)
        with _anchored_working_directory(database_directory_fd):
            connection = _connect_anchored(path.name, database_fd)
            tables = _table_names(connection)
            recorded: dict[int, str] = {}
            if "schema_migrations" in tables:
                recorded = {
                    int(row[0]): str(row[1])
                    for row in connection.execute(
                        "SELECT version, checksum FROM schema_migrations"
                    )
                }
            for migration in MIGRATIONS:
                known = recorded.get(migration.version)
                if known is not None:
                    if known != migration.checksum:
                        raise MigrationError("schema migration checksum mismatch")
                    continue
                if existed and backup_path is None and tables:
                    backup_path = _verified_backup(
                        connection,
                        database_name=path.name,
                        backup_directory=backup_directory,
                        backup_fd=backup_fd,
                    )
                applied_at = datetime.now(UTC).isoformat().replace("'", "''")
                script = (
                    "BEGIN IMMEDIATE;\n"
                    + migration.sql
                    + "\nINSERT INTO schema_migrations(version, checksum, applied_at) VALUES ("
                    + f"{migration.version}, '{migration.checksum}', '{applied_at}');\nCOMMIT;"
                )
                try:
                    connection.executescript(script)
                except sqlite3.Error as error:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise MigrationError(f"migration {migration.version} failed") from error
                applied.append(migration.version)
                tables = _table_names(connection)
            if not _integrity_check(connection):
                raise MigrationError("database integrity check failed")
            connection.close()
            connection = None
            os.fsync(database_fd)
            os.fsync(database_directory_fd)
    finally:
        if connection is not None:
            connection.close()
        if database_fd >= 0:
            os.close(database_fd)
        if backup_fd >= 0:
            os.close(backup_fd)
        os.close(database_directory_fd)
    return MigrationResult(tuple(applied), backup_path)
