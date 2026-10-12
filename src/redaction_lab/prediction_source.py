"""Application-owned, redacted-PDF-derived prediction source records.

This module is an internal ingestion boundary, not a public authorization API.
The surrounding trusted service must authenticate project access before calling it.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
import re

from redaction_lab.canonical import CANONICALIZER_VERSION, canonicalize_redacted
from redaction_lab.contracts import (
    CanonicalRedactedDocument,
    DetectionEvidence,
    DocumentRole,
    RedactionTarget,
    ScopeStatus,
)
from redaction_lab.pdf_detector import (
    DETECTOR_VERSION,
    DetectionStatus,
    detect_targets,
)


PREDICTION_SOURCE_VERSION = "prediction-source-v1"
PREDICTION_SOURCE_PROVENANCE = "internal-redacted-pdf-byte-ingestion-v1"
_TARGET_MARKER = re.compile(r"\[\[TARGET:([^\]]+)\]\]")


@dataclass(frozen=True)
class PredictionSource:
    source_id: str
    source_version: str
    project_id: str
    source_sha256: str
    role: DocumentRole
    redacted_document_version_id: str
    detector_version: str
    canonicalizer_version: str
    canonical_document: CanonicalRedactedDocument
    targets: tuple[RedactionTarget, ...]
    provenance: str

    @property
    def target_versions(self) -> tuple[str, ...]:
        return tuple(target.target_version for target in self.targets)


@dataclass(frozen=True)
class PredictionTargetObservation:
    """Untrusted geometry reported by the isolated parser."""

    page_index: int
    normalized_bbox: tuple[float, float, float, float]
    rectangle_index: int


@dataclass(frozen=True)
class PredictionSourceMaterial:
    """Non-authoritative worker material from which the host builds a source."""

    source_sha256: str
    page_count: int
    detector_version: str
    canonicalizer_version: str
    canonical_text: str
    canonical_hash: str
    targets: tuple[PredictionTargetObservation, ...]


def _source_ids(project_id: str, source_sha256: str) -> tuple[str, str, str]:
    material = json.dumps(
        (
            PREDICTION_SOURCE_VERSION,
            project_id,
            source_sha256,
            DETECTOR_VERSION,
            CANONICALIZER_VERSION,
        ),
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = sha256(material).hexdigest()
    return (
        f"source-{digest}",
        f"redacted-{digest}-{DETECTOR_VERSION}",
        f"canonical-{digest}-{CANONICALIZER_VERSION}",
    )


def _target_from_observation(
    observation: PredictionTargetObservation,
    *,
    project_id: str,
    redacted_document_version_id: str,
) -> RedactionTarget:
    bbox = tuple(float(value) for value in observation.normalized_bbox)
    if (
        isinstance(observation.page_index, bool)
        or isinstance(observation.rectangle_index, bool)
        or observation.page_index < 0
        or observation.rectangle_index < 0
        or len(bbox) != 4
        or not all(isfinite(value) and 0.0 <= value <= 1.0 for value in bbox)
        or bbox[0] >= bbox[2]
        or bbox[1] >= bbox[3]
    ):
        raise ValueError("invalid worker target observation")
    identity_material = json.dumps(
        (
            project_id,
            redacted_document_version_id,
            observation.page_index,
            bbox,
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
        page_index=observation.page_index,
        normalized_bbox=bbox,
        visible_context_locator=(
            f"page:{observation.page_index};bbox:"
            + ",".join(f"{value:.8f}" for value in bbox)
        ),
        scope_status=ScopeStatus.SUPPORTED,
        detection_method="vector-near-black-text-occlusion",
        detection_evidence=DetectionEvidence(
            rectangle_count=1,
            source_object_ids=(
                f"page-{observation.page_index}-rect-{observation.rectangle_index}",
            ),
        ),
        detector_version=DETECTOR_VERSION,
    )


def _expected_target(target: RedactionTarget) -> RedactionTarget:
    prefix = f"page-{target.page_index}-rect-"
    identifiers = target.detection_evidence.source_object_ids
    if len(identifiers) != 1 or not identifiers[0].startswith(prefix):
        raise ValueError("stored prediction source target evidence failure")
    try:
        rectangle_index = int(identifiers[0][len(prefix) :])
    except ValueError as error:
        raise ValueError("stored prediction source target evidence failure") from error
    return _target_from_observation(
        PredictionTargetObservation(
            page_index=target.page_index,
            normalized_bbox=target.normalized_bbox,
            rectangle_index=rectangle_index,
        ),
        project_id=target.project_id,
        redacted_document_version_id=target.redacted_document_version_id,
    )


def validate_prediction_source(source: PredictionSource) -> None:
    """Fail closed if an immutable stored source no longer self-validates."""

    source_id, redacted_version, canonical_version = _source_ids(
        source.project_id, source.source_sha256
    )
    canonical = source.canonical_document
    if (
        source.source_version != PREDICTION_SOURCE_VERSION
        or source.source_id != source_id
        or source.role is not DocumentRole.REDACTED
        or source.redacted_document_version_id != redacted_version
        or source.detector_version != DETECTOR_VERSION
        or source.canonicalizer_version != CANONICALIZER_VERSION
        or source.provenance != PREDICTION_SOURCE_PROVENANCE
        or canonical.project_id != source.project_id
        or canonical.redacted_document_version_id != redacted_version
        or canonical.canonical_document_version_id != canonical_version
        or canonical.canonicalizer_version != CANONICALIZER_VERSION
        or sha256(canonical.canonical_text.encode("utf-8")).hexdigest()
        != canonical.canonical_hash
        or not source.targets
        or canonical.target_ids
        != tuple(target.target_id for target in source.targets)
        or len(set(canonical.target_ids)) != len(canonical.target_ids)
        or tuple(_TARGET_MARKER.findall(canonical.canonical_text))
        != canonical.target_ids
        or tuple(source.targets)
        != tuple(
            sorted(
                source.targets,
                key=lambda target: (
                    target.page_index,
                    -target.normalized_bbox[3],
                    target.normalized_bbox[0],
                ),
            )
        )
    ):
        raise ValueError("stored prediction source integrity failure")
    for target in source.targets:
        if (
            target.project_id != source.project_id
            or target.redacted_document_version_id != redacted_version
            or target.scope_status is not ScopeStatus.SUPPORTED
            or target.detector_version != DETECTOR_VERSION
            or target != _expected_target(target)
        ):
            raise ValueError("stored prediction source target integrity failure")
    evidence_ids = tuple(
        identifier
        for target in source.targets
        for identifier in target.detection_evidence.source_object_ids
    )
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("stored prediction source target evidence failure")


def build_prediction_source_from_material(
    pdf_bytes: bytes,
    *,
    project_id: str,
    material: PredictionSourceMaterial,
) -> PredictionSource:
    """Build host-owned Task-4 authority from bounded isolated-worker material.

    This verifies structure and provenance bindings without parsing the PDF. It
    deliberately cannot establish the semantic correctness of parser output.
    """

    project_id = project_id.strip()
    if not project_id:
        raise ValueError("project context must be nonblank")
    actual_sha256 = sha256(pdf_bytes).hexdigest()
    if material.source_sha256 != actual_sha256:
        raise ValueError("worker material does not match input bytes")
    if (
        material.detector_version != DETECTOR_VERSION
        or material.canonicalizer_version != CANONICALIZER_VERSION
    ):
        raise ValueError("worker material uses an unapproved code version")
    if not 1 <= material.page_count <= 100:
        raise ValueError("worker page count is outside the approved limit")
    if not material.targets or len(material.targets) > 10_000:
        raise ValueError("worker material must contain a bounded target set")
    if len(material.canonical_text.encode("utf-8")) > 12 * 1024 * 1024:
        raise ValueError("worker canonical text exceeds the approved limit")
    if sha256(material.canonical_text.encode("utf-8")).hexdigest() != material.canonical_hash:
        raise ValueError("worker canonical text hash mismatch")
    source_id, redacted_version, canonical_version = _source_ids(
        project_id, actual_sha256
    )
    targets = tuple(
        _target_from_observation(
            observation,
            project_id=project_id,
            redacted_document_version_id=redacted_version,
        )
        for observation in material.targets
    )
    if any(target.page_index >= material.page_count for target in targets):
        raise ValueError("worker target page is outside the document")
    if len({target.target_id for target in targets}) != len(targets):
        raise ValueError("worker target observations are not unique")
    evidence_ids = tuple(
        identifier
        for target in targets
        for identifier in target.detection_evidence.source_object_ids
    )
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("worker target evidence identifiers are not unique")
    expected_order = tuple(
        sorted(
            targets,
            key=lambda target: (
                target.page_index,
                -target.normalized_bbox[3],
                target.normalized_bbox[0],
            ),
        )
    )
    if targets != expected_order:
        raise ValueError("worker targets are not in canonical order")
    canonical = CanonicalRedactedDocument(
        canonical_document_version_id=canonical_version,
        project_id=project_id,
        redacted_document_version_id=redacted_version,
        canonical_hash=material.canonical_hash,
        canonical_text=material.canonical_text,
        target_ids=tuple(target.target_id for target in targets),
        canonicalizer_version=CANONICALIZER_VERSION,
    )
    source = PredictionSource(
        source_id=source_id,
        source_version=PREDICTION_SOURCE_VERSION,
        project_id=project_id,
        source_sha256=actual_sha256,
        role=DocumentRole.REDACTED,
        redacted_document_version_id=redacted_version,
        detector_version=DETECTOR_VERSION,
        canonicalizer_version=CANONICALIZER_VERSION,
        canonical_document=canonical,
        targets=targets,
        provenance=PREDICTION_SOURCE_PROVENANCE,
    )
    validate_prediction_source(source)
    return source


def derive_prediction_source(pdf_bytes: bytes, *, project_id: str) -> PredictionSource:
    """Derive authority only from actual redacted PDF bytes and project context.

    ``project_id`` is an identity selector. The trusted caller is responsible for
    authenticating access to that project before invoking this internal function.
    """

    project_id = project_id.strip()
    if not project_id:
        raise ValueError("project context must be nonblank")
    source_sha256 = sha256(pdf_bytes).hexdigest()
    source_id, redacted_version, canonical_version = _source_ids(
        project_id, source_sha256
    )
    detection = detect_targets(
        pdf_bytes,
        project_id=project_id,
        redacted_document_version_id=redacted_version,
    )
    if detection.status is not DetectionStatus.SUPPORTED or not detection.targets:
        raise ValueError("source must be a supported redacted PDF with text targets")
    canonical = canonicalize_redacted(
        pdf_bytes,
        detection,
        project_id=project_id,
        redacted_document_version_id=redacted_version,
        canonical_document_version_id=canonical_version,
    )
    source = PredictionSource(
        source_id=source_id,
        source_version=PREDICTION_SOURCE_VERSION,
        project_id=project_id,
        source_sha256=source_sha256,
        role=DocumentRole.REDACTED,
        redacted_document_version_id=redacted_version,
        detector_version=DETECTOR_VERSION,
        canonicalizer_version=CANONICALIZER_VERSION,
        canonical_document=canonical,
        targets=detection.targets,
        provenance=PREDICTION_SOURCE_PROVENANCE,
    )
    validate_prediction_source(source)
    return source
