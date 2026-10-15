// Grade-only replay against the exact arrival tree. No fixture/measurement writes.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { replay, load } = require('./tone_feedback.cjs');
const { inputs, makeReport: toneReport, csv } = require('./tone_feedback_audit.cjs');
const { makeReport: naturalReport } = require('./natural_family_audit.cjs');
const { audit: measurementAudit } = require('./measurement_audit.cjs');
const root = path.resolve(__dirname, '../..');
const directory = path.join(root, 'docs/research/pronunciation-v2/2026-10-13-conservative-grading');
const read = p => JSON.parse(fs.readFileSync(p));
const before = read(path.join(directory, 'baseline.json'));
const concernBefore = read(path.join(directory, 'concern-baseline.json'));
const { learnerPitchEvidence, gradeLearnerPitch, CONSERVATIVE_RED, MINIMUM_LEARNER_CONCERN, COMPATIBLE_PROBE_CONSENSUS } = load('@/speech/learnerPitchGrade');
const reviews = {
  '8d252264:果': 'The sustained stepwise rise, .759 support, .726 runner-up separation and 7/7 probes give affirmative reason to check the missing low/dip. The early reversal and small gap keep this below decisive correction; retain amber.',
  '4b9dbd2b:要': 'A rise ends in a substantial downward retreat. T2 wins at only .480 with .377 separation. Seven agreeing probes repeat the same weak interpretation; consistency cannot supply missing family support. The substantial retreat and low absolute support do not warrant a learner warning; grade green.',
  '4b9dbd2b:一': 'The broad fall ends in a rebound. The fall has .719 support and T3 remains at .232, leaving only .488 runner-up separation. The explicit T2 surface rule is preserved, but a categorical correction is too strong.',
  '4b9dbd2b:苹': 'An asymmetric valley has a much larger recovery than initial fall. T3 is strong (.923), yet expected T2 retains .308 support. This is exactly the case where a high winning score alone must not erase a plausible acceptable explanation.',
  '8faf1a90:一': 'The small fall includes a flattened middle and terminal wavering. T4 has .803 support with 7/7 probes and no T2 support. It is a plausible mismatch, but does not reach the conservative .900 support floor. Weak strength is not the veto.',
  'a5acd04c:我': 'The contour first rises and crests before falling. The weak fall scores .542 with .358 separation. The fall is only a marginal score leader over a mixed crest-and-fall gesture. Stable probes cannot supply enough affirmative support for a learner warning; keep the family and grade green.',
  'a5acd04c:一': 'A shallow crest, dip, and terminal recovery compete within this contour. The level winner scores .448 with .198 separation and only 5/7 probe agreement. T3 (.250) and T4 (.190) remain alternatives. These independent weak-support, narrow-margin and instability signals do not establish a learner problem; grade green while preserving the level score leader.',
  'a5acd04c:苹': 'A small opening crest precedes a large clean fall. The fall scores .867 with .844 separation and 7/7 probes. This is the closest softened historical red to the support cutoff; it remains a meaningful amber concern, not green. Its support falls below the .923–.976 high-support cluster.',
  'b9067bec:想': 'An early dip and a later hump precede the final fall. The falling family is stable but only .484 supported. A .429 margin against weak alternatives cannot turn low absolute support into a meaningful learner concern. The mixed dip/hump/fall does not establish a coherent wrong family; grade green.',
  '208711dc-c437-4afe-b6d3-2aa0e16fb7cb:想': 'The older human contour falls, briefly recovers/levels, then falls again. Its T4 family has .711 support and 7/7 probes. It is less decisive than the newest .974 fall; retain possible-mismatch advice in amber. No gesture-strength gate is involved.',
};
const ambiguityReviews = {
  '89cee47e:想': 'The measured gesture spans 5.407 semitones with opposing movement; T3 support is zero and all seven probes remain unclear. The mixed contour gives reason to ask for a clearer low/dip, without claiming that the weak T4 leader is correct.',
  '6b5b2135:我': 'A 3.461-semitone recovery with direction reversals competes with a low/dip interpretation; four probes choose a rise and three abstain, while expected T3 has only .084 support. This mixed rise/low interpretation remains a possible concern.',
  '6b5b2135:想': 'Substantial opposing movements (1.520-semitone fall and 3.413 recovery in the family features) do not resolve into a coherent low/dip; all probes abstain and T3 support is zero. Mixed geometry, not the weak T4 leader, warrants amber.',
  'ee8a8b32:想': 'The 2.323-semitone mixed gesture lacks a coherent low/dip, with zero T3 support and seven unclear probes. The concern is conflicting movement, not the weak level score leader.',
  '8d252264:一': 'The .410-semitone dip before a 2.130 rise creates real rise/valley competition: probes return T3 four times, expected T2 once, and unclear twice. T2 support .428 is plausible, so no correction is justified; preserve the specific interpretation warning.',
  '8d252264:苹': 'The 3.400-semitone mixed movement is split almost equally between rising and falling duration; every probe abstains. A nominal expected T2 lead of .206 does not resolve the contradictory gesture, so retain the ambiguity warning.',
  '8faf1a90:要': 'The expected fall competes with a level/low interpretation in a 1.140-semitone gesture; probes yield six unclear results and one T3. Expected T4 support .286 remains possible, but the measured direction is unresolved enough to mention cautiously.',
  'a5acd04c:果': 'The .806-semitone dip is followed by a 5.178-semitone rise; T3 and T2 differ by only .052, and four probes abstain. The dominant recovery makes a genuine rise/valley question despite plausible expected T3.',
  'b9067bec:我': 'A 1.695-semitone family fall with little recovery competes with acceptable reduced T3 (.403); five probes choose T4 and two abstain. This is a real fall-versus-low ambiguity, not enough for correction but worth a cautious check.',
  '5c70f317:想': 'A dip, recovery and opposing terminal movement span 2.503 semitones; six probes abstain and only one retains T3. The expected-family leader does not settle the mixed contour, so the trustworthy ambiguity stays amber.',
};
const count = rows => rows.reduce((out, r) => { const key = r.grade.agreement; out[key] = (out[key] || 0) + 1; return out; }, {});
// Everything except the downstream grade and its color must remain identical.
const upstream = value => Array.isArray(value) ? value.map(upstream) : value && typeof value === 'object'
  ? Object.fromEntries(Object.entries(value).filter(([k]) => !['grade', 'color'].includes(k)).map(([k, v]) => [k, upstream(v)])) : value;
function detail(r) {
  const e = learnerPitchEvidence(r.observed, r.expected);
  return { id: r.id, expected: r.expected, observedFamily: r.observed.tone, decision: r.observed.decision,
    evidence: r.observed.evidence, strength: r.observed.strength, acousticReason: r.observed.reason,
    ...e, fits: r.observed.fits, probes: r.observed.perturbations, grade: r.grade };
}
function changes(rows, oldRows) {
  return rows.flatMap(r => {
    const old = oldRows.find(o => o.id === r.id);
    assert(old, r.id);
    if (r.grade.agreement === old.grade.agreement) return [];
    const category = old.grade.agreement === 'CLEAR_DIFFERENCE' && r.grade.agreement === 'PARTIAL_OR_WEAK'
      ? 'non-decisive mismatch softened' : old.grade.agreement === 'CLEAR_DIFFERENCE' && r.grade.agreement === 'STRONG_MATCH'
        ? 'weak mismatch below concern floor' : r.grade.agreement === 'STRONG_MATCH' && old.grade.agreement === 'PARTIAL_OR_WEAK'
        ? 'weak-compatible no longer penalized' : old.grade.agreement === 'UNAVAILABLE' && r.grade.agreement === 'PARTIAL_OR_WEAK'
          ? 'true ambiguity moved to amber' : 'unexpected regression';
    const review = reviews[r.id] ?? (category === 'true ambiguity moved to amber'
      ? `Measurement is trustworthy; ${r.observed.reason} describes interpretation uncertainty, not missing pitch. Preserve all scores and use amber.`
      : category === 'weak-compatible no longer penalized'
        ? 'All seven probes retain the compatible family. Small excursion and moderate matching support alone do not justify withholding green; coaching survives.' : null);
    assert(review, `Unreviewed change: ${r.id}`);
    return [{ ...detail(r), oldGrade: old.grade, category, review }];
  });
}
function makeReport() {
  const natural = JSON.parse(JSON.stringify(naturalReport()));
  const fixtures = read(path.join(root, 'apps/mobile/src/__tests__/fixtures/pitchRobustnessPhysical.json'));
  const physical = JSON.parse(JSON.stringify(replay({ analyses: fixtures })));
  const history = JSON.parse(JSON.stringify(replay(inputs())));
  const supplementalPhysical = JSON.parse(JSON.stringify(replay({ analyses:
    ['pitch_measurement_430fcc2e', 'pitch_projection_89cee47e'].map(f => read(path.join(root, `services/api/tests/fixtures/${f}.json`))).map(a => ({ ...a, id: a.id ?? `projection:${a.provenance.recording.slice(0, 8)}` })) })));
  assert.deepEqual(upstream(history), upstream(before.history), 'historical/control measurements or families changed');
  assert.deepEqual(upstream(physical), upstream(before.physical), 'newest physical measurements or families changed');
  assert.deepEqual(upstream(supplementalPhysical), upstream(before.supplementalPhysical), 'supplemental physical evidence changed');
  for (const key of ['historical', 'synthetic'])
    assert.deepEqual(natural[key].map(r => [r.id, r.shape, r.observed]), before.natural[key].map(r => [r.id, r.shape, r.observed]));
  assert.deepEqual(natural.physical.map(a => a.units.map(r => [r.shape, r.observed, r.expected, r.role])),
    before.natural.physical.map(a => a.units.map(r => [r.shape, r.observed, r.expected, r.role])));
  const fingerprints = read(path.join(directory, 'frozen-inputs.json'));
  for (const [file, sha] of Object.entries(fingerprints))
    assert.equal(createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex'), sha, file);
  const units = a => a.chunks.flatMap(c => c.constituents.map(u => ({ ...u, id: `${a.id}:${u.unit.text}` })));
  const historicalChanges = changes(natural.historical, before.natural.historical);
  const olderUnits = natural.physical.flatMap(a => a.units);
  const olderChanges = changes(olderUnits, before.natural.physical.flatMap(a => a.units));
  const supplementalChanges = changes(supplementalPhysical.analyses.flatMap(units), before.supplementalPhysical.analyses.flatMap(units));
  const calibration = natural.synthetic.map(r => {
    const expected = { tone: Number(r.observed.best?.at(-1) ?? 3), basis: 'resolved_surface', label: 'constructed best-family target', coaching: null, reason: 'control' };
    return detail({ ...r, expected, grade: gradeLearnerPitch(r.observed, expected, true) });
  });
  const previousCalibration = read(path.join(root, 'docs/research/pronunciation-v2/2026-10-13-natural-acceptance/results.json')).calibration;
  const calibrationChanges = calibration.flatMap(r => {
    const old = previousCalibration.find(o => o.id === r.id).matchingGrade;
    return old.agreement === r.grade.agreement ? [] : [{ ...r, oldGrade: old }];
  });
  const all = [...history.rows, ...history.analyses.flatMap(units), ...olderUnits, ...physical.analyses.flatMap(units),
    ...supplementalPhysical.analyses.flatMap(units)]
    .map(detail).concat(calibration);
  const reds = all.filter(r => r.grade.agreement === 'CLEAR_DIFFERENCE').map(r => ({ ...r,
    review: `Trustworthy ${r.winner} is incompatible with ${r.acceptable.join('/')}; support ${r.support.toFixed(6)}, acceptable support ${r.acceptableSupport.toFixed(6)}, runner-up gap ${r.runnerUpMargin.toFixed(6)}, acceptable gap ${r.acceptableMargin.toFixed(6)}, clarity ${r.clarity.toFixed(6)}, ${r.probeAgreement}/${r.probeCount} probes. It clears every conservative correction gate; the context does not license this family.` }));
  const ambers = all.filter(r => r.grade.agreement === 'PARTIAL_OR_WEAK').map(r => ({ ...r,
    review: r.grade.reason === 'ambiguous_family_interpretation' ? ambiguityReviews[r.id.replace('projection:', '')] ?? `Trustworthy ${r.acousticReason}; interpretation remains unresolved.`
      : r.grade.reason === 'compatible_perturbation_uncertainty' ? `Only ${r.probeAgreement}/${r.probeCount} probes retain the compatible family; sensitivity, not weakness, justifies amber.`
        : reviews[r.id] ?? `A stable incompatible gesture has support ${r.support.toFixed(3)}, acceptable support ${r.acceptableSupport.toFixed(3)}, acceptable gap ${r.acceptableMargin.toFixed(3)}, runner-up gap ${r.runnerUpMargin.toFixed(3)}, clarity ${r.clarity.toFixed(3)}, and ${r.probeAgreement}/${r.probeCount} probes. This affirmative separation warrants asking the learner to check the tone, while the full red certificate is absent.` }));
  const concernChanges = natural.historical.flatMap(r => {
    const old = concernBefore.historical.find(o => o.id === r.id);
    if (old.grade.agreement === r.grade.agreement) return [];
    assert.equal(old.grade.agreement, 'PARTIAL_OR_WEAK');
    assert.equal(r.grade.agreement, 'STRONG_MATCH');
    assert(reviews[r.id], `Unreviewed concern change: ${r.id}`);
    return [{ ...detail(r), oldGrade: old.grade, review: reviews[r.id] }];
  });
  for (const old of concernBefore.reds) assert(reds.some(r => r.id === old.id), `Lost red: ${old.id}`);
  return { policy: { red: CONSERVATIVE_RED, concern: MINIMUM_LEARNER_CONCERN, compatibleConsensus: COMPATIBLE_PROBE_CONSENSUS },
    invariants: { acousticFamilyChanges: 0, measurementChanges: 0, selectedFrameChanges: 0, frozenFiles: Object.keys(fingerprints).length },
    distribution: { before: count(before.natural.historical), after: count(natural.historical) },
    concernDistribution: { before: count(concernBefore.historical), after: count(natural.historical) }, concernChanges,
    older: natural.physical.map(a => ({ id: a.id, units: a.units.map(detail), chunks: a.chunks })),
    historical: natural.historical.map(detail), historicalChanges, olderChanges, supplementalChanges,
    supplementalPhysical: supplementalPhysical.analyses.map(a => ({ id: a.id, units: units(a).map(detail) })),
    newest: physical.analyses.map(a => ({ id: a.id, units: units(a).map(detail), chunks: a.chunks.map(c => ({ text: c.text, grade: c.grade })) })),
    calibration, calibrationChanges, reds, ambers, frozenControls: natural.summary.frozenControls,
    measurement: [...fixtures, ...read(path.join(root, 'apps/mobile/src/__tests__/fixtures/toneClassificationPhysical.json')),
      read(path.join(root, 'services/api/tests/fixtures/pitch_measurement_430fcc2e.json'))].map(measurementAudit) };
}
module.exports = { makeReport, directory };
if (require.main === module) {
  const result = makeReport(), tone = toneReport();
  fs.writeFileSync(path.join(directory, 'results.json'), JSON.stringify(result, null, 2) + '\n');
  fs.writeFileSync(path.join(directory, 'tone-feedback-results.json'), JSON.stringify(tone, null, 2) + '\n');
  fs.writeFileSync(path.join(directory, 'tone-feedback-matrix.csv'), csv([...tone.rows, ...tone.chunks]));
  console.log(JSON.stringify({ invariants: result.invariants, distribution: result.distribution,
    historicalChanges: result.historicalChanges.length, olderChanges: result.olderChanges.length,
    redIds: result.reds.map(r => r.id) }, null, 2));
}
