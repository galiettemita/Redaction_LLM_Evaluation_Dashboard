from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
import json
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import ProxyHandler

import pytest

from redaction_lab.adapters.base import build_prediction_manifest
from redaction_lab.adapters.ollama import OllamaAdapter, _NoRedirectHandler
from redaction_lab.contracts import (
    AttemptStatus,
    CanonicalRedactedDocument,
    RunDefinition,
)


NOW = datetime(2026, 10, 9, tzinfo=UTC)
CANONICAL_TEXT = (
    "Before [[TARGET:target-001]] between [[TARGET:target-002]] after."
)
HASH_A = sha256(CANONICAL_TEXT.encode()).hexdigest()


def _document(**overrides: object) -> CanonicalRedactedDocument:
    values: dict[str, object] = {
        "canonical_document_version_id": "canonical-v1",
        "project_id": "project-001",
        "redacted_document_version_id": "redacted-v1",
        "canonical_hash": HASH_A,
        "canonical_text": CANONICAL_TEXT,
        "target_ids": ("target-001", "target-002"),
        "canonicalizer_version": "safe-visible-text-v1",
    }
    values.update(overrides)
    return CanonicalRedactedDocument.model_validate(values)


def _run(**overrides: object) -> RunDefinition:
    values: dict[str, object] = {
        "run_id": "run-001",
        "run_version": "run-v1",
        "project_id": "project-001",
        "target_versions": ("target-v1", "target-v2"),
        "model_ids": ("local-model",),
        "experiment_condition": "redacted-document-only",
        "canonical_document_version_id": "canonical-v1",
        "canonical_document_hash": HASH_A,
        "common_context_budget": 4096,
        "context_policy": "common-full-document",
        "prompt_id": "prompt-001",
        "prompt_version": "prompt-v1",
        "settings": {"temperature": 0},
        "attempt_policy": "one-frozen-attempt",
        "tool_permissions": (),
        "budget_label": "synthetic-no-spend",
        "created_by": "test-suite",
        "created_at": NOW,
    }
    values.update(overrides)
    return RunDefinition.model_validate(values)


def _manifest(target_id: str = "target-001"):
    return build_prediction_manifest(_document(), target_id, _run())


def test_each_target_starts_from_the_same_frozen_redacted_context() -> None:
    document = _document()
    first = build_prediction_manifest(document, "target-001", _run())
    second = build_prediction_manifest(document, "target-002", _run())

    assert document.canonical_text == (
        "Before [[TARGET:target-001]] between [[TARGET:target-002]] after."
    )
    assert first.target_marker == "[[TARGET:target-001]]"
    assert second.target_marker == "[[TARGET:target-002]]"
    assert first.canonical_redacted_text == (
        "Before [[TARGET:target-001]] between [[REDACTED:target-002]] after."
    )
    assert second.canonical_redacted_text == (
        "Before [[REDACTED:target-001]] between [[TARGET:target-002]] after."
    )
    assert first.target_version == "target-v1"
    assert second.target_version == "target-v2"


@pytest.mark.parametrize(
    ("document_overrides", "run_overrides", "target_id"),
    [
        ({"project_id": "other-project"}, {}, "target-001"),
        ({}, {"canonical_document_hash": "b" * 64}, "target-001"),
        ({}, {"canonical_document_version_id": "other-canonical"}, "target-001"),
        ({}, {"target_versions": ("target-v1",)}, "target-001"),
        ({}, {"model_ids": ("model-a", "model-b")}, "target-001"),
        ({}, {"tool_permissions": ("web",)}, "target-001"),
        ({}, {}, "missing-target"),
    ],
)
def test_manifest_builder_rejects_mismatched_or_unsafe_run_inputs(
    document_overrides: dict[str, object],
    run_overrides: dict[str, object],
    target_id: str,
) -> None:
    with pytest.raises(ValueError):
        build_prediction_manifest(
            _document(**document_overrides), target_id, _run(**run_overrides)
        )


def test_manifest_builder_fails_closed_when_full_context_exceeds_budget() -> None:
    byte_length = len(_document().canonical_text.encode("utf-8"))
    with pytest.raises(ValueError, match="budget"):
        build_prediction_manifest(
            _document(), "target-001", _run(common_context_budget=byte_length - 1)
        )


def test_manifest_builder_rejects_forged_canonical_text_hash() -> None:
    with pytest.raises(ValueError, match="canonical hash"):
        build_prediction_manifest(
            _document(canonical_text="Leaked truth [[TARGET:target-001]] and "
            "[[TARGET:target-002]]."),
            "target-001",
            _run(),
        )


def test_manifest_builder_rejects_an_unregistered_target_marker() -> None:
    text = CANONICAL_TEXT + " [[TARGET:undeclared-target]]"
    with pytest.raises(ValueError, match="marker invariant"):
        build_prediction_manifest(
            _document(canonical_text=text, canonical_hash=sha256(text.encode()).hexdigest()),
            "target-001",
            _run(canonical_document_hash=sha256(text.encode()).hexdigest()),
        )


def test_request_serialization_has_no_reference_or_cross_target_answer_channel() -> None:
    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="local-model-config-v1",
        transport=lambda *_: None,
    )
    prepared = adapter.prepare(_manifest())
    request = json.loads(prepared.body)
    serialized = prepared.body.decode("utf-8").lower()

    assert set(request) == {"model", "options", "prompt", "stream"}
    assert set(request["options"]) == {"temperature"}
    assert "reference" not in serialized
    assert "revealed" not in serialized
    assert "filename" not in serialized
    assert "mapping" not in serialized
    assert "evaluation" not in serialized
    assert "prior prediction" not in serialized
    assert "hidden answer" not in serialized
    assert "[[target:target-001]]" in serialized
    assert "[[redacted:target-002]]" in serialized


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://127.0.0.1:11434",
        "http://localhost:11434",
        "http://127.0.0.2:11434",
        "http://[::1]:11434",
        "http://user:pass@127.0.0.1:11434",
        "http://127.0.0.1",
        "http://127.0.0.1:0",
        "http://127.0.0.1:70000",
        "http://127.0.0.1:11434/path",
        "http://127.0.0.1:11434?query=yes",
        "file:///tmp/socket",
    ],
)
def test_remote_or_ambiguous_endpoint_is_rejected(endpoint: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        OllamaAdapter(
            endpoint=endpoint,
            model_id="local-model",
            model_config_id="config-v1",
        )


def test_default_http_opener_disables_proxies_and_redirects() -> None:
    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    assert any(
        isinstance(handler, ProxyHandler) and handler.proxies == {}
        for handler in adapter.http_handlers
    )
    assert any(
        isinstance(handler, _NoRedirectHandler) for handler in adapter.http_handlers
    )
    redirect_handler = next(
        handler
        for handler in adapter.http_handlers
        if isinstance(handler, _NoRedirectHandler)
    )
    with pytest.raises(HTTPError, match="redirect rejected"):
        redirect_handler.redirect_request(
            Request("http://127.0.0.1:11434/api/generate"),
            None,
            302,
            "Found",
            {},
            "http://example.com/escape",
        )


def test_strict_success_response_and_hashes_are_deterministic() -> None:
    calls: list[tuple[str, bytes, float]] = []

    async def transport(endpoint: str, body: bytes, timeout: float) -> bytes:
        calls.append((endpoint, body, timeout))
        return json.dumps(
            {
                "response": json.dumps(
                    {"status": "prediction", "text": "  Agent Cedar, Ph.D.  "}
                ),
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 21,
                "eval_count": 2,
            }
        ).encode()

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
        transport=transport,
        timeout_seconds=9,
    )
    manifest = _manifest()
    first = asyncio.run(adapter.predict(manifest))
    second = asyncio.run(adapter.predict(manifest))

    assert first.status is AttemptStatus.SUCCEEDED
    assert first.prediction == "  Agent Cedar, Ph.D.  "
    assert first.usage.input_tokens == 21
    assert first.usage.output_tokens == 2
    assert first.usage.total_tokens == 23
    assert first.request_hash == second.request_hash == adapter.prepare(manifest).request_hash
    assert first.response_hash == second.response_hash
    assert calls[0][0] == "http://127.0.0.1:11434/api/generate"
    assert calls[0][2] == 9


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "response": json.dumps({"status": "refused"}),
                "done": True,
                "done_reason": "stop",
            },
            AttemptStatus.REFUSED,
        ),
        ({"response": "", "done": True, "done_reason": "stop"}, AttemptStatus.MALFORMED),
        ({"response": "I refuse", "done": True}, AttemptStatus.MALFORMED),
        (
            {
                "response": json.dumps(
                    {"status": "prediction", "text": "guess", "extra": True}
                ),
                "done": True,
            },
            AttemptStatus.MALFORMED,
        ),
        ({"response": "guess", "done": False}, AttemptStatus.MALFORMED),
        ({"error": "model unavailable"}, AttemptStatus.ERROR),
        (["not", "an", "object"], AttemptStatus.MALFORMED),
    ],
)
def test_refusal_malformed_and_error_are_distinct(
    payload: object, expected: AttemptStatus
) -> None:
    async def transport(*_: object) -> bytes:
        return json.dumps(payload).encode()

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
        transport=transport,
    )
    response = asyncio.run(adapter.predict(_manifest()))

    assert response.status is expected
    assert response.prediction is None


def test_timeout_is_not_folded_into_error() -> None:
    async def transport(*_: object) -> bytes:
        raise TimeoutError("ambiguous local timeout")

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
        transport=transport,
    )
    response = asyncio.run(adapter.predict(_manifest()))

    assert response.status is AttemptStatus.TIMEOUT
    assert response.prediction is None
    assert response.response_hash is None


def test_adapter_has_no_pdf_or_hidden_text_input_channel() -> None:
    hidden_selectable_text = "REFERENCE-ONLY SECRET"
    seen_body = b""

    async def transport(_: str, body: bytes, __: float) -> bytes:
        nonlocal seen_body
        seen_body = body
        return json.dumps(
            {
                "response": json.dumps(
                    {"status": "prediction", "text": "guess"}
                ),
                "done": True,
                "done_reason": "stop",
            }
        ).encode()

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
        transport=transport,
    )
    asyncio.run(adapter.predict(_manifest()))

    assert hidden_selectable_text.encode() not in seen_body
    assert b"%PDF" not in seen_body
