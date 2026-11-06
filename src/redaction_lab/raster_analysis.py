"""Conservative scanned-text PDF analysis inside the isolated worker."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from io import BytesIO
from math import ceil, isfinite
import re
from statistics import median
from typing import Protocol

from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream
import pypdfium2 as pdfium

from redaction_lab.ocr import OcrEngine, OcrFailure, OcrPage, OcrWord
from redaction_lab.pdf_detector import _suppress_parser_debug_logs


RASTER_DETECTOR_VERSION = "raster-dark-text-v1"
RASTER_CANONICALIZER_VERSION = "ocr-visible-text-v1"
RASTER_REFERENCE_VERSION = "ocr-reference-text-v1"
RASTER_RENDER_DPI = 200
MAX_RASTER_PAGES = 25
MAX_PAGE_PIXELS = 8_000_000
MAX_TOTAL_PIXELS = 100_000_000
MAX_RASTER_TARGETS = 1_000
_BLACK_THRESHOLD = 60


class RasterStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    NO_REDACTIONS = "NO_REDACTIONS"
    UNSUPPORTED = "UNSUPPORTED"


class _RasterFailure(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class RenderedPage:
    page_index: int
    image: Image.Image


@dataclass(frozen=True)
class RenderedDocument:
    page_count: int
    pages: Iterable[RenderedPage]


class RasterRenderer(Protocol):
    def render(self, pdf_bytes: bytes) -> RenderedDocument | tuple[RenderedPage, ...]: ...


@dataclass(frozen=True)
class RasterTargetObservation:
    page_index: int
    normalized_bbox: tuple[float, float, float, float]
    rectangle_index: int


@dataclass(frozen=True)
class RasterRedactedAnalysis:
    status: RasterStatus
    page_count: int
    targets: tuple[RasterTargetObservation, ...] = ()
    canonical_text: str | None = None
    canonical_hash: str | None = None
    reason_code: str | None = None
    detector_version: str = RASTER_DETECTOR_VERSION
    canonicalizer_version: str = RASTER_CANONICALIZER_VERSION


@dataclass(frozen=True)
class RasterReferenceAnalysis:
    status: RasterStatus
    page_count: int
    reference_text: str | None = None
    reference_hash: str | None = None
    reason_code: str | None = None
    canonicalizer_version: str = RASTER_REFERENCE_VERSION


@dataclass(frozen=True)
class _Component:
    bbox: tuple[int, int, int, int]
    black_area: int


class PdfiumRasterRenderer:
    """Preflight every page before yielding bounded composited rasters."""

    @staticmethod
    def _resolved(value):
        return value.get_object() if hasattr(value, "get_object") else value

    def _preflight(self, pdf_bytes: bytes) -> int:
        try:
            with _suppress_parser_debug_logs() as diagnostics:
                reader = PdfReader(BytesIO(pdf_bytes), strict=True)
                if reader.is_encrypted or diagnostics.unsafe_seen:
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                root = self._resolved(reader.trailer.get("/Root", {}))
                if any(key in root for key in ("/OpenAction", "/AA", "/OCProperties")):
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                names = self._resolved(root.get("/Names", {}))
                if "/JavaScript" in names:
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                page_count = len(reader.pages)
                if not 1 <= page_count <= MAX_RASTER_PAGES:
                    raise _RasterFailure("RASTER_PAGE_LIMIT")
                total_pixels = 0
                for page in reader.pages:
                    if int(page.get("/Rotate", 0) or 0) % 360:
                        raise _RasterFailure("UNSAFE_RASTER_PDF")
                    if page.get("/Annots") or page.get("/AA"):
                        raise _RasterFailure("UNSAFE_RASTER_PDF")
                    width_points = float(page.cropbox.width)
                    height_points = float(page.cropbox.height)
                    if (
                        not isfinite(width_points)
                        or not isfinite(height_points)
                        or width_points <= 0
                        or height_points <= 0
                    ):
                        raise _RasterFailure("UNSAFE_RASTER_PDF")
                    render_width = ceil(width_points * RASTER_RENDER_DPI / 72)
                    render_height = ceil(height_points * RASTER_RENDER_DPI / 72)
                    page_pixels = render_width * render_height
                    total_pixels += page_pixels
                    if (
                        page_pixels > MAX_PAGE_PIXELS
                        or total_pixels > MAX_TOTAL_PIXELS
                    ):
                        raise _RasterFailure("RASTER_PIXEL_LIMIT")
                    resources = self._resolved(page.get("/Resources", {}))
                    xobjects = self._resolved(resources.get("/XObject", {}))
                    image_names: set[str] = set()
                    for value in xobjects.values():
                        resolved = self._resolved(value)
                        if str(resolved.get("/Subtype")) != "/Image":
                            raise _RasterFailure("UNSAFE_RASTER_PDF")
                        image_width = int(resolved.get("/Width", 0))
                        image_height = int(resolved.get("/Height", 0))
                        if (
                            image_width <= 0
                            or image_height <= 0
                            or image_width * image_height > MAX_PAGE_PIXELS
                        ):
                            raise _RasterFailure("RASTER_PIXEL_LIMIT")
                    image_names.update(str(name) for name in xobjects)
                    if len(image_names) != 1:
                        raise _RasterFailure("UNSAFE_RASTER_PDF")
                    self._validate_page_composition(
                        reader, page, next(iter(image_names))
                    )
                if diagnostics.unsafe_seen:
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                return page_count
        except _RasterFailure:
            raise
        except Exception:
            raise _RasterFailure("UNSAFE_RASTER_PDF") from None

    @staticmethod
    def _validate_page_composition(reader, page, image_name: str) -> None:
        """Allow one crop-covering image plus non-painting OCR text overlay."""

        operations = ContentStream(page.get_contents(), reader).operations
        image_calls = [
            (index, operands)
            for index, (operands, operator) in enumerate(operations)
            if operator == b"Do"
        ]
        if len(image_calls) != 1 or str(image_calls[0][1][0]) != image_name:
            raise _RasterFailure("UNSAFE_RASTER_PDF")
        image_index = image_calls[0][0]
        transforms = [
            tuple(float(value) for value in operands)
            for operands, operator in operations[:image_index]
            if operator == b"cm"
        ]
        if any(len(transform) != 6 for transform in transforms):
            raise _RasterFailure("UNSAFE_RASTER_PDF")
        non_identity = [
            transform
            for transform in transforms
            if transform != (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        ]
        if len(non_identity) != 1:
            raise _RasterFailure("UNSAFE_RASTER_PDF")
        a, b, c, d, e, f = non_identity[0]
        if not all(isfinite(value) for value in (a, b, c, d, e, f)) or b or c or a <= 0 or d <= 0:
            raise _RasterFailure("UNSAFE_RASTER_PDF")
        crop = tuple(float(value) for value in page.cropbox)
        tolerance = 2.0
        if (
            e > crop[0] + tolerance
            or f > crop[1] + tolerance
            or e + a < crop[2] - tolerance
            or f + d < crop[3] - tolerance
        ):
            raise _RasterFailure("UNSAFE_RASTER_PDF")

        allowed_outside_text = {b"q", b"Q", b"cm", b"g", b"Do"}
        allowed_inside_text = {
            b"BT", b"ET", b"BDC", b"BMC", b"EMC", b"g", b"rg",
            b"G", b"RG", b"Tf", b"Tc", b"Tr", b"Tm", b"Td", b"TD",
            b"Tj", b"TJ", b"Tw", b"Tz", b"TL", b"Ts", b"T*", b"'", b'"',
        }
        in_text = False
        for _operands, operator in operations:
            if operator == b"BT":
                if in_text:
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                in_text = True
            if operator not in (allowed_inside_text if in_text else allowed_outside_text):
                raise _RasterFailure("UNSAFE_RASTER_PDF")
            if operator == b"ET":
                if not in_text:
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                in_text = False
        if in_text:
            raise _RasterFailure("UNSAFE_RASTER_PDF")

    def render(self, pdf_bytes: bytes) -> RenderedDocument:
        page_count = self._preflight(pdf_bytes)

        def pages() -> Iterable[RenderedPage]:
            try:
                document = pdfium.PdfDocument(pdf_bytes)
                if len(document) != page_count:
                    raise _RasterFailure("UNSAFE_RASTER_PDF")
                for page_index in range(page_count):
                    page = document[page_index]
                    image = page.render(scale=RASTER_RENDER_DPI / 72).to_pil().convert(
                        "RGB"
                    )
                    yield RenderedPage(page_index=page_index, image=image)
            except _RasterFailure:
                raise
            except Exception:
                raise _RasterFailure("RASTER_RENDER_FAILED") from None

        return RenderedDocument(page_count=page_count, pages=pages())


def _document(renderer: RasterRenderer, pdf_bytes: bytes) -> RenderedDocument:
    rendered = renderer.render(pdf_bytes)
    if isinstance(rendered, tuple):
        return RenderedDocument(page_count=len(rendered), pages=rendered)
    return rendered


def _union_components(image: Image.Image, minimum_run: int) -> tuple[_Component, ...]:
    grayscale = image.convert("L")
    width, height = grayscale.size
    mask = grayscale.point(
        tuple(1 if value <= _BLACK_THRESHOLD else 0 for value in range(256))
    ).tobytes()
    pattern = re.compile(b"\x01{" + str(minimum_run).encode("ascii") + b",}")
    parent: list[int] = []
    runs: list[tuple[int, int, int]] = []
    previous: list[tuple[int, int, int]] = []

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(first: int, second: int) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for y in range(height):
        row = mask[y * width : (y + 1) * width]
        current: list[tuple[int, int, int]] = []
        for match in pattern.finditer(row):
            node = len(parent)
            parent.append(node)
            x0, x1 = match.start(), match.end()
            runs.append((y, x0, x1))
            current.append((x0, x1, node))
            for old_x0, old_x1, old_node in previous:
                if min(x1, old_x1) > max(x0, old_x0):
                    union(node, old_node)
        previous = current

    grouped: dict[int, list[int]] = {}
    for node in range(len(runs)):
        grouped.setdefault(find(node), []).append(node)
    components: list[_Component] = []
    for nodes in grouped.values():
        selected = [runs[node] for node in nodes]
        x0 = min(run[1] for run in selected)
        y0 = min(run[0] for run in selected)
        x1 = max(run[2] for run in selected)
        y1 = max(run[0] for run in selected) + 1
        components.append(
            _Component(
                bbox=(x0, y0, x1, y1),
                black_area=sum(run[2] - run[1] for run in selected),
            )
        )
    return tuple(components)


def _intersects(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(
        first[3], second[3]
    ) > max(first[1], second[1])


def _text_context(
    box: tuple[int, int, int, int], words: tuple[OcrWord, ...], median_height: float
) -> bool:
    x0, y0, x1, y1 = box
    for word in words:
        wx0, wy0, wx1, wy1 = word.bbox
        if _intersects(box, word.bbox):
            continue
        vertical_overlap = min(y1, wy1) - max(y0, wy0)
        horizontal_distance = min(abs(wx1 - x0), abs(wx0 - x1))
        if vertical_overlap > 0 and horizontal_distance <= 8 * median_height:
            return True
        horizontal_overlap = min(x1, wx1) - max(x0, wx0)
        vertical_distance = min(abs(wy1 - y0), abs(wy0 - y1))
        if horizontal_overlap > 0 and vertical_distance <= 3 * median_height:
            return True
    return False


def _target_components(page: OcrPage, image: Image.Image) -> tuple[_Component, ...]:
    heights = [word.bbox[3] - word.bbox[1] for word in page.words]
    median_height = float(median(heights))
    minimum_run = max(12, int(median_height * 0.6))
    width, height = image.size
    candidates: list[_Component] = []
    unresolved: list[_Component] = []
    for component in _union_components(image, minimum_run):
        x0, y0, x1, y1 = component.bbox
        box_width, box_height = x1 - x0, y1 - y0
        area = box_width * box_height
        page_fraction = area / (width * height)
        rectangularity = component.black_area / area
        if page_fraction >= 0.25:
            raise _RasterFailure("WHOLE_PAGE_OCCLUSION")
        if (
            box_width < max(20, median_height * 1.2)
            or box_height < max(8, median_height * 0.6)
            or box_width > width * 0.95
            or box_height > height * 0.35
            or rectangularity < 0.60
        ):
            continue
        if not _text_context(component.bbox, page.words, median_height):
            unresolved.append(component)
            continue
        candidates.append(component)
    for component in unresolved:
        x0, y0, x1, y1 = component.bbox
        adjacent = any(
            min(x1, other.bbox[2]) > max(x0, other.bbox[0])
            and min(abs(y1 - other.bbox[1]), abs(y0 - other.bbox[3]))
            <= 2 * median_height
            for other in candidates
        )
        if not adjacent:
            raise _RasterFailure("AMBIGUOUS_RASTER_REGION")
        candidates.append(component)
    return tuple(sorted(candidates, key=lambda item: (item.bbox[1], item.bbox[0])))


def _validate_ocr(page: OcrPage) -> None:
    if len(page.words) < 5:
        raise _RasterFailure("OCR_QUALITY_UNCERTAIN")
    confidences = [word.confidence for word in page.words]
    if sum(value >= 60 for value in confidences) / len(confidences) < 0.60 or sum(
        confidences
    ) / len(confidences) < 60:
        raise _RasterFailure("OCR_QUALITY_UNCERTAIN")


def _validate_reference_ocr(page: OcrPage) -> None:
    _validate_ocr(page)
    if any(word.confidence < 60 for word in page.words):
        raise _RasterFailure("OCR_QUALITY_UNCERTAIN")


def _normalized(
    box: tuple[int, int, int, int], width: int, height: int
) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    return tuple(
        round(value, 8)
        for value in (x0 / width, 1 - y1 / height, x1 / width, 1 - y0 / height)
    )  # type: ignore[return-value]


def _page_text(
    page: OcrPage,
    targets: tuple[tuple[_Component, RasterTargetObservation, str], ...],
) -> str:
    visible = tuple(
        word
        for word in page.words
        if not any(_intersects(word.bbox, component.bbox) for component, _, _ in targets)
    )
    lines: dict[tuple[int, int, int], list[tuple[int, str]]] = {}
    line_top: dict[tuple[int, int, int], float] = {}
    for word in visible:
        lines.setdefault(word.line_key, []).append((word.bbox[0], word.text))
        line_top.setdefault(word.line_key, (word.bbox[1] + word.bbox[3]) / 2)
    heights = [word.bbox[3] - word.bbox[1] for word in page.words]
    median_height = float(median(heights))
    for component, _observation, marker in targets:
        x0, y0, _x1, y1 = component.bbox
        center = (y0 + y1) / 2
        if line_top:
            selected = min(line_top, key=lambda key: abs(line_top[key] - center))
            if abs(line_top[selected] - center) > 3 * median_height:
                selected = (-1, -1, len(lines) + 1)
                line_top[selected] = center
        else:
            selected = (-1, -1, len(lines) + 1)
            line_top[selected] = center
        lines.setdefault(selected, []).append((x0, f"[[TARGET:{marker}]]"))
    rendered = []
    for key in sorted(lines, key=lambda item: (line_top[item], item)):
        text = " ".join(piece for _, piece in sorted(lines[key], key=lambda item: item[0]))
        if text.strip():
            rendered.append(text.strip())
    return "\n".join(rendered)


def _unsupported_redacted(reason: str, page_count: int = 0) -> RasterRedactedAnalysis:
    return RasterRedactedAnalysis(
        status=RasterStatus.UNSUPPORTED,
        page_count=page_count,
        reason_code=reason,
    )


def _unsupported_reference(reason: str, page_count: int = 0) -> RasterReferenceAnalysis:
    return RasterReferenceAnalysis(
        status=RasterStatus.UNSUPPORTED,
        page_count=page_count,
        reason_code=reason,
    )


def analyze_redacted_scan(
    pdf_bytes: bytes,
    *,
    ocr_engine: OcrEngine,
    marker_id: Callable[[RasterTargetObservation], str],
    renderer: RasterRenderer | None = None,
) -> RasterRedactedAnalysis:
    renderer = renderer or PdfiumRasterRenderer()
    page_count = 0
    try:
        document = _document(renderer, pdf_bytes)
        page_count = document.page_count
        if not 1 <= page_count <= MAX_RASTER_PAGES:
            raise _RasterFailure("RASTER_PAGE_LIMIT")
        total_pixels = 0
        observations: list[RasterTargetObservation] = []
        pages: list[str] = []
        observed_pages = 0
        for rendered in document.pages:
            if rendered.page_index != observed_pages:
                raise _RasterFailure("RASTER_PAGE_ORDER_INVALID")
            observed_pages += 1
            width, height = rendered.image.size
            pixels = width * height
            total_pixels += pixels
            if pixels > MAX_PAGE_PIXELS or total_pixels > MAX_TOTAL_PIXELS:
                raise _RasterFailure("RASTER_PIXEL_LIMIT")
            ocr_page = ocr_engine.recognize(rendered.image)
            if (ocr_page.width, ocr_page.height) != (width, height):
                raise _RasterFailure("OCR_GEOMETRY_INVALID")
            _validate_ocr(ocr_page)
            components = _target_components(ocr_page, rendered.image)
            page_targets: list[tuple[_Component, RasterTargetObservation, str]] = []
            for rectangle_index, component in enumerate(components):
                observation = RasterTargetObservation(
                    page_index=rendered.page_index,
                    normalized_bbox=_normalized(component.bbox, width, height),
                    rectangle_index=rectangle_index,
                )
                marker = marker_id(observation).strip()
                if not marker or any(character in marker for character in "[]\r\n"):
                    raise _RasterFailure("TARGET_ID_INVALID")
                observations.append(observation)
                page_targets.append((component, observation, marker))
            if len(observations) > MAX_RASTER_TARGETS:
                raise _RasterFailure("RASTER_TARGET_LIMIT")
            pages.append(_page_text(ocr_page, tuple(page_targets)))
        if observed_pages != page_count:
            raise _RasterFailure("RASTER_PAGE_COUNT_MISMATCH")
        if not observations:
            return RasterRedactedAnalysis(
                status=RasterStatus.NO_REDACTIONS,
                page_count=page_count,
                reason_code="NO_SUPPORTED_REDACTIONS",
            )
        canonical_text = "\n\n".join(pages)
        observation_by_marker = {
            marker_id(observation): observation for observation in observations
        }
        canonical_markers = tuple(re.findall(r"\[\[TARGET:([^\]]+)\]\]", canonical_text))
        if (
            len(observation_by_marker) != len(observations)
            or len(canonical_markers) != len(observations)
            or set(canonical_markers) != set(observation_by_marker)
        ):
            raise _RasterFailure("CANONICAL_MARKER_INVALID")
        ordered_observations = tuple(
            observation_by_marker[marker] for marker in canonical_markers
        )
        return RasterRedactedAnalysis(
            status=RasterStatus.SUPPORTED,
            page_count=page_count,
            targets=ordered_observations,
            canonical_text=canonical_text,
            canonical_hash=sha256(canonical_text.encode()).hexdigest(),
        )
    except OcrFailure:
        return _unsupported_redacted("OCR_EXECUTION_FAILED", page_count)
    except _RasterFailure as error:
        return _unsupported_redacted(error.reason_code, page_count)
    except Exception:
        return _unsupported_redacted("RASTER_ANALYSIS_FAILED", page_count)


def analyze_reference_scan(
    pdf_bytes: bytes,
    *,
    ocr_engine: OcrEngine,
    renderer: RasterRenderer | None = None,
) -> RasterReferenceAnalysis:
    renderer = renderer or PdfiumRasterRenderer()
    page_count = 0
    try:
        document = _document(renderer, pdf_bytes)
        page_count = document.page_count
        if not 1 <= page_count <= MAX_RASTER_PAGES:
            raise _RasterFailure("RASTER_PAGE_LIMIT")
        total_pixels = 0
        pages: list[str] = []
        observed_pages = 0
        for rendered in document.pages:
            if rendered.page_index != observed_pages:
                raise _RasterFailure("RASTER_PAGE_ORDER_INVALID")
            observed_pages += 1
            width, height = rendered.image.size
            pixels = width * height
            total_pixels += pixels
            if pixels > MAX_PAGE_PIXELS or total_pixels > MAX_TOTAL_PIXELS:
                raise _RasterFailure("RASTER_PIXEL_LIMIT")
            ocr_page = ocr_engine.recognize(rendered.image)
            if (ocr_page.width, ocr_page.height) != (width, height):
                raise _RasterFailure("OCR_GEOMETRY_INVALID")
            _validate_reference_ocr(ocr_page)
            if _target_components(ocr_page, rendered.image):
                raise _RasterFailure("REFERENCE_PARTIALLY_HIDDEN")
            pages.append(_page_text(ocr_page, ()))
        if observed_pages != page_count:
            raise _RasterFailure("RASTER_PAGE_COUNT_MISMATCH")
        reference_text = "\n\n".join(pages)
        return RasterReferenceAnalysis(
            status=RasterStatus.SUPPORTED,
            page_count=page_count,
            reference_text=reference_text,
            reference_hash=sha256(reference_text.encode()).hexdigest(),
        )
    except OcrFailure:
        return _unsupported_reference("OCR_EXECUTION_FAILED", page_count)
    except _RasterFailure as error:
        reason = (
            "REFERENCE_PARTIALLY_HIDDEN"
            if error.reason_code == "AMBIGUOUS_RASTER_REGION"
            else error.reason_code
        )
        return _unsupported_reference(reason, page_count)
    except Exception:
        return _unsupported_reference("RASTER_ANALYSIS_FAILED", page_count)
