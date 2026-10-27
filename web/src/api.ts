/** API v0.2 consumer. Predictions are provenance records, never revealed truth. */
export type Health = { api_version: '0.2'; state: 'READY' | 'DEGRADED'; runtime_qualified: false; mode: 'local' };
export type Handle = { version_id: string; job_id: string };
export type ProcessingStatus = 'ACCEPTED' | 'PROCESSING' | 'READY' | 'NO_REDACTIONS' | 'UNSUPPORTED' | 'FAILED';
export type Job = Handle & { status: ProcessingStatus; reason_code: string | null; source_id: string | null };
export type ProcessReceipt = { job_id: string; status: ProcessingStatus; reason_code: string | null; source_id: string | null };
export type Document = Handle & { role: 'REDACTED'; sha256: string; byte_size: number;
  processing_status: ProcessingStatus; page_count: number | null; reason_code: string | null; source_id: string | null };
export type AcceptedUpload = { pair_id: string; project_id: string; redacted: Handle & {
  sha256: string; byte_size: number; status: 'ACCEPTED' };
  reference: { version_id: string; sha256: string; byte_size: number } | null; truth_status: 'UNKNOWN' };
export type AttemptStatus = 'SUCCEEDED' | 'REFUSED' | 'TIMEOUT' | 'MALFORMED' | 'ERROR' | 'IN_DOUBT';
export type PredictionTarget = { target_id: string; target_version: string; page_index: number;
  normalized_bbox: [number, number, number, number]; attempt_id: string; attempt_status: AttemptStatus;
  prediction: string | null; model_id: string; provider_model_id: string | null; model_config_id: string;
  request_hash: string; response_hash: string | null };
export type Results = { version_id: string; status: 'PENDING' | 'UNSUPPORTED' | 'NO_REDACTIONS' | 'FAILED' | 'NEEDS_REVIEW' | 'AVAILABLE';
  targets: PredictionTarget[]; summaries: { target: null; document: null; model: null };
  score_status: 'NONE'; verified_score: null; experimental_score: null; truth_status: 'UNKNOWN' };
export type Snapshot = { document: Document; job: Job; results: Results };
const MAX_BYTES = 25 * 1024 * 1024;
const processing = ['ACCEPTED', 'PROCESSING', 'READY', 'NO_REDACTIONS', 'UNSUPPORTED', 'FAILED'];
const resultStates = ['PENDING', 'UNSUPPORTED', 'NO_REDACTIONS', 'FAILED', 'NEEDS_REVIEW', 'AVAILABLE'];
const identifier = (value: unknown): value is string => typeof value === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(value);
const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const nullableText = (value: unknown) => value === null || (typeof value === 'string' && value.length <= 256);
const digest = (value: unknown) => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const bytes = (value: unknown) => typeof value === 'number' && Number.isSafeInteger(value) && value > 0 && value <= MAX_BYTES;
const status = (value: unknown) => typeof value === 'string' && processing.includes(value);
const boundedText = (value: unknown, limit = 256) => typeof value === 'string' && value.length > 0 && value.length <= limit && !/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value);
function predictionTarget(value: unknown): value is PredictionTarget {
  if (!object(value) || !identifier(value.target_id) || !identifier(value.target_version) ||
      !identifier(value.attempt_id) || !boundedText(value.model_id) || !boundedText(value.model_config_id) ||
      !(value.provider_model_id === null || boundedText(value.provider_model_id)) || !digest(value.request_hash) ||
      !(value.response_hash === null || digest(value.response_hash)) ||
      typeof value.attempt_status !== 'string' || !['SUCCEEDED', 'REFUSED', 'TIMEOUT', 'MALFORMED', 'ERROR', 'IN_DOUBT'].includes(value.attempt_status) ||
      typeof value.page_index !== 'number' || !Number.isInteger(value.page_index) || value.page_index < 0 || value.page_index >= 100 ||
      !Array.isArray(value.normalized_bbox) || value.normalized_bbox.length !== 4 ||
      !value.normalized_bbox.every(coordinate => typeof coordinate === 'number' && Number.isFinite(coordinate) && coordinate >= 0 && coordinate <= 1)) return false;
  const [x0, y0, x1, y1] = value.normalized_bbox;
  if (!(x0 < x1 && y0 < y1)) return false;
  return value.attempt_status === 'SUCCEEDED'
    ? boundedText(value.prediction, 1_048_576) && value.response_hash !== null && value.provider_model_id === value.model_id
    : value.prediction === null;
}
export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status = 0) {
    super(message); this.name = 'ApiError'; this.code = code; this.status = status;
  }
}
const mismatch = () => new ApiError('CONTRACT_MISMATCH', 'The local service response does not match API contract v0.2.');
function checked<T>(value: unknown, valid: boolean): T { if (!valid) throw mismatch(); return value as T; }
function requireId(value: string) { if (!identifier(value)) throw new ApiError('INVALID_INPUT', 'The saved identifier is invalid.'); return value; }
export function validatePdf(file: File | null, required = true): void {
  if (!file) { if (required) throw new ApiError('INVALID_INPUT', 'A redacted PDF is required.'); return; }
  if (!/\.pdf$/i.test(file.name) || (file.type !== '' && file.type !== 'application/pdf')) {
    throw new ApiError('INVALID_INPUT', 'Choose a PDF file.');
  }
  if (file.size === 0) throw new ApiError('INVALID_INPUT', 'The PDF is empty.');
  if (file.size > MAX_BYTES) throw new ApiError('INVALID_INPUT', 'Each PDF must be 25 MiB or smaller.');
}
function publicError(code: string, httpStatus: number): ApiError {
  const messages: Record<string, string> = {
    RUNTIME_UNVERIFIED: 'PDF processing is unavailable because this installation is not qualified. Your accepted job has not started.',
    MODEL_RUNTIME_UNVERIFIED: 'The document is ready, but model inference is unavailable because this installation is not qualified.',
    PAYLOAD_TOO_LARGE: 'Each PDF must be 25 MiB or smaller.',
    JOB_CONFLICT: 'This job cannot be started now. Refresh its saved status.',
    UPLOAD_CONFLICT: 'This upload already has a job. Restore its saved status instead of starting again.',
    NOT_FOUND: 'The saved document or job was not found on this installation.',
    RESULTS_UNAVAILABLE: 'Results are unavailable for this document.',
  };
  return new ApiError(code, messages[code] ?? ({
    400: 'The local service rejected this request.', 404: 'The saved document or job was not found.',
    409: 'The request conflicts with stored work. Refresh the saved status.', 413: 'The upload is too large.',
    415: 'The service accepts PDF uploads only.', 422: 'The service could not accept this PDF or request.',
    503: 'Document processing is unavailable on this installation.',
  } as Record<number, string>)[httpStatus] ?? 'The local service request failed.', httpStatus);
}
export function createApi(origin: string, transport: typeof fetch = globalThis.fetch) {
  const url = new URL(origin);
  if (!['http:', 'https:'].includes(url.protocol) || url.hostname !== '127.0.0.1' ||
      url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new ApiError('LOCAL_ONLY', 'Open the application at its local 127.0.0.1 address.');
  }
  async function request(path: string, method = 'GET', body?: FormData, signal?: AbortSignal): Promise<unknown> {
    let response: Response;
    try {
      response = await transport(path, { method, body, signal, headers: { Accept: 'application/json' },
        credentials: 'same-origin', mode: 'same-origin', redirect: 'error', cache: 'no-store' });
    } catch (error) {
      if (signal?.aborted) throw new ApiError('ABORTED', 'Status refresh was cancelled.');
      throw new ApiError('CONNECTION_FAILED', 'Could not reach the local service. Refresh saved status before repeating an upload or process request.');
    }
    if (response.headers.get('X-Redaction-Lab-API') !== '0.2' ||
        response.headers.get('Content-Type')?.split(';')[0].trim() !== 'application/json') throw mismatch();
    let payload: unknown;
    try { payload = await response.json(); } catch { throw mismatch(); }
    if (!response.ok) {
      if (!object(payload) || !object(payload.error) || typeof payload.error.code !== 'string' ||
          typeof payload.error.message !== 'string') throw mismatch();
      throw publicError(payload.error.code, response.status);
    }
    return payload;
  }
  async function health(signal?: AbortSignal): Promise<Health> {
    const value = await request('/api/v1/health', 'GET', undefined, signal);
    return checked(value, object(value) && value.api_version === '0.2' && typeof value.state === 'string' && ['READY', 'DEGRADED'].includes(value.state) &&
      value.runtime_qualified === false && value.mode === 'local');
  }
  async function upload(projectId: string, redacted: File | null, reference: File | null): Promise<AcceptedUpload> {
    if (!identifier(projectId)) throw new ApiError('INVALID_INPUT', 'Enter a project ID using letters, numbers, hyphens or underscores (up to 128 characters).');
    validatePdf(redacted); validatePdf(reference, false);
    const body = new FormData(); body.append('project_id', projectId); body.append('redacted_pdf', redacted!);
    if (reference) body.append('reference_pdf', reference);
    const value = await request('/api/v1/documents', 'POST', body);
    const r = object(value) ? value.redacted : null;
    const ref = object(value) ? value.reference : undefined;
    return checked(value, object(value) && identifier(value.pair_id) && value.project_id === projectId && value.truth_status === 'UNKNOWN' &&
      object(r) && identifier(r.version_id) && identifier(r.job_id) && digest(r.sha256) && bytes(r.byte_size) && r.status === 'ACCEPTED' &&
      (ref === null || (object(ref) && identifier(ref.version_id) && digest(ref.sha256) && bytes(ref.byte_size))) &&
      (reference ? ref !== null : ref === null));
  }
  async function document(versionId: string, signal?: AbortSignal): Promise<Document> {
    const value = await request(`/api/v1/documents/${requireId(versionId)}`, 'GET', undefined, signal);
    return checked(value, object(value) && value.version_id === versionId && value.role === 'REDACTED' &&
      digest(value.sha256) && bytes(value.byte_size) && identifier(value.job_id) && status(value.processing_status) &&
      (value.page_count === null || (typeof value.page_count === 'number' && Number.isInteger(value.page_count) && value.page_count > 0 && value.page_count <= 100)) &&
      nullableText(value.reason_code) && nullableText(value.source_id));
  }
  function validateJob(value: unknown, jobId: string): Job {
    return checked(value, object(value) && value.job_id === jobId && identifier(value.version_id) && status(value.status) &&
      nullableText(value.reason_code) && nullableText(value.source_id));
  }
  async function job(jobId: string, signal?: AbortSignal): Promise<Job> {
    return validateJob(await request(`/api/v1/jobs/${requireId(jobId)}`, 'GET', undefined, signal), jobId);
  }
  async function process(jobId: string): Promise<ProcessReceipt> {
    const value = await request(`/api/v1/jobs/${requireId(jobId)}/process`, 'POST');
    return checked(value, object(value) && value.job_id === jobId && status(value.status) &&
      nullableText(value.reason_code) && nullableText(value.source_id));
  }
  async function results(versionId: string, signal?: AbortSignal): Promise<Results> {
    const value = await request(`/api/v1/results/${requireId(versionId)}`, 'GET', undefined, signal);
    return checked(value, object(value) && value.version_id === versionId && typeof value.status === 'string' && resultStates.includes(value.status) &&
      Array.isArray(value.targets) && value.targets.every(predictionTarget) &&
      new Set(value.targets.map(target => target.target_id)).size === value.targets.length &&
      new Set(value.targets.map(target => target.attempt_id)).size === value.targets.length && object(value.summaries) &&
      value.summaries.target === null && value.summaries.document === null && value.summaries.model === null &&
      value.score_status === 'NONE' && value.verified_score === null && value.experimental_score === null && value.truth_status === 'UNKNOWN');
  }
  async function snapshot(handle: Handle, signal?: AbortSignal): Promise<Snapshot> {
    const [d, j, r] = await Promise.all([document(handle.version_id, signal), job(handle.job_id, signal), results(handle.version_id, signal)]);
    if (d.job_id !== handle.job_id || j.version_id !== handle.version_id) throw mismatch();
    return { document: d, job: j, results: r };
  }
  return { health, upload, document, job, process, results, snapshot };
}
export function serializeHandle(handle: Handle): string {
  requireId(handle.version_id); requireId(handle.job_id);
  return JSON.stringify({ schema: 1, version_id: handle.version_id, job_id: handle.job_id });
}
export function restoreHandle(raw: string | null): Handle | null {
  if (!raw) return null;
  try {
    const value: unknown = JSON.parse(raw);
    if (!object(value) || Object.keys(value).length !== 3 || value.schema !== 1 ||
        !identifier(value.version_id) || !identifier(value.job_id)) return null;
    return { version_id: value.version_id, job_id: value.job_id };
  } catch { return null; }
}
export function presentResults(result: Results) {
  const state = {
    PENDING: ['Waiting for processing', 'No predictions are available while document processing is pending.'],
    UNSUPPORTED: ['Unsupported document', 'This document could not provide reliably supported text redactions.'],
    NO_REDACTIONS: ['No supported text redactions found', 'Processing found no supported text redactions. No predictions are available.'],
    FAILED: ['Document processing failed', 'A processing failure is not an incorrect prediction. No accuracy can be established.'],
    NEEDS_REVIEW: ['Needs review', 'The document needs review. Predictions and scores are unavailable.'],
    AVAILABLE: ['Document processing complete', result.targets.length ? `${result.targets.length} model attempt${result.targets.length === 1 ? '' : 's'} available. Accuracy remains unknown.` : 'No model prediction attempts are available.'],
  }[result.status];
  return { heading: state[0], detail: state[1], accuracy: 'Accuracy unknown', targetScore: 'Not available',
    documentScore: 'Not available', modelScore: 'Not available', targets: result.targets };
}
