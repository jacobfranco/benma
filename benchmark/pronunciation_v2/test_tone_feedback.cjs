const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { makeReport, csv } = require('./tone_feedback_audit.cjs');
const out = path.resolve(__dirname, '../../docs/research/pronunciation-v2/2026-10-13-conservative-grading');

test('production replay is deterministic, immutable, and agrees with the published numeric calibration', () => {
  const first = makeReport(), second = makeReport();
  assert.deepEqual(first, second);
  assert.equal(JSON.stringify(first, null, 2) + '\n', fs.readFileSync(path.join(out, 'tone-feedback-results.json'), 'utf8'));
  assert.equal(csv([...first.rows, ...first.chunks]), fs.readFileSync(path.join(out, 'tone-feedback-matrix.csv'), 'utf8'));
  assert.equal(first.summary.corpus_units, 53);
  assert.equal(first.summary.clean_shapes, 29);
  assert(first.summary.lost_classifiable.includes('0b194cf9:买'));
  assert.equal(first.summary.unavailable_evidence, 14);
  assert.deepEqual(first.summary.trustworthy_families, { TONE_3: 18, UNCLEAR: 10, TONE_2: 2, TONE_4: 8, TONE_1: 1 });
  assert.deepEqual(first.summary.current, { STRONG_MATCH: 20, UNAVAILABLE: 14, PARTIAL_OR_WEAK: 16, CLEAR_DIFFERENCE: 3 });
  assert.equal(first.summary.current.UNAVAILABLE, 14);
  assert.equal(first.summary.classifiable_but_context_unresolved.length, 0);
});
test('fresh physical regression and constructed chunk controls keep provenance and all four grades separate', () => {
  const report = makeReport();
  const physical = report.rows.filter(r => r.provenance === 'fresh_saved_measurements');
  assert.deepEqual(physical.map(r => [r.id.split(':').at(-1), r.observed.tone]), [
    ['我', 'UNCLEAR'], ['想', 'TONE_3'], ['买', 'UNCLEAR'], ['这', 'TONE_4'], ['个', 'UNCLEAR'],
  ]);
  assert.deepEqual(physical.map(r => [r.expected.basis, r.color]), [
    ['lexical_family', 'gray'], ['lexical_family', 'green'], ['lexical_family', 'gray'],
    ['resolved_surface', 'green'], ['neutral', 'gray'],
  ]);
  const neutral = report.rows.find(r => r.id === 'constructed:这个-ambiguous-neutral:个');
  assert.equal(neutral.observed.tone, 'UNCLEAR');
  assert.equal(neutral.role, 'neutral_measured_accepted');
  assert.equal(neutral.color, 'green');
  const chunk = id => report.chunks.find(r => r.id === `${id}:这个`);
  assert.equal(chunk(report.summary.fresh_analysis_id).color, 'green');
  for (const [id, color] of [['mismatch', 'red'], ['unclear', 'gray'], ['weak', 'green'], ['measured-neutral', 'green'], ['ambiguous-neutral', 'green'], ['contradictory-neutral', 'green']]) {
    assert.equal(chunk(`constructed:这个-${id}`).color, color);
    assert.equal(chunk(`constructed:这个-${id}`).provenance, 'constructed_control');
  }
  const unreliable = report.rows.find(r => r.id === 'constructed:这个-contradictory-neutral:个');
  assert.equal(unreliable.role, 'neutral_unreliable_nonveto');
  assert.equal(unreliable.grade.agreement, 'UNAVAILABLE');
  assert.equal(unreliable.color, 'gray');
});
