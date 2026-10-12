from __future__ import annotations

import os
from pathlib import Path

from redaction_lab.application.paths import initialize_paths, resolve_paths


def test_explicit_home_is_portable_and_initialized_privately(tmp_path: Path) -> None:
    root = tmp_path / "recipient-home"

    paths = initialize_paths(resolve_paths({"REDACTION_LAB_HOME": str(root)}))

    assert paths.root == root.resolve()
    assert paths.database == paths.root / "redaction-lab.sqlite3"
    assert paths.artifacts.parent == paths.root
    assert paths.temporary.parent == paths.root
    assert not str(paths.root).startswith("/Users/galiettemita")
    for directory in (paths.root, paths.artifacts, paths.temporary, paths.logs, paths.backups):
        assert directory.is_dir()
        assert os.stat(directory).st_mode & 0o077 == 0


def test_relative_or_blank_explicit_home_is_rejected() -> None:
    for value in ("", "relative/path"):
        try:
            resolve_paths({"REDACTION_LAB_HOME": value})
        except ValueError as error:
            assert "REDACTION_LAB_HOME" in str(error)
        else:
            raise AssertionError("unsafe application home was accepted")
