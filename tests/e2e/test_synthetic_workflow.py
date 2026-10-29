from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.api.app import create_app
from redaction_lab.application.application_store import ApplicationStore
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.inference_runtime import VerifiedInferenceRuntime
from redaction_lab.application.isolation import WorkerObservation
from redaction_lab.application.upload_service import UploadService
from redaction_lab.application.worker_protocol import (
    WORKER_PROTOCOL_VERSION,
    WorkerRequest,
    process_request,
)
from redaction_lab.contracts import AttemptStatus, PredictionManifest, TokenUsage
from redaction_lab.fixtures import make_synthetic_pair


class InProcessSyntheticPdfWorker:
    """Exercise the real parser contract while replacing only Podman transport."""

    @staticmethod
    def ensure_available() -> None:
        return None

    @staticmethod
    def process(pdf_bytes: bytes, *, project_id: str, role):
        request = WorkerRequest(
            protocol_version=WORKER_PROTOCOL_VERSION,
            request_nonce=sha256(project_id.encode()).hexdigest()[:32],
            project_id=project_id,
            role=role,
            input_sha256=sha256(pdf_bytes).hexdigest(),
            byte_count=len(pdf_bytes),
        )
        return WorkerObservation(
            response=process_request(request, pdf_bytes),
            image_digest="sha256:" + "a" * 64,
        )


class SyntheticPredictionAdapter(PredictionAdapter):
    model_id = "qwen2.5:1.5b-instruct-q4_K_M"
    model_config_id = "ollama-synthetic-e2e-config"

    def __init__(self) -> None:
        self.manifests: list[PredictionManifest] = []

    def request_hash(self, manifest: PredictionManifest) -> str:
        return sha256((manifest.manifest_id + self.model_config_id).encode()).hexdigest()

    async def predict(self, manifest: PredictionManifest) -> PredictionResponse:
        self.manifests.append(manifest)
        request_hash = self.request_hash(manifest)
        if len(self.manifests) % 2 == 0:
            return PredictionResponse(
                status=AttemptStatus.MALFORMED,
                request_hash=request_hash,
                response_hash=sha256(b"synthetic malformed output").hexdigest(),
                prediction=None,
                usage=TokenUsage(),
                model_config_id=self.model_config_id,
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                provider_model_id=self.model_id,
            )
        raw = f"synthetic prediction for {manifest.target_id}".encode()
        return PredictionResponse(
            status=AttemptStatus.SUCCEEDED,
            request_hash=request_hash,
            response_hash=sha256(raw).hexdigest(),
            prediction=raw.decode(),
            usage=TokenUsage(input_tokens=10, output_tokens=3, total_tokens=13),
            model_config_id=self.model_config_id,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            provider_model_id=self.model_id,
        )


def _verified(adapter: PredictionAdapter) -> VerifiedInferenceRuntime:
    return VerifiedInferenceRuntime(
        adapter=adapter,
        model_id=adapter.model_id,
        model_config_id=adapter.model_config_id,
        model_manifest_digest="sha256:" + "b" * 64,
    )


def _multipart(
    project_id: str, redacted: bytes, reference: bytes | None
) -> tuple[bytes, str]:
    boundary = "synthetic-e2e-boundary"
    parts = [
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="project_id"\r\n\r\n'
            f"{project_id}\r\n"
        ).encode(),
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="redacted_pdf"; filename="redacted.pdf"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        ).encode()
        + redacted
        + b"\r\n",
    ]
    if reference is not None:
        parts.append(
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="reference_pdf"; filename="reference.pdf"\r\n'
                "Content-Type: application/pdf\r\n\r\n"
            ).encode()
            + reference
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _request(
    app, method: str, path: str, *, body: bytes = b"", content_type: str = ""
) -> tuple[int, dict[str, object]]:
    captured: dict[str, object] = {}

    def start_response(status, _headers):
        captured["status"] = int(status.split()[0])

    environment = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "HTTP_HOST": "127.0.0.1:8765",
        "HTTP_ORIGIN": "http://127.0.0.1:8765",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.url_scheme": "http",
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    payload = json.loads(b"".join(app(environment, start_response)))
    return int(captured["status"]), payload


def _upload(app, project_id: str, redacted: bytes, reference: bytes | None):
    body, content_type = _multipart(project_id, redacted, reference)
    status, payload = _request(
        app, "POST", "/api/v1/documents", body=body, content_type=content_type
    )
    assert status == 201
    return payload


def _snapshot(app, receipt: dict[str, object]) -> tuple[dict[str, object], ...]:
    redacted = receipt["redacted"]
    assert isinstance(redacted, dict)
    version_id = redacted["version_id"]
    job_id = redacted["job_id"]
    values = (
        _request(app, "GET", f"/api/v1/documents/{version_id}"),
        _request(app, "GET", f"/api/v1/jobs/{job_id}"),
        _request(app, "GET", f"/api/v1/results/{version_id}"),
    )
    assert [status for status, _ in values] == [200, 200, 200]
    return tuple(payload for _, payload in values)


def test_two_reference_pairs_and_required_only_upload_complete_without_leakage(
    tmp_path: Path, monkeypatch
) -> None:
    first_redacted, first_reference = make_synthetic_pair(
        "two_boxes", tmp_path / "first-fixture"
    )
    second_redacted, second_reference = make_synthetic_pair(
        "adjacent_boxes", tmp_path / "second-fixture"
    )
    third_redacted, _ = make_synthetic_pair(
        "repeated_anchors", tmp_path / "third-fixture"
    )
    artifacts_path = tmp_path / "artifacts"
    temporary_path = tmp_path / "temporary"
    database_path = tmp_path / "application.sqlite3"
    backup_path = tmp_path / "backups"
    artifacts = ArtifactStore(artifacts_path, temporary_path)
    store = ApplicationStore(database_path, backup_directory=backup_path)
    app = create_app(UploadService(artifacts, store))
    adapter = SyntheticPredictionAdapter()
    monkeypatch.setattr(
        "redaction_lab.application.document_worker.ApplicationPdfWorker",
        InProcessSyntheticPdfWorker,
    )
    monkeypatch.setattr(
        "redaction_lab.application.prediction_service.InferenceRuntime.verified",
        lambda _self: _verified(adapter),
    )
    try:
        receipts = (
            _upload(
                app,
                "project-first",
                first_redacted.read_bytes(),
                first_reference.read_bytes(),
            ),
            _upload(
                app,
                "project-second",
                second_redacted.read_bytes(),
                second_reference.read_bytes(),
            ),
            _upload(app, "project-third", third_redacted.read_bytes(), None),
        )
        for receipt in receipts:
            redacted = receipt["redacted"]
            assert isinstance(redacted, dict)
            status, result = _request(
                app,
                "POST",
                f"/api/v1/jobs/{redacted['job_id']}/process",
            )
            assert status == 200
            assert result["status"] == "READY"

        snapshots = tuple(_snapshot(app, receipt) for receipt in receipts)
        calls_after_first_completion = len(adapter.manifests)
        first_redacted_receipt = receipts[0]["redacted"]
        assert isinstance(first_redacted_receipt, dict)
        replay_status, replay = _request(
            app,
            "POST",
            f"/api/v1/jobs/{first_redacted_receipt['job_id']}/process",
        )
        assert replay_status == 200
        assert replay["status"] == "READY"
        assert len(adapter.manifests) == calls_after_first_completion
    finally:
        artifacts.close()

    reopened_artifacts = ArtifactStore(artifacts_path, temporary_path)
    reopened = create_app(
        UploadService(
            reopened_artifacts,
            ApplicationStore(database_path, backup_directory=backup_path),
        )
    )
    try:
        assert tuple(_snapshot(reopened, receipt) for receipt in receipts) == snapshots
    finally:
        reopened_artifacts.close()

    assert receipts[0]["reference"] is not None
    assert receipts[1]["reference"] is not None
    assert receipts[2]["reference"] is None
    assert all(receipt["truth_status"] == "UNKNOWN" for receipt in receipts)
    result_payloads = [snapshot[2] for snapshot in snapshots]
    assert all(result["status"] == "AVAILABLE" for result in result_payloads)
    assert all(result["truth_status"] == "UNKNOWN" for result in result_payloads)
    assert all(result["verified_score"] is None for result in result_payloads)
    assert all(result["experimental_score"] is None for result in result_payloads)
    assert all(result["targets"] for result in result_payloads)
    persisted_target_ids = [
        target["target_id"]
        for result in result_payloads
        for target in result["targets"]
    ]
    assert persisted_target_ids == [manifest.target_id for manifest in adapter.manifests]
    assert len(persisted_target_ids) == len(set(persisted_target_ids))
    assert {target["attempt_status"] for result in result_payloads for target in result["targets"]} == {
        "SUCCEEDED",
        "MALFORMED",
    }
    for manifest in adapter.manifests:
        assert manifest.canonical_redacted_text.count(manifest.target_marker) == 1
        assert "Agent Cedar" not in manifest.canonical_redacted_text
        assert "12 paper stars" not in manifest.canonical_redacted_text
        assert "ALPHA BRAVO" not in manifest.canonical_redacted_text
        assert "REFERENCE" not in manifest.canonical_redacted_text
