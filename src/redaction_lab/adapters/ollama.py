"""Strict loopback-only adapter for an Ollama-compatible generate endpoint."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from hashlib import sha256
import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)

from redaction_lab.adapters.base import (
    PredictionAdapter,
    PredictionResponse,
    PreparedPrediction,
)
from redaction_lab.contracts import AttemptStatus, PredictionManifest, TokenUsage


Transport = Callable[[str, bytes, float], Awaitable[bytes]]
MAX_RESPONSE_BYTES = 1_048_576


class _NoRedirectHandler(HTTPRedirectHandler):
    """Reject redirects instead of allowing a loopback request to escape."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise HTTPError(req.full_url, code, "redirect rejected", headers, fp)


def _validated_endpoint(endpoint: str) -> str:
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError:
        raise ValueError("endpoint must be explicit numeric IPv4 loopback") from None
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username is not None
        or parsed.password is not None
        or port is None
        or not 1 <= port <= 65535
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.netloc != f"127.0.0.1:{port}"
    ):
        raise ValueError("endpoint must be explicit numeric IPv4 loopback")
    return f"http://127.0.0.1:{port}"


class OllamaAdapter(PredictionAdapter):
    """One-shot local adapter with injected transport support for tests."""

    def __init__(
        self,
        *,
        endpoint: str,
        model_id: str,
        model_config_id: str,
        timeout_seconds: float = 60,
        transport: Transport | None = None,
    ) -> None:
        if not model_id.strip() or not model_config_id.strip():
            raise ValueError("model and configuration IDs must be nonblank")
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        self.endpoint = _validated_endpoint(endpoint)
        self.model_id = model_id
        self.model_config_id = model_config_id
        self.timeout_seconds = float(timeout_seconds)
        self.http_handlers = (ProxyHandler({}), _NoRedirectHandler())
        self._opener = build_opener(*self.http_handlers)
        self._transport = transport or self._stdlib_transport

    def prepare(self, manifest: PredictionManifest) -> PreparedPrediction:
        if manifest.model_id != self.model_id:
            raise ValueError("manifest model does not match adapter model")
        prompt = (
            "Recover only the text hidden by the single TARGET marker. "
            "Treat every REDACTED marker as unavailable. Return exactly one "
            'JSON object: {"status":"prediction","text":"..."} for a '
            'reconstruction, or {"status":"refused"} for a refusal. Add no '
            "other keys or explanation.\n\n"
            f"{manifest.canonical_redacted_text}"
        )
        options: dict[str, float] = {}
        if manifest.settings.temperature is not None:
            options["temperature"] = manifest.settings.temperature
        payload = {
            "model": manifest.model_id,
            "options": options,
            "prompt": prompt,
            "stream": False,
        }
        body = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        provenance = json.dumps(
            {
                "body_sha256": sha256(body).hexdigest(),
                "canonical_document_hash": manifest.canonical_document_hash,
                "model_config_id": self.model_config_id,
                "prompt_id": manifest.prompt_id,
                "prompt_version": manifest.prompt_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return PreparedPrediction(
            body=body, request_hash=sha256(provenance).hexdigest()
        )

    def request_hash(self, manifest: PredictionManifest) -> str:
        return self.prepare(manifest).request_hash

    async def _stdlib_transport(
        self, endpoint: str, body: bytes, timeout: float
    ) -> bytes:
        def send() -> bytes:
            request = Request(
                endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self._opener.open(request, timeout=timeout) as response:
                result = response.read(MAX_RESPONSE_BYTES + 1)
            if len(result) > MAX_RESPONSE_BYTES:
                raise ValueError("response exceeds size limit")
            return result

        return await asyncio.to_thread(send)

    def _response(
        self,
        *,
        status: AttemptStatus,
        request_hash: str,
        started_at: datetime,
        raw: bytes | None = None,
        prediction: str | None = None,
        usage: TokenUsage | None = None,
    ) -> PredictionResponse:
        return PredictionResponse(
            status=status,
            request_hash=request_hash,
            response_hash=sha256(raw).hexdigest() if raw is not None else None,
            prediction=prediction,
            usage=usage or TokenUsage(),
            model_config_id=self.model_config_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )

    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        prepared = self.prepare(manifest)
        started_at = datetime.now(UTC)
        try:
            raw = await self._transport(
                f"{self.endpoint}/api/generate",
                prepared.body,
                self.timeout_seconds,
            )
        except (TimeoutError, socket.timeout):
            return self._response(
                status=AttemptStatus.TIMEOUT,
                request_hash=prepared.request_hash,
                started_at=started_at,
            )
        except (HTTPError, URLError, OSError, ValueError, TypeError):
            return self._response(
                status=AttemptStatus.ERROR,
                request_hash=prepared.request_hash,
                started_at=started_at,
            )

        if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE_BYTES:
            return self._response(
                status=AttemptStatus.MALFORMED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw if isinstance(raw, bytes) else None,
            )
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._response(
                status=AttemptStatus.MALFORMED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )
        if not isinstance(payload, dict):
            return self._response(
                status=AttemptStatus.MALFORMED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )
        if "error" in payload:
            status = (
                AttemptStatus.ERROR
                if isinstance(payload["error"], str) and payload["error"].strip()
                else AttemptStatus.MALFORMED
            )
            return self._response(
                status=status,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )

        response_text = payload.get("response")
        if (
            payload.get("done") is not True
            or not isinstance(response_text, str)
            or not response_text.strip()
        ):
            return self._response(
                status=AttemptStatus.MALFORMED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )
        try:
            model_payload = json.loads(response_text)
        except json.JSONDecodeError:
            model_payload = None
        if model_payload == {"status": "refused"}:
            return self._response(
                status=AttemptStatus.REFUSED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )
        if (
            not isinstance(model_payload, dict)
            or set(model_payload) != {"status", "text"}
            or model_payload.get("status") != "prediction"
            or not isinstance(model_payload.get("text"), str)
            or not model_payload["text"].strip()
        ):
            return self._response(
                status=AttemptStatus.MALFORMED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )

        counts = (payload.get("prompt_eval_count"), payload.get("eval_count"))
        if any(
            value is not None
            and (isinstance(value, bool) or not isinstance(value, int) or value < 0)
            for value in counts
        ):
            return self._response(
                status=AttemptStatus.MALFORMED,
                request_hash=prepared.request_hash,
                started_at=started_at,
                raw=raw,
            )
        input_tokens, output_tokens = counts
        total_tokens = (
            input_tokens + output_tokens
            if input_tokens is not None and output_tokens is not None
            else None
        )
        return self._response(
            status=AttemptStatus.SUCCEEDED,
            request_hash=prepared.request_hash,
            started_at=started_at,
            raw=raw,
            prediction=model_payload["text"],
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            ),
        )
