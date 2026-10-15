const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { makeReport, directory } = require('./natural_family_audit.cjs');

test('natural family audit reproduces reviewed immutable evidence and every changed historical row', () => {
  const report = JSON.parse(JSON.stringify(makeReport()));
  // Prior classification calibration is frozen; this pass intentionally changes
  // grading and expectation metadata, reviewed separately by natural_acceptance.
  const saved = JSON.parse(fs.readFileSync(path.join(directory, 'results.json')));
  assert.equal(report.historical.length, 53);
  assert.deepEqual(report.historical.map(r => r.observed), saved.historical.map(r => r.observed));
  assert.deepEqual(report.synthetic.map(r => r.observed), saved.synthetic.map(r => r.observed));
  assert.deepEqual(report.physical.map(a => a.units.map(r => r.observed)), saved.physical.map(a => a.units.map(r => r.observed)));
  for (const row of report.historical) {
    if (row.observed.evidence === 'unavailable') {
      assert.equal(row.observed.decision, 'UNAVAILABLE'); assert.equal(row.observed.tone, 'UNCLEAR');
      assert(Object.values(row.observed.fits).every(v => v === 0));
    }
  }
});

test('clean physical families are robust; unavailable controls cannot gain a family', () => {
  const report = JSON.parse(JSON.stringify(makeReport()));
  for (const take of report.physical) for (const row of take.perturbations) {
    const family = row.results.original.family;
    for (const r of Object.values(row.results)) assert.equal(r.family, family, row.id);
  }
  for (const control of report.summary.frozenControls) assert.equal(control.grade, 'UNAVAILABLE');
  assert.deepEqual(report.physical[1].units.slice(0, 2).map(r => [r.after.family, r.after.strength, r.after.grade]),
    [['TONE_3', 'weak', 'STRONG_MATCH'], ['TONE_4', 'weak', 'PARTIAL_OR_WEAK']]);
});
