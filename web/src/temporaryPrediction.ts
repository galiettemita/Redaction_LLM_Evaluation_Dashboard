export type TemporaryPredictionMarker = {
  marker_index: number;
  candidates: string[];
  basis: string;
};

export type TemporaryPredictionResult = {
  status: 'TEMPORARY_UNVALIDATED';
  truth_status: 'UNKNOWN';
  score_status: 'NONE';
  verified_score: null;
  experimental_score: null;
  markers: TemporaryPredictionMarker[];
};

const MARKER = '[REDACTED]';
const MAX_UTF8_BYTES = 4000;
const MAX_MARKERS = 8;

const CUES = {
  person: new Set(['met', 'contacted', 'called', 'emailed', 'named', 'agent', 'dr', 'mr', 'ms', 'professor']),
  place: new Set(['in', 'at', 'from', 'near', 'toward', 'inside']),
  time: new Set(['on', 'during', 'before', 'after', 'since', 'until']),
} as const;

const GENERIC_CANDIDATES = {
  person: ['a person', 'an individual', 'someone'],
  place: ['a place', 'a location', 'somewhere'],
  time: ['a time', 'a date', 'a period'],
  fallback: ['an unspecified item', 'something', 'an unknown detail'],
} as const;

const BASIS = {
  person: 'Nearby person cue; generic heuristic only.',
  place: 'Nearby place cue; generic heuristic only.',
  time: 'Nearby time cue; generic heuristic only.',
  fallback: 'No nearby recognized cue; generic fallback only.',
} as const;

function cueForWord(word: string | undefined): keyof typeof CUES | undefined {
  if (!word) return undefined;
  const normalized = word.toLowerCase();
  if (CUES.person.has(normalized)) return 'person';
  if (CUES.place.has(normalized)) return 'place';
  if (CUES.time.has(normalized)) return 'time';
  return undefined;
}

function markerPrediction(text: string, markerOffset: number, markerIndex: number): TemporaryPredictionMarker {
  const before = text.slice(0, markerOffset).match(/[A-Za-z]+/g) ?? [];
  const after = text.slice(markerOffset + MARKER.length).match(/[A-Za-z]+/g) ?? [];
  const leftCue = cueForWord(before.at(-1));
  const rightCue = cueForWord(after[0]);
  const cue = leftCue ?? rightCue;
  const kind = cue ?? 'fallback';
  return {
    marker_index: markerIndex,
    candidates: [...GENERIC_CANDIDATES[kind]],
    basis: BASIS[kind],
  };
}

function hasUnpairedSurrogate(text: string): boolean {
  for (let index = 0; index < text.length; index++) {
    const codeUnit = text.charCodeAt(index);
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const next = text.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return true;
      index++;
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) {
      return true;
    }
  }
  return false;
}

export function generateTemporaryPredictions(text: string): TemporaryPredictionResult {
  if (typeof text !== 'string' || text.length === 0) {
    throw new TypeError('Input must be a nonempty string.');
  }
  if (hasUnpairedSurrogate(text)) {
    throw new TypeError('Input contains an unpaired Unicode surrogate.');
  }
  if (new TextEncoder().encode(text).byteLength > MAX_UTF8_BYTES) {
    throw new RangeError('Input exceeds the 4000 UTF-8 byte limit.');
  }
  if (text.includes('\0')) {
    throw new TypeError('Input contains a NUL character.');
  }
  const normalizedText = text.toLowerCase().replace(/\u017F/g, 's');
  if (/[<>]/.test(text) || /javascript[\s\u001C-\u001F\u0085\uFEFF]*:/.test(normalizedText)) {
    throw new TypeError('Input contains markup or a javascript-style payload.');
  }

  const offsets: number[] = [];
  let offset = text.indexOf(MARKER);
  while (offset !== -1) {
    offsets.push(offset);
    offset = text.indexOf(MARKER, offset + MARKER.length);
  }
  if (offsets.length === 0 || offsets.length > MAX_MARKERS) {
    throw new RangeError('Input must contain between one and eight exact [REDACTED] markers.');
  }

  return {
    status: 'TEMPORARY_UNVALIDATED',
    truth_status: 'UNKNOWN',
    score_status: 'NONE',
    verified_score: null,
    experimental_score: null,
    markers: offsets.map((markerOffset, index) => markerPrediction(text, markerOffset, index + 1)),
  };
}
