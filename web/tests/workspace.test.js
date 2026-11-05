import test from 'node:test';
import assert from 'node:assert/strict';
import * as api from '../src/api.ts';

test('local PDF preview URL is revoked on replacement, removal, and disposal', async () => {
  assert.equal(typeof api.createPdfPreview, 'function', 'a lifecycle owner for the local preview is missing');
  const preview = api.createPdfPreview();
  const first = preview.select(new File(['%PDF-first'], 'first.pdf', {type: 'application/pdf'}));
  assert.match(first, /^blob:/); assert.equal(await (await fetch(first)).text(), '%PDF-first');
  const second = preview.select(new File(['%PDF-second'], 'second.pdf', {type: 'application/pdf'}));
  await assert.rejects(fetch(first)); assert.equal(await (await fetch(second)).text(), '%PDF-second');
  assert.equal(preview.select(null), null); await assert.rejects(fetch(second));
  const third = preview.select(new File(['%PDF-third'], 'third.pdf', {type: 'application/pdf'}));
  preview.dispose(); await assert.rejects(fetch(third)); preview.dispose();
});
test('release changes preserve target selection and missing reference never switches', () => {
  assert.equal(typeof api.workspaceTransition, 'function', 'workspace transitions missing');
  const state = {release: 'redacted', selected: 'target-2', actionError: 'Previous action failed', readError: ''};
  assert.deepEqual(api.workspaceTransition(state, {type: 'release', release: 'reference', available: false}), state);
  const next = api.workspaceTransition(state, {type: 'release', release: 'reference', available: true});
  assert.equal(next.release, 'reference'); assert.equal(next.selected, 'target-2');
  assert.equal(api.workspaceTransition(next, {type: 'refreshed'}).actionError, 'Previous action failed');
});
test('keyboard navigation selects distinct targets without wrapping or changing model identity', () => {
  assert.equal(typeof api.keyboardTarget, 'function', 'target keyboard navigation missing');
  for (const [key, current, want] of [['ArrowDown','a','b'], ['ArrowUp','b','a'], ['End','a','c'], ['Home','c','a'], ['ArrowDown','c','c'], ['Tab','a',null]]) {
    assert.equal(api.keyboardTarget(['a','b','c'], current, key), want);
  }
});
test('technical failures have separate friendly meanings and cannot become factual scores', () => {
  assert.equal(typeof api.attemptCopy, 'function', 'technical-state presentation missing');
  const expected = {REFUSED: /declined/i, TIMEOUT: /time limit/i, MALFORMED: /format/i, ERROR: /service error/i, IN_DOUBT: /uncertain/i};
  for (const [state, pattern] of Object.entries(expected)) assert.match(api.attemptCopy(state), pattern);
  assert.equal(typeof api.scoreCopy, 'function');
  assert.equal(api.scoreCopy(null), 'Accuracy unknown');
  assert.equal(api.scoreCopy(0), '0.0 / 100');
  assert.equal(api.scoreCopy(81.5), '81.5 / 100');
});

// Render the real React components; TypeScript compilation uses the pinned build tool.
import { transformSync } from 'esbuild';
import { readFile } from 'node:fs/promises';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
async function components() {
  let code = transformSync(await readFile(new URL('../src/App.tsx', import.meta.url), 'utf8'), {loader: 'tsx', jsx: 'automatic', format: 'esm'}).code;
  for (const [name, url] of [['./temporaryPrediction', new URL('../src/temporaryPrediction.ts', import.meta.url).href], ['./api', new URL('../src/api.ts', import.meta.url).href], ['react', import.meta.resolve('react')], ['react/jsx-runtime', import.meta.resolve('react/jsx-runtime')]]) code = code.replaceAll(`from "${name}"`, `from "${url}"`);
  return import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));
}
test('result panels render escaped prediction, method, score channels, counts and separate model summaries', async () => {
  const {ResultsPanel} = await components(); assert.equal(typeof ResultsPanel, 'function', 'document results panel is missing');
  const counts = {requested: 2, eligible: 1, scored: 1, unknown: 1, excluded: 3, technical_failures: 1};
  const evaluation = {experimental_score: 60, verified_score: null, method_id: 'experimental-text-agreement-v1', scale: '0–100 text agreement',
    subscores: {normalized_exact_match: false, token_precision: .8, token_recall: .8, token_f1: .8, ordered_token_agreement: .8, character_trigram_f1: .8, critical_detail_agreement: 0}, warnings: ['Quantity differs'], applied_caps: [60]};
  const summary = {...evaluation, summary_id: 'summary-doc', model_id: 'model-1', model_config_id: 'config-1', counts, denominator: 1};
  const results = {status: 'AVAILABLE', progress: {total: 2, pending: 0, running: 0, terminal: 2}, counts,
    targets: [{target_id: 't1', target_version: 'v1', attempt_id: 'attempt-1', model_id: 'model-1', model_config_id: 'config-1', page_index: 2, normalized_bbox: [.1,.2,.3,.4], attempt_status: 'SUCCEEDED', prediction: '<script>bad()</script>',
      mapping: {scoreability: 'SCOREABLE', exact_revealed_text: 'Exact reference', explanation: 'Unique aligned span'}, evaluation}],
    summaries: {target: [{...summary, summary_id: 'summary-target', target_id: 't1', target_version: 'v1', counts: {requested: 1, eligible: 1, scored: 1, unknown: 0, excluded: 0, technical_failures: 0}}], document: [summary], model: [{...summary, summary_id: 'summary-model', document_count: 1}]}};
  const html = renderToStaticMarkup(createElement(ResultsPanel, {results, selected: 't1:v1', onSelect: () => {}}));
  assert.match(html, /EXPERIMENTAL — NOT SCIENTIFICALLY VALIDATED/);
  assert.match(html, /60.0 \/ 100/); assert.match(html, /Verified accuracy unknown/);
  assert.match(html, /&lt;script&gt;bad\(\)&lt;\/script&gt;/); assert.doesNotMatch(html, /<script>/);
  assert.match(html, /experimental-text-agreement-v1/); assert.match(html, /Quantity differs/);
  for (const label of ['Requested', 'Eligible', 'Scored', 'Unknown', 'Excluded', 'Technical failures', 'Redaction scored-cell denominator', 'Scored-cell denominator', 'Scored-document denominator']) assert.ok(html.includes(label), label);
  assert.match(html, /Page 3/); assert.match(html, /aria-pressed="true"/);
});
test('local PDF frame carries an accessible title and never invents a restored preview or reference page', async () => {
  const {PdfPanel} = await components(); assert.equal(typeof PdfPanel, 'function', 'PDF viewer is missing');
  const missing = renderToStaticMarkup(createElement(PdfPanel, {url: null, release: 'redacted', page: 4}));
  assert.match(missing, /select the PDF again/i); assert.doesNotMatch(missing, /<iframe/);
  const redacted = renderToStaticMarkup(createElement(PdfPanel, {url: 'blob:local-selected', release: 'redacted', page: 4}));
  assert.match(redacted, /title="Redacted PDF preview"/); assert.match(redacted, /#page=4/);
  const reference = renderToStaticMarkup(createElement(PdfPanel, {url: 'blob:local-reference', release: 'reference', page: 4}));
  assert.match(reference, /title="Reference PDF preview"/); assert.doesNotMatch(reference, /#page=4/);
});
test('rendered target buttons wire keyboard selection to focus and retain native click activation', async () => {
  const {ResultsPanel} = await components();
  const chosen = []; const focused = [];
  const row = {target_id: 'a', target_version: 'v1', attempt_id: 'first', page_index: 0};
  const result = {status: 'AVAILABLE', targets: [row, {...row, target_id: 'b', attempt_id: 'second', page_index: 1}],
    progress: {total: 2, pending: 0, running: 0, terminal: 2}, counts: {requested: 2, eligible: 0, scored: 0, unknown: 2, excluded: 0, technical_failures: 0}, summaries: {target: [], document: [], model: []}};
  const tree = ResultsPanel({results: result, selected: 'a:v1', onSelect: key => chosen.push(key)});
  const buttons = [];
  function visit(node) { if (!node || typeof node !== 'object') return; if (node.type === 'button') buttons.push(node); for (const child of [node.props?.children].flat(Infinity)) visit(child); }
  visit(tree); assert.equal(buttons.length, 2);
  let prevented = false;
  buttons[0].props.onKeyDown({key: 'ArrowDown', preventDefault() {prevented = true;}, currentTarget: {parentElement: {querySelectorAll() { return [{focus() {focused.push('a');}}, {focus() {focused.push('b');}}]; }}}});
  assert.equal(prevented, true); assert.deepEqual(chosen, ['b:v1']); assert.deepEqual(focused, ['b']);
  buttons[0].props.onClick(); assert.deepEqual(chosen, ['b:v1', 'a:v1']);
});
