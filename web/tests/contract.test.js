import test from 'node:test';
import assert from 'node:assert/strict';

// Exercise the real TypeScript adapter with a controlled transport. No HTTP server,
// PDF processing, model, installed React, or third-party test runner is needed.
let api;
try { api = await import('../src/api.ts'); } catch (error) {
  if (error.code !== 'ERR_MODULE_NOT_FOUND') throw error;
}
const health = { api_version: '0.3', state: 'DEGRADED', runtime_qualified: false, mode: 'local' };
const upload = { pair_id: 'pair-1', project_id: 'project-1', redacted: {
  version_id: 'version-1', job_id: 'job-1', sha256: 'a'.repeat(64), byte_size: 9, status: 'ACCEPTED'
}, reference: null, truth_status: 'UNKNOWN' };
const document = { version_id: 'version-1', role: 'REDACTED', sha256: 'a'.repeat(64), byte_size: 9,
  processing_status: 'ACCEPTED', page_count: null, job_id: 'job-1', reason_code: null, source_id: null };
const job = { job_id: 'job-1', version_id: 'version-1', status: 'ACCEPTED', reason_code: null, source_id: null };
const result = { version_id: 'version-1', status: 'PENDING', targets: [],
  summaries: { target: [], document: [], model: [] }, progress: {total: 0, pending: 0, running: 0, terminal: 0}, counts: {requested: 0, eligible: 0, scored: 0, unknown: 0, excluded: 0, technical_failures: 0}, score_status: 'NONE',
  verified_score: null, experimental_score: null, truth_status: 'UNKNOWN' };
const pdf = () => new File(['%PDF-test'], 'synthetic.pdf', { type: 'application/pdf' });
function response(body, status = 200, version = '0.3') {
  return new Response(JSON.stringify(body), { status, headers: {
    'Content-Type': 'application/json', 'X-Redaction-Lab-API': version
  } });
}
function client(transport) {
  assert.ok(api, 'Frontend API implementation is missing');
  return api.createApi('http://127.0.0.1:8765', transport);
}
test('accepts the local v0.3 health shape without upgrading runtime readiness', async () => {
  assert.deepEqual(await client(async () => response(health)).health(), health);
});
test('rejects non-string health state instead of coercing JSON arrays into readiness', async () => {
  for (const state of [['READY'], ['DEGRADED'], null, 1, true, { state: 'READY' }]) {
    await assert.rejects(() => client(async () => response({ ...health, state })).health(), /contract/i);
  }
});
test('uploads only exact multipart fields to a relative same-origin route', async () => {
  const calls = [];
  const accepted = await client(async (path, options) => {
    calls.push([path, options]); return response(upload, 201);
  }).upload('project-1', pdf(), null);
  assert.equal(accepted.truth_status, 'UNKNOWN');
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], '/api/v1/documents');
  assert.equal(calls[0][1].method, 'POST');
  assert.deepEqual([...calls[0][1].body.keys()], ['project_id', 'redacted_pdf']);
  assert.equal(calls[0][1].headers['Content-Type'], undefined);
  assert.equal(calls[0][1].redirect, 'error');
});
test('optional reference is sent only as the documented upload part', async () => {
  let form;
  await client(async (_, options) => { form = options.body; return response({ ...upload,
    reference: { version_id: 'ref-1', sha256: 'b'.repeat(64), byte_size: 9 } }, 201);
  }).upload('project-1', pdf(), pdf());
  assert.deepEqual([...form.keys()], ['project_id', 'redacted_pdf', 'reference_pdf']);
});
test('rejects external, localhost, file and credential-bearing origins before transport', () => {
  assert.ok(api, 'Frontend API implementation is missing');
  for (const origin of ['https://example.org', 'http://localhost:8765', 'file:///tmp/app',
    'http://user@127.0.0.1:8765', 'http://127.0.0.1:8765/other']) {
    assert.throws(() => api.createApi(origin, () => { throw new Error('must not call'); }));
  }
});
test('rejects missing, empty, non-PDF and oversized uploads before transport', async () => {
  let calls = 0;
  const local = client(async () => { calls++; return response(upload, 201); });
  for (const file of [null, new File([], 'empty.pdf', { type: 'application/pdf' }),
    new File(['x'], 'image.png', { type: 'image/png' }),
    new File(['x'], 'wrong.pdf', { type: 'text/html' }),
    new File([new Uint8Array(25 * 1024 * 1024 + 1)], 'large.pdf', { type: 'application/pdf' })]) {
    await assert.rejects(() => local.upload('project-1', file, null), /PDF|required|empty|25 MiB/);
  }
  await assert.rejects(() => local.upload('', pdf(), null), /project/i);
  assert.equal(calls, 0);
});
test('accepts PDF filename fallback when the browser omits its MIME type', async () => {
  const file = new File(['%PDF-test'], 'test.PDF');
  await client(async () => response(upload, 201)).upload('project-1', file, null);
});
test('refresh and reconnect read stored state using GET without creating work', async () => {
  const calls = [];
  const local = client(async (path, options) => {
    calls.push([path, options.method]);
    return response(path.includes('/documents/') ? document : path.includes('/jobs/') ? job : result);
  });
  const snapshot = await local.snapshot({ version_id: 'version-1', job_id: 'job-1' });
  assert.deepEqual(snapshot, { document, job, results: result });
  assert.deepEqual(calls.sort(), [
    ['/api/v1/documents/version-1', 'GET'], ['/api/v1/jobs/job-1', 'GET'], ['/api/v1/results/version-1', 'GET']
  ]);
});
test('rejects mismatched response identities rather than displaying another document', async () => {
  const local = client(async path => response(path.includes('/documents/') ? document :
    path.includes('/jobs/') ? { ...job, version_id: 'other' } : result));
  await assert.rejects(() => local.snapshot({ version_id: 'version-1', job_id: 'job-1' }), /contract/i);
});
test('explicit process uses body-free POST and preserves unverified acceptance', async () => {
  let calls = 0;
  const local = client(async (path, options) => {
    calls++; assert.equal(path, '/api/v1/jobs/job-1/process');
    assert.equal(options.method, 'POST'); assert.equal(options.body, undefined);
    return response({ error: { code: 'RUNTIME_UNVERIFIED', message: 'private /path/not-for-ui' },
      job_id: 'job-1', status: 'ACCEPTED' }, 503);
  });
  await assert.rejects(() => local.process('job-1'), error => {
    assert.equal(error.code, 'RUNTIME_UNVERIFIED');
    assert.equal(error.status, 503);
    assert.match(error.message, /not qualified/);
    assert.doesNotMatch(error.message, /private|\/path/); return true;
  });
  assert.equal(calls, 1);
});
test('accepts the documented process receipt without inventing a version_id field', async () => {
  const receipt = { job_id: 'job-1', status: 'READY', reason_code: null, source_id: 'source-1' };
  assert.deepEqual(await client(async () => response(receipt)).process('job-1'), receipt);
});
test('never retries a failed write or reveals raw transport errors', async () => {
  let calls = 0;
  const local = client(async () => { calls++; throw new Error('secret path'); });
  await assert.rejects(() => local.upload('project-1', pdf(), null), error => {
    assert.equal(error.code, 'CONNECTION_FAILED'); assert.doesNotMatch(error.message, /secret/); return true;
  });
  assert.equal(calls, 1);
});
test('rejects missing or incompatible contract headers and malformed JSON', async () => {
  for (const transport of [async () => response(health, 200, '0.1'),
    async () => new Response('broken', { headers: { 'X-Redaction-Lab-API': '0.3', 'Content-Type': 'application/json' } }),
    async () => new Response(JSON.stringify(health), { headers: { 'Content-Type': 'text/html' } })]) {
    await assert.rejects(() => client(transport).health(), /contract/i);
  }
});
test('renders every result state with null scores and no invented predictions', () => {
  assert.ok(api, 'Frontend API implementation is missing');
  const labels = { PENDING: 'Waiting for processing', UNSUPPORTED: 'Unsupported document',
    NO_REDACTIONS: 'No supported text redactions found', FAILED: 'Document processing failed',
    NEEDS_REVIEW: 'Needs review', AVAILABLE: 'Document processing complete' };
  for (const [status, heading] of Object.entries(labels)) {
    const view = api.presentResults({ ...result, status });
    assert.equal(view.heading, heading);
    assert.equal(view.accuracy, 'Accuracy unknown');
    assert.equal(view.targetScore, 'Not available');
    assert.equal(view.documentScore, 'Not available');
    assert.equal(view.modelScore, 'Not available');
    assert.match(view.detail, /prediction|processing|text redactions|review|supported/i);
  }
});
test('rejects numeric scores, fabricated targets and promoted reference truth', async () => {
  for (const change of [{ verified_score: 0 }, { experimental_score: 87 },
    { truth_status: 'CONFIRMED' }, { targets: [{ target_id: 'fake' }] },
    { summaries: { target: null, document: { score: 100 }, model: null } }]) {
    const local = client(async () => response({ ...result, ...change }));
    await assert.rejects(() => local.results('version-1'), /contract/i);
  }
});
test('accepts exact v0.3 model-attempt provenance while preserving null scores', async () => {
  const target = { target_id: 'target-1', target_version: 'target-v1', page_index: 0,
    normalized_bbox: [0.1, 0.3, 0.3, 0.4], attempt_id: 'attempt-1', attempt_status: 'SUCCEEDED',
    prediction: '<script>inert prediction text</script>', model_id: 'model-1', provider_model_id: 'model-1',
    model_config_id: 'config-1', request_hash: 'b'.repeat(64), response_hash: 'c'.repeat(64), mapping: null, evaluation: null };
  const value = { ...result, status: 'AVAILABLE', targets: [target], progress: {total: 1, pending: 0, running: 0, terminal: 1}, counts: {requested: 1, eligible: 0, scored: 0, unknown: 1, excluded: 0, technical_failures: 0} };
  const received = await client(async () => response(value)).results('version-1');
  assert.deepEqual(received.targets, [target]);
  const view = api.presentResults(received);
  assert.deepEqual(view.targets, [target]);
  assert.equal(view.targetScore, 'Not available');
});
test('rejects non-string result status instead of coercing JSON arrays into completion', async () => {
  for (const status of [['AVAILABLE'], ['PENDING'], null, 1, true, { status: 'AVAILABLE' }]) {
    await assert.rejects(() => client(async () => response({ ...result, status })).results('version-1'), /contract/i);
  }
});
test('rejects malformed document metadata and unsupported processing states', async () => {
  for (const change of [{ byte_size: -1 }, { page_count: 101 }, { role: 'REFERENCE' },
    { processing_status: 'PREDICTED' }, { sha256: 'incorrect' }]) {
    await assert.rejects(() => client(async () => response({ ...document, ...change })).document('version-1'), /contract/i);
  }
});
test('recovers only versioned opaque handles, with no stored file content or implicit work', () => {
  assert.ok(api, 'Frontend API implementation is missing');
  const handle = { version_id: 'version-1', job_id: 'job-1' };
  assert.deepEqual(api.restoreHandle(api.serializeHandle(handle)), handle);
  for (const raw of ['bad json', '{"schema":2}', '{"schema":1,"version_id":"../../secret","job_id":"job-1"}',
    '{"schema":1,"version_id":"v","job_id":"j","reference_text":"secret"}']) {
    assert.equal(api.restoreHandle(raw), null);
  }
});
test('status refresh does not accept unsafe IDs or replay POST', async () => {
  let calls = 0;
  const local = client(async () => { calls++; return response(document); });
  await assert.rejects(() => local.document('../unsafe'), /identifier/i);
  assert.equal(calls, 0);
});

// Hand-derived single scored cell: every agreement component is exactly one.
function scoredResult() {
  const counts = {requested: 1, eligible: 1, scored: 1, unknown: 0, excluded: 0, technical_failures: 0};
  const evaluation = {evaluation_id: 'eval-1', schema_version: 'experimental-text-agreement-evidence-v1',
    method_id: 'experimental-text-agreement-v1', scale: '0–100 text agreement', score_status: 'EXPERIMENTAL',
    experimental_score: 100, verified_score: null, reason: null, prediction_hash: 'a'.repeat(64), reference_hash: 'b'.repeat(64),
    subscores: {normalized_exact_match: true, token_precision: 1, token_recall: 1, token_f1: 1, ordered_token_agreement: 1, character_trigram_f1: 1, critical_detail_agreement: 1}, warnings: [], applied_caps: []};
  const mapping = {mapping_id: 'mapping-1', mapping_version: 'mapping-v1', reference_document_version_id: 'ref-1',
    mapping_method_version: 'text-first-experimental-reference-v1', provenance: 'USER_SUPPLIED_EXPERIMENTAL',
    status: 'CONFIRMED', scoreability: 'SCOREABLE', exact_revealed_text: 'twelve aircraft', reference_token_locator: 'tokens:4:6',
    redacted_canonical_hash: 'c'.repeat(64), reference_canonical_hash: 'd'.repeat(64), explanation: 'Unique complete span supported by both surrounding anchors.'};
  const row = {target_id: 'target-1', target_version: 'target-v1', page_index: 0, normalized_bbox: [0.1, 0.2, 0.3, 0.4],
    attempt_id: 'attempt-1', attempt_status: 'SUCCEEDED', prediction: 'twelve aircraft', model_id: 'qwen2.5:1.5b',
    provider_model_id: 'qwen2.5:1.5b', model_config_id: 'config-1', request_hash: 'a'.repeat(64), response_hash: 'b'.repeat(64), mapping, evaluation};
  const common = {summary_id: 'summary-target', schema_version: 'experimental-summary-v1', model_id: row.model_id,
    model_config_id: row.model_config_id, method_id: evaluation.method_id, scale: evaluation.scale, score_status: 'EXPERIMENTAL',
    experimental_score: 100, verified_score: null, counts, denominator: 1, member_ids: ['eval-1']};
  return {...result, status: 'AVAILABLE', targets: [row], score_status: 'EXPERIMENTAL', counts,
    progress: {total: 1, pending: 0, running: 0, terminal: 1}, summaries: {
      target: [{...common, target_id: 'target-1', target_version: 'target-v1'}],
      document: [{...common, summary_id: 'summary-doc', document_version_id: 'version-1'}],
      model: [{...common, summary_id: 'summary-model', member_ids: ['summary-doc'], document_version_ids: ['version-1'], document_count: 1}]}};
}
test('accepts numeric experimental evidence at all three levels with verified null', async () => {
  const value = scoredResult();
  assert.deepEqual(await client(async () => response(value)).results('version-1'), value);
});
test('multiple models may share target identity but never attempt or comparison-cell identity', async () => {
  const value = scoredResult(); value.summaries = {target: [], document: [], model: []};
  value.targets.push({...structuredClone(value.targets[0]), attempt_id: 'attempt-2', model_id: 'model-2', provider_model_id: 'model-2', model_config_id: 'config-2', evaluation: {...value.targets[0].evaluation, evaluation_id: 'eval-2'}});
  value.counts = {requested: 2, eligible: 2, scored: 2, unknown: 0, excluded: 0, technical_failures: 0}; value.progress = {total: 2, pending: 0, running: 0, terminal: 2};
  assert.equal((await client(async () => response(value)).results('version-1')).targets.length, 2);
  for (const change of [{attempt_id: 'attempt-1'}, {model_id: 'qwen2.5:1.5b', provider_model_id: 'qwen2.5:1.5b', model_config_id: 'config-1'}]) {
    const bad = structuredClone(value); Object.assign(bad.targets[1], change);
    await assert.rejects(() => client(async () => response(bad)).results('version-1'), /contract/i);
  }
});
test('fails closed on invalid experimental evidence, counts, progress and grouped membership', async () => {
  const mutations = [
    v => v.targets[0].evaluation.verified_score = 0,
    v => delete v.targets[0].evaluation.method_id,
    v => delete v.targets[0].evaluation.scale,
    v => delete v.targets[0].mapping.provenance,
    v => v.targets[0].evaluation.subscores.token_f1 = 1.1,
    v => v.targets[0].evaluation.experimental_score = 101,
    v => v.targets[0].mapping.exact_revealed_text = null,
    v => v.targets[0].mapping.target_id = 'another-target',
    v => v.targets[0].evaluation.reason = 'PARTIAL_REFERENCE',
    v => v.targets[0].mapping.status = 'PARTIAL',
    v => v.targets[0].evaluation.applied_caps = [60],
    v => v.counts.scored = 0,
    v => v.counts.eligible = 0,
    v => v.counts.technical_failures = 1,
    v => v.progress.terminal = 0,
    v => v.summaries.document[0].model_id = 'other-model',
    v => v.summaries.target[0].target_version = 'other-version',
    v => v.summaries.document[0].member_ids = ['missing-evaluation'],
    v => v.summaries.document[0].counts.scored = 0,
    v => v.summaries.model[0].document_count = 2,
    v => v.summaries.model[0].verified_score = 100,
    v => v.summaries.model[0].denominator = 0,
  ];
  for (const mutate of mutations) {
    const value = scoredResult(); mutate(value);
    await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
  }
});
test('zero denominator and failed attempts preserve unknown rather than zero', async () => {
  const value = scoredResult(); const row = value.targets[0];
  row.attempt_status = 'TIMEOUT'; row.prediction = null; row.response_hash = null;
  row.evaluation = {...row.evaluation, score_status: 'NONE', experimental_score: null, reason: 'TIMEOUT', prediction_hash: null, subscores: null};
  value.counts = {requested: 1, eligible: 1, scored: 0, unknown: 0, excluded: 0, technical_failures: 1};
  value.score_status = 'NONE';
  for (const level of Object.values(value.summaries)) for (const summary of level) Object.assign(summary, {score_status: 'NONE', experimental_score: null, denominator: 0, counts: value.counts});
  assert.equal((await client(async () => response(value)).results('version-1')).summaries.model[0].experimental_score, null);
  value.summaries.model[0].experimental_score = 0;
  await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
});
test('HTTPS is permitted only for the current browser origin and still uses relative requests', async () => {
  const previous = globalThis.location;
  globalThis.location = {origin: 'https://controlled.example'};
  try {
    let requested;
    assert.deepEqual(await api.createApi('https://controlled.example', async path => {requested = path; return response(health);}).health(), health);
    assert.equal(requested, '/api/v1/health');
    assert.throws(() => api.createApi('https://other.example'));
    assert.throws(() => api.createApi('http://127.0.0.1:8765'));
  } finally { if (previous === undefined) delete globalThis.location; else globalThis.location = previous; }
});
test('accepts each persisted unknown mapping state and rejects invented states', async () => {
  for (const status of ['ABSENT', 'PARTIAL', 'AMBIGUOUS', 'UNREADABLE', 'CONFLICTING']) {
    const value = scoredResult(); const row = value.targets[0];
    Object.assign(row.mapping, {status, scoreability: 'NOT_SCOREABLE', exact_revealed_text: null, reference_token_locator: null});
    Object.assign(row.evaluation, {score_status: 'NONE', experimental_score: null, subscores: null, reference_hash: null, reason: 'PARTIAL_REFERENCE'});
    value.score_status = 'NONE'; value.counts = {requested: 1, eligible: 0, scored: 0, unknown: 1, excluded: 0, technical_failures: 0};
    value.summaries = {target: [], document: [], model: []};
    assert.equal((await client(async () => response(value)).results('version-1')).targets[0].mapping.exact_revealed_text, null);
    row.mapping.status = 'MADE_UP'; await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
  }
});
test('summary truth and technical counts remain bound to their member attempts', async () => {
  const value = scoredResult(); value.summaries.document[0].counts = {requested: 2, eligible: 1, scored: 1, unknown: 1, excluded: 0, technical_failures: 1};
  await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
});

function technicalResult(status = 'TIMEOUT') {
  const value = scoredResult(); const row = value.targets[0];
  Object.assign(row, {attempt_status: status, prediction: null, response_hash: null});
  Object.assign(row.evaluation, {score_status: 'NONE', experimental_score: null, reason: status, prediction_hash: null, subscores: null});
  value.counts = {requested: 1, eligible: 1, scored: 0, unknown: 0, excluded: 0, technical_failures: 1};
  value.score_status = 'NONE';
  for (const level of Object.values(value.summaries)) for (const summary of level) Object.assign(summary, {score_status: 'NONE', experimental_score: null, denominator: 0, counts: {...value.counts}});
  return value;
}
test('rejects TIMEOUT hidden by mutually consistent zero technical-failure summaries', async () => {
  const value = technicalResult();
  for (const level of Object.values(value.summaries)) for (const summary of level) summary.counts.technical_failures = 0;
  assert.equal(value.counts.technical_failures, 1);
  await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
});
test('validates individual target, document and model failure counts across technical statuses', async () => {
  for (const status of ['REFUSED', 'TIMEOUT', 'MALFORMED', 'ERROR']) {
    const value = technicalResult(status);
    assert.deepEqual(await client(async () => response(value)).results('version-1'), value);
    for (const level of ['target', 'document', 'model']) {
      const bad = structuredClone(value); bad.summaries[level][0].counts.technical_failures = 0;
      await assert.rejects(() => client(async () => response(bad)).results('version-1'), /contract/i);
    }
  }
});
test('mixed scored and timeout members preserve counts and completed-answer denominator', async () => {
  const value = scoredResult(); const failed = technicalResult();
  const row = failed.targets[0]; row.target_id = 'target-2'; row.attempt_id = 'attempt-2'; row.evaluation.evaluation_id = 'eval-2';
  value.targets.push(row);
  const targetSummary = failed.summaries.target[0];
  Object.assign(targetSummary, {summary_id: 'summary-target-2', target_id: 'target-2', member_ids: ['eval-2']});
  value.summaries.target.push(targetSummary);
  value.counts = {requested: 2, eligible: 2, scored: 1, unknown: 0, excluded: 0, technical_failures: 1};
  value.progress = {total: 2, pending: 0, running: 0, terminal: 2};
  value.summaries.document[0].member_ids = ['eval-1', 'eval-2'];
  value.summaries.document[0].counts = {...value.counts}; value.summaries.model[0].counts = {...value.counts};
  assert.equal((await client(async () => response(value)).results('version-1')).summaries.document[0].denominator, 1);
  value.summaries.document[0].counts.technical_failures = 0; value.summaries.model[0].counts.technical_failures = 0;
  await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
});
function unresolvedResult() {
  const value = technicalResult('IN_DOUBT'); const row = value.targets[0];
  row.mapping = null; row.evaluation = null; row.provider_model_id = null;
  value.progress = {total: 2, pending: 1, running: 0, terminal: 1};
  value.counts = {requested: 2, eligible: 0, scored: 0, unknown: 2, excluded: 0, technical_failures: 1};
  const first = value.summaries.target[0]; first.member_ids = ['intent-1']; first.counts = {requested: 1, eligible: 0, scored: 0, unknown: 1, excluded: 0, technical_failures: 1};
  value.summaries.target.push({...structuredClone(first), summary_id: 'summary-pending', target_id: 'target-2', member_ids: ['intent-2'], counts: {...first.counts, technical_failures: 0}});
  value.summaries.document[0].member_ids = ['intent-1', 'intent-2'];
  value.summaries.document[0].counts = {...value.counts}; value.summaries.model[0].counts = {...value.counts};
  return value;
}
test('pending intents and unresolved terminal attempts bind through unique target summaries', async () => {
  const value = unresolvedResult();
  assert.deepEqual(await client(async () => response(value)).results('version-1'), value);
  for (const mutate of [
    v => {for (const level of Object.values(v.summaries)) for (const summary of level) summary.counts.technical_failures = 0;},
    v => v.summaries.target[1].counts.technical_failures = 1,
    v => v.summaries.document[0].member_ids = ['intent-1', 'unbound-intent'],
    v => v.summaries.target[1].member_ids = ['intent-1'],
    v => v.summaries.target[0].target_id = 'missing-target',
  ]) {
    const bad = structuredClone(value); mutate(bad);
    await assert.rejects(() => client(async () => response(bad)).results('version-1'), /contract/i);
  }
});
test('shared immutable target geometry cannot diverge between model attempts', async () => {
  const value = scoredResult(); value.summaries = {target: [], document: [], model: []};
  value.targets.push({...structuredClone(value.targets[0]), attempt_id: 'attempt-2', model_id: 'model-2', provider_model_id: 'model-2', model_config_id: 'config-2', evaluation: {...value.targets[0].evaluation, evaluation_id: 'eval-2'}});
  value.counts = {requested: 2, eligible: 2, scored: 2, unknown: 0, excluded: 0, technical_failures: 0}; value.progress = {total: 2, pending: 0, running: 0, terminal: 2};
  assert.equal((await client(async () => response(value)).results('version-1')).targets.length, 2);
  for (const change of [{page_index: 50}, {normalized_bbox: [.6, .7, .8, .9]}, {page_index: 50, normalized_bbox: [.6, .7, .8, .9]}]) {
    const bad = structuredClone(value); Object.assign(bad.targets[1], change);
    await assert.rejects(() => client(async () => response(bad)).results('version-1'), /contract/i);
  }
});
test('unsupported nested evaluation identity cannot contradict the enclosing immutable row', async () => {
  for (const [key, value] of Object.entries({attempt_id: 'other-attempt', target_id: 'other-target', target_version: 'other-version', model_id: 'other-model', model_config_id: 'other-config', provider_model_id: 'other-provider', mapping_id: 'other-mapping'})) {
    const bad = scoredResult(); bad.targets[0].evaluation[key] = value;
    await assert.rejects(() => client(async () => response(bad)).results('version-1'), /contract/i);
  }
});
test('extra attempt payload fields cannot impersonate an unresolved-member binding', async () => {
  const value = technicalResult(); value.targets[0].row = null;
  for (const level of Object.values(value.summaries)) for (const summary of level) summary.counts = {requested: 1, eligible: 0, scored: 0, unknown: 1, excluded: 0, technical_failures: 0};
  await assert.rejects(() => client(async () => response(value)).results('version-1'), /contract/i);
});
