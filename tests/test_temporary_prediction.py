from __future__ import annotations

import ast
from pathlib import Path

import pytest

from redaction_lab.temporary_prediction import generate_temporary_predictions


def test_returns_unvalidated_unknown_result_with_generic_person_candidates() -> None:
    result = generate_temporary_predictions("She met [REDACTED] yesterday.")

    assert result == {
        "status": "TEMPORARY_UNVALIDATED",
        "truth_status": "UNKNOWN",
        "score_status": "NONE",
        "verified_score": None,
        "experimental_score": None,
        "markers": [
            {
                "marker_index": 1,
                "candidates": ("a person", "an individual", "someone"),
                "basis": "Nearby person cue; generic heuristic only.",
            }
        ],
    }


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "No marker here.",
        "[redacted]",
        "[Redacted]",
        "[REDACTED] " * 9,
        "x" * 4001 + " [REDACTED]",
        "before\x00[REDACTED]",
        "<b>[REDACTED]</b>",
        "<script>alert(1)</script> [REDACTED]",
        "javascript:alert(1) [REDACTED]",
        "JaVaScRiPt :alert(1) [REDACTED]",
        "İjavascript:alert(1) [REDACTED]",
        "javascript\ufeff:alert(1) [REDACTED]",
        "javascript\u0085:alert(1) [REDACTED]",
        "\ud800[REDACTED]",
    ],
)
def test_rejects_empty_invalid_or_hostile_text(text: str) -> None:
    with pytest.raises(ValueError):
        generate_temporary_predictions(text)


def test_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        generate_temporary_predictions(123)  # type: ignore[arg-type]


def test_enforces_utf8_byte_limit_including_multibyte_text() -> None:
    exact_limit = "é" * 1995 + "[REDACTED]"
    over_limit = "é" * 1996 + "[REDACTED]"

    result = generate_temporary_predictions(exact_limit)

    assert len(exact_limit.encode("utf-8")) == 4000
    assert result["status"] == "TEMPORARY_UNVALIDATED"
    with pytest.raises(ValueError):
        generate_temporary_predictions(over_limit)


def test_generates_one_generic_candidate_group_per_exact_marker() -> None:
    result = generate_temporary_predictions(
        "They met [REDACTED] in [REDACTED] on [REDACTED]."
    )

    assert result["markers"] == [
        {
            "marker_index": 1,
            "candidates": ("a person", "an individual", "someone"),
            "basis": "Nearby person cue; generic heuristic only.",
        },
        {
            "marker_index": 2,
            "candidates": ("a place", "a location", "somewhere"),
            "basis": "Nearby place cue; generic heuristic only.",
        },
        {
            "marker_index": 3,
            "candidates": ("a time", "a date", "a period"),
            "basis": "Nearby time cue; generic heuristic only.",
        },
    ]


def test_candidate_output_is_deterministic() -> None:
    text = "Contacted [REDACTED] near [REDACTED]."

    assert generate_temporary_predictions(text) == generate_temporary_predictions(text)


def test_ignores_cues_beyond_the_immediate_ascii_words() -> None:
    result = generate_temporary_predictions("met x [REDACTED] y at")

    assert result["markers"] == [
        {
            "marker_index": 1,
            "candidates": ("an unspecified item", "something", "an unknown detail"),
            "basis": "No nearby recognized cue; generic fallback only.",
        }
    ]


def test_accepts_one_and_eight_markers_but_rejects_nine() -> None:
    one = generate_temporary_predictions("[REDACTED]")
    eight = generate_temporary_predictions("[REDACTED] " * 8)

    assert len(one["markers"]) == 1  # type: ignore[arg-type]
    assert len(eight["markers"]) == 8  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        generate_temporary_predictions("[REDACTED] " * 9)


def test_python_helper_has_no_imports_or_io_network_calls() -> None:
    source_path = Path(__file__).parents[1] / "src/redaction_lab/temporary_prediction.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    assert not [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    forbidden_calls = {"open", "input", "print", "eval", "exec", "compile"}
    assert not [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in forbidden_calls
    ]
