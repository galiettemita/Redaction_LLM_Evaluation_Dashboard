from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject

from redaction_lab.ocr import OcrPage, OcrWord
from redaction_lab.raster_analysis import (
    PdfiumRasterRenderer,
    RasterStatus,
    RenderedPage,
    analyze_redacted_scan,
    analyze_reference_scan,
)


def _word(
    text: str,
    bbox: tuple[int, int, int, int],
    *,
    confidence: float = 95.0,
    line: int = 1,
) -> OcrWord:
    return OcrWord(
        text=text,
        confidence=confidence,
        bbox=bbox,
        line_key=(1, 1, line),
    )


def _ocr_page(
    words: tuple[OcrWord, ...], *, width: int = 400, height: int = 300
) -> OcrPage:
    return OcrPage(width=width, height=height, words=words)


@dataclass
class QueueOcr:
    pages: list[OcrPage]
    calls: int = 0

    def recognize(self, image: Image.Image) -> OcrPage:
        page = self.pages[self.calls]
        self.calls += 1
        assert image.size == (page.width, page.height)
        return page


@dataclass(frozen=True)
class StaticRenderer:
    pages: tuple[RenderedPage, ...]

    def render(self, pdf_bytes: bytes) -> tuple[RenderedPage, ...]:
        assert pdf_bytes
        return self.pages


def _page(
    *,
    rectangles: tuple[tuple[int, int, int, int], ...] = (),
    index: int = 0,
    width: int = 400,
    height: int = 300,
) -> RenderedPage:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for rectangle in rectangles:
        draw.rectangle(rectangle, fill=(0, 0, 0))
    return RenderedPage(page_index=index, image=image)


def _marker(observation) -> str:
    return f"target-{observation.page_index}-{observation.rectangle_index}"


def test_scan_targets_use_bottom_origin_coordinates_and_reading_order_markers() -> None:
    rendered = _page(rectangles=((80, 45, 230, 75), (110, 155, 300, 185)))
    ocr = QueueOcr(
        [
            _ocr_page(
                (
                    _word("First", (20, 50, 60, 70), line=1),
                    _word("right", (250, 50, 290, 70), line=1),
                    _word("Second", (20, 160, 80, 180), line=2),
                    _word("end", (320, 160, 350, 180), line=2),
                    _word("Footer", (20, 250, 70, 270), line=3),
                )
            )
        ]
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=ocr,
        renderer=StaticRenderer((rendered,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.SUPPORTED
    assert len(result.targets) == 2
    assert result.targets[0].normalized_bbox == (0.2, 0.74666667, 0.5775, 0.85)
    assert result.targets[1].normalized_bbox == (0.275, 0.38, 0.7525, 0.48333333)
    assert result.canonical_text == (
        "First [[TARGET:target-0-0]] right\n"
        "Second [[TARGET:target-0-1]] end\nFooter"
    )
    assert result.canonical_hash is not None


def test_white_label_does_not_split_black_region_and_is_removed_from_prompt() -> None:
    rendered = _page(rectangles=((60, 90, 340, 140),))
    draw = ImageDraw.Draw(rendered.image)
    draw.rectangle((70, 95, 120, 115), fill="white")
    ocr = QueueOcr(
        [
            _ocr_page(
                (
                    _word("Before", (10, 100, 55, 120)),
                    _word("EXEMPTION", (72, 96, 118, 114)),
                    _word("After", (345, 100, 390, 120)),
                    _word("Context", (20, 180, 80, 200), line=2),
                    _word("below", (90, 180, 130, 200), line=2),
                )
            )
        ]
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=ocr,
        renderer=StaticRenderer((rendered,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.SUPPORTED
    assert len(result.targets) == 1
    assert "EXEMPTION" not in (result.canonical_text or "")
    assert result.canonical_text == "Before [[TARGET:target-0-0]] After\nContext below"


def test_low_confidence_scan_is_unsupported_instead_of_silently_empty() -> None:
    page = _page(rectangles=((80, 45, 230, 75),))
    words = tuple(
        _word(f"word{index}", (10 + index * 30, 100, 35 + index * 30, 120), confidence=25)
        for index in range(6)
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((page,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "OCR_QUALITY_UNCERTAIN"
    assert result.targets == ()
    assert result.canonical_text is None


def test_one_ambiguous_black_region_invalidates_other_supported_targets() -> None:
    rendered = _page(rectangles=((80, 45, 230, 75), (280, 220, 370, 245)))
    words = (
        _word("Before", (20, 50, 65, 70)),
        _word("after", (245, 50, 275, 70)),
        _word("Enough", (20, 100, 70, 120), line=2),
        _word("visible", (80, 100, 125, 120), line=2),
        _word("context", (135, 100, 185, 120), line=2),
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((rendered,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "AMBIGUOUS_RASTER_REGION"
    assert result.targets == ()


def test_contextless_bar_adjacent_to_a_supported_bar_is_not_silently_omitted() -> None:
    rendered = _page(rectangles=((80, 45, 230, 75), (80, 78, 230, 108)))
    words = (
        _word("Before", (20, 50, 65, 70)),
        _word("after", (245, 50, 275, 70)),
        _word("Enough", (20, 150, 70, 170), line=2),
        _word("visible", (80, 150, 125, 170), line=2),
        _word("context", (135, 150, 185, 170), line=2),
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((rendered,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.SUPPORTED
    assert len(result.targets) == 2


def test_target_observations_follow_canonical_marker_order_when_lines_collapse() -> None:
    rendered = _page(rectangles=((250, 45, 350, 75), (80, 78, 230, 108)))
    words = (
        _word("Before", (20, 60, 65, 80)),
        _word("after", (360, 60, 395, 80)),
        _word("Enough", (20, 150, 70, 170), line=2),
        _word("visible", (80, 150, 125, 170), line=2),
        _word("context", (135, 150, 185, 170), line=2),
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((rendered,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.SUPPORTED
    assert tuple(target.rectangle_index for target in result.targets) == (1, 0)
    assert (result.canonical_text or "").index("target-0-1") < (
        result.canonical_text or ""
    ).index("target-0-0")


def test_reference_rejects_any_uncertain_word_instead_of_scoring_it() -> None:
    words = tuple(
        _word(
            text,
            (20 + index * 45, 20, 55 + index * 45, 40),
            confidence=0 if text == "999999" else 100,
        )
        for index, text in enumerate(("Known", "text", "is", "clear", "except", "999999"))
    )

    result = analyze_reference_scan(
        b"synthetic-reference",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((_page(),)),
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "OCR_QUALITY_UNCERTAIN"
    assert result.reference_text is None


def test_whole_page_black_region_is_explicitly_unsupported() -> None:
    page = _page(rectangles=((0, 0, 399, 299),))
    words = tuple(
        _word(f"word{index}", (10 + index * 40, 100, 40 + index * 40, 120))
        for index in range(6)
    )

    result = analyze_redacted_scan(
        b"synthetic-scan",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((page,)),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "WHOLE_PAGE_OCCLUSION"


def test_reference_with_residual_black_text_region_is_unknown() -> None:
    page = _page(rectangles=((80, 45, 230, 75),))
    words = (
        _word("Visible", (20, 50, 65, 70)),
        _word("after", (250, 50, 290, 70)),
        _word("More", (20, 100, 60, 120), line=2),
        _word("reference", (70, 100, 130, 120), line=2),
        _word("context", (140, 100, 190, 120), line=2),
    )

    result = analyze_reference_scan(
        b"synthetic-reference",
        ocr_engine=QueueOcr([_ocr_page(words)]),
        renderer=StaticRenderer((page,)),
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "REFERENCE_PARTIALLY_HIDDEN"
    assert result.reference_text is None


def test_clean_reference_preserves_page_and_line_order() -> None:
    pages = (_page(index=0), _page(index=1))
    first = _ocr_page(
        (
            _word("First", (20, 20, 60, 40), line=1),
            _word("line", (70, 20, 100, 40), line=1),
            _word("Second", (20, 60, 70, 80), line=2),
            _word("line", (80, 60, 110, 80), line=2),
            _word("Enough", (20, 100, 70, 120), line=3),
        )
    )
    second = _ocr_page(
        tuple(
            _word(text, (20 + index * 50, 20, 60 + index * 50, 40), line=1)
            for index, text in enumerate(("Third", "page", "has", "text", "too"))
        )
    )

    result = analyze_reference_scan(
        b"synthetic-reference",
        ocr_engine=QueueOcr([first, second]),
        renderer=StaticRenderer(pages),
    )

    assert result.status is RasterStatus.SUPPORTED
    assert result.reference_text == "First line\nSecond line\nEnough\n\nThird page has text too"
    assert result.reference_hash is not None


def test_multipage_targets_keep_page_identity_and_effective_render_boundary() -> None:
    pages = (
        _page(index=0, rectangles=((20, 20, 120, 50),), width=200, height=100),
        _page(index=1, rectangles=((100, 100, 300, 150),), width=400, height=200),
    )
    ocr_pages = [
        _ocr_page(
            (
                _word("A", (2, 25, 15, 45)),
                _word("B", (130, 25, 145, 45)),
                _word("C", (2, 70, 15, 90), line=2),
                _word("D", (20, 70, 35, 90), line=2),
                _word("E", (40, 70, 55, 90), line=2),
            ),
            width=200,
            height=100,
        ),
        _ocr_page(
            (
                _word("F", (20, 110, 40, 130)),
                _word("G", (320, 110, 340, 130)),
                _word("H", (20, 170, 40, 190), line=2),
                _word("I", (50, 170, 70, 190), line=2),
                _word("J", (80, 170, 100, 190), line=2),
            ),
            width=400,
            height=200,
        ),
    ]

    result = analyze_redacted_scan(
        b"synthetic-cropped-scan",
        ocr_engine=QueueOcr(ocr_pages),
        renderer=StaticRenderer(pages),
        marker_id=_marker,
    )

    assert result.status is RasterStatus.SUPPORTED
    assert tuple(target.page_index for target in result.targets) == (0, 1)
    assert result.targets[0].normalized_bbox == (0.1, 0.49, 0.605, 0.8)
    assert result.targets[1].normalized_bbox == (0.25, 0.245, 0.7525, 0.5)
    assert "[[TARGET:target-0-0]]" in (result.canonical_text or "")
    assert "[[TARGET:target-1-0]]" in (result.canonical_text or "")


def _scan_pdf(*, unsafe_second_page: bool = False) -> bytes:
    image = Image.new("RGB", (612, 792), "white")
    output = BytesIO()
    canvas = Canvas(output, pagesize=(612, 792), invariant=1)
    for page_index in range(2):
        canvas.drawImage(ImageReader(image), 0, 0, width=612, height=792)
        if unsafe_second_page and page_index == 1:
            canvas.linkURL("https://example.invalid", (10, 10, 50, 30))
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def _scan_pdf_with_inert_attachment() -> bytes:
    reader = PdfReader(BytesIO(_scan_pdf()))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_attachment("ignored.txt", b"SYNTHETIC_EMBEDDED_SECRET")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_whole_document_preflight_rejects_unsafe_later_page_before_ocr() -> None:
    ocr = QueueOcr([])

    result = analyze_reference_scan(
        _scan_pdf(unsafe_second_page=True),
        ocr_engine=ocr,
        renderer=PdfiumRasterRenderer(),
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "UNSAFE_RASTER_PDF"
    assert ocr.calls == 0


def test_huge_declared_page_is_rejected_before_pdfium_allocates() -> None:
    image = Image.new("RGB", (1, 1), "white")
    output = BytesIO()
    canvas = Canvas(output, pagesize=(100_000, 100_000), invariant=1)
    canvas.drawImage(ImageReader(image), 0, 0, width=100_000, height=100_000)
    canvas.save()
    ocr = QueueOcr([])

    result = analyze_reference_scan(
        output.getvalue(), ocr_engine=ocr, renderer=PdfiumRasterRenderer()
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "RASTER_PIXEL_LIMIT"
    assert ocr.calls == 0


def test_small_image_placement_cannot_masquerade_as_a_scanned_page() -> None:
    image = Image.new("RGB", (20, 20), "white")
    output = BytesIO()
    canvas = Canvas(output, pagesize=(400, 300), invariant=1)
    canvas.drawImage(ImageReader(image), 10, 10, width=20, height=20)
    canvas.save()
    ocr = QueueOcr([])

    result = analyze_reference_scan(
        output.getvalue(), ocr_engine=ocr, renderer=PdfiumRasterRenderer()
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "UNSAFE_RASTER_PDF"
    assert ocr.calls == 0


def test_restored_fake_transform_cannot_authorize_a_tiny_image() -> None:
    image = Image.new("RGB", (1, 1), "black")
    source = BytesIO()
    canvas = Canvas(source, pagesize=(400, 300), invariant=1)
    canvas.drawImage(ImageReader(image), 0, 0, width=1, height=1)
    canvas.save()
    reader = PdfReader(BytesIO(source.getvalue()))
    original = reader.pages[0].get_contents().get_data()
    replacement = DecodedStreamObject()
    replacement.set_data(b"q 400 0 0 300 0 0 cm Q\n" + original)
    output = BytesIO()
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    writer.pages[0].replace_contents(replacement)
    writer.write(output)
    ocr = QueueOcr([])

    result = analyze_reference_scan(
        output.getvalue(), ocr_engine=ocr, renderer=PdfiumRasterRenderer()
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "UNSAFE_RASTER_PDF"
    assert ocr.calls == 0


def test_painting_text_overlay_is_rejected_before_ocr() -> None:
    image = Image.new("RGB", (400, 300), "white")
    output = BytesIO()
    canvas = Canvas(output, pagesize=(400, 300), invariant=1)
    canvas.drawImage(ImageReader(image), 0, 0, width=400, height=300)
    canvas.drawString(20, 20, "painted overlay")
    canvas.save()
    ocr = QueueOcr([])

    result = analyze_reference_scan(
        output.getvalue(), ocr_engine=ocr, renderer=PdfiumRasterRenderer()
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "UNSAFE_RASTER_PDF"
    assert ocr.calls == 0


def test_restored_text_mode_cannot_authorize_a_painting_overlay() -> None:
    image = Image.new("RGB", (400, 300), "white")
    source = BytesIO()
    canvas = Canvas(source, pagesize=(400, 300), invariant=1)
    canvas.drawImage(ImageReader(image), 0, 0, width=400, height=300)
    canvas.drawString(20, 20, "painted overlay")
    canvas.save()
    reader = PdfReader(BytesIO(source.getvalue()))
    original = reader.pages[0].get_contents().get_data()
    replacement = DecodedStreamObject()
    replacement.set_data(b"q BT /F1 12 Tf 3 Tr ET Q\n" + original)
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    writer.pages[0].replace_contents(replacement)
    output = BytesIO()
    writer.write(output)
    ocr = QueueOcr([])

    result = analyze_reference_scan(
        output.getvalue(), ocr_engine=ocr, renderer=PdfiumRasterRenderer()
    )

    assert result.status is RasterStatus.UNSUPPORTED
    assert result.reason_code == "UNSAFE_RASTER_PDF"
    assert ocr.calls == 0


def test_inert_embedded_attachment_is_ignored_and_never_enters_reference_text() -> None:
    words = tuple(
        _word(text, (20 + index * 60, 20, 70 + index * 60, 40))
        for index, text in enumerate(("Visible", "page", "text", "only", "here"))
    )
    ocr = QueueOcr([_ocr_page(words, width=1700, height=2200)] * 2)

    result = analyze_reference_scan(
        _scan_pdf_with_inert_attachment(),
        ocr_engine=ocr,
        renderer=PdfiumRasterRenderer(),
    )

    assert result.status is RasterStatus.SUPPORTED
    assert "SYNTHETIC_EMBEDDED_SECRET" not in (result.reference_text or "")


def test_raster_page_and_pixel_limits_fail_before_ocr() -> None:
    too_many = tuple(_page(index=index, width=20, height=20) for index in range(26))
    ocr = QueueOcr([])

    page_result = analyze_reference_scan(
        b"synthetic-many-pages",
        ocr_engine=ocr,
        renderer=StaticRenderer(too_many),
    )
    pixel_result = analyze_reference_scan(
        b"synthetic-large-page",
        ocr_engine=ocr,
        renderer=StaticRenderer((_page(width=3000, height=3000),)),
    )

    assert page_result.reason_code == "RASTER_PAGE_LIMIT"
    assert pixel_result.reason_code == "RASTER_PIXEL_LIMIT"
    assert ocr.calls == 0
