"""Crash-conscious content-addressed storage for uploaded PDF bytes."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import time
from typing import Iterable
from uuid import uuid4

from redaction_lab.application.config import MAX_PDF_BYTES, TEMPORARY_RETENTION_SECONDS


_KEY = re.compile(r"^sha256/([0-9a-f]{2})/([0-9a-f]{64})\.pdf$")


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
        for directory in (self.artifact_root, self.temporary_root):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            directory.chmod(0o700)

    @staticmethod
    def _key(digest: str) -> str:
        return f"sha256/{digest[:2]}/{digest}.pdf"

    def path_for(self, logical_key: str) -> Path:
        match = _KEY.fullmatch(logical_key)
        if match is None or match.group(1) != match.group(2)[:2]:
            raise ValueError("invalid artifact logical key")
        candidate = self.artifact_root / logical_key
        if candidate.is_symlink():
            raise ArtifactIntegrityError("artifact path must not be a symbolic link")
        return candidate

    def publish(self, chunks: Iterable[bytes]) -> ArtifactRecord:
        temporary = self.temporary_root / f"{uuid4().hex}.part"
        digest = sha256()
        size = 0
        prefix = bytearray()
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as handle:
                for chunk in chunks:
                    if not isinstance(chunk, bytes):
                        raise TypeError("upload chunks must be bytes")
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError("PDF exceeds the 25 MiB size limit")
                    if len(prefix) < 5:
                        prefix.extend(chunk[: 5 - len(prefix)])
                    digest.update(chunk)
                    handle.write(chunk)
                if bytes(prefix) != b"%PDF-":
                    raise ValueError("upload does not have a PDF signature")
                handle.flush()
                os.fsync(handle.fileno())
            hexdigest = digest.hexdigest()
            logical_key = self._key(hexdigest)
            destination = self.path_for(logical_key)
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            destination.parent.chmod(0o700)
            if destination.exists():
                existing = destination.read_bytes()
                if sha256(existing).hexdigest() != hexdigest or len(existing) != size:
                    raise ArtifactIntegrityError("existing artifact digest mismatch")
                temporary.unlink(missing_ok=True)
            else:
                os.replace(temporary, destination)
                destination.chmod(0o600)
                directory_fd = os.open(destination.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            return ArtifactRecord(logical_key, hexdigest, size)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def read(self, logical_key: str, *, expected_sha256: str) -> bytes:
        path = self.path_for(logical_key)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            value = handle.read(self.max_bytes + 1)
        if len(value) > self.max_bytes or sha256(value).hexdigest() != expected_sha256:
            raise ArtifactIntegrityError("artifact digest or size integrity failure")
        return value

    def recover(
        self,
        *,
        referenced_keys: set[str],
        now_epoch: float | None = None,
        temporary_ttl_seconds: int = TEMPORARY_RETENTION_SECONDS,
    ) -> ArtifactRecovery:
        now = time.time() if now_epoch is None else now_epoch
        removed: list[Path] = []
        for path in self.temporary_root.glob("*.part"):
            if path.is_file() and not path.is_symlink() and now - path.stat().st_mtime >= temporary_ttl_seconds:
                path.unlink()
                removed.append(path)
        orphans = sorted(
            str(path.relative_to(self.artifact_root))
            for path in self.artifact_root.glob("sha256/*/*.pdf")
            if not path.is_symlink()
            and str(path.relative_to(self.artifact_root)) not in referenced_keys
        )
        return ArtifactRecovery(tuple(sorted(removed)), tuple(orphans))
