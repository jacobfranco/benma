const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { evaluate } = require('./evaluate.cjs');
const input = fs.readFileSync(`${__dirname}/stage0.dataset.jsonl`, 'utf8').trim().split('\n').map(JSON.parse);
const clone = x => JSON.parse(JSON.stringify(x));
const baseline = '0'.repeat(64);
test('63-unit export matches the saved historical and physical grades without modifying inputs', () => {
  const before = JSON.stringify(input), rows = evaluate(input, baseline);
  assert.equal(JSON.stringify(input), before);
  assert.equal(rows.length, 63);
  const audit = JSON.parse(fs.readFileSync(`${__dirname}/../../docs/research/pronunciation-v2/2026-10-13-conservative-grading/results.json`));
  for (const row of rows) {
    const old = row.source.kind === 'historical_row'
      ? audit.historical.find(r => r.id === row.source.row_id)
      : audit.newest.find(r => r.id === row.source.analysis_id).units.find(r => r.id.endsWith(`:${row.target.syllable}`));
    assert.deepEqual(row.deterministic.learner_grade, old.grade);
    assert.deepEqual(row.deterministic.family_scores, old.fits);
    assert.equal(row.deterministic.observed_family, old.observedFamily);
  }
  assert.equal(rows.at(-1).deterministic.chunk.color, 'green');
  assert.equal(rows.at(-1).deterministic.color, 'gray');
});
test('rejects wrong source, target ownership, lexical expectation and duplicate IDs', () => {
  for (const alter of [r => { r.source.sha256 = '0'.repeat(64); },
    r => { r.target.start_seconds += .01; }, r => { r.target.syllable_index = 999; },
    r => { r.expected.lexical_tone = 1; }, r => { r.expected.acceptable_families = ['TONE_4']; }]) {
    const row = clone(input[0]); alter(row);
    assert.throws(() => evaluate([row], baseline));
  }
  assert.throws(() => evaluate([input[0], input[0]], baseline), /Duplicate example_id/);
});
test('preserves conflicting raw listener labels; rejects unknown speakers and speaker leakage in training splits', () => {
  const a = clone(input[0]), b = clone(input[1]);
  for (const row of [a, b]) {
    row.speaker_id = 'pilot-speaker'; row.partition = 'train';
    row.annotations = [
      { annotator_id: 'listener-a', acceptability: 'acceptable', perceived_tone: null, notes: null },
      { annotator_id: 'listener-b', acceptability: 'borderline', perceived_tone: 'T4', notes: null },
    ];
    row.disagreement = { status: 'disputed', counts: { acceptable: 1, borderline: 1, incorrect: 0, ungradable: 0 },
      adjudicated_label: null, adjudicator_id: null, notes: null };
  }
  assert.deepEqual(evaluate([a], baseline)[0].annotations, a.annotations);
  b.partition = 'test';
  assert.throws(() => evaluate([a, b], baseline), /Speaker leakage/);
  a.speaker_id = null;
  assert.throws(() => evaluate([a], baseline));
  a.speaker_id = 'pilot-speaker'; a.disagreement.counts.acceptable = 0;
  assert.throws(() => evaluate([a], baseline), /Judgment counts/);
});
