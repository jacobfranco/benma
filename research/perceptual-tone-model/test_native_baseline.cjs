const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const { classify } = require('./native_baseline.cjs');
const { replay } = require('../../benchmark/pronunciation_v2/tone_feedback.cjs');
const { verifyBaseline } = require('./evaluate.cjs');

test('native acoustic adapter matches frozen replay and ignores target labels', () => {
  verifyBaseline();
  const root = path.resolve(__dirname, '../..');
  const rows = JSON.parse(fs.readFileSync(path.join(root, 'docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json')));
  const context = JSON.parse(fs.readFileSync(path.join(root, 'docs/research/pronunciation-v2/2026-10-09-product-feedback/expected-context.json'))).units;
  const expected = replay({ rows, context }).rows;
  for (let i = 0; i < rows.length; i++) {
    const before = JSON.stringify(rows[i]);
    const result = classify(rows[i]);
    const observed = expected[i].observed;
    assert.equal(result.prediction, observed.decision === 'NUMBERED' ? observed.tone.replace('TONE_', 'T') : null);
    assert.deepEqual(result, classify({ ...rows[i], lexical_tone: 1, expected_surface_tone: 4, text: 'POISON' }));
    assert.equal(JSON.stringify(rows[i]), before);
  }
  assert.equal(classify({}).prediction, null);
  assert.equal(classify({ grouped: true, segments: [] }).prediction, null);
});
