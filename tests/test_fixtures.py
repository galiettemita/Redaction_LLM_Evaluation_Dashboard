from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfReader
from pypdf.generic import ContentStream
from reportlab.pdfbase.pdfmetrics import stringWidth

from redaction_lab.fixtures import SYNTHETIC_CASES, make_synthetic_pair


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def _rectangles(path: Path) -> list[tuple[float, float, float, float]]:
    reader = PdfReader(path)
    page = reader.pages[0]
    operations = ContentStream(page.get_contents(), reader).operations
    return [
        tuple(float(value) for value in operands)
        for operands, operator in operations
        if operator == b"re"
    ]


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
        "partially_revealed_reference",
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


@pytest.mark.parametrize(
    ("case", "release", "covered_spans"),
    [
        (
            "two_boxes",
            "redacted",
            [
                (700, "The synthetic courier was ", "Agent Cedar"),
                (664, "The synthetic package contained ", "12 paper stars"),
            ],
        ),
        (
            "adjacent_boxes",
            "redacted",
            [
                (700, "Codes ", "ALPHA"),
                (700, "Codes ALPHA ", "BRAVO"),
            ],
        ),
        (
            "repeated_anchors",
            "redacted",
            [
                (700, "The unit transferred ", "BLUE"),
                (664, "The unit transferred ", "GREEN"),
            ],
        ),
        (
            "still_hidden_reference",
            "reference",
            [(700, "The synthetic destination was ", "ORCHARD SEVEN")],
        ),
        (
            "partially_revealed_reference",
            "reference",
            [(700, "The synthetic authorization code was ORCHARD ", "SEVEN")],
        ),
        (
            "hidden_text_layer",
            "redacted",
            [(700, "The hidden token is ", "SYNTHETIC_TRAP_TOKEN")],
        ),
    ],
)
def test_redaction_rectangles_fully_cover_intended_text(
    case: str,
    release: str,
    covered_spans: list[tuple[float, str, str]],
    tmp_path: Path,
) -> None:
    redacted, reference = make_synthetic_pair(case, tmp_path / case)
    path = redacted if release == "redacted" else reference
    rectangles = _rectangles(path)

    for baseline, prefix, secret in covered_spans:
        start = 72 + stringWidth(prefix, "Helvetica", 11)
        end = start + stringWidth(secret, "Helvetica", 11)
        assert any(
            x <= start and x + width >= end and y <= baseline <= y + height
            for x, y, width, height in rectangles
        )


def test_case_registry_is_explicit_and_unknown_cases_fail(tmp_path: Path) -> None:
    assert SYNTHETIC_CASES == (
        "two_boxes",
        "adjacent_boxes",
        "repeated_anchors",
        "still_hidden_reference",
        "partially_revealed_reference",
        "hidden_text_layer",
    )

    with pytest.raises(ValueError, match="unknown synthetic case"):
        make_synthetic_pair("not-a-case", tmp_path)


def test_partial_reference_reveals_only_part_of_one_contiguous_target(
    tmp_path: Path,
) -> None:
    redacted, reference = make_synthetic_pair("partially_revealed_reference", tmp_path)
    redacted_rectangles = _rectangles(redacted)
    reference_rectangles = _rectangles(reference)

    full_start = 72 + stringWidth(
        "The synthetic authorization code was ", "Helvetica", 11
    )
    partial_start = full_start + stringWidth("ORCHARD ", "Helvetica", 11)

    assert any(x <= full_start for x, _, _, _ in redacted_rectangles)
    assert any(
        x <= partial_start and x > full_start
        for x, _, _, _ in reference_rectangles
    )
    assert "ORCHARD SEVEN" in _text(reference)
