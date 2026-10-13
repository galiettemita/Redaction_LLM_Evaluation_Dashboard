"""WSGI orchestration for the frozen Redaction Lab local API v0.1."""

from __future__ import annotations

import os
import re
from hashlib import sha256
from json import JSONDecodeError
from threading import Lock
from typing import Mapping

from redaction_lab.api.http import (
    HttpProblem,
    MAX_UPLOAD_BODY_BYTES,
    StartResponse,
    json_response,
    parse_document_upload,
    read_bounded_body,
    validate_local_request,
)
from redaction_lab.application.application_store import (
    ProcessingStatus,
    StoredApplicationJob,
    StoredDocumentVersion,
)
from redaction_lab.application.artifact_store import ArtifactIntegrityError
from redaction_lab.application.document_worker import DocumentWorker
from redaction_lab.application.isolation import RuntimeUnavailable
from redaction_lab.application.upload_service import UploadService
from redaction_lab.contracts import DocumentRole


_DOCUMENT_ROUTE = re.compile(r"^/api/v1/documents/([^/]+)$")
_JOB_ROUTE = re.compile(r"^/api/v1/jobs/([^/]+)$")
_PROCESS_ROUTE = re.compile(r"^/api/v1/jobs/([^/]+)/process$")
_RESULT_ROUTE = re.compile(r"^/api/v1/results/([^/]+)$")
_RESULT_STATUS = {
    ProcessingStatus.ACCEPTED: "PENDING",
    ProcessingStatus.PROCESSING: "PENDING",
    ProcessingStatus.READY: "AVAILABLE",
    ProcessingStatus.NO_REDACTIONS: "NO_REDACTIONS",
    ProcessingStatus.UNSUPPORTED: "UNSUPPORTED",
    ProcessingStatus.FAILED: "FAILED",
}


class LocalApi:
    """A dependency-free WSGI app over application-owned Task 7A services."""

    def __init__(self, uploads: UploadService) -> None:
        self.uploads = uploads
        self.store = uploads.store
        self.artifacts = uploads.artifacts
        self._orchestration_lock = Lock()

    @staticmethod
    def _error(problem: HttpProblem) -> dict[str, object]:
        return {
            "error": {"code": problem.code, "message": problem.message}
        }

    def _job_for_version(self, version_id: str) -> StoredApplicationJob:
        with self.store.connect() as connection:
            row = connection.execute(
                "SELECT job_id FROM application_jobs WHERE document_version_id=?",
                (version_id,),
            ).fetchone()
        if row is None:
            raise KeyError(version_id)
        return self.store.get_job(str(row["job_id"]))

    @staticmethod
    def _document_payload(
        version: StoredDocumentVersion, job: StoredApplicationJob
    ) -> dict[str, object]:
        return {
            "version_id": version.version_id,
            "role": version.role.value,
            "sha256": version.sha256,
            "byte_size": version.byte_size,
            "processing_status": version.processing_state.value,
            "page_count": version.page_count,
            "job_id": job.job_id,
            "reason_code": job.reason_code,
            "source_id": version.source_id,
        }

    @staticmethod
    def _job_payload(job: StoredApplicationJob) -> dict[str, object]:
        return {
            "job_id": job.job_id,
            "version_id": job.version_id,
            "status": job.status.value,
            "reason_code": job.reason_code,
            "source_id": job.source_id,
        }

    @staticmethod
    def _result_payload(version: StoredDocumentVersion) -> dict[str, object]:
        return {
            "version_id": version.version_id,
            "status": _RESULT_STATUS[version.processing_state],
            "targets": [],
            "summaries": {"target": None, "document": None, "model": None},
            "score_status": "NONE",
            "verified_score": None,
            "experimental_score": None,
            "truth_status": "UNKNOWN",
        }

    @staticmethod
    def _raise_upload_conflict(status: ProcessingStatus) -> None:
        message = (
            "This document upload is already processing"
            if status is ProcessingStatus.PROCESSING
            else "This document upload already has a terminal job"
        )
        raise HttpProblem(409, "UPLOAD_CONFLICT", message)

    def _upload(self, environment: Mapping[str, object]) -> tuple[int, dict[str, object]]:
        body = read_bounded_body(environment, max_bytes=MAX_UPLOAD_BODY_BYTES)
        request = parse_document_upload(str(environment.get("CONTENT_TYPE", "")), body)
        redacted_digest = sha256(request.redacted_pdf).hexdigest()
        with self.store.connect() as connection:
            existing = connection.execute(
                """SELECT j.status FROM document_versions v
                   JOIN application_jobs j ON j.document_version_id=v.version_id
                   WHERE v.project_id=? AND v.role='REDACTED' AND v.sha256=?""",
                (request.project_id, redacted_digest),
            ).fetchone()
        if existing is not None:
            existing_status = ProcessingStatus(existing["status"])
            if existing_status is not ProcessingStatus.ACCEPTED:
                self._raise_upload_conflict(existing_status)
        pair = self.uploads.accept_pair(
            project_id=request.project_id,
            redacted_chunks=(request.redacted_pdf,),
            reference_chunks=(request.reference_pdf,)
            if request.reference_pdf is not None
            else None,
        )
        redacted = self.store.get_version(pair.redacted_version_id)
        redacted_job = self._job_for_version(redacted.version_id)
        if redacted_job.status is not ProcessingStatus.ACCEPTED:
            self._raise_upload_conflict(redacted_job.status)
        reference = (
            self.store.get_version(pair.reference_version_id)
            if pair.reference_version_id is not None
            else None
        )
        return 201, {
            "pair_id": pair.pair_id,
            "project_id": pair.project_id,
            "redacted": {
                "version_id": redacted.version_id,
                "job_id": redacted_job.job_id,
                "sha256": redacted.sha256,
                "byte_size": redacted.byte_size,
                "status": "ACCEPTED",
            },
            "reference": (
                {
                    "version_id": reference.version_id,
                    "sha256": reference.sha256,
                    "byte_size": reference.byte_size,
                }
                if reference is not None
                else None
            ),
            "truth_status": "UNKNOWN",
        }

    def _process(self, job_id: str) -> tuple[int, dict[str, object]]:
        with self._orchestration_lock:
            job = self.store.get_job(job_id)
            if job.status is not ProcessingStatus.ACCEPTED:
                raise HttpProblem(409, "JOB_CONFLICT", "Job is not accepted work")
            with self.store.connect() as connection:
                next_row = connection.execute(
                    "SELECT job_id FROM application_jobs WHERE status='ACCEPTED' "
                    "ORDER BY created_at, job_id LIMIT 1"
                ).fetchone()
            if next_row is None or next_row["job_id"] != job_id:
                raise HttpProblem(
                    409,
                    "JOB_CONFLICT",
                    "An earlier document job must be processed first",
                )
            try:
                worked = DocumentWorker(self.store, self.artifacts).run_once(
                    owner=f"local-api-{os.getpid()}"
                )
            except (
                RuntimeUnavailable,
                OSError,
                JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ):
                current = self.store.get_job(job_id)
                if (
                    current.status is not ProcessingStatus.ACCEPTED
                    or current.owner is not None
                ):
                    raise
                return 503, {
                    "error": {
                        "code": "RUNTIME_UNVERIFIED",
                        "message": (
                            "PDF processing runtime is not qualified on this installation"
                        ),
                    },
                    "job_id": current.job_id,
                    "status": current.status.value,
                }
            if not worked:
                raise HttpProblem(409, "JOB_CONFLICT", "Another job is processing")
            return 200, self._job_payload(self.store.get_job(job_id))

    def _dispatch(
        self, environment: Mapping[str, object]
    ) -> tuple[int, dict[str, object]]:
        method = str(environment.get("REQUEST_METHOD", "")).upper()
        path = str(environment.get("PATH_INFO", ""))
        if method == "GET" and path == "/api/v1/health":
            return 200, {
                "api_version": "0.1",
                "state": "DEGRADED",
                "runtime_qualified": False,
                "mode": "local",
            }
        if method == "POST" and path == "/api/v1/documents":
            with self._orchestration_lock:
                return self._upload(environment)
        match = _DOCUMENT_ROUTE.fullmatch(path)
        if method == "GET" and match is not None:
            version = self.store.get_version(match.group(1))
            return 200, self._document_payload(
                version, self._job_for_version(version.version_id)
            )
        match = _JOB_ROUTE.fullmatch(path)
        if method == "GET" and match is not None:
            return 200, self._job_payload(self.store.get_job(match.group(1)))
        match = _PROCESS_ROUTE.fullmatch(path)
        if method == "POST" and match is not None:
            if str(environment.get("CONTENT_LENGTH", "")) not in {"", "0"}:
                raise HttpProblem(
                    400, "INVALID_REQUEST", "Process request must not include a body"
                )
            return self._process(match.group(1))
        match = _RESULT_ROUTE.fullmatch(path)
        if method == "GET" and match is not None:
            version = self.store.get_version(match.group(1))
            if version.role is not DocumentRole.REDACTED:
                raise HttpProblem(
                    409,
                    "RESULTS_UNAVAILABLE",
                    "Results are available only for redacted documents",
                )
            return 200, self._result_payload(version)
        raise HttpProblem(404, "NOT_FOUND", "Resource was not found")

    def __call__(self, environment: Mapping[str, object], start_response: StartResponse):
        try:
            validate_local_request(environment)
            status, payload = self._dispatch(environment)
        except KeyError:
            status = 404
            payload = self._error(
                HttpProblem(404, "NOT_FOUND", "Resource was not found")
            )
        except HttpProblem as problem:
            status = problem.status
            payload = self._error(problem)
        except ArtifactIntegrityError:
            status = 500
            payload = self._error(
                HttpProblem(500, "INTERNAL_ERROR", "The local API request failed")
            )
        except ValueError:
            status = 422
            payload = self._error(
                HttpProblem(422, "INVALID_INPUT", "Request input is invalid")
            )
        except Exception:
            status = 500
            payload = self._error(
                HttpProblem(500, "INTERNAL_ERROR", "The local API request failed")
            )
        return json_response(start_response, status, payload)


def create_app(uploads: UploadService) -> LocalApi:
    """Compose the API without a caller-provided worker or authority callback."""

    return LocalApi(uploads)
