"""Safe visible-text canonicalization for redacted PDFs."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from typing import Any

import pdfplumber

from redaction_lab.contracts import CanonicalRedactedDocument
from redaction_lab.pdf_detector import (
    DetectionResult,
    DetectionStatus,
    _suppress_parser_debug_logs,
    detect_targets,
)


CANONICALIZER_VERSION = "safe-visible-text-v1"


def _intersects(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(
        first[3], second[3]
    ) > max(first[1], second[1])


def _target_bbox(
    target: Any, page_width: float, page_height: float
) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = target.normalized_bbox
    return (x0 * page_width, y0 * page_height, x1 * page_width, y1 * page_height)


def _page_text(page: Any, targets: tuple[Any, ...]) -> str:
    page_width = float(page.width)
    page_height = float(page.height)
    target_boxes = [
        (target, _target_bbox(target, page_width, page_height)) for target in targets
    ]
    events: list[tuple[float, float, int, str]] = []
    for char_index, char in enumerate(page.chars):
        bbox = (
            float(char["x0"]),
            float(char["y0"]),
            float(char["x1"]),
            float(char["y1"]),
        )
        if any(_intersects(bbox, target_bbox) for _, target_bbox in target_boxes):
            continue
        events.append(
            (
                float(char["top"]),
                float(char["x0"]),
                char_index,
                str(char.get("text", "")),
            )
        )
    marker_offset = len(events) + 1
    for target_index, (target, bbox) in enumerate(target_boxes):
        top = page_height - bbox[3]
        events.append(
            (
                top,
                bbox[0],
                marker_offset + target_index,
                f" [[TARGET:{target.target_id}]] ",
            )
        )

    lines: list[list[tuple[float, float, int, str]]] = []
    for event in sorted(events, key=lambda item: (item[0], item[1], item[2])):
        if not lines or abs(lines[-1][0][0] - event[0]) > 3.0:
            lines.append([event])
        else:
            lines[-1].append(event)

    rendered_lines: list[str] = []
    for line in lines:
        pieces = [
            event[3] for event in sorted(line, key=lambda item: (item[1], item[2]))
        ]
        rendered = re.sub(r"[ \t]+", " ", "".join(pieces)).strip()
        if rendered:
            rendered_lines.append(rendered)
    return "\n".join(rendered_lines)


def canonicalize_redacted(
    pdf_bytes: bytes,
    detection: DetectionResult,
    *,
    project_id: str,
    redacted_document_version_id: str,
    canonical_document_version_id: str,
) -> CanonicalRedactedDocument:
    if detection.status is DetectionStatus.UNSUPPORTED:
        raise ValueError("unsupported detection cannot be canonicalized")
    if (
        detection.project_id != project_id
        or detection.redacted_document_version_id != redacted_document_version_id
    ):
        raise ValueError("detection identity mismatch")
    source_sha256 = sha256(pdf_bytes).hexdigest()
    if source_sha256 != detection.source_sha256:
        raise ValueError("source hash mismatch")
    verified_detection = detect_targets(
        pdf_bytes,
        project_id=project_id,
        redacted_document_version_id=redacted_document_version_id,
    )
    if verified_detection != detection:
        raise ValueError("detection verification mismatch")

    try:
        with _suppress_parser_debug_logs():
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                if len(pdf.pages) != detection.page_count:
                    raise ValueError("page count mismatch")
                pages: list[str] = []
                for page_index, page in enumerate(pdf.pages):
                    page_targets = tuple(
                        target
                        for target in detection.targets
                        if target.page_index == page_index
                    )
                    pages.append(_page_text(page, page_targets))
    except Exception:
        raise ValueError("canonical PDF parse failed") from None

    canonical_text = "\n\n".join(pages)
    target_ids = tuple(target.target_id for target in detection.targets)
    for target_id in target_ids:
        marker = f"[[TARGET:{target_id}]]"
        if canonical_text.count(marker) != 1:
            raise ValueError("canonical marker invariant failed")

    return CanonicalRedactedDocument(
        canonical_document_version_id=canonical_document_version_id,
        project_id=project_id,
        redacted_document_version_id=redacted_document_version_id,
        canonical_hash=sha256(canonical_text.encode("utf-8")).hexdigest(),
        canonical_text=canonical_text,
        target_ids=target_ids,
        canonicalizer_version=CANONICALIZER_VERSION,
    )
