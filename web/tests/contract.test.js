import test from 'node:test';
import assert from 'node:assert/strict';

// Exercise the real TypeScript adapter with a controlled transport. No HTTP server,
// PDF processing, model, installed React, or third-party test runner is needed.
let api;
try { api = await import('../src/api.ts'); } catch (error) {
  if (error.code !== 'ERR_MODULE_NOT_FOUND') throw error;
}
const health = { api_version: '0.1', state: 'DEGRADED', runtime_qualified: false, mode: 'local' };
const upload = { pair_id: 'pair-1', project_id: 'project-1', redacted: {
  version_id: 'version-1', job_id: 'job-1', sha256: 'a'.repeat(64), byte_size: 9, status: 'ACCEPTED'
}, reference: null, truth_status: 'UNKNOWN' };
const document = { version_id: 'version-1', role: 'REDACTED', sha256: 'a'.repeat(64), byte_size: 9,
  processing_status: 'ACCEPTED', page_count: null, job_id: 'job-1', reason_code: null, source_id: null };
const job = { job_id: 'job-1', version_id: 'version-1', status: 'ACCEPTED', reason_code: null, source_id: null };
const result = { version_id: 'version-1', status: 'PENDING', targets: [],
  summaries: { target: null, document: null, model: null }, score_status: 'NONE',
  verified_score: null, experimental_score: null, truth_status: 'UNKNOWN' };
const pdf = () => new File(['%PDF-test'], 'synthetic.pdf', { type: 'application/pdf' });
function response(body, status = 200, version = '0.1') {
  return new Response(JSON.stringify(body), { status, headers: {
    'Content-Type': 'application/json', 'X-Redaction-Lab-API': version
  } });
}
function client(transport) {
  assert.ok(api, 'Frontend API implementation is missing');
  return api.createApi('http://127.0.0.1:8765', transport);
}
test('accepts the local v0.1 health shape without upgrading runtime readiness', async () => {
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
  for (const transport of [async () => response(health, 200, '0.2'),
    async () => new Response('broken', { headers: { 'X-Redaction-Lab-API': '0.1', 'Content-Type': 'application/json' } }),
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
