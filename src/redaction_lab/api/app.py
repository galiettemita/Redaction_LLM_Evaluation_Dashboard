"""WSGI orchestration for the backwards-compatible local API v0.3."""

from __future__ import annotations

import os
import re
import asyncio
from hashlib import sha256
from json import JSONDecodeError
from collections import defaultdict
from threading import Lock
from typing import Mapping

from redaction_lab.api.http import (
    API_VERSION,
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
from redaction_lab.application.inference_runtime import InferenceRuntimeUnavailable
from redaction_lab.application.prediction_service import PredictionService
from redaction_lab.application.evaluation_service import EvaluationService
from redaction_lab.application.upload_service import UploadService
from redaction_lab.contracts import DocumentRole, ExperimentalSummaryCell, ExperimentalSummaryProfile
from redaction_lab.evaluator import experimental_prediction_protocol
from redaction_lab.summary import build_experimental_summary, build_experimental_model_summary


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
        self.predictions = PredictionService(self.store)
        self.evaluations = EvaluationService(self.store)
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
    def _result_payload(
        version: StoredDocumentVersion,
        targets: tuple[dict[str, object], ...] = (),
    ) -> dict[str, object]:
        return {
            "version_id": version.version_id,
            "status": _RESULT_STATUS[version.processing_state],
            "targets": list(targets),
            "summaries": {"target": [], "document": [], "model": []},
            "progress": {"total": 0, "pending": 0, "running": 0, "terminal": 0},
            "counts": {"requested": 0, "eligible": 0, "scored": 0, "unknown": 0, "excluded": 0, "technical_failures": 0},
            "score_status": "NONE",
            "verified_score": None,
            "experimental_score": None,
            "truth_status": "UNKNOWN",
        }

    def _pair_for_version(self, version_id):
        pairs = self.store.pairs_for_redacted(version_id)
        if len(pairs) > 1:
            raise HttpProblem(409, "PAIR_CONFLICT", "Document has multiple associated reference choices")
        return pairs[0] if pairs else None

    def _evaluate(self, version_id, pair):
        """Only the explicit process command writes evidence; never replace a result."""
        if pair and pair.reference_version_id:
            reference_job = self._job_for_version(pair.reference_version_id)
            if reference_job.status in {ProcessingStatus.ACCEPTED, ProcessingStatus.PROCESSING}:
                # An unavailable runtime, lost claim, or concurrent reference worker
                # leaves truth pending. Do not freeze a terminal MISSING_REFERENCE
                # record that would prevent a later explicit process from evaluating.
                return
        version = self.store.get_version(version_id)
        source_id, run = self.predictions._stored_run(version_id)
        if run is None:
            return
        source = self.predictions.runs.source(source_id)
        identity = self.predictions._runtime_identity(run)
        groups = defaultdict(list)
        for job in self.predictions.runs.jobs_for_run(run.run_id, project_id=version.project_id):
            records = self.evaluations.list_evaluations(project_id=version.project_id, attempt_id=job.attempt_id) if job.attempt_id else ()
            if len(records) > 1:
                raise ValueError("multiple evaluations for frozen application attempt")
            record = records[0] if records else None
            if record is None and job.attempt_id and job.state not in {"PENDING", "IN_DOUBT"}:
                record = self.evaluations.evaluate_attempt(
                    project_id=version.project_id, attempt_id=job.attempt_id,
                    pair_id=pair.pair_id if pair else None,
                )
            if record:
                cell = ExperimentalSummaryCell.from_evaluation(record)
            else:
                cell = ExperimentalSummaryCell(
                    intent_id=job.job_id,
                    profile=ExperimentalSummaryProfile(project_id=version.project_id,
                        model_id=job.manifest.model_id, model_config_id=identity[1],
                        provider_model_id=None, prediction_protocol_id=experimental_prediction_protocol(run)),
                    document_version_id=source.redacted_document_version_id,
                    target_id=job.manifest.target_id, target_version=job.manifest.target_version,
                    status=job.state,
                )
            groups[cell.profile].append(cell)
        for cells in groups.values():
            for cell in cells:
                self.evaluations.evaluations.store_experimental_summary(
                    build_experimental_summary((cell,), summary_level="TARGET"))
            document = self.evaluations.evaluations.store_experimental_summary(
                build_experimental_summary(cells, summary_level="DOCUMENT"))
            self.evaluations.evaluations.store_experimental_summary(
                build_experimental_model_summary((document,)))

    @staticmethod
    def _evaluation_payload(record):
        evidence = record.evidence
        return {
            "evaluation_id": record.evaluation_id, "schema_version": record.evidence_schema_version,
            "method_id": record.method_id, "scale": record.scale,
            "score_status": record.score_status.value, "experimental_score": record.experimental_score,
            "verified_score": None, "reason": record.reason,
            "prediction_hash": record.prediction_hash, "reference_hash": record.reference_hash,
            "subscores": evidence.subscores.model_dump(mode="json") if evidence else None,
            "warnings": list(evidence.warnings) if evidence else [],
            "applied_caps": list(evidence.applied_caps) if evidence else [],
        }

    @staticmethod
    def _summary_payload(summary, version_id):
        result = {key: getattr(summary, key) for key in (
            "summary_id", "schema_version", "scale", "experimental_score", "verified_score", "denominator")}
        result.update({"model_id": summary.profile.model_id,
            "model_config_id": summary.profile.model_config_id,
            "method_id": summary.profile.method_id, "score_status": summary.score_status.value,
            "counts": summary.counts.model_dump(), "member_ids": list(summary.member_ids)})
        if summary.summary_level.value == "TARGET":
            result.update(target_id=summary.scope_id, target_version=summary.target_version)
        elif summary.summary_level.value == "DOCUMENT":
            result["document_version_id"] = version_id
        else:
            result.update(document_version_ids=[version_id], document_count=summary.document_count)
        return result

    def _results(self, version):
        targets = self.predictions.results(version.version_id) if version.processing_state is ProcessingStatus.READY else ()
        result = self._result_payload(version, targets)
        if version.processing_state is not ProcessingStatus.READY:
            return result
        progress = self.predictions.progress(version.version_id)
        result["progress"] = progress
        source_id, run = self.predictions._stored_run(version.version_id)
        source = self.predictions.runs.source(source_id)
        records = {}
        for row in targets:
            values = self.evaluations.list_evaluations(project_id=version.project_id, attempt_id=row["attempt_id"])
            if len(values) > 1:
                raise ValueError("multiple evaluations for frozen application attempt")
            record = values[0] if values else None
            row.update(mapping=None, evaluation=None)
            if record:
                # get_evaluation already revalidates full immutable provenance; also
                # bind the enclosing API row rather than trusting an ID-only lookup.
                if any(getattr(record, key) != row[key] for key in (
                        "attempt_id", "target_id", "target_version", "model_id", "model_config_id", "provider_model_id")):
                    raise ValueError("evaluation does not bind result row")
                if any(getattr(record, key) != getattr(source, key) for key in (
                        "project_id", "source_id", "source_version", "source_sha256", "redacted_document_version_id")):
                    raise ValueError("evaluation does not bind current source")
                records[record.job_id] = record
                row["evaluation"] = self._evaluation_payload(record)
                if record.mapping:
                    mapping = record.mapping
                    if (mapping.project_id != source.project_id
                            or mapping.target_id != row["target_id"]
                            or mapping.target_version != row["target_version"]
                            or mapping.redacted_document_version_id != source.redacted_document_version_id
                            or mapping.redacted_canonical_hash not in (None, source.canonical_document.canonical_hash)):
                        raise ValueError("mapping does not bind current source")
                    row["mapping"] = record.mapping.model_dump(mode="json")
                    # API document identity is the upload ID. Keep the authenticated
                    # internal source identity unchanged in immutable storage.
                    row["mapping"]["redacted_document_version_id"] = version.version_id
                    row["mapping"]["explanation"] = record.mapping.explanation
        eligible = sum(record.eligible for record in records.values())
        scored = sum(record.experimental_score is not None for record in records.values())
        result["counts"].update(requested=progress["total"], eligible=eligible, scored=scored,
            unknown=progress["total"]-eligible,
            technical_failures=sum(row["attempt_status"] in {"REFUSED", "TIMEOUT", "MALFORMED", "ERROR", "IN_DOUBT"} for row in targets))
        result["score_status"] = "EXPERIMENTAL" if scored else "NONE"
        if run is None:
            return result
        jobs = {job.job_id: job for job in self.predictions.runs.jobs_for_run(run.run_id, project_id=version.project_id)}
        # Only snapshots of current durable cells; old revisions remain in storage.
        for summary in self.evaluations.list_summaries(project_id=version.project_id):
            if summary.document_version_ids != (source.redacted_document_version_id,):
                continue
            if not summary.cells or any(
                cell.intent_id not in jobs
                or cell.evaluation != records.get(cell.intent_id)
                or (cell.evaluation is None and cell.status != jobs[cell.intent_id].state)
                for cell in summary.cells
            ):
                continue
            result["summaries"][summary.summary_level.value.lower()].append(self._summary_payload(summary, version.version_id))
        return result

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
            pair = self._pair_for_version(job.version_id) if job.role is DocumentRole.REDACTED else None
            if job.status is ProcessingStatus.READY:
                current = job
            elif job.status is not ProcessingStatus.ACCEPTED:
                raise HttpProblem(409, "JOB_CONFLICT", "Job is not accepted work")
            else:
                with self.store.connect() as connection:
                    next_row = connection.execute(
                        "SELECT job_id FROM application_jobs WHERE status='ACCEPTED' "
                        "ORDER BY CASE role WHEN 'REDACTED' THEN 0 ELSE 1 END, "
                        "created_at, job_id LIMIT 1"
                    ).fetchone()
                if next_row is None or next_row["job_id"] != job_id:
                    raise HttpProblem(
                        409,
                        "JOB_CONFLICT",
                        "An earlier document job must be processed first",
                    )
                try:
                    worked = DocumentWorker(self.store, self.artifacts).run_once(
                        owner=f"local-api-{os.getpid()}",
                        expected_job_id=job_id,
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
                current = self.store.get_job(job_id)
            if current.status is ProcessingStatus.READY and current.role is DocumentRole.REDACTED:
                if pair and pair.reference_version_id:
                    reference_job = self._job_for_version(pair.reference_version_id)
                    if reference_job.status is ProcessingStatus.ACCEPTED:
                        try:
                            DocumentWorker(self.store, self.artifacts).run_once(
                                owner=f"local-api-{os.getpid()}", expected_job_id=reference_job.job_id)
                        except RuntimeUnavailable:
                            # A missing reference capability cannot discard a valid prediction.
                            pass
                try:
                    asyncio.run(self.predictions.run(current.version_id))
                except InferenceRuntimeUnavailable:
                    return 503, {
                        "error": {
                            "code": "MODEL_RUNTIME_UNVERIFIED",
                            "message": "Model inference runtime is not qualified on this installation",
                        },
                        "job_id": current.job_id,
                        "status": current.status.value,
                    }
                self._evaluate(current.version_id, pair)
            return 200, self._job_payload(current)

    def _dispatch(
        self, environment: Mapping[str, object]
    ) -> tuple[int, dict[str, object]]:
        method = str(environment.get("REQUEST_METHOD", "")).upper()
        path = str(environment.get("PATH_INFO", ""))
        if method == "GET" and path == "/api/v1/health":
            return 200, {
                "api_version": API_VERSION,
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
            return 200, self._results(version)
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
