"""Immutable allowlist for the October 12 synthetic reference demonstration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest


@dataclass(frozen=True, slots=True)
class ApprovedSyntheticReferencePair:
    """One application-owned, byte-pinned synthetic PDF pairing."""

    project_id: str
    redacted_document_id: str
    redacted_version_id: str
    redacted_sha256: str
    reference_document_id: str
    reference_version_id: str
    reference_sha256: str
    fixture_case: str
    generator_provenance: str


APPROVED_SYNTHETIC_REFERENCE_PAIRS = (
    ApprovedSyntheticReferencePair(
        project_id="project-rl-mvp-003",
        redacted_document_id="synthetic-two-boxes-redacted",
        redacted_version_id="redacted-document-v1",
        redacted_sha256=(
            "2ce777d994b52281fe51f15194f4beecf47e1feb6332dfdc6873114dfe37faa2"
        ),
        reference_document_id="synthetic-two-boxes-reference",
        reference_version_id="reference-document-v1",
        reference_sha256=(
            "8316ae58f9a6e86c42764f3c47cb37a7e284e546eceba84dcfb3934bc5908eb4"
        ),
        fixture_case="two_boxes",
        generator_provenance=(
            "redaction_lab.fixtures.make_synthetic_pair@fixture-generator-v1"
        ),
    ),
)


def resolve_approved_synthetic_pair(
    *,
    redacted_pdf: bytes,
    reference_pdf: bytes,
    project_id: str,
    redacted_version_id: str,
    reference_version_id: str,
) -> ApprovedSyntheticReferencePair | None:
    """Resolve only when both actual byte streams and their pairing match."""

    redacted_digest = sha256(redacted_pdf).hexdigest()
    reference_digest = sha256(reference_pdf).hexdigest()
    for pair in APPROVED_SYNTHETIC_REFERENCE_PAIRS:
        if (
            pair.project_id == project_id
            and pair.redacted_version_id == redacted_version_id
            and pair.reference_version_id == reference_version_id
            and compare_digest(pair.redacted_sha256, redacted_digest)
            and compare_digest(pair.reference_sha256, reference_digest)
        ):
            return pair
    return None
