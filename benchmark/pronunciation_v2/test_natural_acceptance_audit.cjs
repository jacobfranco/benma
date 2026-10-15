const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const { makeReport, directory } = require('./natural_acceptance_audit.cjs');
test('natural acceptance replays exactly and every historical grade change is reviewed', () => {
  const r = JSON.parse(JSON.stringify(makeReport()));
  assert.equal(JSON.stringify(r, null, 2) + '\n', fs.readFileSync(path.join(directory, 'results.json'), 'utf8'));
  assert.equal(r.historicalFamilyChanges, 0);
  assert.equal(r.changes.length, 4);
  assert(r.changes.every(c => c.review.length > 80 && c.before.agreement === 'PARTIAL_OR_WEAK' && c.after.agreement === 'STRONG_MATCH'));
  assert(r.frozenControls.every(c => c.grade === 'UNAVAILABLE'));
  assert(r.physical[0].units.every(u => u.after.observed.decision === 'UNAVAILABLE'));
  assert.deepEqual(r.physical[1].units.map(u => u.after.grade.agreement),
    ['STRONG_MATCH', 'CLEAR_DIFFERENCE', 'STRONG_MATCH', 'STRONG_MATCH', 'UNAVAILABLE']);
});
