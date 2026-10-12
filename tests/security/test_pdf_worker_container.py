from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_packaging_declares_no_network_no_host_mounts_and_pinned_runtime() -> None:
    containerfile = (ROOT / "packaging/pdf-worker/Containerfile").read_text()
    configuration = (ROOT / "packaging/pdf-worker/containers.conf").read_text()
    runtime = json.loads((ROOT / "packaging/pdf-worker/runtime.lock").read_text())

    assert "@sha256:" in containerfile
    assert "USER 65532:65532" in containerfile
    assert "volumes = []" in configuration
    assert runtime["protocol_version"] == "pdf-worker-v1"
    assert runtime["image_digest"].startswith("sha256:")
    assert runtime["runtime_verified"] is False


def test_scripts_are_offline_and_never_embed_user_paths_or_credentials() -> None:
    text = "\n".join(
        (ROOT / path).read_text()
        for path in ("scripts/build-pdf-worker.sh", "scripts/verify-pdf-worker.sh")
    )
    assert "--network=none" in text
    assert "--pull=never" in text
    assert "/Users/galiettemita" not in text
    assert "TOKEN=" not in text and "PASSWORD=" not in text
