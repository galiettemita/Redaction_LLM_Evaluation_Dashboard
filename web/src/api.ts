/** API v0.3 consumer. Predictions are provenance records, never revealed truth. */
export type Health = { api_version: '0.3'; state: 'READY' | 'DEGRADED'; runtime_qualified: false; mode: 'local' };
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
  request_hash: string; response_hash: string | null; mapping: Mapping | null; evaluation: Evaluation | null };
export type Counts = { requested: number; eligible: number; scored: number; unknown: number; excluded: number; technical_failures: number };
export type Mapping = {mapping_id: string; mapping_version: string; reference_document_version_id: string | null;
  mapping_method_version: string; provenance: 'USER_SUPPLIED_EXPERIMENTAL'; status: string; scoreability: 'SCOREABLE' | 'NOT_SCOREABLE';
  exact_revealed_text: string | null; reference_token_locator: string | null; redacted_canonical_hash: string | null;
  reference_canonical_hash: string | null; explanation: string};
export type Subscores = {normalized_exact_match: boolean; token_precision: number; token_recall: number; token_f1: number;
  ordered_token_agreement: number; character_trigram_f1: number; critical_detail_agreement: number};
export type Evaluation = {evaluation_id: string; schema_version: string; method_id: string; scale: string;
  score_status: 'NONE' | 'EXPERIMENTAL'; experimental_score: number | null; verified_score: null; reason: string | null;
  prediction_hash: string | null; reference_hash: string | null; subscores: Subscores | null; warnings: string[]; applied_caps: number[]};
export type Summary = {summary_id: string; schema_version: string; model_id: string; model_config_id: string; method_id: string; scale: string;
  score_status: 'NONE' | 'EXPERIMENTAL'; experimental_score: number | null; verified_score: null; counts: Counts; denominator: number; member_ids: string[];
  target_id?: string; target_version?: string; document_version_id?: string; document_version_ids?: string[]; document_count?: number};
export type Results = { version_id: string; status: 'PENDING' | 'UNSUPPORTED' | 'NO_REDACTIONS' | 'FAILED' | 'NEEDS_REVIEW' | 'AVAILABLE';
  targets: PredictionTarget[]; summaries: { target: Summary[]; document: Summary[]; model: Summary[] };
  progress: {total: number; pending: number; running: number; terminal: number}; counts: Counts;
  score_status: 'NONE' | 'EXPERIMENTAL'; verified_score: null; experimental_score: null; truth_status: 'UNKNOWN' };
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
const mismatch = () => new ApiError('CONTRACT_MISMATCH', 'The local service response does not match API contract v0.3.');
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
  if (!['http:', 'https:'].includes(url.protocol) ||
      (globalThis.location ? url.origin !== globalThis.location.origin : url.hostname !== '127.0.0.1') ||
      (url.hostname !== '127.0.0.1' && url.protocol !== 'https:') ||
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
    if (response.headers.get('X-Redaction-Lab-API') !== '0.3' ||
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
    return checked(value, object(value) && value.api_version === '0.3' && typeof value.state === 'string' && ['READY', 'DEGRADED'].includes(value.state) &&
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
    return checked(value, validResults(value, versionId));
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
    AVAILABLE: ['Document processing complete', result.targets.length ? `${result.targets.length} model attempt${result.targets.length === 1 ? '' : 's'} available. Verified accuracy remains unknown. Experimental agreement is shown separately when available.` : 'No model prediction attempts are available.'],
  }[result.status];
  return { heading: state[0], detail: state[1], accuracy: 'Accuracy unknown', targetScore: 'Not available',
    documentScore: 'Not available', modelScore: 'Not available', targets: result.targets };
}

export const EXPERIMENTAL_LABEL = 'EXPERIMENTAL — NOT SCIENTIFICALLY VALIDATED';
const METHOD = 'experimental-text-agreement-v1';
const SCALE = '0–100 text agreement';
const integer = (x: unknown): x is number => typeof x === 'number' && Number.isSafeInteger(x) && x >= 0;
const unit = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x) && x >= 0 && x <= 1;
const score = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x) && x >= 0 && x <= 100;
const ids = (x: unknown): x is string[] => Array.isArray(x) && x.every(identifier) && new Set(x).size === x.length;
const nullableHash = (x: unknown) => x === null || digest(x);
function validCounts(x: unknown): x is Counts {
  return object(x) && ['requested', 'eligible', 'scored', 'unknown', 'excluded', 'technical_failures'].every(k => integer(x[k])) &&
    x.requested === (x.eligible as number) + (x.unknown as number) && (x.scored as number) <= (x.eligible as number) &&
    (x.technical_failures as number) <= (x.requested as number) - (x.scored as number);
}
function validMapping(x: unknown, row: PredictionTarget, version: string): x is Mapping | null {
  if (x === null) return true;
  if (!object(x) || !identifier(x.mapping_id) || !boundedText(x.mapping_version) ||
      !boundedText(x.mapping_method_version) || x.provenance !== 'USER_SUPPLIED_EXPERIMENTAL' ||
      !boundedText(x.explanation, 4096) || !nullableHash(x.redacted_canonical_hash) || !nullableHash(x.reference_canonical_hash) ||
      !(x.reference_document_version_id === null || identifier(x.reference_document_version_id)) ||
      !(x.reference_token_locator === null || boundedText(x.reference_token_locator)) ||
      ('target_id' in x && x.target_id !== row.target_id) || ('target_version' in x && x.target_version !== row.target_version) ||
      ('redacted_document_version_id' in x && x.redacted_document_version_id !== version)) return false;
  if (x.status === 'CONFIRMED') return x.scoreability === 'SCOREABLE' && boundedText(x.exact_revealed_text, 32768) &&
    identifier(x.reference_document_version_id) && boundedText(x.reference_token_locator) && digest(x.redacted_canonical_hash) && digest(x.reference_canonical_hash);
  return typeof x.status === 'string' && ['ABSENT', 'PARTIAL', 'AMBIGUOUS', 'UNREADABLE', 'CONFLICTING'].includes(x.status) &&
    x.scoreability === 'NOT_SCOREABLE' && x.exact_revealed_text === null;
}
function validEvaluation(x: unknown, row: PredictionTarget): x is Evaluation | null {
  if (x === null) return true;
  if (!object(x) || !Object.keys(x).every(key => ['evaluation_id', 'schema_version', 'method_id', 'scale', 'score_status', 'experimental_score', 'verified_score', 'reason', 'prediction_hash', 'reference_hash', 'subscores', 'warnings', 'applied_caps'].includes(key)) ||
      !identifier(x.evaluation_id) || x.schema_version !== 'experimental-text-agreement-evidence-v1' ||
      x.method_id !== METHOD || x.scale !== SCALE || x.verified_score !== null || !nullableHash(x.prediction_hash) || !nullableHash(x.reference_hash) ||
      !Array.isArray(x.warnings) || !x.warnings.every(w => boundedText(w, 1024)) || !Array.isArray(x.applied_caps) ||
      !x.applied_caps.every(c => c === 35 || c === 60) || new Set(x.applied_caps).size !== x.applied_caps.length) return false;
  if (x.experimental_score === null) return x.score_status === 'NONE' && x.subscores === null && boundedText(x.reason) && x.warnings.length === 0 && x.applied_caps.length === 0;
  return x.score_status === 'EXPERIMENTAL' && score(x.experimental_score) && x.reason === null &&
    row.attempt_status === 'SUCCEEDED' && row.mapping?.scoreability === 'SCOREABLE' &&
    digest(x.prediction_hash) && digest(x.reference_hash) && object(x.subscores) &&
    typeof x.subscores.normalized_exact_match === 'boolean' &&
    ['token_precision', 'token_recall', 'token_f1', 'ordered_token_agreement', 'character_trigram_f1', 'critical_detail_agreement'].every(k => unit((x.subscores as Record<string, unknown>)[k])) &&
    x.applied_caps.every(cap => (x.experimental_score as number) <= cap);
}
function validSummary(x: unknown, level: 'target' | 'document' | 'model', version: string): x is Summary {
  if (!object(x) || !identifier(x.summary_id) || x.schema_version !== 'experimental-summary-v1' ||
      !boundedText(x.model_id) || !boundedText(x.model_config_id) || x.method_id !== METHOD || x.scale !== SCALE ||
      x.verified_score !== null || !validCounts(x.counts) || !integer(x.denominator) || !ids(x.member_ids)) return false;
  if (x.denominator === 0 ? x.experimental_score !== null || x.score_status !== 'NONE' : !score(x.experimental_score) || x.score_status !== 'EXPERIMENTAL') return false;
  if (level === 'model') return ids(x.document_version_ids) && x.document_version_ids.length === 1 && x.document_version_ids[0] === version &&
    x.document_count === x.document_version_ids.length && x.denominator <= x.document_count && x.member_ids.length === x.document_count;
  return x.denominator === x.counts.scored && x.member_ids.length === x.counts.requested &&
    (level === 'target' ? identifier(x.target_id) && identifier(x.target_version) && x.counts.requested === 1 : x.document_version_id === version);
}
function validResults(x: unknown, version: string): x is Results {
  if (!object(x) || x.version_id !== version || typeof x.status !== 'string' || !resultStates.includes(x.status) ||
      x.verified_score !== null || x.experimental_score !== null || x.truth_status !== 'UNKNOWN' || !validCounts(x.counts) ||
      !object(x.progress) || !['total', 'pending', 'running', 'terminal'].every(k => integer((x.progress as Record<string, unknown>)[k])) ||
      x.progress.total !== x.counts.requested || x.progress.total !== (x.progress.pending as number) + (x.progress.running as number) + (x.progress.terminal as number) ||
      !Array.isArray(x.targets) || !x.targets.every(predictionTarget) || !object(x.summaries)) return false;
  const rows = x.targets;
  if (rows.length !== x.progress.terminal || new Set(rows.map(r => r.attempt_id)).size !== rows.length ||
      new Set(rows.map(r => JSON.stringify([r.target_id, r.target_version, r.model_id, r.model_config_id]))).size !== rows.length ||
      !rows.every(r => validMapping(r.mapping, r, version) && validEvaluation(r.evaluation, r))) return false;
  const locators = new Map<string, PredictionTarget>();
  for (const row of rows) {
    const key = JSON.stringify([row.target_id, row.target_version]);
    const prior = locators.get(key);
    if (prior && (prior.page_index !== row.page_index || prior.normalized_bbox.some((coordinate, index) => coordinate !== row.normalized_bbox[index]))) return false;
    locators.set(key, row);
  }
  const evaluations = rows.filter(r => r.evaluation !== null);
  if (new Set(evaluations.map(r => r.evaluation!.evaluation_id)).size !== evaluations.length ||
      rows.filter(r => r.mapping?.scoreability === 'SCOREABLE').length !== x.counts.eligible ||
      rows.filter(r => r.evaluation?.experimental_score != null).length !== x.counts.scored ||
      rows.filter(r => r.attempt_status !== 'SUCCEEDED').length !== x.counts.technical_failures ||
      x.score_status !== (x.counts.scored ? 'EXPERIMENTAL' : 'NONE')) return false;
  for (const level of ['target', 'document', 'model'] as const) {
    const list = x.summaries[level];
    if (!Array.isArray(list) || !list.every(s => validSummary(s, level, version))) return false;
  }
  const summaries = x.summaries as Results['summaries'];
  const all = [...summaries.target, ...summaries.document, ...summaries.model];
  if (new Set(all.map(s => s.summary_id)).size !== all.length) return false;
  const byEvaluation = new Map(evaluations.map(row => [row.evaluation!.evaluation_id, row]));
  // Before evaluation, member_ids contain opaque intent IDs. A single-cell
  // target summary supplies the exact target/model binding absent from that ID.
  // Never assume an unknown member is pending: it can be an IN_DOUBT attempt.
  const unresolved = new Map<string, {row: PredictionTarget | null; model_id: string; model_config_id: string}>();
  const summarizedCells = new Set<string>();
  let pendingMembers = 0;
  for (const summary of summaries.target) {
    const member = summary.member_ids[0];
    const key = JSON.stringify([summary.target_id, summary.target_version, summary.model_id, summary.model_config_id]);
    if (summarizedCells.has(key)) return false;
    summarizedCells.add(key);
    const row = rows.find(r => r.target_id === summary.target_id && r.target_version === summary.target_version &&
      r.model_id === summary.model_id && r.model_config_id === summary.model_config_id) ?? null;
    if (byEvaluation.has(member)) {
      if (byEvaluation.get(member) !== row) return false;
    } else {
      if (unresolved.has(member) || row?.evaluation) return false;
      unresolved.set(member, {row, model_id: summary.model_id, model_config_id: summary.model_config_id});
      if (!row) pendingMembers++;
    }
  }
  if (pendingMembers > (x.progress.pending as number) + (x.progress.running as number)) return false;
  for (const level of ['target', 'document', 'model'] as const) for (const summary of summaries[level]) {
    if (level === 'model') {
      const documents = summaries.document.filter(d => summary.member_ids.includes(d.summary_id));
      if (documents.some(d => d.model_id !== summary.model_id || d.model_config_id !== summary.model_config_id) ||
          documents.length !== summary.member_ids.length || documents.filter(d => d.experimental_score !== null).length !== summary.denominator) return false;
      for (const key of ['requested', 'eligible', 'scored', 'unknown', 'technical_failures'] as const) if (documents.reduce((sum, d) => sum + d.counts[key], 0) !== summary.counts[key]) return false;
    } else {
      const cells: (PredictionTarget | null)[] = [];
      for (const member of summary.member_ids) {
        const evaluated = byEvaluation.get(member);
        const pending = unresolved.get(member);
        const identity = evaluated ?? pending;
        if (!identity || identity.model_id !== summary.model_id || identity.model_config_id !== summary.model_config_id) return false;
        cells.push(evaluated ?? pending!.row);
      }
      const terminal = cells.filter((cell): cell is PredictionTarget => cell !== null);
      if (level === 'target' && terminal.some(r => r.target_id !== summary.target_id || r.target_version !== summary.target_version)) return false;
      const eligible = terminal.filter(r => r.mapping?.scoreability === 'SCOREABLE').length;
      if (terminal.filter(r => r.evaluation?.experimental_score != null).length !== summary.counts.scored ||
          eligible !== summary.counts.eligible || cells.length - eligible !== summary.counts.unknown ||
          terminal.filter(r => r.attempt_status !== 'SUCCEEDED').length !== summary.counts.technical_failures) return false;
    }
  }
  return true;
}

/** Owns only URLs for explicitly selected browser files. Dispose is used by React cleanup. */
export function createPdfPreview() {
  let current: string | null = null;
  function dispose() { if (current) URL.revokeObjectURL(current); current = null; }
  return { select(file: File | null) { dispose(); if (file) { validatePdf(file); current = URL.createObjectURL(file); } return current; }, dispose };
}
export type WorkspaceState = { release: 'redacted' | 'reference'; selected: string | null; actionError: string; readError: string };
export type WorkspaceAction = {type: 'release'; release: WorkspaceState['release']; available: boolean} |
  {type: 'select'; selected: string | null} | {type: 'action-error' | 'read-error'; message: string} | {type: 'refreshed'};
export function workspaceTransition(state: WorkspaceState, action: WorkspaceAction): WorkspaceState {
  if (action.type === 'release') return action.available ? {...state, release: action.release} : state;
  if (action.type === 'select') return {...state, selected: action.selected};
  if (action.type === 'action-error') return {...state, actionError: action.message};
  if (action.type === 'read-error') return {...state, readError: action.message};
  return {...state, readError: ''};
}
export function keyboardTarget(ids: string[], current: string, key: string): string | null {
  if (!ids.length) return null;
  const index = Math.max(0, ids.indexOf(current));
  if (key === 'Home') return ids[0];
  if (key === 'End') return ids[ids.length - 1];
  if (key === 'ArrowDown') return ids[Math.min(ids.length - 1, index + 1)];
  if (key === 'ArrowUp') return ids[Math.max(0, index - 1)];
  return null;
}
export function attemptCopy(status: AttemptStatus): string {
  return {SUCCEEDED: 'Prediction received', REFUSED: 'The model declined to answer.', TIMEOUT: 'The model reached its time limit.',
    MALFORMED: 'The model returned an unsupported answer format.', ERROR: 'A model service error prevented an answer.',
    IN_DOUBT: 'The outcome is uncertain. This attempt will not be retried automatically.'}[status];
}
export function scoreCopy(value: number | null): string { return value === null ? 'Accuracy unknown' : `${value.toFixed(1)} / 100`; }
