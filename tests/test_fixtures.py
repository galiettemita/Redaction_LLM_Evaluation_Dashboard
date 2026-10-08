from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfReader

from redaction_lab.fixtures import SYNTHETIC_CASES, make_synthetic_pair


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def test_synthetic_fixture_is_reproducible(tmp_path: Path) -> None:
    first = make_synthetic_pair("two_boxes", tmp_path / "first")
    second = make_synthetic_pair("two_boxes", tmp_path / "second")

    assert [_digest(path) for path in first] == [_digest(path) for path in second]


@pytest.mark.parametrize(
    "case",
    [
        "two_boxes",
        "adjacent_boxes",
        "repeated_anchors",
        "still_hidden_reference",
        "hidden_text_layer",
    ],
)
def test_supported_synthetic_cases_create_pdf_pairs(
    case: str, tmp_path: Path
) -> None:
    redacted, reference = make_synthetic_pair(case, tmp_path / case)

    assert redacted.name == f"{case}-redacted.pdf"
    assert reference.name == f"{case}-reference.pdf"
    assert redacted.read_bytes().startswith(b"%PDF-")
    assert reference.read_bytes().startswith(b"%PDF-")
    assert _digest(redacted) != _digest(reference)


def test_hidden_text_layer_trap_is_extractable_beneath_overlay(
    tmp_path: Path,
) -> None:
    redacted, reference = make_synthetic_pair("hidden_text_layer", tmp_path)

    assert "SYNTHETIC_TRAP_TOKEN" in _text(redacted)
    assert "SYNTHETIC_TRAP_TOKEN" in _text(reference)


def test_case_registry_is_explicit_and_unknown_cases_fail(tmp_path: Path) -> None:
    assert SYNTHETIC_CASES == (
        "two_boxes",
        "adjacent_boxes",
        "repeated_anchors",
        "still_hidden_reference",
        "hidden_text_layer",
    )

    with pytest.raises(ValueError, match="unknown synthetic case"):
        make_synthetic_pair("not-a-case", tmp_path)
