"""Deterministic, fail-closed alignment of redacted and reference PDFs."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from io import BytesIO
import json
import re
import pdfplumber

from redaction_lab.canonical import canonicalize_redacted
from redaction_lab.contracts import (
    CanonicalRedactedDocument,
    RedactionTarget,
    ReferenceMapping,
    ReferenceScoreability,
    ReferenceStatus,
    ScopeStatus,
)
from redaction_lab.pdf_detector import (
    DetectionResult,
    DetectionStatus,
    _suppress_parser_debug_logs,
    detect_targets,
)


MAPPING_METHOD_VERSION = "text-first-reference-v1"
GLOBAL_ALIGNMENT_VERSION = "monotonic-word-sequence-v1"
_MARKER_RE = re.compile(r"\[\[TARGET:([^\]]+)\]\]")
_WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)


@dataclass(frozen=True)
class _Token:
    normalized: str
    start: int
    end: int
    line: int


@dataclass(frozen=True)
class _Candidate:
    start: int
    end: int
    left: tuple[str, ...]
    right: tuple[str, ...]
    left_boundary: bool
    right_boundary: bool


def _normalize(value: str) -> str:
    return value.casefold().replace("’", "'")


def _tokens(text: str) -> tuple[_Token, ...]:
    marker_ranges = tuple(
        (match.start(), match.end()) for match in _MARKER_RE.finditer(text)
    )
    tokens: list[_Token] = []
    for match in _WORD_RE.finditer(text):
        if any(start <= match.start() < end for start, end in marker_ranges):
            continue
        tokens.append(
            _Token(
                normalized=_normalize(match.group()),
                start=match.start(),
                end=match.end(),
                line=text.count("\n", 0, match.start()),
            )
        )
    return tuple(tokens)


def _occurrences(haystack: tuple[str, ...], needle: tuple[str, ...]) -> list[int]:
    if not needle or len(needle) > len(haystack):
        return []
    return [
        index
        for index in range(len(haystack) - len(needle) + 1)
        if haystack[index : index + len(needle)] == needle
    ]


def _validate_inputs(
    redacted: CanonicalRedactedDocument,
    targets: tuple[RedactionTarget, ...],
) -> tuple[tuple[int, int, str], ...]:
    if (
        sha256(redacted.canonical_text.encode("utf-8")).hexdigest()
        != redacted.canonical_hash
    ):
        raise ValueError("canonical hash mismatch")
    if len(targets) != len(redacted.target_ids):
        raise ValueError("target identity mismatch")
    target_ids = tuple(target.target_id for target in targets)
    if target_ids != redacted.target_ids or len(set(target_ids)) != len(target_ids):
        raise ValueError("target identity mismatch")
    if any(
        target.project_id != redacted.project_id
        or target.redacted_document_version_id != redacted.redacted_document_version_id
        or target.scope_status is not ScopeStatus.SUPPORTED
        for target in targets
    ):
        raise ValueError("target identity mismatch")

    markers = tuple(
        (match.start(), match.end(), match.group(1))
        for match in _MARKER_RE.finditer(redacted.canonical_text)
    )
    if (
        len(markers) != len(targets)
        or tuple(marker[2] for marker in markers) != target_ids
        or any(
            redacted.canonical_text.count(f"[[TARGET:{target_id}]]") != 1
            for target_id in target_ids
        )
    ):
        raise ValueError("canonical marker invariant failed")
    return markers


def _mapping_id(
    redacted: CanonicalRedactedDocument,
    target: RedactionTarget,
    reference_document_version_id: str | None,
    reference_canonical_version_id: str | None,
    reference_hash: str | None,
    mapping_version: str,
    status: ReferenceStatus,
) -> str:
    identity = json.dumps(
        {
            "mapping_version": mapping_version,
            "method": MAPPING_METHOD_VERSION,
            "project_id": redacted.project_id,
            "redacted_hash": redacted.canonical_hash,
            "reference_document_version_id": reference_document_version_id,
            "reference_canonical_version_id": reference_canonical_version_id,
            "reference_hash": reference_hash,
            "status": status.value,
            "target_id": target.target_id,
            "target_version": target.target_version,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"mapping-{sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def _unconfirmed(
    redacted: CanonicalRedactedDocument,
    target: RedactionTarget,
    *,
    status: ReferenceStatus,
    mapping_version: str,
    reference_document_version_id: str | None,
    reference_canonical_version_id: str | None,
    reference_hash: str | None,
    candidate_unique: bool | None = None,
    complete_revelation: bool | None = None,
    readable: bool | None = None,
) -> ReferenceMapping:
    return ReferenceMapping(
        mapping_id=_mapping_id(
            redacted,
            target,
            reference_document_version_id,
            reference_canonical_version_id,
            reference_hash,
            mapping_version,
            status,
        ),
        mapping_version=mapping_version,
        project_id=redacted.project_id,
        target_id=target.target_id,
        target_version=target.target_version,
        redacted_document_version_id=redacted.redacted_document_version_id,
        reference_document_version_id=reference_document_version_id,
        status=status,
        scoreability=ReferenceScoreability.NOT_SCOREABLE,
        reference_canonical_version_id=reference_canonical_version_id,
        reference_canonical_hash=reference_hash,
        candidate_unique=candidate_unique,
        complete_revelation=complete_revelation,
        readable=readable,
        reliably_aligned=False,
        mapping_method_version=MAPPING_METHOD_VERSION,
        provenance="deterministic text-first reference alignment",
    )


def _reference_document(
    reference_pdf: bytes,
    *,
    project_id: str,
    reference_document_version_id: str,
    reference_canonical_version_id: str,
) -> tuple[DetectionResult, CanonicalRedactedDocument] | None:
    try:
        detection = detect_targets(
            reference_pdf,
            project_id=project_id,
            redacted_document_version_id=reference_document_version_id,
        )
        if detection.status is DetectionStatus.UNSUPPORTED:
            return None
        canonical = canonicalize_redacted(
            reference_pdf,
            detection,
            project_id=project_id,
            redacted_document_version_id=reference_document_version_id,
            canonical_document_version_id=reference_canonical_version_id,
        )
        return detection, canonical
    except Exception:
        return None


def _line_context(
    text: str,
    marker_start: int,
    marker_end: int,
) -> tuple[tuple[str, ...], tuple[str, ...], bool, bool, bool]:
    line_start = text.rfind("\n", 0, marker_start) + 1
    next_newline = text.find("\n", marker_end)
    line_end = len(text) if next_newline < 0 else next_newline
    left = tuple(token.normalized for token in _tokens(text[line_start:marker_start]))
    right = tuple(token.normalized for token in _tokens(text[marker_end:line_end]))
    left_boundary = not _tokens(text[:marker_start])
    right_boundary = not _tokens(text[marker_end:])
    other_marker_on_line = bool(
        _MARKER_RE.search(text[line_start:marker_start])
        or _MARKER_RE.search(text[marker_end:line_end])
    )
    return left, right, left_boundary, right_boundary, other_marker_on_line


def _anchor_candidates(
    reference_tokens: tuple[_Token, ...],
    left: tuple[str, ...],
    right: tuple[str, ...],
    left_boundary: bool,
    right_boundary: bool,
) -> list[_Candidate]:
    words = tuple(token.normalized for token in reference_tokens)
    candidates: list[_Candidate] = []
    max_width = max(len(left), len(right), 1)
    for width in range(1, max_width + 1):
        left_anchor = left[-min(width, len(left)) :] if left else ()
        right_anchor = right[: min(width, len(right))] if right else ()
        left_occurrences = _occurrences(words, left_anchor) if left_anchor else [-1]
        right_occurrences = (
            _occurrences(words, right_anchor) if right_anchor else [len(words)]
        )
        found: list[_Candidate] = []
        for left_at in left_occurrences:
            start = left_at + len(left_anchor) if left_anchor else 0
            for right_at in right_occurrences:
                end = right_at if right_anchor else len(words)
                if end <= start:
                    continue
                if not right_anchor and start < len(reference_tokens):
                    line = reference_tokens[start].line
                    end = next(
                        (
                            index
                            for index in range(start, len(reference_tokens))
                            if reference_tokens[index].line != line
                        ),
                        len(reference_tokens),
                    )
                if not left_anchor and end > 0:
                    line = reference_tokens[end - 1].line
                    start = next(
                        (
                            index + 1
                            for index in range(end - 1, -1, -1)
                            if reference_tokens[index].line != line
                        ),
                        0,
                    )
                if end <= start:
                    continue
                found.append(
                    _Candidate(
                        start=start,
                        end=end,
                        left=left_anchor,
                        right=right_anchor,
                        left_boundary=left_boundary and not left_anchor,
                        right_boundary=right_boundary and not right_anchor,
                    )
                )
        unique = list(dict.fromkeys(found))
        if len(unique) == 1:
            return unique
        if len(unique) > 1:
            candidates = unique
    return candidates


def _hidden_reference_match_count(
    reference_text: str,
    left: tuple[str, ...],
    right: tuple[str, ...],
) -> int:
    matches = 0
    for marker in _MARKER_RE.finditer(reference_text):
        hidden_left, hidden_right, _, _, _ = _line_context(
            reference_text, marker.start(), marker.end()
        )
        left_matches = bool(left) and bool(_occurrences(hidden_left, left))
        right_matches = bool(right) and bool(_occurrences(hidden_right, right))
        if left_matches or right_matches:
            matches += 1
    return matches


def _candidate_contains_marker(
    reference_text: str,
    reference_tokens: tuple[_Token, ...],
    candidate: _Candidate,
) -> bool:
    start = reference_tokens[candidate.start].start
    end = reference_tokens[candidate.end - 1].end
    return bool(_MARKER_RE.search(reference_text, start, end))


def _globally_supported(
    candidate: _Candidate,
    marker_start: int,
    marker_end: int,
    redacted_tokens: tuple[_Token, ...],
    matching_pairs: frozenset[tuple[int, int]],
) -> bool:
    left_red = [
        index
        for index, token in enumerate(redacted_tokens)
        if token.end <= marker_start
    ]
    right_red = [
        index
        for index, token in enumerate(redacted_tokens)
        if token.start >= marker_end
    ]
    left_ok = candidate.left_boundary
    if candidate.left and left_red:
        width = len(candidate.left)
        red_start = left_red[-1] - width + 1
        ref_start = candidate.start - width
        left_ok = red_start >= 0 and all(
            (red_start + offset, ref_start + offset) in matching_pairs
            for offset in range(width)
        )
    right_ok = candidate.right_boundary
    if candidate.right and right_red:
        width = len(candidate.right)
        red_start = right_red[0]
        ref_start = candidate.end
        right_ok = all(
            (red_start + offset, ref_start + offset) in matching_pairs
            for offset in range(width)
        )
    return left_ok or right_ok


def _intersects(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(
        first[3], second[3]
    ) > max(first[1], second[1])


def _absolute_box(
    target: RedactionTarget, width: float, height: float
) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = target.normalized_bbox
    return x0 * width, y0 * height, x1 * width, y1 * height


def _reference_boxes_overlap(
    target: RedactionTarget,
    detection: DetectionResult,
) -> bool:
    return any(
        other.page_index == target.page_index
        and _intersects(target.normalized_bbox, other.normalized_bbox)
        for other in detection.targets
    )


def _geometry_quote(
    reference_pdf: bytes,
    target: RedactionTarget,
    detection: DetectionResult,
) -> str | None:
    try:
        with _suppress_parser_debug_logs():
            with pdfplumber.open(BytesIO(reference_pdf)) as pdf:
                if target.page_index >= len(pdf.pages):
                    return None
                page = pdf.pages[target.page_index]
                box = _absolute_box(target, float(page.width), float(page.height))
                reference_boxes = tuple(
                    _absolute_box(other, float(page.width), float(page.height))
                    for other in detection.targets
                    if other.page_index == target.page_index
                )
                chars = []
                for index, char in enumerate(page.chars):
                    char_box = (
                        float(char["x0"]),
                        float(char["y0"]),
                        float(char["x1"]),
                        float(char["y1"]),
                    )
                    if not _intersects(char_box, box):
                        continue
                    if any(_intersects(char_box, hidden) for hidden in reference_boxes):
                        continue
                    chars.append(
                        (
                            float(char["top"]),
                            float(char["x0"]),
                            index,
                            str(char.get("text", "")),
                        )
                    )
        quote = "".join(item[3] for item in sorted(chars)).strip()
        return quote or None
    except Exception:
        return None


def _geometry_candidate(
    reference_pdf: bytes,
    target: RedactionTarget,
    detection: DetectionResult,
    reference_tokens: tuple[_Token, ...],
    left: tuple[str, ...],
    right: tuple[str, ...],
    left_boundary: bool,
    right_boundary: bool,
) -> list[_Candidate]:
    quote = _geometry_quote(reference_pdf, target, detection)
    if quote is None:
        return []
    quote_words = tuple(token.normalized for token in _tokens(quote))
    words = tuple(token.normalized for token in reference_tokens)
    occurrences = _occurrences(words, quote_words)
    candidates: list[_Candidate] = []
    for start in occurrences:
        end = start + len(quote_words)
        left_evidence: tuple[str, ...] = ()
        right_evidence: tuple[str, ...] = ()
        for width in range(1, len(left) + 1):
            anchor = left[-width:]
            if (
                start >= width
                and words[start - width : start] == anchor
                and len(_occurrences(words, anchor)) == 1
            ):
                left_evidence = anchor
        for width in range(1, len(right) + 1):
            anchor = right[:width]
            if (
                words[end : end + width] == anchor
                and len(_occurrences(words, anchor)) == 1
            ):
                right_evidence = anchor
        has_left = bool(left_evidence) or (left_boundary and start == 0)
        has_right = bool(right_evidence) or (right_boundary and end == len(words))
        if not (has_left or has_right):
            continue
        candidates.append(
            _Candidate(
                start=start,
                end=end,
                left=left_evidence,
                right=right_evidence,
                left_boundary=left_boundary and start == 0,
                right_boundary=right_boundary and end == len(words),
            )
        )
    return list(dict.fromkeys(candidates))


def _line_boundary_evidence(side: str) -> tuple[str, ...]:
    return (f"visible-{side}-line-boundary",)


def _confirmed(
    redacted: CanonicalRedactedDocument,
    target: RedactionTarget,
    candidate: _Candidate,
    reference_text: str,
    reference_tokens: tuple[_Token, ...],
    *,
    mapping_version: str,
    reference_document_version_id: str,
    reference_canonical_version_id: str,
    reference_hash: str,
) -> ReferenceMapping:
    first = reference_tokens[candidate.start]
    last = reference_tokens[candidate.end - 1]
    exact = reference_text[first.start : last.end]
    left = candidate.left or (
        () if candidate.left_boundary else _line_boundary_evidence("left")
    )
    right = candidate.right or (
        () if candidate.right_boundary else _line_boundary_evidence("right")
    )
    return ReferenceMapping(
        mapping_id=_mapping_id(
            redacted,
            target,
            reference_document_version_id,
            reference_canonical_version_id,
            reference_hash,
            mapping_version,
            ReferenceStatus.CONFIRMED,
        ),
        mapping_version=mapping_version,
        project_id=redacted.project_id,
        target_id=target.target_id,
        target_version=target.target_version,
        redacted_document_version_id=redacted.redacted_document_version_id,
        reference_document_version_id=reference_document_version_id,
        status=ReferenceStatus.CONFIRMED,
        scoreability=ReferenceScoreability.SCOREABLE,
        exact_revealed_text=exact,
        reference_token_locator=(
            f"tokens:{candidate.start}-{candidate.end};"
            f"chars:{first.start}-{last.end}"
        ),
        redacted_canonical_version_id=redacted.canonical_document_version_id,
        reference_canonical_version_id=reference_canonical_version_id,
        redacted_canonical_hash=redacted.canonical_hash,
        reference_canonical_hash=reference_hash,
        global_alignment_version=GLOBAL_ALIGNMENT_VERSION,
        left_anchor_evidence=left,
        right_anchor_evidence=right,
        left_document_boundary=candidate.left_boundary,
        right_document_boundary=candidate.right_boundary,
        candidate_unique=True,
        complete_revelation=True,
        readable=True,
        reliably_aligned=True,
        mapping_method_version=MAPPING_METHOD_VERSION,
        provenance="safe canonical reference text with deterministic token offsets",
    )


def _monotonic_pairs(
    redacted_tokens: tuple[_Token, ...],
    reference_tokens: tuple[_Token, ...],
) -> tuple[tuple[int, int, int], ...]:
    matcher = SequenceMatcher(
        None,
        tuple(token.normalized for token in redacted_tokens),
        tuple(token.normalized for token in reference_tokens),
        autojunk=False,
    )
    return tuple(
        (block.a, block.b, block.size)
        for block in matcher.get_matching_blocks()
        if block.size
    )


def _expanded_pairs(
    blocks: tuple[tuple[int, int, int], ...],
) -> frozenset[tuple[int, int]]:
    return frozenset(
        (redacted_start + offset, reference_start + offset)
        for redacted_start, reference_start, size in blocks
        for offset in range(size)
    )


def align_reference(
    redacted: CanonicalRedactedDocument,
    reference_pdf: bytes | None,
    *,
    targets: tuple[RedactionTarget, ...],
    reference_document_version_id: str | None,
    reference_canonical_version_id: str | None,
    mapping_version: str,
) -> list[ReferenceMapping]:
    """Return one safe mapping per target; uncertain candidates never expose truth."""

    markers = _validate_inputs(redacted, targets)
    if not mapping_version or not mapping_version.strip():
        raise ValueError("mapping version is required")
    if reference_pdf is None:
        if (
            reference_document_version_id is not None
            or reference_canonical_version_id is not None
        ):
            raise ValueError(
                "absent reference must not have reference version identifiers"
            )
        return [
            _unconfirmed(
                redacted,
                target,
                status=ReferenceStatus.ABSENT,
                mapping_version=mapping_version,
                reference_document_version_id=None,
                reference_canonical_version_id=None,
                reference_hash=None,
            )
            for target in targets
        ]
    if (
        not reference_document_version_id
        or not reference_document_version_id.strip()
        or not reference_canonical_version_id
        or not reference_canonical_version_id.strip()
    ):
        raise ValueError("reference version identifiers are required")

    parsed = _reference_document(
        reference_pdf,
        project_id=redacted.project_id,
        reference_document_version_id=reference_document_version_id,
        reference_canonical_version_id=reference_canonical_version_id,
    )
    if parsed is None:
        return [
            _unconfirmed(
                redacted,
                target,
                status=ReferenceStatus.UNREADABLE,
                mapping_version=mapping_version,
                reference_document_version_id=reference_document_version_id,
                reference_canonical_version_id=reference_canonical_version_id,
                reference_hash=None,
                readable=False,
            )
            for target in targets
        ]

    detection, reference = parsed
    reference_tokens = _tokens(reference.canonical_text)
    redacted_tokens = _tokens(redacted.canonical_text)
    global_pairs = _monotonic_pairs(redacted_tokens, reference_tokens)
    if not reference_tokens or not global_pairs:
        return [
            _unconfirmed(
                redacted,
                target,
                status=ReferenceStatus.CONFLICTING,
                mapping_version=mapping_version,
                reference_document_version_id=reference_document_version_id,
                reference_canonical_version_id=reference_canonical_version_id,
                reference_hash=reference.canonical_hash,
                readable=bool(reference_tokens),
            )
            for target in targets
        ]
    matching_pairs = _expanded_pairs(global_pairs)

    results: list[ReferenceMapping] = []
    confirmed_ranges: list[tuple[int, int, int]] = []
    for index, (target, marker) in enumerate(zip(targets, markers, strict=True)):
        if _reference_boxes_overlap(target, detection):
            results.append(
                _unconfirmed(
                    redacted,
                    target,
                    status=ReferenceStatus.PARTIAL,
                    mapping_version=mapping_version,
                    reference_document_version_id=reference_document_version_id,
                    reference_canonical_version_id=reference_canonical_version_id,
                    reference_hash=reference.canonical_hash,
                    complete_revelation=False,
                    readable=True,
                )
            )
            continue
        left, right, left_boundary, right_boundary, adjacent = _line_context(
            redacted.canonical_text, marker[0], marker[1]
        )
        if adjacent:
            candidates = _geometry_candidate(
                reference_pdf,
                target,
                detection,
                reference_tokens,
                left,
                right,
                left_boundary,
                right_boundary,
            )
        else:
            candidates = _anchor_candidates(
                reference_tokens,
                left,
                right,
                left_boundary,
                right_boundary,
            )
        hidden_matches = _hidden_reference_match_count(
            reference.canonical_text, left, right
        )
        if hidden_matches or any(
            _candidate_contains_marker(
                reference.canonical_text, reference_tokens, candidate
            )
            for candidate in candidates
        ):
            results.append(
                _unconfirmed(
                    redacted,
                    target,
                    status=ReferenceStatus.PARTIAL,
                    mapping_version=mapping_version,
                    reference_document_version_id=reference_document_version_id,
                    reference_canonical_version_id=reference_canonical_version_id,
                    reference_hash=reference.canonical_hash,
                    candidate_unique=hidden_matches == 1,
                    complete_revelation=False,
                    readable=True,
                )
            )
            continue
        if len(candidates) != 1:
            status = (
                ReferenceStatus.AMBIGUOUS
                if len(candidates) > 1
                else ReferenceStatus.CONFLICTING
            )
            results.append(
                _unconfirmed(
                    redacted,
                    target,
                    status=status,
                    mapping_version=mapping_version,
                    reference_document_version_id=reference_document_version_id,
                    reference_canonical_version_id=reference_canonical_version_id,
                    reference_hash=reference.canonical_hash,
                    candidate_unique=False,
                    readable=True,
                )
            )
            continue
        candidate = candidates[0]
        if not _globally_supported(
            candidate,
            marker[0],
            marker[1],
            redacted_tokens,
            matching_pairs,
        ):
            results.append(
                _unconfirmed(
                    redacted,
                    target,
                    status=ReferenceStatus.CONFLICTING,
                    mapping_version=mapping_version,
                    reference_document_version_id=reference_document_version_id,
                    reference_canonical_version_id=reference_canonical_version_id,
                    reference_hash=reference.canonical_hash,
                    candidate_unique=True,
                    complete_revelation=True,
                    readable=True,
                )
            )
            continue
        results.append(
            _confirmed(
                redacted,
                target,
                candidate,
                reference.canonical_text,
                reference_tokens,
                mapping_version=mapping_version,
                reference_document_version_id=reference_document_version_id,
                reference_canonical_version_id=reference_canonical_version_id,
                reference_hash=reference.canonical_hash,
            )
        )
        confirmed_ranges.append((index, candidate.start, candidate.end))

    previous_end = -1
    for index, start, end in confirmed_ranges:
        if start < previous_end:
            target = targets[index]
            results[index] = _unconfirmed(
                redacted,
                target,
                status=ReferenceStatus.CONFLICTING,
                mapping_version=mapping_version,
                reference_document_version_id=reference_document_version_id,
                reference_canonical_version_id=reference_canonical_version_id,
                reference_hash=reference.canonical_hash,
                candidate_unique=True,
                complete_revelation=True,
                readable=True,
            )
        previous_end = max(previous_end, end)
    return results
