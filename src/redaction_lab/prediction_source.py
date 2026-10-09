"""Application-owned, redacted-PDF-derived prediction source records.

This module is an internal ingestion boundary, not a public authorization API.
The surrounding trusted service must authenticate project access before calling it.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from redaction_lab.canonical import CANONICALIZER_VERSION, canonicalize_redacted
from redaction_lab.contracts import (
    CanonicalRedactedDocument,
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
    ):
        raise ValueError("stored prediction source integrity failure")
    for target in source.targets:
        if (
            target.project_id != source.project_id
            or target.redacted_document_version_id != redacted_version
            or target.scope_status is not ScopeStatus.SUPPORTED
            or target.detector_version != DETECTOR_VERSION
        ):
            raise ValueError("stored prediction source target integrity failure")


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
