const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const { makeReport, directory } = require('./conservative_grading_audit.cjs');
test('conservative replay freezes upstream evidence and reviews every grade change, red, and amber', () => {
  const r = makeReport();
  assert.equal(JSON.stringify(r, null, 2) + '\n', fs.readFileSync(path.join(directory, 'results.json'), 'utf8'));
  assert.deepEqual(r.distribution.after, { STRONG_MATCH: 20, PARTIAL_OR_WEAK: 16, UNAVAILABLE: 14, CLEAR_DIFFERENCE: 3 });
  assert.equal(r.historicalChanges.length, 19);
  assert.equal(r.historicalChanges.filter(c => c.category === 'non-decisive mismatch softened').length, 5);
  assert.equal(r.historicalChanges.filter(c => c.category === 'weak mismatch below concern floor').length, 4);
  assert.equal(r.historicalChanges.filter(c => c.category === 'true ambiguity moved to amber').length, 10);
  assert(r.historicalChanges.every(c => c.category !== 'unexpected regression' && c.review.length > 80));
  assert.equal(r.olderChanges.length, 2);
  assert(r.reds.every(r => r.review.length > 100 && r.evidence === 'trustworthy' && r.consensus === 1));
  assert(r.ambers.every(r => r.review.length > 40));
  assert.equal(r.newest[1].units[0].grade.coaching, 'Dip is shallow.');
  assert.equal(r.newest[1].units[2].grade.coaching, 'Dip is shallow.');
  assert.deepEqual(r.newest[1].units.map(r => r.grade.agreement),
    ['STRONG_MATCH', 'CLEAR_DIFFERENCE', 'STRONG_MATCH', 'STRONG_MATCH', 'UNAVAILABLE']);
  assert(r.frozenControls.every(c => c.grade === 'UNAVAILABLE'));
});

test('minimum concern replay reviews exactly four newly green leaders and preserves every red gate', () => {
  const r = makeReport();
  assert.deepEqual(r.concernDistribution.before, { STRONG_MATCH: 16, PARTIAL_OR_WEAK: 20, UNAVAILABLE: 14, CLEAR_DIFFERENCE: 3 });
  assert.deepEqual(r.concernChanges.map(c => c.id), ['4b9dbd2b:要', 'a5acd04c:我', 'a5acd04c:一', 'b9067bec:想']);
  for (const c of r.concernChanges) {
    assert.equal(c.oldGrade.agreement, 'PARTIAL_OR_WEAK');
    assert.equal(c.grade.agreement, 'STRONG_MATCH');
    assert.equal(c.evidence, 'trustworthy');
    assert(!c.acceptable.includes(c.winner));
    assert(c.support < r.policy.concern.support);
    assert(c.review.length > 100);
  }
  assert.deepEqual({ ...r.policy.red }, { support: .9, acceptableSupportMax: .2, acceptableMargin: .7,
    runnerUpMargin: .6, clarity: .9, minimumProbes: 7, consensus: 1 });
  for (const c of r.reds) {
    assert.equal(c.decision, 'NUMBERED');
    assert(!c.acceptable.includes(c.winner));
    assert(c.support >= .9 && c.acceptableSupport <= .2 && c.acceptableMargin >= .7);
    assert(c.runnerUpMargin >= .6 && c.clarity >= .9 && c.probeCount >= 7 && c.consensus === 1);
  }
  for (const c of r.ambers.filter(c => c.grade.reason === 'nondecisive_incompatible_family')) {
    assert(c.support >= .65 && c.acceptableSupport <= .4 && c.acceptableMargin >= .5);
    assert(c.runnerUpMargin >= .45 && c.clarity >= .9 && c.probeCount >= 7 && c.consensus >= 6 / 7);
  }
  assert.equal(r.older[1].units.find(c => c.id.endsWith(':想')).grade.agreement, 'PARTIAL_OR_WEAK');
  assert.deepEqual(r.invariants, { acousticFamilyChanges: 0, measurementChanges: 0, selectedFrameChanges: 0, frozenFiles: 186 });
});
