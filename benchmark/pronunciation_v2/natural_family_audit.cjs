// Offline interpretation audit. Frozen analyses and measurements are never written.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { load, replay } = require('./tone_feedback.cjs');
const { inputs } = require('./tone_feedback_audit.cjs');
const root = path.resolve(__dirname, '../..');
const directory = path.join(root, 'docs/research/pronunciation-v2/2026-10-12-natural-family');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file)));
const baseline = read('docs/research/pronunciation-v2/2026-10-12-natural-family/baseline.json');
const physical = read('apps/mobile/src/__tests__/fixtures/toneClassificationPhysical.json');
const matrix = read('apps/mobile/src/__tests__/fixtures/naturalToneContours.json');
const { classifyPitchShape } = load('@/speech/pitchShape');
const { classifyToneLikeness, NATURAL_FAMILY, TONE_MARGIN } = load('@/speech/toneLikeness');
const { unitShape } = load('@/speech/pitchShapeEvidence');
const count = (rows, key) => rows.reduce((out, r) => { const k = key(r); out[k] = (out[k] || 0) + 1; return out; }, {});
const compact = r => ({ family: r.observed.tone, strength: r.observed.strength, variant: r.observed.variant,
  reason: r.observed.reason, grade: r.grade?.agreement ?? null, gradeReason: r.grade?.reason ?? null });
const pointsFor = c => Array.from({ length: 61 }, (_, i) => {
  const x = i / 60, j = c.knots.findIndex(k => k[0] >= x);
  const [b, yb] = c.knots[Math.max(0, j)], [a, ya] = c.knots[Math.max(0, j - 1)];
  return { timestamp_seconds: i * .01, normalized_semitones: a === b ? yb : ya + (yb - ya) * (x - a) / (b - a) };
});
function variations(segments) {
  const points = segments.flat();
  return {
    original: segments,
    transpose_up: segments.map(s => s.map(p => ({ ...p, normalized_semitones: p.normalized_semitones + 24 }))),
    transpose_down: segments.map(s => s.map(p => ({ ...p, normalized_semitones: p.normalized_semitones - .3 }))),
    delete_first: segments.map(s => s.filter(p => p !== points[0])),
    delete_last: segments.map(s => s.filter(p => p !== points.at(-1))),
    delete_middle: segments.map(s => s.filter(p => p !== points[Math.floor(points.length / 2)])),
    delete_tenth: segments.map(s => s.filter(p => points.indexOf(p) % 10 !== 9)),
    timing_jitter: segments.map(s => s.map((p, i) => ({ ...p, timestamp_seconds: p.timestamp_seconds + (i % 2 ? .002 : 0) }))),
    endpoint_pitch: segments.map(s => s.map(p => ({ ...p, normalized_semitones: p.normalized_semitones + (p === points[0] ? .015 : 0) }))),
  };
}
function stability(segments, classify) {
  return Object.fromEntries(Object.entries(variations(segments)).map(([name, s]) => [name, compact({ observed: classify(s) })]));
}
function grayRate(before, after) {
  // Hold the trustworthy denominator fixed at current structural checks. The old
  // code sometimes emitted a family despite a raw flag; report that separately.
  const trusted = after.filter(r => r.observed.evidence === 'trustworthy');
  const safeIds = new Set(trusted.map(r => r.id)), oldSafe = before.filter(r => safeIds.has(r.id));
  const rejected = after.filter(r => r.observed.evidence === 'unavailable');
  const grayBefore = oldSafe.filter(r => r.observed.tone === 'UNCLEAR').length;
  const grayAfter = trusted.filter(r => r.observed.tone === 'UNCLEAR').length;
  return { trustworthyUnits: trusted.length, before: count(oldSafe, r => r.observed.tone), after: count(trusted, r => r.observed.tone),
    trustworthyGrayBefore: grayBefore, trustworthyGrayAfter: grayAfter,
    grayFractionBefore: trusted.length ? grayBefore / trusted.length : null,
    grayFractionAfter: trusted.length ? grayAfter / trusted.length : null,
    untrustworthyUnits: rejected.length,
    untrustworthyBefore: count(before.filter(r => rejected.some(a => a.id === r.id)),
      r => r.observed.tone === 'UNCLEAR' ? 'UNAVAILABLE' : 'NUMBERED_DESPITE_UNSAFE_EVIDENCE'),
    untrustworthyAfter: count(rejected, r => r.observed.decision),
    previouslyNumberedDespiteCurrentSafety: before.filter(r => rejected.some(a => a.id === r.id) && r.observed.tone !== 'UNCLEAR').map(r => r.id) };
}
function makeReport() {
  const input = inputs(), saved = JSON.stringify({ input, physical, matrix });
  input.analyses = [...input.analyses, ...physical];
  const result = replay(input), historical = result.rows.slice(0, 53);
  const units = a => a.chunks.flatMap(c => c.constituents.map(e => ({ id: `${a.id}:${e.unit.text}`, text: e.unit.text,
    shape: e.shape, observed: e.observed, expected: e.expected, grade: e.grade, role: e.role })));
  const takes = result.analyses.slice(-2).map((a, i) => {
    const rows = units(a), before = baseline.physical[i];
    const perturbations = a.chunks.flatMap(c => c.constituents.map(e => ({ id: `${a.id}:${e.unit.text}`,
      results: stability(e.pitch.segments, segments => classifyToneLikeness(unitShape(physical[i].data, e.unit, segments), segments)) })));
    return { id: a.id, label: i === 0 ? 'Google' : 'Human', grayRate: grayRate(before.units, rows),
      units: rows.map((r, j) => ({ ...r, before: compact(before.units[j]), after: compact(r) })),
      chunks: a.chunks.map((c, j) => ({ text: c.text, before: before.chunks[j].grade.agreement, after: c.grade.agreement })), perturbations };
  });
  const synthetic = matrix.map(c => {
    const points = pointsFor(c), shape = classifyPitchShape([points]), observed = classifyToneLikeness(shape, [points]);
    assert.equal(observed.tone, c.tone, c.id); assert.equal(observed.strength, c.strength, c.id);
    const perturbations = stability([points], s => classifyToneLikeness(classifyPitchShape(s), s));
    if (c.tone !== 'UNCLEAR') for (const [name, r] of Object.entries(perturbations)) assert.equal(r.family, c.tone, `${c.id}:${name}`);
    return { id: c.id, knots: c.knots, shape, observed, before: compact(baseline.synthetic.find(r => r.id === c.id)), after: compact({ observed }), perturbations };
  });
  const smallMovementSweep = [-1, 1].flatMap(sign => Array.from({ length: 61 }, (_, i) => {
    const amplitude = Number((.1 + i * .005).toFixed(3));
    const points = Array.from({ length: 61 }, (_, j) => ({ timestamp_seconds: j * .01, normalized_semitones: sign * amplitude * j / 60 }));
    const observed = classifyToneLikeness(classifyPitchShape([points]), [points]);
    return { direction: sign > 0 ? 'rise' : 'fall', amplitude, decision: observed.decision, ...compact({ observed }),
      fits: observed.fits, margin: observed.margin };
  }));
  for (let i = 1; i < smallMovementSweep.length; i++) {
    const a = smallMovementSweep[i - 1], b = smallMovementSweep[i];
    if (a.direction === b.direction) for (const family of Object.keys(a.fits)) assert(Math.abs(a.fits[family] - b.fits[family]) < .025);
  }
  const historicalPerturbations = input.rows.slice(0, 53).map(row => {
    const segments = row.segments.map(s => s.map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
    const flags = row.segments.flat().filter(p => row.flagged_indices.includes(p.index)).map(p => p.t);
    return { id: row.id, results: stability(segments, s => classifyToneLikeness(row.grouped
      ? { shape: 'UNCLEAR', reason: 'grouped_timing', features: {}, perturbations: {} }
      : classifyPitchShape(s, flags, !!row.flagged_indices.length), s)) };
  });
  for (const r of [...historicalPerturbations, ...takes.flatMap(t => t.perturbations)]) {
    for (const key of ['transpose_up', 'transpose_down']) assert.equal(r.results[key].family, r.results.original.family, `${r.id}:${key}`);
  }
  const changes = historical.flatMap((r, i) => {
    const before = compact(baseline.historical[i]), after = compact(r);
    return JSON.stringify(before) === JSON.stringify(after) ? [] : [{ id: r.id, before, after, fits: r.observed.fits,
      decision: r.observed.decision, evidence: r.observed.evidence,
      best: r.observed.best, runnerUp: r.observed.runnerUp,
      margin: r.observed.margin, features: r.observed.features, expected: r.expected }];
  });
  // Evidence remains exactly as supplied; exclude the analyses append above.
  input.analyses = input.analyses.slice(0, -physical.length);
  assert.equal(JSON.stringify({ input, physical, matrix }), saved);
  const files = ['apps/mobile/src/__tests__/fixtures/toneClassificationPhysical.json',
    'apps/mobile/src/__tests__/fixtures/toneFeedbackPhysical.json',
    'services/api/tests/fixtures/pitch_measurement_430fcc2e.json',
    'docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json'];
  const frozenControls = [historical.find(r => r.id === '89cee47e:买'), ...units(result.analyses[0]).filter(r => r.text === '买'),
    ...takes[0].units.filter(r => r.text === '买')];
  const sparse = read('services/api/tests/fixtures/pitch_measurement_430fcc2e.json');
  frozenControls.push(...units(replay({ analyses: [sparse] }).analyses[0]).filter(r => r.text === '买'));
  for (const r of frozenControls) assert.equal(r.grade.agreement, 'UNAVAILABLE');
  return { constants: { ...NATURAL_FAMILY, margin: TONE_MARGIN }, inputHashes: Object.fromEntries(files.map(f => [f,
    crypto.createHash('sha256').update(fs.readFileSync(path.join(root, f))).digest('hex')])),
    summary: { historical: grayRate(baseline.historical, historical), historicalGradesBefore: count(baseline.historical, r => r.grade.agreement),
      historicalGradesAfter: count(historical, r => r.grade.agreement),
      familyOrStrengthChanges: changes.filter(r => r.before.family !== r.after.family || r.before.strength !== r.after.strength).length,
      synthetic: grayRate(baseline.synthetic, synthetic), frozenControls: frozenControls.map(r => ({ id: r.id, ...compact(r) })) },
    historical, changes, trustworthyGray: historical.filter(r => r.observed.evidence === 'trustworthy' && r.observed.tone === 'UNCLEAR'),
    physical: takes, synthetic, smallMovementSweep, historicalPerturbations };
}
module.exports = { makeReport, directory };
if (require.main === module) {
  const report = makeReport();
  fs.writeFileSync(path.join(directory, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report.summary, null, 2));
}
