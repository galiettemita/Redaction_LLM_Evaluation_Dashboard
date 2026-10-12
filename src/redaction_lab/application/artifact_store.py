"""Crash-conscious, descriptor-confined storage for uploaded PDF bytes."""

from __future__ import annotations

from dataclasses import dataclass
import errno
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
import time
from typing import Iterable
from uuid import uuid4

from redaction_lab.application.config import MAX_PDF_BYTES, TEMPORARY_RETENTION_SECONDS
from redaction_lab.application.paths import open_verified_directory, preflight_directories


_KEY = re.compile(r"^sha256/([0-9a-f]{2})/([0-9a-f]{64})\.pdf$")
_PREFIX = re.compile(r"^[0-9a-f]{2}$")
_FILE_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
_DIRECTORY_FLAGS = _FILE_FLAGS | getattr(os, "O_DIRECTORY", 0)


class ArtifactIntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactRecord:
    logical_key: str
    sha256: str
    byte_size: int


@dataclass(frozen=True)
class ArtifactRecovery:
    removed_temporaries: tuple[Path, ...]
    orphan_keys: tuple[str, ...]


class ArtifactStore:
    def __init__(
        self,
        artifact_root: Path,
        temporary_root: Path,
        *,
        max_bytes: int = MAX_PDF_BYTES,
    ) -> None:
        self.artifact_root = Path(artifact_root)
        self.temporary_root = Path(temporary_root)
        self.max_bytes = max_bytes
        try:
            preflight_directories((self.artifact_root, self.temporary_root))
            self._artifact_fd = open_verified_directory(self.artifact_root, create=True)
            try:
                self._temporary_fd = open_verified_directory(self.temporary_root, create=True)
            except Exception:
                os.close(self._artifact_fd)
                raise
        except ValueError as error:
            raise ArtifactIntegrityError(str(error)) from error

    def close(self) -> None:
        for attribute in ("_artifact_fd", "_temporary_fd"):
            descriptor = getattr(self, attribute, None)
            if descriptor is not None:
                os.close(descriptor)
                setattr(self, attribute, None)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def _key(digest: str) -> str:
        return f"sha256/{digest[:2]}/{digest}.pdf"

    @staticmethod
    def _parts(logical_key: str) -> tuple[str, str]:
        match = _KEY.fullmatch(logical_key)
        if match is None or match.group(1) != match.group(2)[:2]:
            raise ValueError("invalid artifact logical key")
        return match.group(1), f"{match.group(2)}.pdf"

    def path_for(self, logical_key: str) -> Path:
        self._parts(logical_key)
        return self.artifact_root / logical_key

    @staticmethod
    def _open_directory(parent_fd: int, name: str, *, create: bool) -> int:
        try:
            metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            if not create:
                raise
            os.mkdir(name, mode=0o700, dir_fd=parent_fd)
            metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ArtifactIntegrityError("artifact parent must not be a symbolic link")
        try:
            descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        except OSError as error:
            if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ArtifactIntegrityError(
                    "artifact parent must not be a symbolic link"
                ) from error
            raise
        os.fchmod(descriptor, 0o700)
        return descriptor

    def _open_prefix(self, prefix: str, *, create: bool) -> tuple[int, int]:
        sha_fd = self._open_directory(self._artifact_fd, "sha256", create=create)
        try:
            prefix_fd = self._open_directory(sha_fd, prefix, create=create)
        except Exception:
            os.close(sha_fd)
            raise
        return sha_fd, prefix_fd

    @staticmethod
    def _open_regular(parent_fd: int, name: str) -> int:
        try:
            descriptor = os.open(name, _FILE_FLAGS, dir_fd=parent_fd)
        except OSError as error:
            if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ArtifactIntegrityError("artifact leaf must not be a symbolic link") from error
            raise
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            raise ArtifactIntegrityError("artifact leaf must be a regular file")
        return descriptor

    def _read_fd(self, descriptor: int) -> bytes:
        value = bytearray()
        while len(value) <= self.max_bytes:
            chunk = os.read(descriptor, min(65_536, self.max_bytes + 1 - len(value)))
            if not chunk:
                break
            value.extend(chunk)
        return bytes(value)

    def _verify_existing(self, prefix_fd: int, name: str, digest: str, size: int) -> None:
        descriptor = self._open_regular(prefix_fd, name)
        try:
            value = self._read_fd(descriptor)
        finally:
            os.close(descriptor)
        if len(value) != size or sha256(value).hexdigest() != digest:
            raise ArtifactIntegrityError("existing artifact digest mismatch")

    def publish(self, chunks: Iterable[bytes]) -> ArtifactRecord:
        temporary_name = f"{uuid4().hex}.part"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(temporary_name, flags, 0o600, dir_fd=self._temporary_fd)
        digest = sha256()
        size = 0
        signature = bytearray()
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                for chunk in chunks:
                    if not isinstance(chunk, bytes):
                        raise TypeError("upload chunks must be bytes")
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError("PDF exceeds the 25 MiB size limit")
                    if len(signature) < 5:
                        signature.extend(chunk[: 5 - len(signature)])
                    digest.update(chunk)
                    handle.write(chunk)
                if bytes(signature) != b"%PDF-":
                    raise ValueError("upload does not have a PDF signature")
                handle.flush()
                os.fsync(handle.fileno())
            hexdigest = digest.hexdigest()
            logical_key = self._key(hexdigest)
            prefix, destination_name = self._parts(logical_key)
            sha_fd, prefix_fd = self._open_prefix(prefix, create=True)
            try:
                try:
                    os.link(
                        temporary_name,
                        destination_name,
                        src_dir_fd=self._temporary_fd,
                        dst_dir_fd=prefix_fd,
                        follow_symlinks=False,
                    )
                    os.fsync(prefix_fd)
                except FileExistsError:
                    self._verify_existing(prefix_fd, destination_name, hexdigest, size)
                except OSError as error:
                    if error.errno == errno.EXDEV:
                        raise ArtifactIntegrityError(
                            "artifact and temporary roots must share a filesystem"
                        ) from error
                    raise
            finally:
                os.close(prefix_fd)
                os.close(sha_fd)
            os.unlink(temporary_name, dir_fd=self._temporary_fd)
            os.fsync(self._temporary_fd)
            return ArtifactRecord(logical_key, hexdigest, size)
        except Exception:
            try:
                os.unlink(temporary_name, dir_fd=self._temporary_fd)
            except FileNotFoundError:
                pass
            raise

    def read(self, logical_key: str, *, expected_sha256: str) -> bytes:
        prefix, name = self._parts(logical_key)
        try:
            sha_fd, prefix_fd = self._open_prefix(prefix, create=False)
        except (FileNotFoundError, NotADirectoryError) as error:
            raise ArtifactIntegrityError("artifact path is missing or invalid") from error
        try:
            descriptor = self._open_regular(prefix_fd, name)
            try:
                result = self._read_fd(descriptor)
            finally:
                os.close(descriptor)
        finally:
            os.close(prefix_fd)
            os.close(sha_fd)
        if len(result) > self.max_bytes or sha256(result).hexdigest() != expected_sha256:
            raise ArtifactIntegrityError("artifact digest or size integrity failure")
        return result

    def recover(
        self,
        *,
        referenced_keys: set[str],
        now_epoch: float | None = None,
        temporary_ttl_seconds: int = TEMPORARY_RETENTION_SECONDS,
    ) -> ArtifactRecovery:
        now = time.time() if now_epoch is None else now_epoch
        stale: list[str] = []
        for name in os.listdir(self._temporary_fd):
            if not name.endswith(".part"):
                continue
            try:
                descriptor = self._open_regular(self._temporary_fd, name)
            except ArtifactIntegrityError as error:
                raise ArtifactIntegrityError("temporary entry must not be a symbolic link") from error
            try:
                if now - os.fstat(descriptor).st_mtime >= temporary_ttl_seconds:
                    stale.append(name)
            finally:
                os.close(descriptor)

        orphans: list[str] = []
        try:
            sha_fd = self._open_directory(self._artifact_fd, "sha256", create=False)
        except FileNotFoundError:
            sha_fd = None
        if sha_fd is not None:
            try:
                for prefix in os.listdir(sha_fd):
                    if not _PREFIX.fullmatch(prefix):
                        continue
                    prefix_fd = self._open_directory(sha_fd, prefix, create=False)
                    try:
                        for name in os.listdir(prefix_fd):
                            logical_key = f"sha256/{prefix}/{name}"
                            if not _KEY.fullmatch(logical_key):
                                continue
                            descriptor = self._open_regular(prefix_fd, name)
                            os.close(descriptor)
                            if logical_key not in referenced_keys:
                                orphans.append(logical_key)
                    finally:
                        os.close(prefix_fd)
            finally:
                os.close(sha_fd)

        removed: list[Path] = []
        for name in sorted(stale):
            os.unlink(name, dir_fd=self._temporary_fd)
            removed.append(self.temporary_root / name)
        if stale:
            os.fsync(self._temporary_fd)
        return ArtifactRecovery(tuple(removed), tuple(sorted(orphans)))
