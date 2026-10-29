from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import pytest

import redaction_lab.application.isolation as isolation_module
from redaction_lab.api.app import LocalApi, create_app
from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application.application_store import StoredDocumentVersion
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.document_worker import DocumentWorker
from redaction_lab.application.isolation import WorkerObservation
from redaction_lab.application.upload_service import UploadService
from redaction_lab.application.inference_runtime import InferenceRuntimeUnavailable
from redaction_lab.application.worker_protocol import (
    WORKER_PROTOCOL_VERSION,
    WorkerResponse,
    WorkerStatus,
)
from redaction_lab.contracts import DocumentRole


def _app(tmp_path: Path):
    artifacts = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    store = ApplicationStore(
        tmp_path / "application.sqlite3", backup_directory=tmp_path / "backups"
    )
    return create_app(UploadService(artifacts, store)), store, artifacts


def _multipart(
    reference: bytes | None = None,
    *,
    redacted: bytes = b"%PDF-redacted-api",
    project_id: str = "project-api",
) -> tuple[bytes, str]:
    boundary = "api-app-test-boundary"
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
    app,
    method: str,
    path: str,
    *,
    body: bytes = b"",
    content_type: str = "",
    host: str = "127.0.0.1:8765",
    origin: str | None = "http://127.0.0.1:8765",
):
    captured: dict[str, object] = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    environment: dict[str, object] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "HTTP_HOST": host,
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.url_scheme": "http",
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    if origin is not None:
        environment["HTTP_ORIGIN"] = origin
    response = b"".join(app(environment, start_response))
    return int(str(captured["status"]).split()[0]), captured["headers"], json.loads(response)


def _upload(
    app,
    *,
    reference: bytes | None = None,
    redacted: bytes = b"%PDF-redacted-api",
    project_id: str = "project-api",
):
    body, content_type = _multipart(
        reference, redacted=redacted, project_id=project_id
    )
    return _request(
        app,
        "POST",
        "/api/v1/documents",
        body=body,
        content_type=content_type,
    )


def test_health_is_versioned_and_truthfully_degraded(tmp_path: Path) -> None:
    app, _, artifacts = _app(tmp_path)
    try:
        status, headers, payload = _request(app, "GET", "/api/v1/health")
    finally:
        artifacts.close()

    assert status == 200
    assert headers["X-Redaction-Lab-API"] == "0.2"
    assert payload == {
        "api_version": "0.2",
        "state": "DEGRADED",
        "runtime_qualified": False,
        "mode": "local",
    }


def test_upload_and_status_routes_use_durable_application_records(tmp_path: Path) -> None:
    app, _, artifacts = _app(tmp_path)
    try:
        status, _, uploaded = _upload(app, reference=b"%PDF-reference-api")
        document_status, _, document = _request(
            app, "GET", f"/api/v1/documents/{uploaded['redacted']['version_id']}"
        )
        job_status, _, job = _request(
            app, "GET", f"/api/v1/jobs/{uploaded['redacted']['job_id']}"
        )
    finally:
        artifacts.close()

    assert status == 201
    assert set(uploaded) == {
        "pair_id",
        "project_id",
        "redacted",
        "reference",
        "truth_status",
    }
    assert set(uploaded["redacted"]) == {
        "version_id",
        "job_id",
        "sha256",
        "byte_size",
        "status",
    }
    assert set(uploaded["reference"]) == {
        "version_id",
        "sha256",
        "byte_size",
    }
    assert uploaded["project_id"] == "project-api"
    assert uploaded["truth_status"] == "UNKNOWN"
    assert uploaded["redacted"]["status"] == "ACCEPTED"
    assert uploaded["redacted"]["byte_size"] == len(b"%PDF-redacted-api")
    assert uploaded["reference"]["byte_size"] == len(b"%PDF-reference-api")
    assert document_status == job_status == 200
    assert document == {
        "version_id": uploaded["redacted"]["version_id"],
        "role": "REDACTED",
        "sha256": uploaded["redacted"]["sha256"],
        "byte_size": len(b"%PDF-redacted-api"),
        "processing_status": "ACCEPTED",
        "page_count": None,
        "job_id": uploaded["redacted"]["job_id"],
        "reason_code": None,
        "source_id": None,
    }
    assert job == {
        "job_id": uploaded["redacted"]["job_id"],
        "version_id": uploaded["redacted"]["version_id"],
        "status": "ACCEPTED",
        "reason_code": None,
        "source_id": None,
    }


def test_results_remain_pending_with_null_scores_and_no_fabricated_targets(
    tmp_path: Path,
) -> None:
    app, _, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app)
        status, _, result = _request(
            app, "GET", f"/api/v1/results/{uploaded['redacted']['version_id']}"
        )
    finally:
        artifacts.close()

    assert status == 200
    assert uploaded["reference"] is None
    assert result == {
        "version_id": uploaded["redacted"]["version_id"],
        "status": "PENDING",
        "targets": [],
        "summaries": {"target": None, "document": None, "model": None},
        "score_status": "NONE",
        "verified_score": None,
        "experimental_score": None,
        "truth_status": "UNKNOWN",
    }


def test_v02_result_payload_exposes_only_revalidated_attempt_provenance() -> None:
    version = StoredDocumentVersion(
        version_id="version-1",
        document_id="document-1",
        project_id="project-1",
        role=__import__("redaction_lab.contracts", fromlist=["DocumentRole"]).DocumentRole.REDACTED,
        artifact_key="sha256/aa/file.pdf",
        sha256="a" * 64,
        byte_size=10,
        page_count=1,
        processing_state=ProcessingStatus.READY,
        source_id="source-1",
        created_at=datetime(2026, 10, 13, tzinfo=UTC),
    )
    target = {
        "target_id": "target-1",
        "target_version": "target-v1",
        "page_index": 0,
        "normalized_bbox": [0.1, 0.2, 0.3, 0.4],
        "attempt_id": "attempt-1",
        "attempt_status": "SUCCEEDED",
        "prediction": "Synthetic prediction <not markup>",
        "model_id": "model-1",
        "provider_model_id": "model-1",
        "model_config_id": "config-1",
        "request_hash": "b" * 64,
        "response_hash": "c" * 64,
    }

    result = LocalApi._result_payload(version, (target,))

    assert result["status"] == "AVAILABLE"
    assert result["targets"] == [target]
    assert result["truth_status"] == "UNKNOWN"
    assert result["score_status"] == "NONE"
    assert result["verified_score"] is None
    assert result["experimental_score"] is None
    assert result["summaries"] == {"target": None, "document": None, "model": None}


def test_unverified_runtime_returns_503_without_claiming_job_or_creating_source(
    tmp_path: Path,
) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        with store.connect() as connection:
            has_source_table = connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='canonical_sources'"
            ).fetchone()
            source_count_before = (
                connection.execute("SELECT count(*) FROM canonical_sources").fetchone()[0]
                if has_source_table is not None
                else 0
            )
        _, _, uploaded = _upload(app)
        job_id = uploaded["redacted"]["job_id"]
        status, _, payload = _request(
            app, "POST", f"/api/v1/jobs/{job_id}/process"
        )
        stored = store.get_job(job_id)
        with store.connect() as connection:
            has_source_table = connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='canonical_sources'"
            ).fetchone()
            source_count_after = (
                connection.execute("SELECT count(*) FROM canonical_sources").fetchone()[0]
                if has_source_table is not None
                else 0
            )
    finally:
        artifacts.close()

    assert status == 503
    assert payload == {
        "error": {
            "code": "RUNTIME_UNVERIFIED",
            "message": "PDF processing runtime is not qualified on this installation",
        },
        "job_id": job_id,
        "status": "ACCEPTED",
    }
    assert stored.status.value == "ACCEPTED"
    assert stored.owner is None
    assert stored.source_id is None
    assert source_count_after == source_count_before


def test_ready_job_can_explicitly_resume_after_model_runtime_recovers(
    tmp_path: Path, monkeypatch
) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app)
        job_id = uploaded["redacted"]["job_id"]
        claimed = store.claim_next(owner="synthetic-document-worker", now=datetime.now(UTC))
        assert claimed is not None
        store.record_runtime(
            job_id,
            owner="synthetic-document-worker",
            request_nonce="a" * 32,
            protocol_version="pdf-worker-v1",
            image_digest="sha256:" + "b" * 64,
            page_count=1,
        )
        version = store.get_version(uploaded["redacted"]["version_id"])
        with store.connect() as connection:
            connection.execute(
                """INSERT INTO canonical_sources (
                    source_id, source_version, project_id, source_sha256, role,
                    redacted_document_version_id, detector_version,
                    canonicalizer_version, canonical_document_version_id,
                    canonical_hash, canonical_json, targets_json, ingested_at, provenance
                ) VALUES (?, ?, ?, ?, 'REDACTED', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "source-synthetic-ready", "synthetic-api-test", version.project_id,
                    version.sha256, version.version_id, "synthetic-detector",
                    "synthetic-canonicalizer", "canonical-synthetic-ready", "c" * 64,
                    "{}", "[]", datetime.now(UTC).isoformat(), "synthetic-api-test",
                ),
            )
        store.complete_job(
            job_id,
            owner="synthetic-document-worker",
            status=ProcessingStatus.READY,
            page_count=1,
            source_id="source-synthetic-ready",
            reason_code=None,
        )

        async def unavailable(version_id):
            raise InferenceRuntimeUnavailable("synthetic unavailable")

        monkeypatch.setattr(app.predictions, "run", unavailable)
        blocked_status, _, blocked = _request(
            app, "POST", f"/api/v1/jobs/{job_id}/process"
        )
        calls = []

        async def recovered(version_id):
            calls.append(version_id)
            return ()

        monkeypatch.setattr(app.predictions, "run", recovered)
        resumed_status, _, resumed = _request(
            app, "POST", f"/api/v1/jobs/{job_id}/process"
        )
    finally:
        artifacts.close()

    assert blocked_status == 503
    assert blocked["error"]["code"] == "MODEL_RUNTIME_UNVERIFIED"
    assert blocked["status"] == "READY"
    assert resumed_status == 200
    assert resumed["status"] == "READY"
    assert calls == [uploaded["redacted"]["version_id"]]


def test_process_request_rejects_nonempty_body_without_claiming_job(
    tmp_path: Path,
) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app)
        job_id = uploaded["redacted"]["job_id"]

        status, _, payload = _request(
            app,
            "POST",
            f"/api/v1/jobs/{job_id}/process",
            body=b"unexpected",
            content_type="application/octet-stream",
        )
        stored = store.get_job(job_id)
    finally:
        artifacts.close()

    assert status == 400
    assert payload == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "Process request must not include a body",
        }
    }
    assert stored.status is ProcessingStatus.ACCEPTED
    assert stored.owner is None


def test_missing_runtime_lock_returns_503_without_claiming_job(
    tmp_path: Path, monkeypatch
) -> None:
    app, store, artifacts = _app(tmp_path)
    missing_lock = tmp_path / "missing-runtime.lock"
    monkeypatch.setattr(isolation_module, "_INSTALL_RUNTIME_LOCK", missing_lock)
    try:
        _, _, uploaded = _upload(app)
        job_id = uploaded["redacted"]["job_id"]

        status, _, payload = _request(
            app, "POST", f"/api/v1/jobs/{job_id}/process"
        )
        stored = store.get_job(job_id)
    finally:
        artifacts.close()

    assert status == 503
    assert payload["error"] == {
        "code": "RUNTIME_UNVERIFIED",
        "message": "PDF processing runtime is not qualified on this installation",
    }
    assert payload["job_id"] == job_id
    assert payload["status"] == "ACCEPTED"
    assert stored.status is ProcessingStatus.ACCEPTED
    assert stored.owner is None


def test_older_optional_reference_does_not_block_next_redacted_process(
    tmp_path: Path, monkeypatch
) -> None:
    app, store, artifacts = _app(tmp_path)
    worker_calls: list[str] = []

    def complete_next_redacted(worker, *, owner, expected_job_id):
        job = worker.store.claim_next(
            owner=owner,
            now=datetime.now(UTC),
            expected_job_id=expected_job_id,
        )
        assert job is not None
        worker_calls.append(job.job_id)
        worker.store.complete_job(
            job.job_id,
            owner=owner,
            status=ProcessingStatus.UNSUPPORTED,
            page_count=None,
            source_id=None,
            reason_code="SYNTHETIC_UNSUPPORTED",
        )
        return True

    async def prediction_must_not_run(_version_id):
        raise AssertionError("unsupported documents must not dispatch prediction")

    monkeypatch.setattr(DocumentWorker, "run_once", complete_next_redacted)
    monkeypatch.setattr(app.predictions, "run", prediction_must_not_run)
    try:
        _, _, first = _upload(
            app,
            redacted=b"%PDF-first-redacted",
            reference=b"%PDF-first-reference",
        )
        first_status, _, first_result = _request(
            app, "POST", f"/api/v1/jobs/{first['redacted']['job_id']}/process"
        )
        _, _, second = _upload(
            app,
            redacted=b"%PDF-second-redacted",
            reference=b"%PDF-second-reference",
        )

        second_status, _, second_result = _request(
            app, "POST", f"/api/v1/jobs/{second['redacted']['job_id']}/process"
        )
        replay_status, _, replay = _request(
            app, "POST", f"/api/v1/jobs/{second['redacted']['job_id']}/process"
        )
        _, _, results = _request(
            app, "GET", f"/api/v1/results/{second['redacted']['version_id']}"
        )
        with store.connect() as connection:
            references = connection.execute(
                "SELECT status, source_id FROM application_jobs "
                "WHERE role='REFERENCE' ORDER BY created_at, job_id"
            ).fetchall()
    finally:
        artifacts.close()

    assert first_status == second_status == 200
    assert first_result["status"] == second_result["status"] == "UNSUPPORTED"
    assert worker_calls == [
        first["redacted"]["job_id"],
        second["redacted"]["job_id"],
    ]
    assert replay_status == 409
    assert replay["error"]["code"] == "JOB_CONFLICT"
    assert len(worker_calls) == 2
    assert [tuple(row) for row in references] == [
        ("ACCEPTED", None),
        ("ACCEPTED", None),
    ]
    assert results["truth_status"] == "UNKNOWN"
    assert results["verified_score"] is None
    assert results["experimental_score"] is None
    assert results["targets"] == []


def test_process_race_never_claims_a_different_project_job(
    tmp_path: Path, monkeypatch
) -> None:
    app_a, store_a, artifacts_a = _app(tmp_path)
    artifacts_b = ArtifactStore(tmp_path / "artifacts", tmp_path / "temporary")
    store_b = ApplicationStore(
        tmp_path / "application.sqlite3", backup_directory=tmp_path / "backups"
    )
    app_b = create_app(UploadService(artifacts_b, store_b))

    class UnsupportedWorker:
        @staticmethod
        def ensure_available() -> None:
            return None

        @staticmethod
        def process(pdf_bytes: bytes, *, project_id: str, role: DocumentRole):
            return WorkerObservation(
                response=WorkerResponse(
                    protocol_version=WORKER_PROTOCOL_VERSION,
                    request_nonce="a" * 32,
                    project_id=project_id,
                    role=role,
                    input_sha256=sha256(pdf_bytes).hexdigest(),
                    status=WorkerStatus.UNSUPPORTED,
                    page_count=0,
                    reason_code="SYNTHETIC_UNSUPPORTED",
                ),
                image_digest="sha256:" + "b" * 64,
            )

    original_run_once = DocumentWorker.run_once
    interleaved = False

    def run_after_other_api_completes_requested_job(
        worker, *, owner, expected_job_id=None
    ):
        nonlocal interleaved
        if not interleaved:
            claimed = app_b.store.claim_next(owner="api-b", now=datetime.now(UTC))
            assert claimed is not None
            app_b.store.complete_job(
                claimed.job_id,
                owner="api-b",
                status=ProcessingStatus.UNSUPPORTED,
                page_count=None,
                source_id=None,
                reason_code="INTERLEAVED_COMPLETION",
            )
            interleaved = True
        options = (
            {"expected_job_id": expected_job_id}
            if expected_job_id is not None
            else {}
        )
        return original_run_once(worker, owner=owner, **options)

    monkeypatch.setattr(
        "redaction_lab.application.document_worker.ApplicationPdfWorker",
        UnsupportedWorker,
    )
    monkeypatch.setattr(
        DocumentWorker, "run_once", run_after_other_api_completes_requested_job
    )
    try:
        _, _, first = _upload(
            app_a, project_id="project-a", redacted=b"%PDF-project-a"
        )
        _, _, second = _upload(
            app_a, project_id="project-b", redacted=b"%PDF-project-b"
        )

        status, _, response = _request(
            app_a, "POST", f"/api/v1/jobs/{first['redacted']['job_id']}/process"
        )
        first_job = store_a.get_job(first["redacted"]["job_id"])
        second_job = store_a.get_job(second["redacted"]["job_id"])
    finally:
        artifacts_b.close()
        artifacts_a.close()

    assert interleaved is True
    assert status == 409
    assert response["error"]["code"] == "JOB_CONFLICT"
    assert first_job.status is ProcessingStatus.UNSUPPORTED
    assert first_job.reason_code == "INTERLEAVED_COMPLETION"
    assert second_job.status is ProcessingStatus.ACCEPTED
    assert second_job.owner is None
    assert second_job.reason_code is None


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/documents/unknown",
        "/api/v1/jobs/unknown",
        "/api/v1/results/unknown",
    ],
)
def test_unknown_records_return_stable_redacted_404(tmp_path: Path, path: str) -> None:
    app, _, artifacts = _app(tmp_path)
    try:
        status, _, payload = _request(app, "GET", path)
    finally:
        artifacts.close()

    assert status == 404
    assert payload == {
        "error": {"code": "NOT_FOUND", "message": "Resource was not found"}
    }


def test_security_guard_runs_before_route_dispatch(tmp_path: Path) -> None:
    app, _, artifacts = _app(tmp_path)
    try:
        status, _, payload = _request(
            app, "GET", "/api/v1/health", host="attacker.test", origin=None
        )
    finally:
        artifacts.close()

    assert status == 400
    assert payload["error"]["code"] == "INVALID_REQUEST"
    assert "attacker.test" not in json.dumps(payload)


def test_artifact_integrity_failure_is_redacted_server_error(tmp_path: Path) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app)
        version = store.get_version(uploaded["redacted"]["version_id"])
        artifacts.path_for(version.artifact_key).write_bytes(b"%PDF-corrupt")

        status, _, payload = _upload(app)
    finally:
        artifacts.close()

    assert status == 500
    assert payload == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "The local API request failed",
        }
    }
    assert str(tmp_path) not in json.dumps(payload)


@pytest.mark.parametrize(
    ("stored_status", "result_status", "reason_code"),
    [
        (ProcessingStatus.NO_REDACTIONS, "NO_REDACTIONS", "NO_SUPPORTED_TARGETS"),
        (ProcessingStatus.UNSUPPORTED, "UNSUPPORTED", "SCANNED_DOCUMENT"),
        (ProcessingStatus.FAILED, "FAILED", "PARSER_FAILURE"),
    ],
)
def test_results_preserve_distinct_terminal_processing_outcomes(
    tmp_path: Path,
    stored_status: ProcessingStatus,
    result_status: str,
    reason_code: str,
) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app)
        job = store.claim_next(owner="test-worker", now=datetime.now(UTC))
        assert job is not None
        store.complete_job(
            job.job_id,
            owner="test-worker",
            status=stored_status,
            page_count=None,
            source_id=None,
            reason_code=reason_code,
        )

        result_code, _, result = _request(
            app, "GET", f"/api/v1/results/{uploaded['redacted']['version_id']}"
        )
        job_code, _, job_payload = _request(
            app, "GET", f"/api/v1/jobs/{job.job_id}"
        )
    finally:
        artifacts.close()

    assert result_code == job_code == 200
    assert result == {
        "version_id": uploaded["redacted"]["version_id"],
        "status": result_status,
        "targets": [],
        "summaries": {"target": None, "document": None, "model": None},
        "score_status": "NONE",
        "verified_score": None,
        "experimental_score": None,
        "truth_status": "UNKNOWN",
    }
    assert job_payload["reason_code"] == reason_code


def test_process_route_never_claims_a_different_queued_job(tmp_path: Path) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        _, _, first = _upload(app, redacted=b"%PDF-first")
        _, _, second = _upload(app, redacted=b"%PDF-second")

        status, _, payload = _request(
            app,
            "POST",
            f"/api/v1/jobs/{second['redacted']['job_id']}/process",
        )
        first_job = store.get_job(first["redacted"]["job_id"])
        second_job = store.get_job(second["redacted"]["job_id"])
    finally:
        artifacts.close()

    assert status == 409
    assert payload["error"]["code"] == "JOB_CONFLICT"
    assert first_job.status is ProcessingStatus.ACCEPTED
    assert second_job.status is ProcessingStatus.ACCEPTED
    assert first_job.owner is second_job.owner is None


def test_reference_version_does_not_expose_prediction_results(tmp_path: Path) -> None:
    app, _, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app, reference=b"%PDF-reference-api")
        status, _, payload = _request(
            app, "GET", f"/api/v1/results/{uploaded['reference']['version_id']}"
        )
    finally:
        artifacts.close()

    assert status == 409
    assert payload == {
        "error": {
            "code": "RESULTS_UNAVAILABLE",
            "message": "Results are available only for redacted documents",
        }
    }


def test_reupload_of_terminal_identity_does_not_claim_a_new_accepted_job(
    tmp_path: Path,
) -> None:
    app, store, artifacts = _app(tmp_path)
    try:
        _, _, uploaded = _upload(app)
        job = store.claim_next(owner="test-worker", now=datetime.now(UTC))
        assert job is not None
        store.complete_job(
            job.job_id,
            owner="test-worker",
            status=ProcessingStatus.NO_REDACTIONS,
            page_count=1,
            source_id=None,
            reason_code="NO_SUPPORTED_TARGETS",
        )

        status, _, payload = _upload(app, reference=b"%PDF-new-reference")
        with store.connect() as connection:
            job_count = connection.execute(
                "SELECT count(*) FROM application_jobs"
            ).fetchone()[0]
            version_count = connection.execute(
                "SELECT count(*) FROM document_versions"
            ).fetchone()[0]
    finally:
        artifacts.close()

    assert status == 409
    assert payload == {
        "error": {
            "code": "UPLOAD_CONFLICT",
            "message": "This document upload already has a terminal job",
        }
    }
    assert store.get_job(uploaded["redacted"]["job_id"]).status is ProcessingStatus.NO_REDACTIONS
    assert job_count == 1
    assert version_count == 1
