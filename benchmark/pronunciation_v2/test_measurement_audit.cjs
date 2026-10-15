const test = require('node:test');
const assert = require('node:assert/strict');
const { audit, summary } = require('./measurement_audit.cjs');
const physical = require('../../services/api/tests/fixtures/pitch_measurement_430fcc2e.json');

test('saved physical raw, retained, ownership, projection and classification are inspectable and immutable', () => {
  const before = JSON.stringify(physical), report = JSON.parse(JSON.stringify(audit(physical)));
  assert.equal(JSON.stringify(physical), before);
  assert.deepEqual(report.units.map(u => [u.source_sample_count, u.raw_voiced_count, u.retained_count, u.segment_count]),
    [[33, 24, 21, 3], [27, 25, 22, 2], [27, 3, 3, 1], [31, 16, 15, 1], [45, 21, 18, 1]]);
  assert.deepEqual(report.global.unowned_retained_timestamps, [1.192]);
  assert.deepEqual(report.chunks.at(-1).constituents, ['这', '个']);
  assert.equal(report.chunks.at(-1).retained_count, 33);
  const mai = report.units[2];
  assert.equal(mai.removed_samples.length, 24);
  assert(mai.removed_samples.every(p => p.reasons.includes('tracker_missing')));
  assert.deepEqual(mai.owned_interval, [1.202, 1.222]);
  for (const unit of report.units) {
    assert(unit.provider_words.length);
    assert.deepEqual(unit.classification_input.map(s => s.map(p => p.timestamp_seconds)),
      unit.graph.segments.map(s => s.map(p => p.timestamp_seconds)));
  }
  assert(!JSON.stringify(summary(report)).includes('classification_input'));
});

test('audit detects changed provenance instead of concealing a missing or reassigned source sample', () => {
  const changed = JSON.parse(JSON.stringify(physical));
  changed.data.tone_graph.filtered.segments[0][0].timestamp_seconds += .001;
  assert.throws(() => audit(changed), /absent from retained raw evidence/);
});
