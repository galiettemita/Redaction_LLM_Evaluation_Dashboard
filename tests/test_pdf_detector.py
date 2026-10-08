from __future__ import annotations

from io import BytesIO
import logging
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    RectangleObject,
    TextStringObject,
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.pdf_detector import DetectionStatus, detect_targets


PROJECT_ID = "project-rl-mvp-002"
DOCUMENT_VERSION_ID = "redacted-document-v1"


def _detect(pdf_bytes: bytes):
    return detect_targets(
        pdf_bytes,
        project_id=PROJECT_ID,
        redacted_document_version_id=DOCUMENT_VERSION_ID,
    )


def _fixture_bytes(case: str, tmp_path: Path) -> bytes:
    redacted, _ = make_synthetic_pair(case, tmp_path / case)
    return redacted.read_bytes()


def _pdf_bytes(draw) -> bytes:
    output = BytesIO()
    canvas = Canvas(output, pagesize=letter, invariant=1, pageCompression=0)
    draw(canvas)
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def _rewrite_page(
    pdf_bytes: bytes,
    *,
    prefix: bytes = b"",
    cropbox: tuple[int, int, int, int] | None = None,
    optional_content_off: bool = False,
) -> bytes:
    reader = PdfReader(BytesIO(pdf_bytes))
    page = reader.pages[0]
    original = page.get_contents().get_data()
    stream = DecodedStreamObject()
    if optional_content_off:
        stream.set_data(b"/OC /HiddenLayer BDC\n" + original + b"\nEMC")
        ocg = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/OCG"),
                NameObject("/Name"): TextStringObject("Hidden synthetic layer"),
            }
        )
        properties = DictionaryObject({NameObject("/HiddenLayer"): ocg})
        page[NameObject("/Resources")][NameObject("/Properties")] = properties
        reader.trailer["/Root"][NameObject("/OCProperties")] = DictionaryObject(
            {
                NameObject("/OCGs"): ArrayObject([ocg]),
                NameObject("/D"): DictionaryObject(
                    {NameObject("/OFF"): ArrayObject([ocg])}
                ),
            }
        )
    else:
        stream.set_data(prefix + original)
    page[NameObject("/Contents")] = stream
    if cropbox is not None:
        page.cropbox = RectangleObject(cropbox)
    writer = PdfWriter()
    writer.add_page(page)
    if optional_content_off:
        writer._root_object[NameObject("/OCProperties")] = reader.trailer["/Root"][
            "/OCProperties"
        ]
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_detects_two_distinct_black_text_boxes(tmp_path: Path) -> None:
    result = _detect(_fixture_bytes("two_boxes", tmp_path))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 2
    assert [target.page_index for target in result.targets] == [0, 0]
    assert len({target.target_id for target in result.targets}) == 2
    assert all(target.project_id == PROJECT_ID for target in result.targets)
    assert all(
        target.redacted_document_version_id == DOCUMENT_VERSION_ID
        for target in result.targets
    )
    assert all(
        0.0 <= coordinate <= 1.0
        for target in result.targets
        for coordinate in target.normalized_bbox
    )


def test_adjacent_boxes_not_merged(tmp_path: Path) -> None:
    result = _detect(_fixture_bytes("adjacent_boxes", tmp_path))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 2
    first, second = result.targets
    assert first.normalized_bbox[2] < second.normalized_bbox[0]


def test_near_black_text_overlay_is_detected() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after prefix.")
        canvas.setFillColorRGB(0.05, 0.05, 0.05)
        canvas.rect(108, 697, 115, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 1


def test_rich_cmyk_black_text_overlay_is_detected() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_TRAP_TOKEN after prefix.")
        canvas.setFillColorCMYK(1, 1, 1, 1)
        canvas.rect(108, 697, 155, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 1


def test_target_ids_and_geometry_are_stable(tmp_path: Path) -> None:
    pdf_bytes = _fixture_bytes("two_boxes", tmp_path)

    first = _detect(pdf_bytes)
    second = _detect(pdf_bytes)

    assert first == second
    assert first.source_sha256 == second.source_sha256
    assert [target.target_id for target in first.targets] == [
        target.target_id for target in second.targets
    ]
    assert [target.normalized_bbox for target in first.targets] == [
        target.normalized_bbox for target in second.targets
    ]


def test_target_ids_are_scoped_to_project(tmp_path: Path) -> None:
    pdf_bytes = _fixture_bytes("two_boxes", tmp_path)

    first_project = detect_targets(
        pdf_bytes,
        project_id="project-one",
        redacted_document_version_id=DOCUMENT_VERSION_ID,
    )
    second_project = detect_targets(
        pdf_bytes,
        project_id="project-two",
        redacted_document_version_id=DOCUMENT_VERSION_ID,
    )

    assert first_project.status is DetectionStatus.SUPPORTED
    assert second_project.status is DetectionStatus.SUPPORTED
    assert {target.target_id for target in first_project.targets}.isdisjoint(
        target.target_id for target in second_project.targets
    )


def test_target_identity_encoding_is_unambiguous(tmp_path: Path) -> None:
    pdf_bytes = _fixture_bytes("two_boxes", tmp_path)

    first = detect_targets(
        pdf_bytes,
        project_id="a|b",
        redacted_document_version_id="c",
    )
    second = detect_targets(
        pdf_bytes,
        project_id="a",
        redacted_document_version_id="b|c",
    )

    assert first.status is DetectionStatus.SUPPORTED
    assert second.status is DetectionStatus.SUPPORTED
    assert {target.target_id for target in first.targets}.isdisjoint(
        target.target_id for target in second.targets
    )


def test_ambiguous_two_column_layout_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 720, "Left column first line")
        canvas.drawString(72, 700, "Left SYNTHETIC_SECRET")
        canvas.drawString(330, 720, "Right column first line")
        canvas.drawString(330, 700, "Right column second line")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(94, 697, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_LAYOUT"


def test_narrow_gutter_two_column_layout_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 720, "Left first line")
        canvas.drawString(72, 700, "Left SYNTHETIC_SECRET")
        canvas.drawString(242, 720, "Right first line")
        canvas.drawString(242, 700, "Right second line")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(94, 697, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "AMBIGUOUS_TEXT_LAYOUT"


def test_staggered_two_column_layout_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 720, "Left first line")
        canvas.drawString(72, 700, "Left SYNTHETIC_SECRET")
        canvas.drawString(330, 712, "Right first line")
        canvas.drawString(330, 692, "Right second line")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(94, 697, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "AMBIGUOUS_TEXT_LAYOUT"


def test_single_line_two_column_layout_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Left SYNTHETIC_SECRET")
        canvas.drawString(330, 700, "Right column note")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(94, 697, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "AMBIGUOUS_TEXT_LAYOUT"


def test_one_line_secondary_column_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 720, "Left column first line")
        canvas.drawString(72, 700, "Left SYNTHETIC_SECRET")
        canvas.drawString(330, 710, "One right-column note")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(94, 697, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "AMBIGUOUS_TEXT_LAYOUT"


def test_staggered_two_one_line_columns_are_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 720, "Left SYNTHETIC_SECRET")
        canvas.drawString(330, 680, "Right column only line")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(94, 717, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "AMBIGUOUS_TEXT_LAYOUT"


def test_single_column_single_line_layout_remains_supported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(108, 697, 112, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 1


def test_single_column_indented_layout_remains_supported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 720, "Ordinary first line")
        canvas.drawString(96, 700, "Indented SYNTHETIC_SECRET after")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(140, 697, 112, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 1


def test_single_column_heading_and_body_remain_supported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(240, 740, "Synthetic heading")
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after the heading")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(108, 697, 112, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.SUPPORTED
    assert len(result.targets) == 1


def test_overlapping_black_text_rectangles_are_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(108, 697, 80, 14, stroke=0, fill=1)
        canvas.rect(160, 697, 70, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "OVERLAPPING_REDACTION_RECTANGLES"


def test_duplicate_black_text_rectangles_are_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(108, 697, 112, 14, stroke=0, fill=1)
        canvas.rect(108, 697, 112, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "OVERLAPPING_REDACTION_RECTANGLES"


def test_black_non_text_art_is_excluded() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible synthetic paragraph with no redaction.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(420, 220, 40, 40, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.NO_REDACTIONS
    assert result.targets == ()
    assert result.ignored_artwork_count == 1


def test_overlapping_remote_black_art_is_excluded() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible synthetic paragraph with no redaction.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(400, 220, 50, 40, stroke=0, fill=1)
        canvas.rect(425, 230, 50, 40, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.NO_REDACTIONS
    assert result.targets == ()
    assert result.ignored_artwork_count == 2


def test_standalone_redaction_like_rectangle_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 730, "Visible context before the hidden line.")
        canvas.drawString(72, 670, "Visible context after the hidden line.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(72, 697, 150, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


def test_standalone_rectangle_inside_text_column_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 780, "Visible context before the hidden section.")
        canvas.drawString(72, 630, "Visible context after the hidden section.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(72, 697, 150, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


def test_standalone_rectangle_at_start_of_text_section_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 650, "Visible text after the hidden section start.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(72, 720, 150, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


def test_standalone_rectangle_at_end_of_text_section_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 750, "Visible text before the hidden section end.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(72, 680, 150, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


@pytest.mark.parametrize("box_y", [720, 620])
def test_near_indented_boundary_rectangle_is_unsupported(box_y: int) -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 670, "Short")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(105, box_y, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


def test_offset_boundary_rectangle_in_general_text_region_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 670, "Short")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(260, 720, 120, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


def test_remote_wide_artwork_remains_excluded() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Short")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(460, 220, 60, 12, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.NO_REDACTIONS
    assert result.targets == ()
    assert result.ignored_artwork_count == 1


def test_non_rectangular_black_occlusion_in_text_flow_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after prefix.")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.roundRect(108, 697, 115, 14, 3, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "NON_RECTANGULAR_BLACK_SHAPE"


def test_table_like_line_art_in_text_flow_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Synthetic table cell")
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.rect(60, 690, 200, 30, stroke=1, fill=0)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "TABLE_OR_LINE_ART_CONTENT"


def test_table_grid_lines_in_text_flow_are_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Synthetic table cell")
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.line(60, 690, 260, 690)
        canvas.line(60, 720, 260, 720)
        canvas.line(60, 690, 60, 720)
        canvas.line(260, 690, 260, 720)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "TABLE_OR_LINE_ART_CONTENT"


def test_single_thick_stroke_over_text_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "SYNTHETIC_TRAP_TOKEN")
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(25)
        canvas.line(70, 704, 230, 704)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "TABLE_OR_LINE_ART_CONTENT"


def test_thick_stroked_curve_over_text_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "SYNTHETIC_TRAP_TOKEN")
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(25)
        path = canvas.beginPath()
        path.moveTo(70, 704)
        path.curveTo(110, 710, 180, 698, 230, 704)
        canvas.drawPath(path, stroke=1, fill=0)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "TABLE_OR_LINE_ART_CONTENT"


def test_grey_ruled_table_with_black_box_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Role")
        canvas.drawString(170, 700, "SYNTHETIC_TRAP_TOKEN")
        canvas.setStrokeColorRGB(0.5, 0.5, 0.5)
        canvas.rect(60, 688, 250, 30, stroke=1, fill=0)
        canvas.line(150, 688, 150, 718)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(168, 697, 140, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "TABLE_OR_LINE_ART_CONTENT"


def test_invisible_text_rendering_mode_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        text = canvas.beginText(72, 700)
        text.setFont("Helvetica", 11)
        text.setTextRenderMode(3)
        text.textLine("SYNTHETIC_TRAP_TOKEN")
        canvas.drawText(text)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "COMPLEX_PAGE_GRAPHICS"


def test_white_text_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFillColorRGB(1, 1, 1)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "SYNTHETIC_TRAP_TOKEN")

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "TEXT_VISIBILITY_UNCERTAIN"


def test_white_rectangle_covering_text_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "SYNTHETIC_TRAP_TOKEN")
        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(70, 697, 160, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "TEXT_VISIBILITY_UNCERTAIN"


def test_nondefault_cropbox_is_unsupported() -> None:
    original = _pdf_bytes(
        lambda canvas: canvas.drawString(500, 700, "SYNTHETIC_TRAP_TOKEN")
    )
    cropped = _rewrite_page(original, cropbox=(0, 0, 300, 792))

    result = _detect(cropped)

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "NONDEFAULT_PAGE_BOUNDARY"


def test_optional_content_is_unsupported() -> None:
    original = _pdf_bytes(
        lambda canvas: canvas.drawString(72, 700, "SYNTHETIC_TRAP_TOKEN")
    )
    layered = _rewrite_page(original, optional_content_off=True)

    result = _detect(layered)

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "COMPLEX_PAGE_GRAPHICS"


def test_text_flow_black_candidate_without_occluded_glyphs_is_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Before")
        canvas.drawString(220, 700, "After")
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(125, 697, 80, 14, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "AMBIGUOUS_TEXT_FLOW_RECTANGLE"


def test_page_without_visible_text_is_explicitly_unsupported() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(72, 650, 180, 30, stroke=0, fill=1)

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "NO_VISIBLE_TEXT"


def test_malformed_pdf_is_explicitly_unsupported() -> None:
    result = _detect(b"not a pdf and contains no safe source text")

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.targets == ()
    assert result.reason_code == "MALFORMED_PDF"
    assert "not a pdf" not in repr(result)


def test_malformed_operands_do_not_leak_through_logs_or_stderr(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    original = _pdf_bytes(
        lambda canvas: canvas.drawString(72, 700, "Visible synthetic text")
    )
    malformed = _rewrite_page(original, prefix=b"(SYNTHETIC_TRAP_TOKEN) g\n")

    with caplog.at_level(logging.DEBUG):
        result = _detect(malformed)
    captured = capsys.readouterr()

    assert result.status is DetectionStatus.UNSUPPORTED
    assert "SYNTHETIC_TRAP_TOKEN" not in caplog.text
    assert "SYNTHETIC_TRAP_TOKEN" not in captured.err


def test_rotated_page_is_explicitly_unsupported() -> None:
    original = _pdf_bytes(
        lambda canvas: canvas.drawString(72, 700, "Visible synthetic text.")
    )
    reader = PdfReader(BytesIO(original))
    reader.pages[0].rotate(90)
    output = BytesIO()
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    writer.write(output)

    result = _detect(output.getvalue())

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "ROTATED_PAGE"


def test_overlay_painted_before_text_is_rejected() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.setFillColorRGB(0, 0, 0)
        canvas.rect(115, 697, 90, 14, stroke=0, fill=1)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, 700, "Visible SYNTHETIC_SECRET after box.")

    result = _detect(_pdf_bytes(draw))

    assert result.status is DetectionStatus.UNSUPPORTED
    assert result.reason_code == "PAINT_ORDER_UNCERTAIN"


def test_zero_redactions_is_distinct_from_unsupported() -> None:
    pdf_bytes = _pdf_bytes(
        lambda canvas: canvas.drawString(72, 700, "Visible synthetic text only.")
    )

    result = _detect(pdf_bytes)

    assert result.status is DetectionStatus.NO_REDACTIONS
    assert result.reason_code is None
