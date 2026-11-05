from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from hashlib import sha256
import sqlite3

import pytest

from redaction_lab.application.application_store import ApplicationStore, ProcessingStatus
from redaction_lab.application.worker_protocol import WorkerResponse, WORKER_PROTOCOL_VERSION
from redaction_lab.contracts import DocumentRole
from redaction_lab.store import RunStore
from redaction_lab.worker import run_pending_once
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from redaction_lab.adapters.base import PredictionAdapter, PredictionResponse
from redaction_lab.contracts import RunDefinition, TokenUsage


class StoredAttemptAdapter(PredictionAdapter):
    model_config_id = 'synthetic-config-v1'

    def request_hash(self, manifest):
        return sha256(manifest.model_dump_json().encode()).hexdigest()

    async def predict(self, manifest):
        now = datetime.now(UTC)
        return PredictionResponse(status='SUCCEEDED', request_hash=self.request_hash(manifest),
            response_hash='f'*64, prediction='Agent Cedar', model_config_id=self.model_config_id,
            provider_model_id=manifest.model_id, usage=TokenUsage(input_tokens=1, output_tokens=2, total_tokens=3),
            started_at=now, completed_at=now)


def _run(source):
    return RunDefinition(run_id='run-1', run_version='run-v1', project_id=source.project_id,
        target_versions=source.target_versions, model_ids=('synthetic-model',),
        experiment_condition='redacted-document-only',
        canonical_document_version_id=source.canonical_document.canonical_document_version_id,
        canonical_document_hash=source.canonical_document.canonical_hash, common_context_budget=4096,
        context_policy='common-full-document', prompt_id='prompt-1', prompt_version='prompt-v1',
        settings={'temperature': 0}, attempt_policy='one-frozen-attempt', tool_permissions=(),
        budget_label='synthetic', created_by='test', created_at=datetime.now(UTC))


def _pdf_bytes(draw):
    data = BytesIO()
    canvas = Canvas(data, pagesize=(612, 792), invariant=1)
    canvas.setFont('Helvetica', 11)
    draw(canvas)
    canvas.save()
    return data.getvalue()


def _overlay(canvas, x, y, prefix, secret):
    start = x + stringWidth(prefix, 'Helvetica', 11) - 1
    canvas.setFillColorRGB(0, 0, 0)
    canvas.rect(start, y-3, stringWidth(secret, 'Helvetica', 11)+2, 14, fill=1, stroke=0)


def _service_inputs(tmp_path, *, reference='The courier Agent Cedar arrived at dawn.'):
    pdf = _pdf_bytes(lambda canvas: (canvas.drawString(72, 700, 'The courier Agent Cedar arrived at dawn.'),
                                    _overlay(canvas, 72, 700, 'The courier ', 'Agent Cedar')))
    app = ApplicationStore(tmp_path / 'app.sqlite3', backup_directory=tmp_path / 'backups')
    digest = sha256(pdf).hexdigest()
    redacted = app.register_upload(project_id='project', role=DocumentRole.REDACTED,
        artifact_key='redacted.pdf', sha256=digest, byte_size=len(pdf))
    job = app.claim_next(owner='worker', now=datetime.now(UTC))
    runs = RunStore(app.path)
    source = runs.source(runs.ingest_redacted_pdf(pdf, project_id='project'))
    app.complete_job(job.job_id, owner='worker', status=ProcessingStatus.READY, page_count=1,
        source_id=source.source_id, reason_code=None)
    ref = app.register_upload(project_id='project', role=DocumentRole.REFERENCE,
        artifact_key='reference.pdf', sha256='c'*64, byte_size=100)
    job = app.claim_next(owner='worker', now=datetime.now(UTC))
    response = WorkerResponse(protocol_version=WORKER_PROTOCOL_VERSION, request_nonce='a'*32,
        project_id='project', role=DocumentRole.REFERENCE, input_sha256='c'*64,
        status='PROCESSABLE', page_count=1, reference_text=reference,
        reference_hash=sha256(reference.encode()).hexdigest(),
        reference_canonicalizer_version='safe-exact-visible-text-v1')
    app.record_runtime(job.job_id, owner='worker', request_nonce=response.request_nonce,
        protocol_version=response.protocol_version, image_digest='sha256:'+'d'*64, page_count=1)
    app.record_reference_source(job.job_id, owner='worker', response=response)
    app.recover_interrupted(now=datetime.now(UTC))
    pair = app.create_pair(project_id='project', redacted_version_id=redacted.version_id, reference_version_id=ref.version_id)
    runs.enqueue(source.source_id, source.targets[0].target_id, _run(source))
    asyncio.run(run_pending_once(runs, StoredAttemptAdapter()))
    return app, pair, runs.attempts()[0]


def test_service_aligns_stored_reference_and_read_paths_do_not_evaluate(tmp_path, monkeypatch):
    from redaction_lab.application.evaluation_service import EvaluationService
    app, pair, attempt = _service_inputs(tmp_path)
    service = EvaluationService(app)
    record = service.evaluate_attempt(project_id='project', attempt_id=attempt.attempt_id, pair_id=pair.pair_id)
    assert record.experimental_score == 100.0
    assert record.mapping.reference_document_version_id == pair.reference_version_id
    assert record.mapping.exact_revealed_text == 'Agent Cedar'
    assert record.verified_score is None
    assert 'Agent Cedar' not in service.evaluations.run_store.resolve_attempt(attempt.attempt_id, project_id='project').manifest.model_dump_json()
    summaries = service.summarize((record,))
    assert {s.summary_level.value for s in summaries} == {'TARGET', 'DOCUMENT', 'MODEL'}
    with sqlite3.connect(app.path) as conn:
        before = tuple(conn.iterdump())
    def forbidden(*args, **kwargs):
        raise AssertionError('read called scoring')
    monkeypatch.setattr('redaction_lab.experimental_scoring.score_text_agreement', forbidden)
    assert service.get_evaluation(record.evaluation_id, project_id='project') == record
    assert service.list_evaluations(project_id='project', attempt_id=attempt.attempt_id) == (record,)
    assert len(service.list_summaries(project_id='project')) == 3
    with sqlite3.connect(app.path) as conn:
        assert tuple(conn.iterdump()) == before


@pytest.mark.parametrize('reference', ['The courier [REDACTED] arrived at dawn.',
    'Wrong document.', 'The courier Agent Cedar arrived at dawn. The courier Agent Birch arrived at dawn.'])
def test_service_persists_unknown_reference_without_zero(tmp_path, reference):
    from redaction_lab.application.evaluation_service import EvaluationService
    app, pair, attempt = _service_inputs(tmp_path, reference=reference)
    record = EvaluationService(app).evaluate_attempt(project_id='project', attempt_id=attempt.attempt_id, pair_id=pair.pair_id)
    assert record.experimental_score is None
    assert record.eligible is False
    assert record.evidence is None


def test_service_missing_reference_and_wrong_pair_fail_closed(tmp_path):
    from redaction_lab.application.evaluation_service import EvaluationService
    app, pair, attempt = _service_inputs(tmp_path)
    service = EvaluationService(app)
    unknown = service.evaluate_attempt(project_id='project', attempt_id=attempt.attempt_id)
    assert unknown.experimental_score is None
    assert unknown.reason == 'MISSING_REFERENCE'
    with pytest.raises(ValueError):
        service.evaluate_attempt(project_id='other-project', attempt_id=attempt.attempt_id, pair_id=pair.pair_id)
    other = app.register_upload(project_id='project', role=DocumentRole.REDACTED,
        artifact_key='other.pdf', sha256='e'*64, byte_size=100)
    bad_pair = app.create_pair(project_id='project', redacted_version_id=other.version_id, reference_version_id=pair.reference_version_id)
    with pytest.raises(ValueError, match='pair|source'):
        service.evaluate_attempt(project_id='project', attempt_id=attempt.attempt_id, pair_id=bad_pair.pair_id)
