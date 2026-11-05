from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
import json

import pytest
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


def _matching_reference_pair(tmp_path):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth
    def paired_pdf(hidden):
        buffer = BytesIO()
        canvas = Canvas(buffer, pagesize=(612, 792), invariant=1)
        canvas.setFont('Helvetica', 11)
        lines = [(700, 'The courier ', 'Agent Cedar', ' arrived at dawn.'),
                (660, 'The package held ', '12 paper stars', ' during transit.')]
        for y, prefix, secret, suffix in lines:
            canvas.drawString(72, y, prefix + secret + suffix)
        if hidden:
            for y, prefix, secret, suffix in lines:
                canvas.setFillColorRGB(0, 0, 0)
                canvas.rect(72 + stringWidth(prefix, 'Helvetica', 11)-1, y-3,
                    stringWidth(secret, 'Helvetica', 11)+2, 14, fill=1, stroke=0)
        canvas.save()
        return buffer.getvalue()
    redacted, reference = tmp_path / 'redacted.pdf', tmp_path / 'reference.pdf'
    redacted.write_bytes(paired_pdf(True))
    reference.write_bytes(paired_pdf(False))
    return redacted, reference


def test_v03_process_persists_reference_evaluations_and_get_is_read_only(tmp_path, monkeypatch):
    import sqlite3
    from redaction_lab.adapters.ollama import OllamaAdapter
    from redaction_lab.application.document_worker import DocumentWorker
    from redaction_lab.application.application_store import ProcessingStatus
    redacted, reference = _matching_reference_pair(tmp_path)
    artifacts = ArtifactStore(tmp_path / 'artifacts', tmp_path / 'temporary')
    store = ApplicationStore(tmp_path / 'app.sqlite3', backup_directory=tmp_path / 'backups')
    app = create_app(UploadService(artifacts, store))
    monkeypatch.setattr('redaction_lab.application.document_worker.ApplicationPdfWorker', InProcessSyntheticPdfWorker)
    adapter = OllamaAdapter(endpoint='http://127.0.0.1:11434', model_id='qwen2.5:1.5b-instruct-q4_K_M', model_config_id='synthetic-envelope-v2')
    async def transport(endpoint, body, timeout):
        assert 'Agent Cedar' not in body.decode()
        assert '12 paper stars' not in body.decode()
        return b'{"model":"qwen2.5:1.5b-instruct-q4_K_M","created_at":"2026-11-05T20:00:00Z","response":"{\\"reconstruction\\":\\"Agent Cedar\\"}","done":true,"done_reason":"stop","prompt_eval_count":63,"eval_count":12,"total_duration":1800000000}'
    monkeypatch.setattr(adapter, '_stdlib_transport', transport)
    monkeypatch.setattr('redaction_lab.application.prediction_service.InferenceRuntime.verified', lambda self: _verified(adapter))
    try:
        receipt = _upload(app, 'experimental', redacted.read_bytes(), reference.read_bytes())
        # A second accepted pair cannot starve the first pair's reference.
        other = _upload(app, 'queued', redacted.read_bytes(), reference.read_bytes())
        version_id = receipt['redacted']['version_id']
        assert DocumentWorker(store, artifacts).run_once(owner='test', expected_job_id=receipt['redacted']['job_id'])
        asyncio.run(app.predictions.run(version_id))
        before = _request(app, 'GET', f'/api/v1/results/{version_id}')[1]
        assert all(row.get('evaluation') is None for row in before['targets'])
        assert before['progress'] == {'total': 2, 'pending': 0, 'running': 0, 'terminal': 2}
        status, _ = _request(app, 'POST', f"/api/v1/jobs/{receipt['redacted']['job_id']}/process")
        assert status == 200
        assert store.get_version(receipt['reference']['version_id']).processing_state is ProcessingStatus.READY
        result = _request(app, 'GET', f'/api/v1/results/{version_id}')[1]
        assert result['counts'] == {'requested': 2, 'eligible': 2, 'scored': 2, 'unknown': 0, 'excluded': 0, 'technical_failures': 0}
        assert result['score_status'] == 'EXPERIMENTAL'
        assert result['verified_score'] is None and result['truth_status'] == 'UNKNOWN'
        assert any(row['evaluation']['experimental_score'] == 100 for row in result['targets'])
        assert all(row['mapping']['provenance'] == 'USER_SUPPLIED_EXPERIMENTAL' for row in result['targets'])
        assert all(row['evaluation']['schema_version'] == 'experimental-text-agreement-evidence-v1' for row in result['targets'])
        assert len(result['summaries']['target']) == 2
        assert len(result['summaries']['document']) == len(result['summaries']['model']) == 1
        assert result['summaries']['model'][0]['denominator'] == 1
        with sqlite3.connect(store.path) as connection:
            snapshot = tuple(connection.iterdump())
        def forbidden(*args, **kwargs):
            raise AssertionError('GET dispatched or evaluated')
        monkeypatch.setattr(app.predictions, 'run', forbidden)
        monkeypatch.setattr('redaction_lab.application.evaluation_service.EvaluationService.evaluate_attempt', forbidden)
        assert _request(app, 'GET', f'/api/v1/results/{version_id}')[1] == result
        with sqlite3.connect(store.path) as connection:
            assert tuple(connection.iterdump()) == snapshot
        reopened = create_app(UploadService(artifacts, ApplicationStore(store.path, backup_directory=tmp_path / 'backups')))
        assert _request(reopened, 'GET', f'/api/v1/results/{version_id}')[1] == result
        assert store.get_job(other['redacted']['job_id']).status is ProcessingStatus.ACCEPTED
    finally:
        artifacts.close()


def test_v03_reference_failure_keeps_success_and_unknown_null_evidence(tmp_path, monkeypatch):
    redacted, _ = make_synthetic_pair('two_boxes', tmp_path / 'fixture')
    artifacts = ArtifactStore(tmp_path / 'artifacts', tmp_path / 'temporary')
    store = ApplicationStore(tmp_path / 'app.sqlite3', backup_directory=tmp_path / 'backups')
    app = create_app(UploadService(artifacts, store))
    adapter = SyntheticPredictionAdapter()
    monkeypatch.setattr('redaction_lab.application.document_worker.ApplicationPdfWorker', InProcessSyntheticPdfWorker)
    monkeypatch.setattr('redaction_lab.application.prediction_service.InferenceRuntime.verified', lambda self: _verified(adapter))
    try:
        receipt = _upload(app, 'bad-reference', redacted.read_bytes(), b'%PDF-invalid-reference')
        status, _ = _request(app, 'POST', f"/api/v1/jobs/{receipt['redacted']['job_id']}/process")
        assert status == 200
        result = _request(app, 'GET', f"/api/v1/results/{receipt['redacted']['version_id']}")[1]
        assert result['counts'] == {'requested': 2, 'eligible': 0, 'scored': 0, 'unknown': 2, 'excluded': 0, 'technical_failures': 1}
        assert {row['attempt_status'] for row in result['targets']} == {'SUCCEEDED', 'MALFORMED'}
        assert all(row['evaluation']['experimental_score'] is None for row in result['targets'])
        assert all(row['mapping'] is None for row in result['targets'])
        first_ids = [row['evaluation']['evaluation_id'] for row in result['targets']]
        assert _request(app, 'POST', f"/api/v1/jobs/{receipt['redacted']['job_id']}/process")[0] == 200
        repeated = _request(app, 'GET', f"/api/v1/results/{receipt['redacted']['version_id']}")[1]
        assert [row['evaluation']['evaluation_id'] for row in repeated['targets']] == first_ids
        assert len(adapter.manifests) == 2
    finally:
        artifacts.close()


def test_v03_interrupted_run_reconnect_is_read_only_and_explicit_resume_is_one_shot(tmp_path, monkeypatch):
    from redaction_lab.application.application_store import ProcessingStatus
    redacted, reference = make_synthetic_pair('two_boxes', tmp_path / 'fixture')
    artifacts = ArtifactStore(tmp_path / 'artifacts', tmp_path / 'temporary')
    store = ApplicationStore(tmp_path / 'app.sqlite3', backup_directory=tmp_path / 'backups')
    app = create_app(UploadService(artifacts, store))
    adapter = SyntheticPredictionAdapter()
    monkeypatch.setattr('redaction_lab.application.document_worker.ApplicationPdfWorker', InProcessSyntheticPdfWorker)
    monkeypatch.setattr('redaction_lab.application.prediction_service.InferenceRuntime.verified', lambda self: _verified(adapter))
    try:
        receipt = _upload(app, 'interruption', redacted.read_bytes(), reference.read_bytes())
        async def crash(manifest):
            # Real reference persistence must precede dispatch, even with an interrupted provider.
            assert store.get_version(receipt['reference']['version_id']).processing_state is ProcessingStatus.READY
            assert store.reference_source(receipt['reference']['version_id']) is not None
            raise RuntimeError('synthetic provider interruption')
        with monkeypatch.context() as crash_patch:
            crash_patch.setattr(adapter, 'predict', crash)
            assert _request(app, 'POST', f"/api/v1/jobs/{receipt['redacted']['job_id']}/process")[0] == 500
        path = f"/api/v1/results/{receipt['redacted']['version_id']}"
        interrupted = _request(app, 'GET', path)[1]
        assert interrupted['progress'] == {'total': 2, 'pending': 1, 'running': 0, 'terminal': 1}
        assert len(interrupted['targets']) == 1 and interrupted['targets'][0]['attempt_status'] == 'IN_DOUBT'
        assert interrupted['targets'][0]['evaluation'] is None
        assert _request(app, 'GET', path)[1] == interrupted
        assert len(adapter.manifests) == 0
        assert _request(app, 'POST', f"/api/v1/jobs/{receipt['redacted']['job_id']}/process")[0] == 200
        complete = _request(app, 'GET', path)[1]
        assert complete['progress'] == {'total': 2, 'pending': 0, 'running': 0, 'terminal': 2}
        assert complete['counts']['requested'] == 2 and complete['counts']['technical_failures'] == 1
        assert len(adapter.manifests) == 1
        assert sum(s['counts']['requested'] for s in complete['summaries']['document']) == 2
    finally:
        artifacts.close()


@pytest.mark.parametrize('interruption', ['runtime_unavailable', 'false_claim', 'already_processing'])
def test_resumable_reference_defers_evidence_until_explicit_retry(tmp_path, monkeypatch, interruption):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from redaction_lab.adapters.ollama import OllamaAdapter
    from redaction_lab.application.document_worker import DocumentWorker
    from redaction_lab.application.isolation import RuntimeUnavailable
    from redaction_lab.application.application_store import ProcessingStatus
    from redaction_lab.contracts import DocumentRole
    import sqlite3

    redacted, reference = _matching_reference_pair(tmp_path)
    artifacts = ArtifactStore(tmp_path / 'artifacts', tmp_path / 'temporary')
    store = ApplicationStore(tmp_path / 'app.sqlite3', backup_directory=tmp_path / 'backups')
    app = create_app(UploadService(artifacts, store))
    monkeypatch.setattr('redaction_lab.application.document_worker.ApplicationPdfWorker', InProcessSyntheticPdfWorker)
    adapter = OllamaAdapter(endpoint='http://127.0.0.1:11434', model_id='qwen2.5:1.5b-instruct-q4_K_M', model_config_id='synthetic-json-v2')
    calls = []
    async def transport(endpoint, body, timeout):
        calls.append(body)
        assert 'Agent Cedar' not in body.decode()
        return b'{"model":"qwen2.5:1.5b-instruct-q4_K_M","response":"{\\"reconstruction\\":\\"Agent Cedar\\"}","done":true,"done_reason":"stop","prompt_eval_count":63,"eval_count":12}'
    monkeypatch.setattr(adapter, '_stdlib_transport', transport)
    monkeypatch.setattr('redaction_lab.application.prediction_service.InferenceRuntime.verified', lambda self: _verified(adapter))
    entered, release = Event(), Event()
    executor = ThreadPoolExecutor(max_workers=1)
    future = None
    try:
        receipt = _upload(app, 'resumable', redacted.read_bytes(), reference.read_bytes())
        version_id = receipt['redacted']['version_id']
        reference_id = receipt['reference']['version_id']
        redacted_job = receipt['redacted']['job_id']
        reference_job = app._job_for_version(reference_id).job_id
        assert DocumentWorker(store, artifacts).run_once(owner='redacted', expected_job_id=redacted_job)
        class TemporarilyBlockedWorker(InProcessSyntheticPdfWorker):
            @staticmethod
            def ensure_available():
                if interruption == 'runtime_unavailable':
                    raise RuntimeUnavailable('synthetic unavailable')
            @staticmethod
            def process(pdf_bytes, *, project_id, role):
                if (interruption == 'already_processing' and role is DocumentRole.REFERENCE
                        or interruption == 'false_claim' and project_id == 'concurrent'):
                    entered.set()
                    assert release.wait(timeout=10), 'test did not release real worker'
                return InProcessSyntheticPdfWorker.process(pdf_bytes, project_id=project_id, role=role)
        with monkeypatch.context() as interrupted:
            interrupted.setattr('redaction_lab.application.document_worker.ApplicationPdfWorker', TemporarilyBlockedWorker)
            if interruption == 'false_claim':
                other = _upload(app, 'concurrent', redacted.read_bytes(), None)
                future = executor.submit(DocumentWorker(store, artifacts).run_once, owner='concurrent', expected_job_id=other['redacted']['job_id'])
            elif interruption == 'already_processing':
                future = executor.submit(DocumentWorker(store, artifacts).run_once, owner='reference', expected_job_id=reference_job)
            if future:
                assert entered.wait(timeout=5)
            status, _ = _request(app, 'POST', f'/api/v1/jobs/{redacted_job}/process')
            assert status == 200
            pending = _request(app, 'GET', f'/api/v1/results/{version_id}')[1]
            assert pending['progress'] == {'total': 2, 'pending': 0, 'running': 0, 'terminal': 2}
            assert pending['counts']['requested'] == pending['counts']['unknown'] == 2
            assert pending['score_status'] == 'NONE'
            assert all(row['attempt_status'] == 'SUCCEEDED' for row in pending['targets'])
            assert all(row['evaluation'] is None and row['mapping'] is None for row in pending['targets'])
            assert pending['summaries'] == {'target': [], 'document': [], 'model': []}
            attempt_ids = [row['attempt_id'] for row in pending['targets']]
            with sqlite3.connect(store.path) as connection:
                assert connection.execute('select count(*) from evaluations').fetchone()[0] == 0
                snapshot = tuple(connection.iterdump())
            assert _request(app, 'GET', f'/api/v1/results/{version_id}')[1] == pending
            with sqlite3.connect(store.path) as connection:
                assert tuple(connection.iterdump()) == snapshot
            assert len(calls) == 2
        release.set()
        if future:
            assert future.result(timeout=10)
        # GET after a concurrent reference finishes still must not evaluate.
        assert all(row['evaluation'] is None for row in _request(app, 'GET', f'/api/v1/results/{version_id}')[1]['targets'])
        assert _request(app, 'POST', f'/api/v1/jobs/{redacted_job}/process')[0] == 200
        final = _request(app, 'GET', f'/api/v1/results/{version_id}')[1]
        assert store.get_version(reference_id).processing_state is ProcessingStatus.READY
        assert [row['attempt_id'] for row in final['targets']] == attempt_ids
        assert len(calls) == 2
        assert final['counts']['eligible'] == final['counts']['scored'] == 2
        assert all(row['evaluation']['experimental_score'] is not None for row in final['targets'])
        assert any(row['evaluation']['experimental_score'] == 100 for row in final['targets'])
        assert _request(app, 'POST', f'/api/v1/jobs/{redacted_job}/process')[0] == 200
        assert _request(app, 'GET', f'/api/v1/results/{version_id}')[1] == final
        assert len(calls) == 2
    finally:
        release.set()
        executor.shutdown(wait=True)
        artifacts.close()
