"""Additive migrations executed in a descriptor-confined helper process."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
import errno
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from typing import Any, Iterator, Sequence

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
_FILE_FLAGS = os.O_RDWR | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
_HELPER_PROTOCOL = "redaction-lab-sqlite-migration-v1"
_HELPER_ARGUMENT = "--isolated-sqlite-migration-helper"
_HELPER_TIMEOUT_SECONDS = 120.0
_MAX_STDOUT_BYTES = 64 * 1024
_MAX_STDERR_BYTES = 8 * 1024
_BACKUP_STAMP_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{12}Z$")
_MIGRATION_LOCK = threading.RLock()
_MIGRATION_LOCK_TIMEOUT_SECONDS = 125.0
_LOCK_FLAGS = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _integrity_check(connection: sqlite3.Connection) -> bool:
    return connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _valid_leaf_name(name: str) -> bool:
    return (
        bool(name)
        and name not in {".", ".."}
        and Path(name).name == name
        and "/" not in name
        and "\x00" not in name
    )


def _migration_lock_name(database_name: str) -> str:
    if not _valid_leaf_name(database_name):
        raise MigrationError("invalid database leaf name")
    digest = sha256(database_name.encode("utf-8")).hexdigest()
    return f".redaction-lab-migration-{digest}.lock"


def _validate_migration_lock(
    database_directory_fd: int,
    lock_fd: int,
    database_name: str,
) -> os.stat_result:
    try:
        directory = os.fstat(database_directory_fd)
        lock = os.fstat(lock_fd)
        name = _migration_lock_name(database_name)
        current = os.stat(name, dir_fd=database_directory_fd, follow_symlinks=False)
    except OSError as error:
        raise MigrationError("unsafe or replaced migration lock file") from error
    if (
        not stat.S_ISDIR(directory.st_mode)
        or not stat.S_ISREG(lock.st_mode)
        or lock.st_uid != os.getuid()
        or lock.st_dev != directory.st_dev
        or lock.st_nlink != 1
        or stat.S_IMODE(lock.st_mode) != 0o600
        or (current.st_dev, current.st_ino) != (lock.st_dev, lock.st_ino)
    ):
        raise MigrationError("unsafe or replaced migration lock file")
    return lock


def _open_migration_lock(database_directory_fd: int, database_name: str) -> int:
    name = _migration_lock_name(database_name)
    created = False
    try:
        descriptor = os.open(
            name,
            _LOCK_FLAGS | os.O_EXCL,
            0o600,
            dir_fd=database_directory_fd,
        )
        created = True
    except FileExistsError:
        try:
            descriptor = os.open(
                name,
                os.O_RDWR | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
                dir_fd=database_directory_fd,
            )
        except OSError as error:
            raise MigrationError("unsafe migration lock file") from error
    except OSError as error:
        raise MigrationError("cannot safely create migration lock file") from error
    try:
        if created:
            os.fchmod(descriptor, 0o600)
            os.fsync(descriptor)
            os.fsync(database_directory_fd)
        _validate_migration_lock(database_directory_fd, descriptor, database_name)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


@contextmanager
def _exclusive_migration_lock(
    database_directory_fd: int,
    database_name: str,
    *,
    timeout_seconds: float | None = None,
) -> Iterator[int]:
    timeout = (
        _MIGRATION_LOCK_TIMEOUT_SECONDS
        if timeout_seconds is None
        else timeout_seconds
    )
    if timeout < 0:
        raise MigrationError("migration lock timeout must not be negative")
    descriptor = _open_migration_lock(database_directory_fd, database_name)
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise MigrationError("migration lock acquisition failed") from error
                if time.monotonic() >= deadline:
                    raise MigrationError(
                        "another Redaction Lab process is migrating this database; "
                        "retry after that process exits"
                    ) from error
                time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        _validate_migration_lock(database_directory_fd, descriptor, database_name)
        yield descriptor
    finally:
        try:
            if acquired:
                _validate_migration_lock(
                    database_directory_fd, descriptor, database_name
                )
        finally:
            try:
                if acquired:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)


def _require_inherited_descriptors(
    database_directory_fd: int,
    database_fd: int,
    backup_fd: int,
    lock_fd: int,
    database_name: str,
) -> tuple[os.stat_result, os.stat_result, os.stat_result]:
    if len({database_directory_fd, database_fd, backup_fd, lock_fd}) != 4:
        raise MigrationError("helper descriptors must be distinct")
    if not _valid_leaf_name(database_name):
        raise MigrationError("invalid database leaf name")
    database_directory = os.fstat(database_directory_fd)
    database = os.fstat(database_fd)
    backup_directory = os.fstat(backup_fd)
    if not stat.S_ISDIR(database_directory.st_mode) or not stat.S_ISDIR(
        backup_directory.st_mode
    ):
        raise MigrationError("helper directory descriptor is not a directory")
    if not stat.S_ISREG(database.st_mode):
        raise MigrationError("helper database descriptor is not a regular file")
    if any(
        metadata.st_uid != os.getuid()
        for metadata in (database_directory, database, backup_directory)
    ):
        raise MigrationError("helper descriptor ownership mismatch")
    current = os.stat(
        database_name,
        dir_fd=database_directory_fd,
        follow_symlinks=False,
    )
    if (current.st_dev, current.st_ino) != (database.st_dev, database.st_ino):
        raise MigrationError("database pathname was replaced before helper open")
    _validate_migration_lock(database_directory_fd, lock_fd, database_name)
    return database_directory, database, backup_directory


def _open_database_leaf(directory_fd: int, name: str) -> tuple[int, bool]:
    try:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        try:
            descriptor = os.open(
                name,
                _FILE_FLAGS | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory_fd,
            )
            return descriptor, False
        except FileExistsError:
            # A concurrent initializer may have created the leaf after stat.
            # Re-enter the no-follow validation path before opening it.
            metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
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
        raise MigrationError("database pathname was replaced during helper open")
    return connection


def _incomplete_backup_pattern(database_name: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\.{re.escape(database_name)}\.[0-9]{{8}}T[0-9]{{12}}Z\.[0-9a-f]{{16}}\.bak\.part$"
    )


def _cleanup_incomplete_backups(backup_fd: int, database_name: str) -> None:
    pattern = _incomplete_backup_pattern(database_name)
    candidates = [name for name in os.listdir(backup_fd) if pattern.fullmatch(name)]
    for name in candidates:
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=backup_fd)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
                raise MigrationError("unsafe incomplete backup entry")
        finally:
            os.close(descriptor)
    for name in candidates:
        os.unlink(name, dir_fd=backup_fd)
    if candidates:
        os.fsync(backup_fd)


def _verified_backup(
    source: sqlite3.Connection,
    *,
    database_name: str,
    backup_fd: int,
) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    final_name = f"{database_name}.{stamp}.bak"
    temporary_name = f".{database_name}.{stamp}.{secrets.token_hex(8)}.bak.part"
    descriptor = os.open(
        temporary_name,
        _FILE_FLAGS | os.O_CREAT | os.O_EXCL,
        0o600,
        dir_fd=backup_fd,
    )
    destination: sqlite3.Connection | None = None
    published = False
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
        os.fsync(descriptor)
        os.link(
            temporary_name,
            final_name,
            src_dir_fd=backup_fd,
            dst_dir_fd=backup_fd,
            follow_symlinks=False,
        )
        published = True
        os.fsync(backup_fd)
        os.unlink(temporary_name, dir_fd=backup_fd)
        os.fsync(backup_fd)
        return final_name
    except Exception:
        if destination is not None:
            destination.close()
        try:
            os.unlink(temporary_name, dir_fd=backup_fd)
            os.fsync(backup_fd)
        except FileNotFoundError:
            pass
        if published:
            raise MigrationError("backup published but temporary cleanup failed")
        raise
    finally:
        os.close(descriptor)


def _apply_migrations(
    connection: sqlite3.Connection,
    *,
    existed: bool,
    database_name: str,
    backup_fd: int,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> tuple[tuple[int, ...], str | None]:
    tables = _table_names(connection)
    recorded: dict[int, str] = {}
    if "schema_migrations" in tables:
        recorded = {
            int(row[0]): str(row[1])
            for row in connection.execute(
                "SELECT version, checksum FROM schema_migrations"
            )
        }
    applied: list[int] = []
    backup_name: str | None = None
    for migration in migrations:
        known = recorded.get(migration.version)
        if known is not None:
            if known != migration.checksum:
                raise MigrationError("schema migration checksum mismatch")
            continue
        if existed and backup_name is None and tables:
            backup_name = _verified_backup(
                connection,
                database_name=database_name,
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
    return tuple(applied), backup_name


def _run_helper(
    database_directory_fd: int,
    database_fd: int,
    backup_fd: int,
    lock_fd: int,
    database_name: str,
    existed: bool,
) -> dict[str, Any]:
    if threading.active_count() != 1:
        raise MigrationError("migration helper must be single-threaded")
    _, database_identity, _ = _require_inherited_descriptors(
        database_directory_fd,
        database_fd,
        backup_fd,
        lock_fd,
        database_name,
    )
    os.set_inheritable(lock_fd, False)
    _cleanup_incomplete_backups(backup_fd, database_name)
    os.fchdir(database_directory_fd)
    connection: sqlite3.Connection | None = None
    try:
        connection = _connect_anchored(database_name, database_fd)
        applied, backup_name = _apply_migrations(
            connection,
            existed=existed,
            database_name=database_name,
            backup_fd=backup_fd,
        )
        connection.close()
        connection = None
        os.fsync(database_fd)
        os.fsync(database_directory_fd)
    finally:
        if connection is not None:
            connection.close()
    return {
        "protocol": _HELPER_PROTOCOL,
        "status": "ok",
        "applied_versions": list(applied),
        "backup_name": backup_name,
        "database_device": database_identity.st_dev,
        "database_inode": database_identity.st_ino,
    }


def _collect_bounded_output(process: subprocess.Popen[bytes]) -> tuple[bytes, bytes]:
    selector = selectors.DefaultSelector()
    assert process.stdout is not None and process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ, ("stdout", _MAX_STDOUT_BYTES))
    selector.register(process.stderr, selectors.EVENT_READ, ("stderr", _MAX_STDERR_BYTES))
    output = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + _HELPER_TIMEOUT_SECONDS
    try:
        while selector.get_map() or process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MigrationError("isolated migration helper timed out")
            for key, _ in selector.select(min(remaining, 0.1)):
                label, limit = key.data
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                if len(output[label]) + len(chunk) > limit:
                    raise MigrationError(f"isolated migration helper {label} exceeded limit")
                output[label].extend(chunk)
        return bytes(output["stdout"]), bytes(output["stderr"])
    except Exception:
        if process.poll() is None:
            process.kill()
        raise
    finally:
        selector.close()
        if process.poll() is None:
            process.kill()
        process.wait()


def _invoke_helper(
    database_directory_fd: int,
    database_fd: int,
    backup_fd: int,
    lock_fd: int,
    database_name: str,
    existed: bool,
) -> dict[str, Any]:
    environment = os.environ.copy()
    # Resolve the application package before launch so helper discovery is
    # independent of the caller's cwd. PYTHONSAFEPATH also keeps that cwd from
    # becoming an import source for this authority-bearing helper.
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    environment["PYTHONSAFEPATH"] = "1"
    command = [
        sys.executable,
        "-B",
        "-m",
        __name__,
        _HELPER_ARGUMENT,
        str(database_directory_fd),
        str(database_fd),
        str(backup_fd),
        str(lock_fd),
        database_name,
        "1" if existed else "0",
    ]
    process = subprocess.Popen(
        command,
        shell=False,
        cwd=None,
        close_fds=True,
        pass_fds=(database_directory_fd, database_fd, backup_fd, lock_fd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    stdout, stderr = _collect_bounded_output(process)
    return _parse_helper_response(stdout, stderr, process.returncode)


def _parse_helper_response(
    stdout: bytes, stderr: bytes, returncode: int
) -> dict[str, Any]:
    if returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        raise MigrationError(
            "isolated migration helper failed"
            + (f": {detail}" if detail else "")
        )
    if stderr:
        raise MigrationError("isolated migration helper produced unexpected stderr")
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise MigrationError("isolated migration helper returned duplicate fields")
            result[key] = value
        return result

    try:
        payload = json.loads(stdout, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MigrationError("isolated migration helper returned invalid JSON") from error
    required = {
        "protocol",
        "status",
        "applied_versions",
        "backup_name",
        "database_device",
        "database_inode",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise MigrationError("isolated migration helper returned an invalid schema")
    if payload["protocol"] != _HELPER_PROTOCOL or payload["status"] != "ok":
        raise MigrationError("isolated migration helper protocol mismatch")
    return payload


def _validate_helper_result(
    payload: dict[str, Any],
    *,
    database_fd: int,
    backup_fd: int,
    database_name: str,
) -> tuple[tuple[int, ...], str | None]:
    identity = os.fstat(database_fd)
    if (
        type(payload["database_device"]) is not int
        or type(payload["database_inode"]) is not int
        or (payload["database_device"], payload["database_inode"])
        != (identity.st_dev, identity.st_ino)
    ):
        raise MigrationError("isolated migration helper database identity mismatch")
    versions = payload["applied_versions"]
    if (
        not isinstance(versions, list)
        or any(type(version) is not int for version in versions)
        or versions != sorted(set(versions))
        or not set(versions).issubset({migration.version for migration in MIGRATIONS})
    ):
        raise MigrationError("isolated migration helper returned invalid versions")
    backup_name = payload["backup_name"]
    if backup_name is not None:
        prefix = f"{database_name}."
        suffix = ".bak"
        if (
            not isinstance(backup_name, str)
            or not backup_name.startswith(prefix)
            or not backup_name.endswith(suffix)
            or not _BACKUP_STAMP_PATTERN.fullmatch(
                backup_name[len(prefix) : -len(suffix)]
            )
        ):
            raise MigrationError("isolated migration helper returned unsafe backup name")
        descriptor = os.open(backup_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=backup_fd)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
                raise MigrationError("isolated migration helper backup is unsafe")
        finally:
            os.close(descriptor)
    return tuple(versions), backup_name


def _migrate_database(path: Path, *, backup_directory: Path) -> MigrationResult:
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
    try:
        with _exclusive_migration_lock(database_directory_fd, path.name) as lock_fd:
            _validate_database_leaf(database_directory_fd, path.name)
            backup_fd = open_verified_directory(backup_directory, create=True)
            database_fd, existed = _open_database_leaf(database_directory_fd, path.name)
            before = os.fstat(database_fd)
            payload = _invoke_helper(
                database_directory_fd,
                database_fd,
                backup_fd,
                lock_fd,
                path.name,
                existed,
            )
            current = os.stat(
                path.name,
                dir_fd=database_directory_fd,
                follow_symlinks=False,
            )
            if (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino):
                raise MigrationError("database pathname was replaced during migration")
            applied, backup_name = _validate_helper_result(
                payload,
                database_fd=database_fd,
                backup_fd=backup_fd,
                database_name=path.name,
            )
            return MigrationResult(
                applied,
                backup_directory / backup_name if backup_name is not None else None,
            )
    finally:
        if database_fd >= 0:
            os.close(database_fd)
        if backup_fd >= 0:
            os.close(backup_fd)
        os.close(database_directory_fd)


def migrate_database(path: Path, *, backup_directory: Path) -> MigrationResult:
    """Migrate one database without mutating the parent process cwd."""

    with _MIGRATION_LOCK:
        return _migrate_database(path, backup_directory=backup_directory)


def _helper_main(arguments: Sequence[str]) -> int:
    if len(arguments) != 7 or arguments[0] != _HELPER_ARGUMENT:
        return 2
    try:
        database_directory_fd, database_fd, backup_fd, lock_fd = (
            int(value) for value in arguments[1:5]
        )
        if arguments[6] not in {"0", "1"}:
            raise MigrationError("invalid existing-database marker")
        payload = _run_helper(
            database_directory_fd,
            database_fd,
            backup_fd,
            lock_fd,
            arguments[5],
            arguments[6] == "1",
        )
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        if len(encoded) > _MAX_STDOUT_BYTES:
            raise MigrationError("helper response exceeded protocol limit")
        os.write(sys.stdout.fileno(), encoded)
        return 0
    except Exception as error:
        message = f"{type(error).__name__}: {error}".encode("utf-8", errors="replace")
        os.write(sys.stderr.fileno(), message[:_MAX_STDERR_BYTES])
        return 1


if __name__ == "__main__":
    raise SystemExit(_helper_main(sys.argv[1:]))
