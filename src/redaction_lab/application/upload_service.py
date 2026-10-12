"""Bounded upload orchestration; acceptance does not imply processability."""

from __future__ import annotations

from typing import Iterable

from redaction_lab.application.application_store import (
    ApplicationStore,
    RegisteredUpload,
    StoredDocumentPair,
)
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.config import MAX_PAIR_BYTES
from redaction_lab.contracts import DocumentRole


class UploadService:
    def __init__(self, artifacts: ArtifactStore, store: ApplicationStore) -> None:
        self.artifacts = artifacts
        self.store = store

    def accept(
        self,
        *,
        project_id: str,
        role: DocumentRole,
        chunks: Iterable[bytes],
        original_filename: str | None = None,
    ) -> RegisteredUpload:
        del original_filename
        artifact = self.artifacts.publish(chunks)
        return self.store.register_upload(
            project_id=project_id,
            role=role,
            artifact_key=artifact.logical_key,
            sha256=artifact.sha256,
            byte_size=artifact.byte_size,
        )

    def accept_pair(
        self,
        *,
        project_id: str,
        redacted_chunks: Iterable[bytes],
        reference_chunks: Iterable[bytes] | None,
    ) -> StoredDocumentPair:
        redacted = self.accept(
            project_id=project_id,
            role=DocumentRole.REDACTED,
            chunks=redacted_chunks,
        )
        reference = (
            self.accept(
                project_id=project_id,
                role=DocumentRole.REFERENCE,
                chunks=reference_chunks,
            )
            if reference_chunks is not None
            else None
        )
        total = redacted.byte_size + (reference.byte_size if reference else 0)
        if total > MAX_PAIR_BYTES:
            raise ValueError("document pair exceeds the 50 MiB combined limit")
        return self.store.create_pair(
            project_id=project_id,
            redacted_version_id=redacted.version_id,
            reference_version_id=reference.version_id if reference else None,
        )
