from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import UTC, datetime
import errno
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import subprocess
import sys
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request
from urllib.request import ProxyHandler

import pytest

import redaction_lab.adapters.ollama as ollama_module
from redaction_lab.adapters.base import build_prediction_manifest
from redaction_lab.adapters.ollama import (
    MAX_RESPONSE_BYTES,
    OllamaAdapter,
    _NoRedirectHandler,
)
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
    )
    prepared = adapter.prepare(_manifest())
    request = json.loads(prepared.body)
    serialized = prepared.body.decode("utf-8").lower()

    assert set(request) == {
        "model", "options", "prompt", "raw", "shift", "stream", "truncate"
    }
    assert request["raw"] is True
    assert request["shift"] is False
    assert request["truncate"] is False
    assert request["options"] == {
        "num_ctx": 32768,
        "num_predict": 1024,
        "temperature": 0.0,
    }
    assert "reference" not in serialized
    assert "revealed" not in serialized
    assert "filename" not in serialized
    assert "mapping" not in serialized
    assert "evaluation" not in serialized
    assert "prior prediction" not in serialized
    assert "hidden answer" not in serialized
    assert "[[target:target-001]]" in serialized
    assert "[[redacted:target-002]]" in serialized


def test_request_rejects_rendered_prompt_that_cannot_fit_without_truncation() -> None:
    manifest = _manifest().model_copy(
        update={"canonical_redacted_text": "x" * 31_000 + "[[TARGET:target-001]]"}
    )
    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="local-model-config-v1",
    )

    with pytest.raises(ValueError, match="context"):
        adapter.prepare(manifest)


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


def test_constructor_rejects_public_transport_injection() -> None:
    with pytest.raises(TypeError, match="transport"):
        OllamaAdapter(
            endpoint="http://127.0.0.1:11434",
            model_id="local-model",
            model_config_id="config-v1",
            transport=lambda *_: None,
        )


def test_transport_enforces_hard_subprocess_deadline(monkeypatch) -> None:
    observed = {}

    def timeout(command, **kwargs):
        observed["command"] = command
        observed["timeout"] = kwargs["timeout"]
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(ollama_module.subprocess, "run", timeout)
    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
        timeout_seconds=0.25,
    )

    with pytest.raises(TimeoutError):
        asyncio.run(
            adapter._stdlib_transport(
                "http://127.0.0.1:11434/api/generate", b"{}", 0.25
            )
        )
    assert observed["timeout"] == 0.25
    assert observed["command"][:3] == [
        sys.executable,
        "-m",
        "redaction_lab.adapters.ollama",
    ]


def test_strict_success_response_and_hashes_are_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, bytes, float]] = []

    async def transport(endpoint: str, body: bytes, timeout: float) -> bytes:
        calls.append((endpoint, body, timeout))
        return json.dumps(
            {
                "model": "local-model",
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
        timeout_seconds=9,
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)
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
    assert first.provider_model_id == "local-model"
    assert calls[0][0] == "http://127.0.0.1:11434/api/generate"
    assert calls[0][2] == 9


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "model": "local-model",
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
    payload: object, expected: AttemptStatus, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def transport(*_: object) -> bytes:
        return json.dumps(payload).encode()

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)
    response = asyncio.run(adapter.predict(_manifest()))

    assert response.status is expected
    assert response.prediction is None


def test_timeout_is_not_folded_into_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def transport(*_: object) -> bytes:
        raise TimeoutError("ambiguous local timeout")

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)
    response = asyncio.run(adapter.predict(_manifest()))

    assert response.status is AttemptStatus.TIMEOUT
    assert response.prediction is None
    assert response.response_hash is None


def test_adapter_has_no_pdf_or_hidden_text_input_channel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hidden_selectable_text = "REFERENCE-ONLY SECRET"
    seen_body = b""

    async def transport(_: str, body: bytes, __: float) -> bytes:
        nonlocal seen_body
        seen_body = body
        return json.dumps(
            {
                "model": "local-model",
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
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)
    asyncio.run(adapter.predict(_manifest()))

    assert hidden_selectable_text.encode() not in seen_body
    assert b"%PDF" not in seen_body


@pytest.mark.parametrize(
    "provider_model",
    [None, "", "different-model"],
)
def test_success_requires_exact_provider_model_identity(
    provider_model: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "model": provider_model,
        "response": json.dumps({"status": "prediction", "text": "guess"}),
        "done": True,
    }

    async def transport(*_: object) -> bytes:
        return json.dumps(payload).encode()

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)

    response = asyncio.run(adapter.predict(_manifest()))

    expected = AttemptStatus.ERROR if provider_model == "different-model" else AttemptStatus.MALFORMED
    assert response.status is expected
    assert response.prediction is None
    assert response.provider_model_id == (
        "different-model" if provider_model == "different-model" else None
    )
    assert response.response_hash is not None


def test_matching_provider_model_allows_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    async def transport(*_: object) -> bytes:
        return json.dumps(
            {
                "model": "local-model",
                "response": json.dumps({"status": "refused"}),
                "done": True,
            }
        ).encode()

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)

    response = asyncio.run(adapter.predict(_manifest()))
    assert response.status is AttemptStatus.REFUSED
    assert response.provider_model_id == "local-model"


@pytest.mark.parametrize(
    "error",
    [
        URLError(socket.timeout("wrapped")),
        URLError(OSError(errno.ETIMEDOUT, "wrapped")),
        OSError(errno.ETIMEDOUT, "direct"),
    ],
)
def test_wrapped_timeout_is_timeout(
    error: BaseException, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def transport(*_: object) -> bytes:
        raise error

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)

    assert asyncio.run(adapter.predict(_manifest())).status is AttemptStatus.TIMEOUT


def test_non_timeout_url_error_remains_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def transport(*_: object) -> bytes:
        raise URLError("connection refused")

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)

    assert asyncio.run(adapter.predict(_manifest())).status is AttemptStatus.ERROR


def test_cyclic_timeout_exception_chain_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = URLError("outer")
    error.__context__ = error

    async def transport(*_: object) -> bytes:
        raise error

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)

    assert asyncio.run(adapter.predict(_manifest())).status is AttemptStatus.ERROR


def test_private_transport_mock_cannot_bypass_response_size_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def transport(*_: object) -> bytes:
        return b"x" * (MAX_RESPONSE_BYTES + 1)

    adapter = OllamaAdapter(
        endpoint="http://127.0.0.1:11434",
        model_id="local-model",
        model_config_id="config-v1",
    )
    monkeypatch.setattr(adapter, "_stdlib_transport", transport)

    response = asyncio.run(adapter.predict(_manifest()))
    assert response.status is AttemptStatus.MALFORMED
    assert response.prediction is None


@contextmanager
def _loopback_response(
    body: bytes,
    *,
    status: int = 200,
    release: threading.Event | None = None,
):
    finished = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if release is not None:
                release.wait(timeout=2)
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def finish(self):
            try:
                super().finish()
            finally:
                finished.set()

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.block_on_close = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", finished
    finally:
        if release is not None:
            release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (MAX_RESPONSE_BYTES, AttemptStatus.SUCCEEDED),
        (MAX_RESPONSE_BYTES + 1, AttemptStatus.MALFORMED),
    ],
)
def test_real_stdlib_transport_bounds_and_classifies_provider_content(
    size: int, expected: AttemptStatus
) -> None:
    payload = {
        "model": "local-model",
        "response": json.dumps({"status": "prediction", "text": "guess"}),
        "done": True,
        "padding": "",
    }
    base = json.dumps(payload, separators=(",", ":")).encode()
    payload["padding"] = "x" * (size - len(base))
    body = json.dumps(payload, separators=(",", ":")).encode()
    assert len(body) == size
    with _loopback_response(body) as (endpoint, finished):
        adapter = OllamaAdapter(
            endpoint=endpoint,
            model_id="local-model",
            model_config_id="config-v1",
        )

        response = asyncio.run(adapter.predict(_manifest()))

        assert response.status is expected
        assert response.prediction == (
            "guess" if expected is AttemptStatus.SUCCEEDED else None
        )
        assert response.response_hash == sha256(body).hexdigest()
        assert finished.wait(timeout=2)


def test_real_stdlib_transport_keeps_timeout_distinct_from_http_error() -> None:
    release = threading.Event()
    with _loopback_response(b"{}", release=release) as (endpoint, _):
        timeout_adapter = OllamaAdapter(
            endpoint=endpoint,
            model_id="local-model",
            model_config_id="config-v1",
            timeout_seconds=0.05,
        )
        assert (
            asyncio.run(timeout_adapter.predict(_manifest())).status
            is AttemptStatus.TIMEOUT
        )

    with _loopback_response(b"unavailable", status=503) as (endpoint, finished):
        error_adapter = OllamaAdapter(
            endpoint=endpoint,
            model_id="local-model",
            model_config_id="config-v1",
        )
        assert (
            asyncio.run(error_adapter.predict(_manifest())).status
            is AttemptStatus.ERROR
        )
        assert finished.wait(timeout=2)


def test_real_stdlib_connection_refusal_remains_error() -> None:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    adapter = OllamaAdapter(
        endpoint=f"http://127.0.0.1:{port}",
        model_id="local-model",
        model_config_id="config-v1",
        timeout_seconds=0.5,
    )

    response = asyncio.run(adapter.predict(_manifest()))

    assert response.status is AttemptStatus.ERROR
