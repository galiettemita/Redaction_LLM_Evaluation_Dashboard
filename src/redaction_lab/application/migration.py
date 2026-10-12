"""Additive, checksummed SQLite migrations with verified pre-migration backup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sqlite3


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


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _verified_backup(path: Path, backup_directory: Path) -> Path:
    backup_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup_directory.chmod(0o700)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_directory / f"{path.name}.{stamp}.bak"
    source = sqlite3.connect(path)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    destination.chmod(0o600)
    with sqlite3.connect(destination) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            destination.unlink(missing_ok=True)
            raise MigrationError("pre-migration backup integrity check failed")
    return destination


def migrate_database(path: Path, *, backup_directory: Path) -> MigrationResult:
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    existed = path.exists() and path.stat().st_size > 0
    connection = sqlite3.connect(path, isolation_level=None)
    backup_path: Path | None = None
    applied: list[int] = []
    try:
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
                connection.close()
                backup_path = _verified_backup(path, Path(backup_directory))
                connection = sqlite3.connect(path, isolation_level=None)
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
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise MigrationError("database integrity check failed")
    finally:
        connection.close()
    return MigrationResult(tuple(applied), backup_path)
