"""Deterministic, wholly synthetic PDF pairs for contract and pipeline tests."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas


SYNTHETIC_CASES = (
    "two_boxes",
    "adjacent_boxes",
    "repeated_anchors",
    "still_hidden_reference",
    "hidden_text_layer",
)

_PAGE_WIDTH, _PAGE_HEIGHT = letter


def _canvas(path: Path, case: str, release: str) -> Canvas:
    canvas = Canvas(
        str(path),
        pagesize=letter,
        invariant=1,
        pageCompression=0,
    )
    canvas.setTitle(f"Redaction Lab synthetic fixture: {case} {release}")
    canvas.setAuthor("Redaction Lab synthetic fixture generator")
    canvas.setSubject("Synthetic test data; contains no real research content")
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(72, _PAGE_HEIGHT - 54, "SYNTHETIC TEST DATA - NOT REAL")
    canvas.setFont("Helvetica", 9)
    canvas.drawString(72, 36, f"case={case}; release={release}")
    return canvas


def _draw_overlay(canvas: Canvas, x: float, y: float, width: float, height: float = 14) -> None:
    canvas.saveState()
    canvas.setFillColorRGB(0, 0, 0)
    canvas.rect(x, y - 3, width, height, stroke=0, fill=1)
    canvas.restoreState()


def _write_two_boxes(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The synthetic courier was Agent Cedar at 09:00.")
    canvas.drawString(72, 664, "The synthetic package contained 12 paper stars.")
    if redacted:
        _draw_overlay(canvas, 195, 700, 68)
        _draw_overlay(canvas, 224, 664, 76)


def _write_adjacent_boxes(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "Codes ALPHA BRAVO were entered separately.")
    if redacted:
        _draw_overlay(canvas, 106, 700, 38)
        _draw_overlay(canvas, 146, 700, 40)


def _write_repeated_anchors(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The unit transferred BLUE before dawn.")
    canvas.drawString(72, 664, "The unit transferred GREEN before dawn.")
    if redacted:
        _draw_overlay(canvas, 174, 700, 34)
        _draw_overlay(canvas, 174, 664, 42)


def _write_still_hidden_reference(
    canvas: Canvas, redacted: bool, is_reference: bool
) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The synthetic destination was ORCHARD SEVEN.")
    if redacted or is_reference:
        _draw_overlay(canvas, 222, 700, 96)


def _write_hidden_text_layer(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The hidden token is SYNTHETIC_TRAP_TOKEN.")
    if redacted:
        _draw_overlay(canvas, 163, 700, 142)


_WRITERS: dict[str, Callable[[Canvas, bool, bool], None]] = {
    "two_boxes": _write_two_boxes,
    "adjacent_boxes": _write_adjacent_boxes,
    "repeated_anchors": _write_repeated_anchors,
    "still_hidden_reference": _write_still_hidden_reference,
    "hidden_text_layer": _write_hidden_text_layer,
}


def _write_pdf(path: Path, case: str, *, redacted: bool) -> None:
    release = "redacted" if redacted else "reference"
    canvas = _canvas(path, case, release)
    _WRITERS[case](canvas, redacted, not redacted)
    canvas.showPage()
    canvas.save()


def make_synthetic_pair(case: str, output_dir: Path) -> tuple[Path, Path]:
    """Create a deterministic redacted/reference PDF pair for a named case."""

    if case not in _WRITERS:
        supported = ", ".join(SYNTHETIC_CASES)
        raise ValueError(f"unknown synthetic case {case!r}; expected one of: {supported}")

    output_dir.mkdir(parents=True, exist_ok=True)
    redacted_path = output_dir / f"{case}-redacted.pdf"
    reference_path = output_dir / f"{case}-reference.pdf"

    _write_pdf(redacted_path, case, redacted=True)
    _write_pdf(reference_path, case, redacted=False)
    return redacted_path, reference_path
