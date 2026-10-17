const assert = require('node:assert/strict');
const { test } = require('node:test');
const { classify } = require('./aishell3_acoustic_baseline.cjs');
const { load } = require('../../benchmark/pronunciation_v2/tone_feedback.cjs');

test('AISHELL bridge executes frozen family inference and ignores annotation fields', () => {
  const row = {
    example_id: 'fixture', start: 0.1, end: 0.4, raw: [],
    segments: [Array.from({ length: 25 }, (_, i) => ({
      timestamp_seconds: 0.11 + i * 0.01, normalized_semitones: 2 - i * 0.18,
    }))], eligibility: { metrics: {} },
  };
  const shape = load('@/speech/pitchShapeEvidence').unitShape(
    { tone_graph: { raw: row.raw } }, { start: row.start, end: row.end, grouped: false }, row.segments);
  const expected = load('@/speech/toneLikeness').classifyToneLikeness(shape, row.segments);
  assert.deepEqual(classify(row).observed, expected);
  assert.deepEqual(classify(row), classify({ ...row, label: 'T3', hanzi: '我', pinyin: 'wo3',
    expected_tone: 3, lexical_tone: 3, corpus_surface_tone: 3, acceptable_families: ['TONE_3'] }));
  assert.equal(classify({ ...row, segments: [] }).prediction, null);
});
