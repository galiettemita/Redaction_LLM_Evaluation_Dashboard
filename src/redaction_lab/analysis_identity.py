"""Stable identities shared by isolated analysis and host material validation."""

from __future__ import annotations

from hashlib import sha256
import json


PREDICTION_SOURCE_VERSION = "prediction-source-v1"
VECTOR_ANALYSIS_METHOD = "vector-near-black-text-occlusion"
RASTER_ANALYSIS_METHOD = "raster-ocr-near-black-text-occlusion"


def source_ids(
    project_id: str,
    source_sha256: str,
    detector_version: str,
    canonicalizer_version: str,
) -> tuple[str, str, str]:
    material = json.dumps(
        (
            PREDICTION_SOURCE_VERSION,
            project_id,
            source_sha256,
            detector_version,
            canonicalizer_version,
        ),
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = sha256(material).hexdigest()
    return (
        f"source-{digest}",
        f"redacted-{digest}-{detector_version}",
        f"canonical-{digest}-{canonicalizer_version}",
    )


def target_id(
    *,
    project_id: str,
    redacted_document_version_id: str,
    page_index: int,
    normalized_bbox: tuple[float, float, float, float],
    detector_version: str,
    analysis_method: str,
) -> str:
    identity: tuple[object, ...] = (
        project_id,
        redacted_document_version_id,
        page_index,
        normalized_bbox,
        detector_version,
    )
    if analysis_method != VECTOR_ANALYSIS_METHOD:
        identity += (analysis_method,)
    digest = sha256(
        json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()[:24]
    return f"target-{digest}"
