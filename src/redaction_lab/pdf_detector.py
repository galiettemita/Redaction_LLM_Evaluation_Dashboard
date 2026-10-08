"""Fail-closed detection for the narrow vector-PDF MVP boundary."""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from io import BytesIO, StringIO
import json
import logging
from math import isclose
from threading import RLock
from typing import Any

import pdfplumber
from pypdf import PdfReader
from pypdf.generic import ContentStream

from redaction_lab.contracts import DetectionEvidence, RedactionTarget, ScopeStatus


DETECTOR_VERSION = "vector-text-rect-v3"
_TEXT_SHOW_OPERATORS = {b"Tj", b"TJ", b"'", b'"'}
_UNSAFE_OPERATORS = {
    b"Do",
    b"W",
    b"W*",
    b"gs",
    b"sh",
    b"BMC",
    b"BDC",
    b"EMC",
    b"MP",
    b"DP",
    b"CS",
    b"cs",
    b"SC",
    b"SCN",
    b"sc",
    b"scn",
}
_FILL_OPERATORS = {b"f", b"f*", b"B", b"B*"}
_PARSER_LOG_LOCK = RLock()


class _ParserDiagnosticSink(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.seen = False

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            self.seen = True


@contextmanager
def _suppress_parser_debug_logs():
    """Capture parser diagnostics without emitting document-bearing messages."""

    with _PARSER_LOG_LOCK:
        parser_loggers = [logging.getLogger("pdfminer"), logging.getLogger("pypdf")]
        parser_loggers.extend(
            logger
            for name, logger in logging.Logger.manager.loggerDict.items()
            if isinstance(logger, logging.Logger)
            and (name.startswith("pdfminer.") or name.startswith("pypdf."))
        )
        original_state = [
            (logger, logger.level, logger.handlers[:], logger.propagate)
            for logger in parser_loggers
        ]
        sink = _ParserDiagnosticSink()
        try:
            for logger in parser_loggers:
                logger.setLevel(logging.NOTSET)
                logger.handlers = [sink]
                logger.propagate = False
            with redirect_stderr(StringIO()):
                yield sink
        finally:
            for logger, level, handlers, propagate in original_state:
                logger.setLevel(level)
                logger.handlers = handlers
                logger.propagate = propagate


class DetectionStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    NO_REDACTIONS = "NO_REDACTIONS"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class DetectionResult:
    status: DetectionStatus
    targets: tuple[RedactionTarget, ...]
    source_sha256: str
    page_count: int
    project_id: str
    redacted_document_version_id: str
    detector_version: str = DETECTOR_VERSION
    reason_code: str | None = None
    ignored_artwork_count: int = 0


@dataclass(frozen=True)
class _PaintedRectangle:
    bbox: tuple[float, float, float, float]
    operation_index: int
    color: tuple[float, ...]


def _unsupported(
    source_sha256: str,
    *,
    page_count: int,
    project_id: str,
    redacted_document_version_id: str,
    reason_code: str,
) -> DetectionResult:
    return DetectionResult(
        status=DetectionStatus.UNSUPPORTED,
        targets=(),
        source_sha256=source_sha256,
        page_count=page_count,
        project_id=project_id,
        redacted_document_version_id=redacted_document_version_id,
        reason_code=reason_code,
    )


def _as_floats(values: list[Any]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _near_black(color: Any) -> bool:
    if isinstance(color, (int, float)):
        return float(color) <= 0.1
    if not isinstance(color, (list, tuple)):
        return False
    components = tuple(float(value) for value in color)
    if len(components) == 1:
        return components[0] <= 0.1
    if len(components) == 3:
        return max(components) <= 0.1
    if len(components) == 4:
        cyan, magenta, yellow, black = components
        red = (1.0 - cyan) * (1.0 - black)
        green = (1.0 - magenta) * (1.0 - black)
        blue = (1.0 - yellow) * (1.0 - black)
        return max(red, green, blue) <= 0.1
    return False


def _intersects(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(
        first[3], second[3]
    ) > max(first[1], second[1])


def _char_bbox(char: dict[str, Any]) -> tuple[float, float, float, float]:
    return (float(char["x0"]), float(char["y0"]), float(char["x1"]), float(char["y1"]))


def _same_text_flow(
    rectangle: tuple[float, float, float, float],
    chars: list[dict[str, Any]],
) -> bool:
    x0, y0, x1, y1 = rectangle
    nearby_gap = max(36.0, (y1 - y0) * 3.0)
    for char in chars:
        if not str(char.get("text", "")).strip():
            continue
        cx0, cy0, cx1, cy1 = _char_bbox(char)
        vertical_overlap = min(y1, cy1) - max(y0, cy0)
        if vertical_overlap <= 0:
            continue
        if cx1 <= x0 and x0 - cx1 <= nearby_gap:
            return True
        if cx0 >= x1 and cx0 - x1 <= nearby_gap:
            return True
    return False


def _aligned_with_text_block(
    rectangle: tuple[float, float, float, float],
    chars: list[dict[str, Any]],
) -> bool:
    x0, _, x1, _ = rectangle
    for char in chars:
        if not str(char.get("text", "")).strip():
            continue
        cx0, _, cx1, _ = _char_bbox(char)
        horizontal_overlap = min(x1, cx1) - max(x0, cx0)
        if horizontal_overlap > 0:
            return True
    return False


def _has_ambiguous_multicolumn_layout(
    chars: list[dict[str, Any]], page_width: float
) -> bool:
    lines: list[list[dict[str, Any]]] = []
    visible_chars = [
        char for char in chars if str(char.get("text", "")).strip()
    ]
    for char in sorted(
        visible_chars, key=lambda item: (float(item["top"]), float(item["x0"]))
    ):
        if not lines or abs(float(lines[-1][0]["top"]) - float(char["top"])) > 3.0:
            lines.append([char])
        else:
            lines[-1].append(char)

    spans: list[tuple[float, float]] = []
    line_span_starts: list[list[float]] = []
    for line in lines:
        ordered = sorted(line, key=lambda item: float(item["x0"]))
        if not ordered:
            continue
        typical_height = sorted(
            float(char["bottom"]) - float(char["top"]) for char in ordered
        )[len(ordered) // 2]
        segment_gap = max(8.0, typical_height * 0.75)
        span_start = float(ordered[0]["x0"])
        current_line_starts = [span_start]
        previous = ordered[0]
        for current in ordered[1:]:
            if float(current["x0"]) - float(previous["x1"]) > segment_gap:
                spans.append((span_start, float(previous["x1"])))
                span_start = float(current["x0"])
                current_line_starts.append(span_start)
            previous = current
        spans.append((span_start, float(previous["x1"])))
        line_span_starts.append(current_line_starts)

    start_tolerance = page_width * 0.05
    column_starts: list[tuple[float, int]] = []
    for start, _ in sorted(spans):
        for index, (known_start, count) in enumerate(column_starts):
            if abs(start - known_start) <= start_tolerance:
                new_count = count + 1
                column_starts[index] = (
                    (known_start * count + start) / new_count,
                    new_count,
                )
                break
        else:
            column_starts.append((start, 1))

    repeated_starts = [start for start, count in column_starts if count >= 2]
    minimum_column_separation = page_width * 0.15
    split_line = any(
        abs(first - second) >= minimum_column_separation
        for starts in line_span_starts
        for index, first in enumerate(starts)
        for second in starts[index + 1 :]
    )
    sparse_secondary_column = any(
        abs(repeated - start) >= minimum_column_separation
        for repeated in repeated_starts
        for start, _ in spans
    )
    return split_line or sparse_secondary_column


def _identity_matrix(operands: list[Any]) -> bool:
    if len(operands) != 6:
        return False
    values = _as_floats(operands)
    expected = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    return all(
        isclose(value, wanted, abs_tol=1e-9) for value, wanted in zip(values, expected)
    )


def _painted_rectangles(
    reader: PdfReader, page_index: int
) -> tuple[list[_PaintedRectangle], int] | None:
    page = reader.pages[page_index]
    stream = ContentStream(page.get_contents(), reader)
    fill_color: tuple[float, ...] = (0.0,)
    color_stack: list[tuple[float, ...]] = []
    pending_rectangles: list[tuple[tuple[float, float, float, float], int]] = []
    painted: list[_PaintedRectangle] = []
    last_text_index = -1

    for index, (operands, operator) in enumerate(stream.operations):
        if operator in _UNSAFE_OPERATORS:
            return None
        if operator == b"cm" and not _identity_matrix(operands):
            return None
        if operator == b"Tr" and _as_floats(operands) != (0.0,):
            return None
        if operator in _TEXT_SHOW_OPERATORS:
            last_text_index = index
        elif operator == b"q":
            color_stack.append(fill_color)
        elif operator == b"Q":
            if not color_stack:
                return None
            fill_color = color_stack.pop()
            pending_rectangles.clear()
        elif operator == b"g":
            fill_color = _as_floats(operands)
        elif operator == b"rg":
            fill_color = _as_floats(operands)
        elif operator == b"k":
            fill_color = _as_floats(operands)
        elif operator == b"re":
            x, y, width, height = _as_floats(operands)
            x0, x1 = sorted((x, x + width))
            y0, y1 = sorted((y, y + height))
            pending_rectangles.append(((x0, y0, x1, y1), index))
        elif operator in _FILL_OPERATORS:
            painted.extend(
                _PaintedRectangle(
                    bbox=bbox,
                    operation_index=operation_index,
                    color=fill_color,
                )
                for bbox, operation_index in pending_rectangles
            )
            pending_rectangles.clear()
        elif operator in {b"n", b"S", b"s"}:
            pending_rectangles.clear()

    if color_stack:
        return None
    return painted, last_text_index


def _matching_paint_index(
    bbox: tuple[float, float, float, float],
    painted: list[_PaintedRectangle],
) -> int | None:
    for rectangle in painted:
        if not _near_black(rectangle.color):
            continue
        if all(
            isclose(actual, expected, abs_tol=0.02)
            for actual, expected in zip(bbox, rectangle.bbox)
        ):
            return rectangle.operation_index
    return None


def _target_for_rectangle(
    *,
    project_id: str,
    redacted_document_version_id: str,
    page_index: int,
    page_width: float,
    page_height: float,
    rectangle_index: int,
    bbox: tuple[float, float, float, float],
) -> RedactionTarget:
    normalized = (
        round(bbox[0] / page_width, 8),
        round(bbox[1] / page_height, 8),
        round(bbox[2] / page_width, 8),
        round(bbox[3] / page_height, 8),
    )
    identity_material = json.dumps(
        (
            project_id,
            redacted_document_version_id,
            page_index,
            normalized,
            DETECTOR_VERSION,
        ),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = sha256(identity_material.encode("utf-8")).hexdigest()[:24]
    return RedactionTarget(
        target_id=f"target-{digest}",
        target_version=f"target-{digest}-{DETECTOR_VERSION}",
        project_id=project_id,
        redacted_document_version_id=redacted_document_version_id,
        page_index=page_index,
        normalized_bbox=normalized,
        visible_context_locator=(
            f"page:{page_index};bbox:"
            + ",".join(f"{value:.8f}" for value in normalized)
        ),
        scope_status=ScopeStatus.SUPPORTED,
        detection_method="vector-near-black-text-occlusion",
        detection_evidence=DetectionEvidence(
            rectangle_count=1,
            source_object_ids=(f"page-{page_index}-rect-{rectangle_index}",),
        ),
        detector_version=DETECTOR_VERSION,
    )


def detect_targets(
    pdf_bytes: bytes,
    *,
    project_id: str,
    redacted_document_version_id: str,
) -> DetectionResult:
    source_sha256 = sha256(pdf_bytes).hexdigest()
    try:
        with _suppress_parser_debug_logs() as diagnostics:
            reader = PdfReader(BytesIO(pdf_bytes), strict=True)
            page_count = len(reader.pages)
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                if diagnostics.seen:
                    return _unsupported(
                        source_sha256,
                        page_count=page_count,
                        project_id=project_id,
                        redacted_document_version_id=redacted_document_version_id,
                        reason_code="MALFORMED_PDF",
                    )
                if len(pdf.pages) != page_count or page_count == 0:
                    return _unsupported(
                        source_sha256,
                        page_count=page_count,
                        project_id=project_id,
                        redacted_document_version_id=redacted_document_version_id,
                        reason_code="MALFORMED_PDF",
                    )

                targets: list[RedactionTarget] = []
                ignored_artwork_count = 0
                for page_index, page in enumerate(pdf.pages):
                    pdf_page = reader.pages[page_index]
                    rotation = (
                        int(pdf_page.get("/Rotate", 0) or 0) % 360
                    )
                    if rotation:
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="ROTATED_PAGE",
                        )
                    cropbox = tuple(float(value) for value in pdf_page.cropbox)
                    mediabox = tuple(float(value) for value in pdf_page.mediabox)
                    if any(
                        not isclose(actual, expected, abs_tol=0.02)
                        for actual, expected in zip(cropbox, mediabox)
                    ):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="NONDEFAULT_PAGE_BOUNDARY",
                        )
                    if page.images or page.annots:
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="IMAGE_OR_ANNOTATION_CONTENT",
                        )
                    chars = list(page.chars)
                    if not any(str(char.get("text", "")).strip() for char in chars):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="NO_VISIBLE_TEXT",
                        )
                    if any(not bool(char.get("upright", True)) for char in chars):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="ROTATED_TEXT",
                        )
                    if any(
                        str(char.get("text", "")).strip()
                        and not _near_black(char.get("non_stroking_color"))
                        for char in chars
                    ):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="TEXT_VISIBILITY_UNCERTAIN",
                        )
                    paint_evidence = _painted_rectangles(reader, page_index)
                    if paint_evidence is None:
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="COMPLEX_PAGE_GRAPHICS",
                        )
                    painted, last_text_index = paint_evidence
                    uncertain_rectangles = [
                        rectangle
                        for rectangle in painted
                        if not _near_black(rectangle.color)
                    ]
                    if any(
                        any(
                            str(char.get("text", "")).strip()
                            and _intersects(rectangle.bbox, _char_bbox(char))
                            for char in chars
                        )
                        or _same_text_flow(rectangle.bbox, chars)
                        for rectangle in uncertain_rectangles
                    ):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="TEXT_VISIBILITY_UNCERTAIN",
                        )
                    lines = list(page.lines)
                    if len(lines) >= 2:
                        line_art_bbox = (
                            min(float(line["x0"]) for line in lines),
                            min(float(line["y0"]) for line in lines),
                            max(float(line["x1"]) for line in lines),
                            max(float(line["y1"]) for line in lines),
                        )
                        if any(
                            str(char.get("text", "")).strip()
                            and _intersects(line_art_bbox, _char_bbox(char))
                            for char in chars
                        ):
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code="TABLE_OR_LINE_ART_CONTENT",
                            )
                        ignored_artwork_count += len(lines)
                    for line in lines:
                        half_width = max(float(line.get("linewidth", 1.0)), 1.0) / 2
                        line_bbox = (
                            float(line["x0"]) - half_width,
                            float(line["y0"]) - half_width,
                            float(line["x1"]) + half_width,
                            float(line["y1"]) + half_width,
                        )
                        if any(
                            str(char.get("text", "")).strip()
                            and _intersects(line_bbox, _char_bbox(char))
                            for char in chars
                        ):
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code="TABLE_OR_LINE_ART_CONTENT",
                            )
                    stroked_rectangles = [
                        rect
                        for rect in page.rects
                        if bool(rect.get("stroke"))
                        and not bool(rect.get("fill"))
                    ]
                    for stroked_rectangle in stroked_rectangles:
                        stroked_bbox = (
                            float(stroked_rectangle["x0"]),
                            float(stroked_rectangle["y0"]),
                            float(stroked_rectangle["x1"]),
                            float(stroked_rectangle["y1"]),
                        )
                        if any(
                            str(char.get("text", "")).strip()
                            and _intersects(stroked_bbox, _char_bbox(char))
                            for char in chars
                        ):
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code="TABLE_OR_LINE_ART_CONTENT",
                            )
                        ignored_artwork_count += 1
                    for curve in page.curves:
                        half_width = (
                            max(float(curve.get("linewidth", 1.0)), 1.0) / 2
                            if bool(curve.get("stroke"))
                            else 0.0
                        )
                        curve_bbox = (
                            float(curve["x0"]) - half_width,
                            float(curve["y0"]) - half_width,
                            float(curve["x1"]) + half_width,
                            float(curve["y1"]) + half_width,
                        )
                        if any(
                            str(char.get("text", "")).strip()
                            and _intersects(curve_bbox, _char_bbox(char))
                            for char in chars
                        ) or _same_text_flow(curve_bbox, chars):
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code=(
                                    "TABLE_OR_LINE_ART_CONTENT"
                                    if bool(curve.get("stroke"))
                                    else "NON_RECTANGULAR_BLACK_SHAPE"
                                ),
                            )
                        ignored_artwork_count += 1
                    rectangles = [
                        rect
                        for rect in page.rects
                        if bool(rect.get("fill"))
                        and _near_black(rect.get("non_stroking_color"))
                    ]
                    rectangle_boxes = [
                        (
                            float(rectangle["x0"]),
                            float(rectangle["y0"]),
                            float(rectangle["x1"]),
                            float(rectangle["y1"]),
                        )
                        for rectangle in rectangles
                    ]
                    text_related_boxes = [
                        bbox
                        for bbox in rectangle_boxes
                        if any(
                            str(char.get("text", "")).strip()
                            and _intersects(bbox, _char_bbox(char))
                            for char in chars
                        )
                        or _same_text_flow(bbox, chars)
                        or _aligned_with_text_block(bbox, chars)
                    ]
                    if any(
                        _intersects(first, second)
                        for index, first in enumerate(text_related_boxes)
                        for second in text_related_boxes[index + 1 :]
                    ):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="OVERLAPPING_REDACTION_RECTANGLES",
                        )
                    for rectangle_index, rectangle in enumerate(rectangles):
                        bbox = (
                            float(rectangle["x0"]),
                            float(rectangle["y0"]),
                            float(rectangle["x1"]),
                            float(rectangle["y1"]),
                        )
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                        if (
                            width <= 0
                            or height <= 0
                            or width >= float(page.width) * 0.8
                            or height >= float(page.height) * 0.25
                        ):
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code="UNSUPPORTED_RECTANGLE_GEOMETRY",
                            )
                        paint_index = _matching_paint_index(bbox, painted)
                        if paint_index is None or paint_index <= last_text_index:
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code="PAINT_ORDER_UNCERTAIN",
                            )
                        occluded_chars = [
                            char
                            for char in chars
                            if str(char.get("text", "")).strip()
                            and _intersects(bbox, _char_bbox(char))
                        ]
                        if not occluded_chars:
                            if _same_text_flow(bbox, chars) or _aligned_with_text_block(
                                bbox, chars
                            ):
                                return _unsupported(
                                    source_sha256,
                                    page_count=page_count,
                                    project_id=project_id,
                                    redacted_document_version_id=redacted_document_version_id,
                                    reason_code="AMBIGUOUS_TEXT_FLOW_RECTANGLE",
                                )
                            ignored_artwork_count += 1
                            continue
                        line_tops = [float(char["top"]) for char in occluded_chars]
                        if max(line_tops) - min(line_tops) > 3.0:
                            return _unsupported(
                                source_sha256,
                                page_count=page_count,
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                reason_code="AMBIGUOUS_MULTILINE_RECTANGLE",
                            )
                        targets.append(
                            _target_for_rectangle(
                                project_id=project_id,
                                redacted_document_version_id=redacted_document_version_id,
                                page_index=page_index,
                                page_width=float(page.width),
                                page_height=float(page.height),
                                rectangle_index=rectangle_index,
                                bbox=bbox,
                            )
                        )
                    if _has_ambiguous_multicolumn_layout(chars, float(page.width)):
                        return _unsupported(
                            source_sha256,
                            page_count=page_count,
                            project_id=project_id,
                            redacted_document_version_id=redacted_document_version_id,
                            reason_code="AMBIGUOUS_TEXT_LAYOUT",
                        )

                if diagnostics.seen:
                    return _unsupported(
                        source_sha256,
                        page_count=page_count,
                        project_id=project_id,
                        redacted_document_version_id=redacted_document_version_id,
                        reason_code="MALFORMED_PDF",
                    )
                targets.sort(
                    key=lambda target: (
                        target.page_index,
                        -target.normalized_bbox[3],
                        target.normalized_bbox[0],
                    )
                )
                status = (
                    DetectionStatus.SUPPORTED
                    if targets
                    else DetectionStatus.NO_REDACTIONS
                )
                return DetectionResult(
                    status=status,
                    targets=tuple(targets),
                    source_sha256=source_sha256,
                    page_count=page_count,
                    project_id=project_id,
                    redacted_document_version_id=redacted_document_version_id,
                    ignored_artwork_count=ignored_artwork_count,
                )
    except Exception:
        return _unsupported(
            source_sha256,
            page_count=0,
            project_id=project_id,
            redacted_document_version_id=redacted_document_version_id,
            reason_code="MALFORMED_PDF",
        )
