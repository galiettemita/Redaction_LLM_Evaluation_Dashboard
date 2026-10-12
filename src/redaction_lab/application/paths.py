"""Portable application paths with descriptor-anchored confinement."""

from __future__ import annotations

from dataclasses import dataclass
import errno
import os
from pathlib import Path
import stat
import sys
from typing import Iterable, Mapping


_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)


@dataclass(frozen=True)
class ApplicationPaths:
    root: Path
    database: Path
    artifacts: Path
    temporary: Path
    logs: Path
    backups: Path


def _require_secure_primitives() -> None:
    if not getattr(os, "O_DIRECTORY", 0) or not getattr(os, "O_NOFOLLOW", 0):
        raise ValueError("secure no-follow directory operations are unavailable")


def _absolute_components(path: Path) -> tuple[str, ...]:
    if not path.is_absolute() or path == Path("/"):
        raise ValueError("application paths must be absolute and must not be root")
    parts = path.parts
    if any(part in {".", "..", ""} for part in parts[1:]):
        raise ValueError("application paths must not contain parent traversal")
    return tuple(parts[1:])


def _raise_path_error(path: Path, error: BaseException | None = None) -> None:
    message = f"application path contains a symbolic link or non-directory: {path}"
    if error is None:
        raise ValueError(message)
    raise ValueError(message) from error


def _audit_directory(path: Path, *, require_owner: bool) -> None:
    """Read-only no-follow traversal. Missing suffixes are acceptable."""

    _require_secure_primitives()
    components = _absolute_components(path)
    descriptor = os.open("/", _DIRECTORY_FLAGS)
    try:
        for index, component in enumerate(components):
            try:
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                return
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                _raise_path_error(path)
            try:
                child = os.open(component, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as error:
                if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                    _raise_path_error(path, error)
                raise
            os.close(descriptor)
            descriptor = child
            if index == len(components) - 1 and require_owner:
                if os.fstat(descriptor).st_uid != os.getuid():
                    raise ValueError("application directory must be owned by the current user")
    finally:
        os.close(descriptor)


def preflight_directories(paths: Iterable[Path]) -> None:
    """Validate every managed path before any caller performs mutation."""

    for path in paths:
        _audit_directory(Path(path), require_owner=True)


def open_verified_directory(path: Path, *, create: bool) -> int:
    """Open an absolute directory without following any path component."""

    path = Path(path)
    components = _absolute_components(path)
    descriptor = os.open("/", _DIRECTORY_FLAGS)
    try:
        for component in components:
            try:
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, mode=0o700, dir_fd=descriptor)
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                _raise_path_error(path)
            try:
                child = os.open(component, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as error:
                if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                    _raise_path_error(path, error)
                raise
            os.close(descriptor)
            descriptor = child
        if os.fstat(descriptor).st_uid != os.getuid():
            raise ValueError("application directory must be owned by the current user")
        os.fchmod(descriptor, 0o700)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def resolve_paths(environment: Mapping[str, str] | None = None) -> ApplicationPaths:
    env = os.environ if environment is None else environment
    explicit = env.get("REDACTION_LAB_HOME")
    if explicit is not None:
        if not explicit.strip():
            raise ValueError("REDACTION_LAB_HOME must be a nonblank absolute path")
        expanded = os.path.expanduser(explicit)
        raw_parts = expanded.split(os.sep)
        if not os.path.isabs(expanded) or any(part in {".", ".."} for part in raw_parts):
            raise ValueError("REDACTION_LAB_HOME must be absolute without parent traversal")
        root = Path(expanded)
        if root == Path("/"):
            raise ValueError("REDACTION_LAB_HOME must not be filesystem root")
        try:
            _audit_directory(root, require_owner=True)
        except ValueError as error:
            raise ValueError(f"REDACTION_LAB_HOME {error}") from error
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "RedactionLab"
    else:
        data_home = env.get("XDG_DATA_HOME")
        root = (
            Path(data_home).expanduser() / "redaction-lab"
            if data_home
            else Path.home() / ".local" / "share" / "redaction-lab"
        )
    _absolute_components(root)
    return ApplicationPaths(
        root=root,
        database=root / "redaction-lab.sqlite3",
        artifacts=root / "artifacts",
        temporary=root / "temporary",
        logs=root / "logs",
        backups=root / "backups",
    )


def initialize_paths(paths: ApplicationPaths) -> ApplicationPaths:
    managed = (paths.root, paths.artifacts, paths.temporary, paths.logs, paths.backups)
    if any(path.parent != paths.root for path in managed[1:]):
        raise ValueError("managed application directories must be direct children of the root")
    preflight_directories(managed)
    for directory in managed:
        descriptor = open_verified_directory(directory, create=True)
        os.close(descriptor)
    return paths
