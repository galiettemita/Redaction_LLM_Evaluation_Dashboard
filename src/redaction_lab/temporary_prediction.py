"""Deterministic, non-authoritative text guesses for the temporary demo."""


_MARKER = "[REDACTED]"
_PERSON_CUES = {
    "met",
    "contacted",
    "called",
    "emailed",
    "named",
    "agent",
    "dr",
    "mr",
    "ms",
    "professor",
}
_PLACE_CUES = {"in", "at", "from", "near", "toward", "inside"}
_TIME_CUES = {"on", "during", "before", "after", "since", "until"}

_CANDIDATES = {
    "person": ("a person", "an individual", "someone"),
    "place": ("a place", "a location", "somewhere"),
    "time": ("a time", "a date", "a period"),
    "fallback": ("an unspecified item", "something", "an unknown detail"),
}
_BASIS = {
    "person": "Nearby person cue; generic heuristic only.",
    "place": "Nearby place cue; generic heuristic only.",
    "time": "Nearby time cue; generic heuristic only.",
    "fallback": "No nearby recognized cue; generic fallback only.",
}


def _ascii_words(text: str) -> list[tuple[str, int, int]]:
    words: list[tuple[str, int, int]] = []
    start: int | None = None

    for index, character in enumerate(text):
        is_ascii_letter = "A" <= character <= "Z" or "a" <= character <= "z"
        if is_ascii_letter:
            if start is None:
                start = index
        elif start is not None:
            words.append((text[start:index].lower(), start, index))
            start = None

    if start is not None:
        words.append((text[start:].lower(), start, len(text)))
    return words


def _category_for_marker(
    marker_start: int,
    marker_end: int,
    words: list[tuple[str, int, int]],
) -> str:
    left_word: str | None = None
    right_word: str | None = None
    for word, start, end in words:
        if end <= marker_start:
            left_word = word
        elif start >= marker_end:
            right_word = word
            break

    for word in (left_word, right_word):
        if word in _PERSON_CUES:
            return "person"
        if word in _PLACE_CUES:
            return "place"
        if word in _TIME_CUES:
            return "time"
    return "fallback"


def _has_javascript_scheme(text: str) -> bool:
    casefolded = text.casefold()
    position = 0
    while True:
        position = casefolded.find("javascript", position)
        if position < 0:
            return False
        end = position + len("javascript")
        while end < len(casefolded) and (
            casefolded[end].isspace() or casefolded[end] == "\ufeff"
        ):
            end += 1
        if end < len(casefolded) and casefolded[end] == ":":
            return True
        position += 1


def generate_temporary_predictions(text: str) -> dict[str, object]:
    """Return generic contextual guesses without asserting hidden text is known."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text or not text.strip():
        raise ValueError("text must not be empty")
    if "\x00" in text:
        raise ValueError("NUL characters are not allowed")
    try:
        encoded_length = len(text.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ValueError("text must be valid UTF-8 encodable Unicode") from error
    if encoded_length > 4000:
        raise ValueError("text exceeds 4000 UTF-8 bytes")
    if "<" in text or ">" in text or _has_javascript_scheme(text):
        raise ValueError("markup-like or script-like text is not allowed")

    marker_count = text.count(_MARKER)
    if marker_count == 0:
        raise ValueError("text must contain the exact [REDACTED] marker")
    if marker_count > 8:
        raise ValueError("text may contain at most 8 markers")

    words = _ascii_words(text)
    markers: list[dict[str, object]] = []
    search_from = 0
    for marker_index in range(1, marker_count + 1):
        marker_start = text.find(_MARKER, search_from)
        marker_end = marker_start + len(_MARKER)
        category = _category_for_marker(marker_start, marker_end, words)
        markers.append(
            {
                "marker_index": marker_index,
                "candidates": _CANDIDATES[category],
                "basis": _BASIS[category],
            }
        )
        search_from = marker_end

    return {
        "status": "TEMPORARY_UNVALIDATED",
        "truth_status": "UNKNOWN",
        "score_status": "NONE",
        "verified_score": None,
        "experimental_score": None,
        "markers": markers,
    }
