from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import logging
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from redaction_lab.canonical import canonicalize_redacted
from redaction_lab.contracts import (
    DocumentRole,
    DocumentVersion,
    PredictionManifest,
    PredictionSettings,
    ReferenceScoreability,
    ReferenceStatus,
)
from redaction_lab.fixtures import make_synthetic_pair
from redaction_lab.pdf_detector import DetectionStatus, detect_targets
from redaction_lab.reference import (
    _Candidate,
    _Token,
    _globally_supported,
    align_reference,
)


PROJECT_ID = "project-rl-mvp-003"
REDACTED_VERSION_ID = "redacted-document-v1"
REDACTED_CANONICAL_ID = "redacted-canonical-v1"
REFERENCE_VERSION_ID = "reference-document-v1"
REFERENCE_CANONICAL_ID = "reference-canonical-v1"
MAPPING_VERSION = "mapping-v1"
_DEFAULT_TRUSTED_RECORD = object()


def _pdf_bytes(draw) -> bytes:
    output = BytesIO()
    canvas = Canvas(output, pagesize=letter, invariant=1, pageCompression=0)
    canvas.setFont("Helvetica", 11)
    draw(canvas)
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def _overlay(
    canvas: Canvas, line_x: float, y: float, prefix: str, secret: str
) -> None:
    x = line_x + stringWidth(prefix, "Helvetica", 11) - 1
    width = stringWidth(secret, "Helvetica", 11) + 2
    canvas.setFillColorRGB(0, 0, 0)
    canvas.rect(x, y - 3, width, 14, stroke=0, fill=1)


def _redacted_context(pdf_bytes: bytes):
    detection = detect_targets(
        pdf_bytes,
        project_id=PROJECT_ID,
        redacted_document_version_id=REDACTED_VERSION_ID,
    )
    assert detection.status is DetectionStatus.SUPPORTED
    canonical = canonicalize_redacted(
        pdf_bytes,
        detection,
        project_id=PROJECT_ID,
        redacted_document_version_id=REDACTED_VERSION_ID,
        canonical_document_version_id=REDACTED_CANONICAL_ID,
    )
    return canonical, detection.targets


def _fixture_context(case: str, tmp_path: Path):
    redacted_path, reference_path = make_synthetic_pair(case, tmp_path / case)
    canonical, targets = _redacted_context(redacted_path.read_bytes())
    return canonical, targets, reference_path.read_bytes()


def _trusted_reference(
    reference_pdf: bytes,
    **updates,
) -> DocumentVersion:
    record = DocumentVersion(
        document_id="reference-document",
        version_id=REFERENCE_VERSION_ID,
        project_id=PROJECT_ID,
        sha256=sha256(reference_pdf).hexdigest(),
        role=DocumentRole.REFERENCE,
        created_at=datetime(2026, 10, 8, tzinfo=timezone.utc),
        provenance="trusted synthetic test registry",
        access_policy="synthetic-test-only",
    )
    return record.model_copy(update=updates)


def _align(
    canonical,
    targets,
    reference_pdf: bytes | None,
    *,
    trusted_reference_document=_DEFAULT_TRUSTED_RECORD,
    reference_document_version_id: str | None = None,
):
    if reference_document_version_id is None and reference_pdf is not None:
        reference_document_version_id = REFERENCE_VERSION_ID
    if trusted_reference_document is _DEFAULT_TRUSTED_RECORD:
        trusted_reference_document = (
            _trusted_reference(reference_pdf) if reference_pdf is not None else None
        )
    return align_reference(
        canonical,
        reference_pdf,
        targets=targets,
        trusted_reference_document=trusted_reference_document,
        reference_document_version_id=reference_document_version_id,
        reference_canonical_version_id=(
            REFERENCE_CANONICAL_ID if reference_pdf is not None else None
        ),
        mapping_version=MAPPING_VERSION,
    )


@pytest.mark.parametrize("supported_side", ["left", "right"])
def test_global_support_requires_both_non_boundary_textual_sides(
    supported_side: str,
) -> None:
    candidate = _Candidate(
        start=2,
        end=3,
        left=("before",),
        right=("after",),
        left_boundary=False,
        right_boundary=False,
    )
    redacted_tokens = (
        _Token("before", 0, 6, 0),
        _Token("after", 20, 25, 0),
    )
    matching_pairs = (
        frozenset({(0, 1)})
        if supported_side == "left"
        else frozenset({(1, 3)})
    )

    assert not _globally_supported(
        candidate,
        marker_start=10,
        marker_end=19,
        redacted_tokens=redacted_tokens,
        matching_pairs=matching_pairs,
    )


def test_extracts_exact_spans_between_anchors(tmp_path: Path) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)

    mappings = _align(canonical, targets, reference_pdf)

    assert [mapping.status for mapping in mappings] == [
        ReferenceStatus.CONFIRMED,
        ReferenceStatus.CONFIRMED,
    ]
    assert [mapping.exact_revealed_text for mapping in mappings] == [
        "Agent Cedar",
        "12 paper stars",
    ]
    assert all(
        mapping.scoreability is ReferenceScoreability.SCOREABLE
        for mapping in mappings
    )
    assert all(mapping.reference_token_locator for mapping in mappings)
    assert all(mapping.left_anchor_evidence for mapping in mappings)
    assert all(
        mapping.right_anchor_evidence or mapping.right_document_boundary
        for mapping in mappings
    )
    assert all(mapping.candidate_unique is True for mapping in mappings)
    assert all(mapping.complete_revelation is True for mapping in mappings)
    assert all(mapping.readable is True for mapping in mappings)
    assert all(mapping.reliably_aligned is True for mapping in mappings)
    assert all(
        mapping.reference_canonical_hash
        != sha256(mapping.exact_revealed_text.encode("utf-8")).hexdigest()
        for mapping in mappings
        if mapping.exact_revealed_text is not None
    )


def test_repeated_anchors_are_ambiguous_and_hide_candidates(tmp_path: Path) -> None:
    canonical, targets, reference_pdf = _fixture_context(
        "repeated_anchors", tmp_path
    )

    mappings = _align(canonical, targets, reference_pdf)

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.AMBIGUOUS
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)
    assert all(
        mapping.scoreability is ReferenceScoreability.NOT_SCOREABLE
        for mapping in mappings
    )
    assert "BLUE" not in str(mappings)
    assert "GREEN" not in str(mappings)


def test_wrong_document_is_conflicting_and_hides_reference_text(
    tmp_path: Path,
) -> None:
    canonical, targets, _ = _fixture_context("two_boxes", tmp_path)
    wrong_reference = _pdf_bytes(
        lambda canvas: canvas.drawString(
            72, 700, "Unrelated synthetic release with different visible context."
        )
    )

    mappings = _align(canonical, targets, wrong_reference)

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.CONFLICTING
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)
    assert "Unrelated synthetic release" not in str(mappings)


def test_wrong_reference_with_matching_local_neighbors_is_conflicting() -> None:
    prefix = "preamble stable alpha "
    suffix = " beta stable tail"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 720, "trusted document opening context")
        canvas.drawString(72, 700, f"{prefix}SECRET{suffix}")
        canvas.drawString(72, 680, "trusted document closing context")
        _overlay(canvas, 72, 700, prefix, "SECRET")

    def draw_wrong_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 720, "unrelated release opening material")
        canvas.drawString(72, 700, f"junk alpha WRONG beta noise")
        canvas.drawString(72, 680, "unrelated release closing material")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))
    reference_pdf = _pdf_bytes(draw_wrong_reference)

    mapping = _align(canonical, targets, reference_pdf)[0]

    assert mapping.status is ReferenceStatus.CONFLICTING
    assert mapping.exact_revealed_text is None
    assert "WRONG" not in str(mapping)


def test_unmatched_reference_context_outside_target_invalidates_pairing() -> None:
    prefix = "alpha "
    suffix = " beta"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 720, "preamble")
        canvas.drawString(72, 700, f"{prefix}SECRET{suffix}")
        canvas.drawString(72, 680, "tail")
        _overlay(canvas, 72, 700, prefix, "SECRET")

    def draw_wrong_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 720, "preamble EXTRA")
        canvas.drawString(72, 700, "alpha WRONG beta")
        canvas.drawString(72, 680, "UNRELATED tail")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))
    reference_pdf = _pdf_bytes(draw_wrong_reference)

    mapping = _align(canonical, targets, reference_pdf)[0]

    assert mapping.status is ReferenceStatus.CONFLICTING
    assert mapping.exact_revealed_text is None
    assert "WRONG" not in str(mapping)


def test_interior_geometry_fallback_cannot_replace_missing_textual_side() -> None:
    prefix = "alpha before "

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}SECRET")
        canvas.drawString(72, 680, "after omega")
        _overlay(canvas, 72, 700, prefix, "SECRET")

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}SECRET")
        canvas.drawString(72, 680, "changed omega")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.CONFLICTING
    assert mapping.scoreability is ReferenceScoreability.NOT_SCOREABLE
    assert mapping.exact_revealed_text is None


def test_globally_reordered_target_passages_invalidate_every_mapping() -> None:
    first_prefix = "The first synthetic value was "
    second_prefix = "The second synthetic value was "

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{first_prefix}ALPHA.")
        canvas.drawString(72, 664, f"{second_prefix}BRAVO.")
        _overlay(canvas, 72, 700, first_prefix, "ALPHA")
        _overlay(canvas, 72, 664, second_prefix, "BRAVO")

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{second_prefix}BRAVO.")
        canvas.drawString(72, 664, f"{first_prefix}ALPHA.")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mappings = _align(canonical, targets, _pdf_bytes(draw_reference))

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.CONFLICTING
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


def test_reordered_fixture_lines_cannot_leave_earlier_target_confirmed(
    tmp_path: Path,
) -> None:
    canonical, targets, _ = _fixture_context("two_boxes", tmp_path)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 738, "SYNTHETIC TEST DATA - NOT REAL")
        canvas.drawString(
            72, 700, "The synthetic package contained 12 paper stars."
        )
        canvas.drawString(
            72, 664, "The synthetic courier was Agent Cedar at 09:00."
        )
        canvas.drawString(72, 36, "case=two_boxes; release=reference")

    mappings = _align(canonical, targets, _pdf_bytes(draw_reference))

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.CONFLICTING
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


def test_one_sided_anchor_cannot_invent_target_endpoint() -> None:
    prefix = "Visible context "

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}SECRET")
        _overlay(canvas, 72, 700, prefix, "SECRET")

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}WRONG EXTRA")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.CONFLICTING
    assert mapping.exact_revealed_text is None
    assert "WRONG" not in str(mapping)


@pytest.mark.parametrize(
    "case,hidden_text",
    [
        ("still_hidden_reference", "ORCHARD SEVEN"),
        ("partially_revealed_reference", "SEVEN"),
    ],
)
def test_hidden_or_partial_reference_is_not_scoreable_and_never_leaks(
    case: str,
    hidden_text: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    canonical, targets, reference_pdf = _fixture_context(case, tmp_path)

    with caplog.at_level(logging.DEBUG):
        mappings = _align(canonical, targets, reference_pdf)

    assert {mapping.status for mapping in mappings} == {ReferenceStatus.PARTIAL}
    assert all(mapping.exact_revealed_text is None for mapping in mappings)
    assert all(
        mapping.scoreability is ReferenceScoreability.NOT_SCOREABLE
        for mapping in mappings
    )
    assert hidden_text not in str(mappings)
    assert hidden_text not in caplog.text


def test_reflowed_still_hidden_reference_marker_cannot_be_confirmed() -> None:
    prefix = "The relocated synthetic destination was "
    secret = "ORCHARD SEVEN"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret}.")
        _overlay(canvas, 72, 700, prefix, secret)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 680, f"{prefix}{secret}.")
        _overlay(canvas, 72, 680, prefix, secret)

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.PARTIAL
    assert mapping.exact_revealed_text is None
    assert secret not in str(mapping)


def test_reflowed_partially_revealed_reference_cannot_confirm_visible_prefix() -> None:
    prefix = "The relocated synthetic authorization was "
    secret = "ORCHARD SEVEN"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret}.")
        _overlay(canvas, 72, 700, prefix, secret)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 680, f"{prefix}{secret}.")
        _overlay(canvas, 72, 680, f"{prefix}ORCHARD ", "SEVEN")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.PARTIAL
    assert mapping.exact_revealed_text is None
    assert secret not in str(mapping)


def test_reflow_without_physical_source_bounds_is_not_scoreable() -> None:
    prefix = "The courier was "
    secret = "Agent Cedar"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 740, "Page 1")
        canvas.drawString(72, 700, f"{prefix}{secret} at noon.")
        _overlay(canvas, 72, 700, prefix, secret)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 740, "Page 9")
        canvas.drawString(72, 700, f"{prefix}Agent")
        canvas.drawString(72, 680, "Cedar at noon.")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.AMBIGUOUS
    assert mapping.scoreability is ReferenceScoreability.NOT_SCOREABLE
    assert mapping.exact_revealed_text is None


def test_reflowed_boundary_punctuation_fails_closed_without_exact_span() -> None:
    prefix = "The courier was "
    secret = "(Agent Cedar),"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret} at noon.")
        _overlay(canvas, 72, 700, prefix, secret)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}(Agent")
        canvas.drawString(72, 680, "Cedar), at noon.")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.AMBIGUOUS
    assert mapping.exact_revealed_text is None
    assert secret not in str(mapping)


@pytest.mark.parametrize(
    "secret",
    ["(Agent-Cedar),", "Agent  Cedar", " SECRET", "SECRET ", " SECRET "],
)
def test_exact_reference_preserves_covered_punctuation_and_whitespace(
    secret: str,
) -> None:
    prefix = "The exact synthetic value was "

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret} at noon.")
        _overlay(canvas, 72, 700, prefix, secret)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret} at noon.")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.CONFIRMED
    assert mapping.exact_revealed_text == secret


def test_character_locator_tracks_the_matched_duplicate_occurrence() -> None:
    prefix = "ALPHA then "
    secret = "ALPHA"

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret} at end.")
        _overlay(canvas, 72, 700, prefix, secret)

    def draw_reference(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}{secret} at end.")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.CONFIRMED
    assert mapping.exact_revealed_text == secret
    assert mapping.reference_token_locator is not None
    assert mapping.reference_token_locator.endswith("chars:11-16")


def test_adjacent_targets_without_two_textual_sides_are_not_scoreable(
    tmp_path: Path,
) -> None:
    canonical, targets, reference_pdf = _fixture_context(
        "adjacent_boxes", tmp_path
    )

    mappings = _align(canonical, targets, reference_pdf)

    assert all(mapping.status is ReferenceStatus.CONFLICTING for mapping in mappings)
    assert all(
        mapping.scoreability is ReferenceScoreability.NOT_SCOREABLE
        for mapping in mappings
    )
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


def test_missing_reference_returns_absent_for_every_target(tmp_path: Path) -> None:
    canonical, targets, _ = _fixture_context("two_boxes", tmp_path)

    mappings = _align(canonical, targets, None)

    assert len(mappings) == len(targets)
    assert {mapping.status for mapping in mappings} == {ReferenceStatus.ABSENT}
    assert all(mapping.reference_document_version_id is None for mapping in mappings)
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


def test_reference_without_trusted_document_binding_is_not_confirmed(
    tmp_path: Path,
) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)

    mappings = _align(
        canonical,
        targets,
        reference_pdf,
        trusted_reference_document=None,
    )

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.CONFLICTING
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


@pytest.mark.parametrize(
    ("record_updates", "expected_version"),
    [
        ({"role": DocumentRole.REDACTED}, REFERENCE_VERSION_ID),
        ({"project_id": "other-project"}, REFERENCE_VERSION_ID),
        ({"version_id": "other-reference-version"}, REFERENCE_VERSION_ID),
        ({"sha256": "0" * 64}, REFERENCE_VERSION_ID),
    ],
)
def test_mismatched_trusted_reference_metadata_is_not_confirmed(
    record_updates: dict[str, object],
    expected_version: str,
    tmp_path: Path,
) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)
    trusted = _trusted_reference(reference_pdf, **record_updates)

    mappings = _align(
        canonical,
        targets,
        reference_pdf,
        trusted_reference_document=trusted,
        reference_document_version_id=expected_version,
    )

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.CONFLICTING
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


def test_trusted_reference_version_must_match_expected_version(
    tmp_path: Path,
) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)
    trusted = _trusted_reference(reference_pdf)

    mappings = _align(
        canonical,
        targets,
        reference_pdf,
        trusted_reference_document=trusted,
        reference_document_version_id="unexpected-reference-version",
    )

    assert {mapping.status for mapping in mappings} == {
        ReferenceStatus.CONFLICTING
    }
    assert all(mapping.exact_revealed_text is None for mapping in mappings)


@pytest.mark.parametrize("at_start", [True, False])
def test_document_boundary_target_uses_explicit_boundary_evidence(
    at_start: bool,
) -> None:
    if at_start:
        visible = "visible tail"

        def draw_redacted(canvas: Canvas) -> None:
            canvas.drawString(72, 700, f"ALPHA {visible}")
            _overlay(canvas, 72, 700, "", "ALPHA")

        def draw_reference(canvas: Canvas) -> None:
            canvas.drawString(72, 700, f"ALPHA {visible}")

    else:
        visible = "Visible head "

        def draw_redacted(canvas: Canvas) -> None:
            canvas.drawString(72, 700, f"{visible}OMEGA")
            _overlay(canvas, 72, 700, visible, "OMEGA")

        def draw_reference(canvas: Canvas) -> None:
            canvas.drawString(72, 700, f"{visible}OMEGA")

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    mapping = _align(canonical, targets, _pdf_bytes(draw_reference))[0]

    assert mapping.status is ReferenceStatus.CONFIRMED
    assert mapping.exact_revealed_text == ("ALPHA" if at_start else "OMEGA")
    assert mapping.left_document_boundary is at_start
    assert mapping.right_document_boundary is (not at_start)


def test_identity_mismatch_and_tampered_canonical_are_rejected(
    tmp_path: Path,
) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)
    wrong_target = targets[0].model_copy(update={"project_id": "other-project"})

    with pytest.raises(ValueError, match="target identity mismatch"):
        _align(canonical, (wrong_target, *targets[1:]), reference_pdf)

    tampered = canonical.model_copy(update={"canonical_text": "tampered"})
    with pytest.raises(ValueError, match="canonical hash mismatch"):
        _align(tampered, targets, reference_pdf)


def test_unexpected_or_duplicate_markers_are_rejected(tmp_path: Path) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)
    duplicated_text = canonical.canonical_text + (
        f" [[TARGET:{targets[0].target_id}]] [[TARGET:unexpected-target]]"
    )
    tampered = canonical.model_copy(
        update={
            "canonical_text": duplicated_text,
            "canonical_hash": sha256(duplicated_text.encode("utf-8")).hexdigest(),
        }
    )

    with pytest.raises(ValueError, match="canonical marker invariant"):
        _align(tampered, targets, reference_pdf)


def test_malformed_reference_fails_closed_without_payload_leak(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    canonical, targets, _ = _fixture_context("two_boxes", tmp_path)
    payload = b"malformed SYNTHETIC_REFERENCE_TRAP"

    with caplog.at_level(logging.DEBUG):
        mappings = _align(canonical, targets, payload)

    assert {mapping.status for mapping in mappings} == {ReferenceStatus.UNREADABLE}
    assert all(mapping.exact_revealed_text is None for mapping in mappings)
    assert "SYNTHETIC_REFERENCE_TRAP" not in str(mappings)
    assert "SYNTHETIC_REFERENCE_TRAP" not in caplog.text


def test_mapping_identity_and_evidence_are_deterministic(tmp_path: Path) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)

    first = _align(canonical, targets, reference_pdf)
    second = _align(canonical, targets, reference_pdf)

    assert first == second
    assert [mapping.mapping_id for mapping in first] == [
        mapping.mapping_id for mapping in second
    ]
    assert all(mapping.mapping_version == MAPPING_VERSION for mapping in first)


def test_changed_reference_spacing_is_unconfirmed_with_distinct_identity() -> None:
    prefix = "The exact identity was "

    def draw_redacted(canvas: Canvas) -> None:
        canvas.drawString(72, 700, f"{prefix}Agent Cedar at noon.")
        _overlay(canvas, 72, 700, prefix, "Agent Cedar")

    def reference(secret: str) -> bytes:
        return _pdf_bytes(
            lambda canvas: canvas.drawString(
                72, 700, f"{prefix}{secret} at noon."
            )
        )

    canonical, targets = _redacted_context(_pdf_bytes(draw_redacted))

    single = _align(canonical, targets, reference("Agent Cedar"))[0]
    doubled = _align(canonical, targets, reference("Agent  Cedar"))[0]

    assert single.status is ReferenceStatus.CONFIRMED
    assert doubled.status is ReferenceStatus.AMBIGUOUS
    assert single.exact_revealed_text != doubled.exact_revealed_text
    assert single.reference_canonical_hash != doubled.reference_canonical_hash
    assert single.mapping_id != doubled.mapping_id


def test_confirmed_reference_never_enters_prediction_manifest(tmp_path: Path) -> None:
    canonical, targets, reference_pdf = _fixture_context("two_boxes", tmp_path)
    mapping = _align(canonical, targets, reference_pdf)[0]
    target = targets[0]
    marker = f"[[TARGET:{target.target_id}]]"
    manifest = PredictionManifest(
        manifest_id="manifest-rl-mvp-003",
        manifest_version="manifest-v1",
        project_id=PROJECT_ID,
        run_id="run-rl-mvp-003",
        target_id=target.target_id,
        target_version=target.target_version,
        canonical_document_version_id=canonical.canonical_document_version_id,
        canonical_document_hash=canonical.canonical_hash,
        canonical_redacted_text=canonical.canonical_text,
        target_marker=marker,
        other_redaction_markers=tuple(
            f"[[TARGET:{other.target_id}]]" for other in targets[1:]
        ),
        prompt_id="prompt-redacted-only",
        prompt_version="prompt-v1",
        model_id="synthetic-model",
        settings=PredictionSettings(temperature=0.0),
    )

    serialized = manifest.model_dump_json()

    assert mapping.status is ReferenceStatus.CONFIRMED
    assert mapping.exact_revealed_text not in serialized
    assert REFERENCE_VERSION_ID not in serialized
