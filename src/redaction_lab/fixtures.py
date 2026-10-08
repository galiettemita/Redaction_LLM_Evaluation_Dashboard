"""Deterministic, wholly synthetic PDF pairs for contract and pipeline tests."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


SYNTHETIC_CASES = (
    "two_boxes",
    "adjacent_boxes",
    "repeated_anchors",
    "still_hidden_reference",
    "partially_revealed_reference",
    "hidden_text_layer",
)

_, _PAGE_HEIGHT = letter


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


def _cover_text(
    canvas: Canvas,
    line_x: float,
    y: float,
    prefix: str,
    secret: str,
    *,
    margin: float = 1.0,
) -> None:
    x = line_x + stringWidth(prefix, "Helvetica", 11) - margin
    width = stringWidth(secret, "Helvetica", 11) + 2 * margin
    _draw_overlay(canvas, x, y, width)


def _write_two_boxes(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The synthetic courier was Agent Cedar at 09:00.")
    canvas.drawString(72, 664, "The synthetic package contained 12 paper stars.")
    if redacted:
        _cover_text(canvas, 72, 700, "The synthetic courier was ", "Agent Cedar")
        _cover_text(
            canvas,
            72,
            664,
            "The synthetic package contained ",
            "12 paper stars",
        )


def _write_adjacent_boxes(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "Codes ALPHA BRAVO were entered separately.")
    if redacted:
        _cover_text(canvas, 72, 700, "Codes ", "ALPHA")
        _cover_text(canvas, 72, 700, "Codes ALPHA ", "BRAVO")


def _write_repeated_anchors(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The unit transferred BLUE before dawn.")
    canvas.drawString(72, 664, "The unit transferred GREEN before dawn.")
    if redacted:
        _cover_text(canvas, 72, 700, "The unit transferred ", "BLUE")
        _cover_text(canvas, 72, 664, "The unit transferred ", "GREEN")


def _write_still_hidden_reference(
    canvas: Canvas, redacted: bool, is_reference: bool
) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The synthetic destination was ORCHARD SEVEN.")
    if redacted or is_reference:
        _cover_text(
            canvas,
            72,
            700,
            "The synthetic destination was ",
            "ORCHARD SEVEN",
        )


def _write_partially_revealed_reference(
    canvas: Canvas, redacted: bool, is_reference: bool
) -> None:
    canvas.setFont("Helvetica", 11)
    prefix = "The synthetic authorization code was "
    canvas.drawString(72, 700, f"{prefix}ORCHARD SEVEN.")
    if redacted:
        _cover_text(canvas, 72, 700, prefix, "ORCHARD SEVEN")
    elif is_reference:
        _cover_text(canvas, 72, 700, f"{prefix}ORCHARD ", "SEVEN")


def _write_hidden_text_layer(canvas: Canvas, redacted: bool, _: bool) -> None:
    canvas.setFont("Helvetica", 11)
    canvas.drawString(72, 700, "The hidden token is SYNTHETIC_TRAP_TOKEN.")
    if redacted:
        _cover_text(
            canvas,
            72,
            700,
            "The hidden token is ",
            "SYNTHETIC_TRAP_TOKEN",
        )


_WRITERS: dict[str, Callable[[Canvas, bool, bool], None]] = {
    "two_boxes": _write_two_boxes,
    "adjacent_boxes": _write_adjacent_boxes,
    "repeated_anchors": _write_repeated_anchors,
    "still_hidden_reference": _write_still_hidden_reference,
    "partially_revealed_reference": _write_partially_revealed_reference,
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
