from __future__ import annotations

from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest

from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.reference_registry import (
    APPROVED_SYNTHETIC_REFERENCE_PAIRS,
    resolve_approved_synthetic_pair,
)


PROJECT_ID = "project-rl-mvp-003"
REDACTED_VERSION_ID = "redacted-document-v1"
REDACTED_CANONICAL_VERSION_ID = "redacted-canonical-v1"
REFERENCE_VERSION_ID = "reference-document-v1"
REFERENCE_CANONICAL_VERSION_ID = "reference-canonical-v1"
EXPECTED_REDACTED_SHA256 = (
    "2ce777d994b52281fe51f15194f4beecf47e1feb6332dfdc6873114dfe37faa2"
)
EXPECTED_REFERENCE_SHA256 = (
    "8316ae58f9a6e86c42764f3c47cb37a7e284e546eceba84dcfb3934bc5908eb4"
)


def _two_boxes(tmp_path: Path) -> tuple[bytes, bytes]:
    redacted_path, reference_path = make_synthetic_pair("two_boxes", tmp_path)
    return redacted_path.read_bytes(), reference_path.read_bytes()


def test_two_boxes_pins_are_literal_and_reproducible(tmp_path: Path) -> None:
    first_redacted, first_reference = _two_boxes(tmp_path / "first")
    second_redacted, second_reference = _two_boxes(tmp_path / "second")

    assert first_redacted == second_redacted
    assert first_reference == second_reference
    assert sha256(first_redacted).hexdigest() == EXPECTED_REDACTED_SHA256
    assert sha256(first_reference).hexdigest() == EXPECTED_REFERENCE_SHA256
    assert len(APPROVED_SYNTHETIC_REFERENCE_PAIRS) == 1
    pair = APPROVED_SYNTHETIC_REFERENCE_PAIRS[0]
    assert pair.redacted_sha256 == EXPECTED_REDACTED_SHA256
    assert pair.reference_sha256 == EXPECTED_REFERENCE_SHA256
    assert pair.project_id == PROJECT_ID
    assert pair.redacted_document_id == "synthetic-two-boxes-redacted"
    assert pair.redacted_version_id == REDACTED_VERSION_ID
    assert pair.redacted_canonical_version_id == REDACTED_CANONICAL_VERSION_ID
    assert pair.reference_document_id == "synthetic-two-boxes-reference"
    assert pair.reference_version_id == REFERENCE_VERSION_ID
    assert pair.reference_canonical_version_id == REFERENCE_CANONICAL_VERSION_ID
    assert pair.fixture_case == "two_boxes"
    assert pair.generator_provenance == (
        "redaction_lab.fixtures.make_synthetic_pair@fixture-generator-v1"
    )


def test_registry_records_and_collection_are_immutable(tmp_path: Path) -> None:
    pair = APPROVED_SYNTHETIC_REFERENCE_PAIRS[0]

    with pytest.raises(FrozenInstanceError):
        pair.project_id = "forged-project"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        APPROVED_SYNTHETIC_REFERENCE_PAIRS.append(pair)  # type: ignore[attr-defined]


def test_resolver_requires_both_actual_byte_streams(tmp_path: Path) -> None:
    redacted_pdf, reference_pdf = _two_boxes(tmp_path)

    resolved = resolve_approved_synthetic_pair(
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        project_id=PROJECT_ID,
        redacted_version_id=REDACTED_VERSION_ID,
        reference_version_id=REFERENCE_VERSION_ID,
    )

    assert resolved is APPROVED_SYNTHETIC_REFERENCE_PAIRS[0]


@pytest.mark.parametrize(
    ("redacted_mutation", "reference_mutation"),
    [
        (lambda value: value + b"\x00", lambda value: value),
        (lambda value: value, lambda value: value + b"\x00"),
        (lambda value: value, lambda value: value[:-1]),
    ],
)
def test_resolver_rejects_changed_bytes(
    redacted_mutation,
    reference_mutation,
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf = _two_boxes(tmp_path)

    assert resolve_approved_synthetic_pair(
        redacted_pdf=redacted_mutation(redacted_pdf),
        reference_pdf=reference_mutation(reference_pdf),
        project_id=PROJECT_ID,
        redacted_version_id=REDACTED_VERSION_ID,
        reference_version_id=REFERENCE_VERSION_ID,
    ) is None


def test_resolver_rejects_swapped_pdf_roles(tmp_path: Path) -> None:
    redacted_pdf, reference_pdf = _two_boxes(tmp_path)

    assert resolve_approved_synthetic_pair(
        redacted_pdf=reference_pdf,
        reference_pdf=redacted_pdf,
        project_id=PROJECT_ID,
        redacted_version_id=REDACTED_VERSION_ID,
        reference_version_id=REFERENCE_VERSION_ID,
    ) is None


@pytest.mark.parametrize(
    ("project_id", "redacted_version_id", "reference_version_id"),
    [
        ("forged-project", REDACTED_VERSION_ID, REFERENCE_VERSION_ID),
        (PROJECT_ID, "forged-redacted-version", REFERENCE_VERSION_ID),
        (PROJECT_ID, REDACTED_VERSION_ID, "forged-reference-version"),
    ],
)
def test_resolver_rejects_incorrect_pairing_claims(
    project_id: str,
    redacted_version_id: str,
    reference_version_id: str,
    tmp_path: Path,
) -> None:
    redacted_pdf, reference_pdf = _two_boxes(tmp_path)

    assert resolve_approved_synthetic_pair(
        redacted_pdf=redacted_pdf,
        reference_pdf=reference_pdf,
        project_id=project_id,
        redacted_version_id=redacted_version_id,
        reference_version_id=reference_version_id,
    ) is None
