"""Platform-resolved paths with no checkout or developer-machine dependency."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Mapping


@dataclass(frozen=True)
class ApplicationPaths:
    root: Path
    database: Path
    artifacts: Path
    temporary: Path
    logs: Path
    backups: Path


def resolve_paths(environment: Mapping[str, str] | None = None) -> ApplicationPaths:
    env = os.environ if environment is None else environment
    explicit = env.get("REDACTION_LAB_HOME")
    if explicit is not None:
        if not explicit.strip():
            raise ValueError("REDACTION_LAB_HOME must be a nonblank absolute path")
        root = Path(explicit).expanduser()
        if not root.is_absolute():
            raise ValueError("REDACTION_LAB_HOME must be an absolute path")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "RedactionLab"
    else:
        data_home = env.get("XDG_DATA_HOME")
        root = (
            Path(data_home).expanduser() / "redaction-lab"
            if data_home
            else Path.home() / ".local" / "share" / "redaction-lab"
        )
    root = root.resolve(strict=False)
    return ApplicationPaths(
        root=root,
        database=root / "redaction-lab.sqlite3",
        artifacts=root / "artifacts",
        temporary=root / "temporary",
        logs=root / "logs",
        backups=root / "backups",
    )


def initialize_paths(paths: ApplicationPaths) -> ApplicationPaths:
    for directory in (
        paths.root,
        paths.artifacts,
        paths.temporary,
        paths.logs,
        paths.backups,
    ):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.chmod(0o700)
        if directory.is_symlink():
            raise ValueError("application directories must not be symbolic links")
    return paths
