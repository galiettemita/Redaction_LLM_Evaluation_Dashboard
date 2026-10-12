from __future__ import annotations

import os
from pathlib import Path

import pytest

from redaction_lab.application.artifact_store import ArtifactIntegrityError, ArtifactStore


def test_content_addressed_publication_is_idempotent_and_verified(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary", max_bytes=32)

    first = store.publish([b"%PDF-1.7\n", b"synthetic"])
    repeated = store.publish([b"%PDF-1.7\nsynthetic"])

    assert first == repeated
    assert first.logical_key.startswith("sha256/")
    assert store.read(first.logical_key, expected_sha256=first.sha256) == b"%PDF-1.7\nsynthetic"
    assert os.stat(store.path_for(first.logical_key)).st_mode & 0o077 == 0


def test_publication_rejects_oversize_non_pdf_and_path_traversal(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary", max_bytes=12)

    with pytest.raises(ValueError, match="25 MiB|size limit"):
        store.publish([b"%PDF-1.7\nxxxx"])
    with pytest.raises(ValueError, match="PDF signature"):
        store.publish([b"not a pdf"])
    with pytest.raises(ValueError, match="logical key"):
        store.read("../../secret", expected_sha256="0" * 64)


def test_read_detects_committed_artifact_tampering(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    record = store.publish([b"%PDF-1.7\noriginal"])
    store.path_for(record.logical_key).write_bytes(b"%PDF-1.7\ntampered")

    with pytest.raises(ArtifactIntegrityError, match="digest"):
        store.read(record.logical_key, expected_sha256=record.sha256)


def test_recovery_removes_only_stale_temporaries_and_reports_orphans(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    record = store.publish([b"%PDF-1.7\norphan"])
    stale = store.temporary_root / "stale.part"
    fresh = store.temporary_root / "fresh.part"
    stale.write_bytes(b"stale")
    fresh.write_bytes(b"fresh")
    os.utime(stale, (0, 0))

    recovery = store.recover(referenced_keys=set(), now_epoch=100_000, temporary_ttl_seconds=10)

    assert stale in recovery.removed_temporaries
    assert fresh.exists()
    assert record.logical_key in recovery.orphan_keys
    assert store.path_for(record.logical_key).exists()
