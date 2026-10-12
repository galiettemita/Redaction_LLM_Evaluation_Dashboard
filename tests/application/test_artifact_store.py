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


@pytest.mark.parametrize("root_name", ["artifacts", "temporary"])
def test_store_rejects_symlinked_roots_before_mutating_other_root(
    tmp_path: Path, root_name: str
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    roots = {"artifacts": tmp_path / "artifacts", "temporary": tmp_path / "temporary"}
    roots[root_name].symlink_to(outside, target_is_directory=True)

    with pytest.raises(ArtifactIntegrityError, match="symbolic|symlink"):
        ArtifactStore(roots["artifacts"], roots["temporary"])

    other = roots["temporary" if root_name == "artifacts" else "artifacts"]
    assert not other.exists()
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("component", ["sha256", "prefix", "leaf"])
def test_artifact_operations_reject_symlinked_content_addressed_components(
    tmp_path: Path, component: str
) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    payload = b"%PDF-1.7\nsymlink"
    digest = __import__("hashlib").sha256(payload).hexdigest()
    outside = tmp_path / "outside"
    outside.mkdir()
    sha_root = store.artifact_root / "sha256"
    prefix = sha_root / digest[:2]
    leaf = prefix / f"{digest}.pdf"
    if component == "sha256":
        sha_root.symlink_to(outside, target_is_directory=True)
    else:
        sha_root.mkdir()
        if component == "prefix":
            prefix.symlink_to(outside, target_is_directory=True)
        else:
            prefix.mkdir()
            target = outside / "target.pdf"
            target.write_bytes(b"outside")
            leaf.symlink_to(target)

    with pytest.raises(ArtifactIntegrityError, match="symbolic|symlink"):
        store.publish([payload])

    assert not (outside / f"{digest}.pdf").exists()


def test_prefix_replacement_race_cannot_redirect_publication(
    tmp_path: Path, monkeypatch
) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    payload = b"%PDF-1.7\nrace"
    outside = tmp_path / "outside"
    outside.mkdir()
    original_link = os.link

    def replace_parent_then_link(src, dst, **kwargs):
        prefix = store.artifact_root / "sha256" / dst[:2]
        moved = prefix.with_name(prefix.name + "-moved")
        prefix.rename(moved)
        prefix.symlink_to(outside, target_is_directory=True)
        return original_link(src, dst, **kwargs)

    monkeypatch.setattr(os, "link", replace_parent_then_link)
    record = store.publish([payload])

    assert record.sha256 == __import__("hashlib").sha256(payload).hexdigest()
    assert list(outside.iterdir()) == []


def test_failed_recovery_on_symlink_does_not_delete_stale_temporary(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    stale = store.temporary_root / "stale.part"
    stale.write_bytes(b"stale")
    os.utime(stale, (0, 0))
    target = tmp_path / "outside.pdf"
    target.write_bytes(b"outside")
    (store.temporary_root / "bad.part").symlink_to(target)

    with pytest.raises(ArtifactIntegrityError, match="symbolic|symlink"):
        store.recover(referenced_keys=set(), now_epoch=100_000, temporary_ttl_seconds=10)

    assert stale.exists()
    assert target.read_bytes() == b"outside"
