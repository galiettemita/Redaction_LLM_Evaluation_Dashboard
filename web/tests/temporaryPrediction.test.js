import test from 'node:test';
import assert from 'node:assert/strict';
import { generateTemporaryPredictions } from '../src/temporaryPrediction.ts';

const expectedResult = (markers) => ({
  status: 'TEMPORARY_UNVALIDATED',
  truth_status: 'UNKNOWN',
  score_status: 'NONE',
  verified_score: null,
  experimental_score: null,
  markers,
});

test('matches the exact cross-language cue fixture and generic fallback', () => {
  assert.deepEqual(generateTemporaryPredictions('They met [REDACTED] in [REDACTED] on [REDACTED].'), expectedResult([
    { marker_index: 1, candidates: ['a person', 'an individual', 'someone'],
      basis: 'Nearby person cue; generic heuristic only.' },
    { marker_index: 2, candidates: ['a place', 'a location', 'somewhere'],
      basis: 'Nearby place cue; generic heuristic only.' },
    { marker_index: 3, candidates: ['a time', 'a date', 'a period'],
      basis: 'Nearby time cue; generic heuristic only.' },
  ]));
  assert.deepEqual(generateTemporaryPredictions('The record mentions [REDACTED] nearby.'), expectedResult([
    { marker_index: 1, candidates: ['an unspecified item', 'something', 'an unknown detail'],
      basis: 'No nearby recognized cue; generic fallback only.' },
  ]));
});

test('uses the left cue when equally near left and right cues differ', () => {
  assert.deepEqual(generateTemporaryPredictions('in [REDACTED] met'), expectedResult([
    { marker_index: 1, candidates: ['a place', 'a location', 'somewhere'],
      basis: 'Nearby place cue; generic heuristic only.' },
  ]));
});

test('accepts only the exact case-sensitive literal marker', () => {
  assert.throws(() => generateTemporaryPredictions('The agent emailed [redacted].'), /marker/i);
  assert.equal(generateTemporaryPredictions('The agent emailed [REDACTED].').markers.length, 1);
});

test('requires a nonempty string with one through eight literal markers', () => {
  for (const invalid of ['', 'ordinary text', '[REDACTED] '.repeat(9), null, 12, {}, ['[REDACTED]']]) {
    assert.throws(() => generateTemporaryPredictions(invalid), /input|marker|string/i);
  }
  assert.equal(generateTemporaryPredictions('[REDACTED]').markers.length, 1);
  assert.equal(generateTemporaryPredictions('[REDACTED] '.repeat(8)).markers.length, 8);
});

test('measures the 4000 byte limit as UTF-8 rather than UTF-16 code units', () => {
  assert.equal(generateTemporaryPredictions(`${'x'.repeat(3990)}[REDACTED]`).markers.length, 1);
  assert.throws(() => generateTemporaryPredictions(`${'x'.repeat(3991)}[REDACTED]`), /4000|byte|long/i);
  assert.equal(generateTemporaryPredictions(`${'🙂'.repeat(997)}[REDACTED]`).markers.length, 1);
  assert.throws(() => generateTemporaryPredictions(`${'🙂'.repeat(998)}[REDACTED]`), /4000|byte|long/i);
});

test('rejects NUL, markup and javascript-style payloads', () => {
  for (const hostile of [
    'A\0 [REDACTED]',
    '<script>alert(1)</script> [REDACTED]',
    'ordinary <b>markup</b> [REDACTED]',
    'javascript:alert(1) [REDACTED]',
    'JaVaScRiPt : alert(1) [REDACTED]',
  ]) {
    assert.throws(() => generateTemporaryPredictions(hostile), /input|markup|payload|NUL/i);
  }
});

test('rejects javascript schemes with Unicode case and separator characters', () => {
  for (const hostile of [
    '\u0130javascript:alert(1) [REDACTED]',
    'javascript\uFEFF:alert(1) [REDACTED]',
    'javascript\u0085:alert(1) [REDACTED]',
    'javascript\u001C:alert(1) [REDACTED]',
    'javascript\u001D:alert(1) [REDACTED]',
    'javascript\u001E:alert(1) [REDACTED]',
    'javascript\u001F:alert(1) [REDACTED]',
    'java\u017Fcript:alert(1) [REDACTED]',
  ]) {
    assert.throws(() => generateTemporaryPredictions(hostile), /input|markup|payload/i);
  }
});

test('rejects isolated UTF-16 surrogate halves while accepting valid Unicode pairs', () => {
  for (const hostile of ['\uD800[REDACTED]', '\uDC00[REDACTED]', '[REDACTED]\uD800']) {
    assert.throws(() => generateTemporaryPredictions(hostile), /surrogate|Unicode|input/i);
  }
  assert.equal(generateTemporaryPredictions('🙂[REDACTED]').markers.length, 1);
});

test('numbers multiple markers in order and returns the same result on every call', () => {
  const input = 'They met [REDACTED] in [REDACTED] on [REDACTED].';
  const first = generateTemporaryPredictions(input);
  assert.deepEqual(first, expectedResult([
    { marker_index: 1, candidates: ['a person', 'an individual', 'someone'],
      basis: 'Nearby person cue; generic heuristic only.' },
    { marker_index: 2, candidates: ['a place', 'a location', 'somewhere'],
      basis: 'Nearby place cue; generic heuristic only.' },
    { marker_index: 3, candidates: ['a time', 'a date', 'a period'],
      basis: 'Nearby time cue; generic heuristic only.' },
  ]));
  assert.deepEqual(generateTemporaryPredictions(input), first);
});

test('does not call fetch or access browser storage and never returns score values', () => {
  const originalFetch = Object.getOwnPropertyDescriptor(globalThis, 'fetch');
  const originalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  let fetchCalls = 0;
  let storageReads = 0;
  Object.defineProperty(globalThis, 'fetch', { configurable: true, value: () => { fetchCalls++; throw new Error('unexpected fetch'); } });
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, get() { storageReads++; throw new Error('unexpected storage'); } });
  try {
    assert.deepEqual(generateTemporaryPredictions('The agent emailed [REDACTED].'), expectedResult([
      { marker_index: 1, candidates: ['a person', 'an individual', 'someone'],
        basis: 'Nearby person cue; generic heuristic only.' },
    ]));
    assert.equal(fetchCalls, 0);
    assert.equal(storageReads, 0);
  } finally {
    if (originalFetch) Object.defineProperty(globalThis, 'fetch', originalFetch);
    else delete globalThis.fetch;
    if (originalStorage) Object.defineProperty(globalThis, 'localStorage', originalStorage);
    else delete globalThis.localStorage;
  }
});
