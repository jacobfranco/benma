// Verify the preserved preceding pass under the current acoustic pipeline.
// Its grades are historical evidence; current grades belong to conservative_grading_audit.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { replay } = require('./tone_feedback.cjs');
const { makeReport: naturalReport } = require('./natural_family_audit.cjs');
const root = path.resolve(__dirname, '../..');
const directory = path.join(root, 'docs/research/pronunciation-v2/2026-10-13-natural-acceptance');
const read = p => JSON.parse(fs.readFileSync(p));
function makeReport() {
  const saved = read(path.join(directory, 'results.json'));
  const before = read(path.join(directory, 'baseline.json'));
  const current = JSON.parse(JSON.stringify(naturalReport()));
  assert.deepEqual(current.historical.map(r => r.observed), saved.historical.map(r => r.observed));
  assert.deepEqual(saved.historical.map(r => r.observed), before.historical.map(r => r.observed));
  assert.deepEqual(current.synthetic.map(r => r.observed), saved.calibration.map(r => r.observed));
  assert.deepEqual(current.physical.map(a => a.units.map(u => u.observed)), saved.olderPhysical.map(a => a.units.map(u => u.observed)));
  const physical = JSON.parse(JSON.stringify(replay({ analyses: read(path.join(root,
    'apps/mobile/src/__tests__/fixtures/pitchRobustnessPhysical.json')) })));
  assert.deepEqual(physical.analyses.map(a => a.chunks.flatMap(c => c.constituents.map(u =>
    [u.observed, u.role, u.pitch.segments.map(s => s.length), u.unit.members[0].pitch_eligibility]))),
  saved.physical.map(a => a.units.map(u => [u.after.observed, u.after.role, u.retainedFrames, u.eligibility])));
  return saved;
}
module.exports = { makeReport, directory };
if (require.main === module) {
  makeReport();
  console.log('Preserved natural-acceptance measurements and families verified; see conservative_grading_audit for current grades.');
}
