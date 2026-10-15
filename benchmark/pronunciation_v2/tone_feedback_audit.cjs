// Frozen measured evidence + explicitly constructed controls. No network/audio.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { replay, load } = require('./tone_feedback.cjs');
const root = path.resolve(__dirname, '../..');
const out = path.join(root, 'docs/research/pronunciation-v2/2026-10-12-natural-family');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file)));
const corpusPath = 'docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json';
const corpus = read(corpusPath);
const context = read('docs/research/pronunciation-v2/2026-10-09-product-feedback/expected-context.json').units;
const fresh = read('apps/mobile/src/__tests__/fixtures/toneFeedbackPhysical.json');
const cases = read('apps/mobile/src/__tests__/fixtures/pronunciationChunkCases.json');
const clone = x => JSON.parse(JSON.stringify(x));
const line = (fn, n = 51, start = 0) => Array.from({ length: n }, (_, i) => ({ t: start + i * .01, st: fn(i / (n - 1)) }));
const valley = (fall, rise) => x => x < .5 ? fall * (1 - 2 * x) : rise * (2 * x - 1);
function inputs() {
  const expected = { ...context };
  const controls = [
    ['level', x => .1 * x, 1], ['rise', x => 4 * x, 2], ['fall', x => -4 * x, 4],
    ['full-t3', valley(4, 4), 3], ['above-start-valley', valley(3, 5), 3],
    ['weak-rise', x => 1.9 * x, 2], ['weak-fall', x => -1.9 * x, 4],
    ['shallow-valley', valley(1.4, 1.4), 3], ['weak-recovery', valley(3, 1.4), 3],
    ['ambiguous-valley', valley(.9, 1.6), 3], ['reduced-low-tail', x => x < .35 ? 3 * (1 - x / .35) : .1 * (x - .35), 3],
    ['sandhi-full-valley', valley(4, 4), 2], ['stable-fall-against-t3', x => -3 * x, 3],
  ].map(([name, fn, tone]) => {
    const id = `constructed:${name}`;
    expected[id] = { characters: name, pinyin: 'control', reading_source: 'dictionary', expected_surface_tone: tone,
      surface_rule: name === 'sandhi-full-valley' ? 'third_tone_pair' : 'constructed_resolved_context' };
    return { id, segments: [line(fn)], grouped: false, flagged_indices: [] };
  });
  const design = text => {
    const fixture = cases.find(c => c.text === text);
    return { ...clone(fresh), id: `constructed:${text}`, alignment_reference_text: text, data: { ...clone(fresh.data), ...clone(fixture),
      duration_seconds: fixture.syllables.length * .6, timing_groups: [], measured_pitch: [],
      tone_graph: { raw: [], filtered: { segments: [] } },
      syllables: fixture.syllables.map((s, i) => ({ ...s, start_seconds: i * .6, end_seconds: (i + 1) * .6 })),
    } };
  };
  const setPitch = (a, index, fn) => {
    const s = a.data.syllables[index], start = s.start_seconds, end = s.end_seconds;
    a.data.tone_graph.raw = a.data.tone_graph.raw.filter(p => p.timestamp_seconds < start || p.timestamp_seconds >= end);
    a.data.tone_graph.filtered.segments = a.data.tone_graph.filtered.segments.map(segment => segment.filter(p => p.timestamp_seconds < start || p.timestamp_seconds >= end)).filter(s => s.length);
    if (fn) a.data.tone_graph.filtered.segments.push(line(fn, Math.floor((end - start) / .01) - 1, start + .01)
      .map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
    a.data.tone_graph.filtered.segments.sort((a, b) => a[0].timestamp_seconds - b[0].timestamp_seconds);
  };
  const analyses = [clone(fresh)];
  for (const [id, fn] of [['mismatch', x => 4 * x], ['unclear', undefined], ['weak', x => -.25 * x]]) {
    const a = clone(fresh); a.id = `constructed:这个-${id}`; setPitch(a, 3, fn); analyses.push(a);
  }
  for (const [id, fn] of [['measured-neutral', x => 4 * x], ['ambiguous-neutral', x => 2.2 * (1 - Math.abs(x * 2 - 1))], ['contradictory-neutral', x => x < .5 ? 4 * x : 12 + 4 * x]]) {
    const a = clone(fresh); a.id = `constructed:这个-${id}`; setPitch(a, 4, fn); analyses.push(a);
  }
  for (const [text, curves] of [['那个', [x => -4 * x]], ['去吧', [x => -4 * x]],
    ['贵州', [x => -4 * x, x => .1 * x]], ['不是', [x => 4 * x, x => -4 * x]],
    ['我想', [valley(4, 4), valley(4, 4)]]]) {
    const a = design(text); curves.forEach((fn, i) => setPitch(a, i, fn));
    if (text === '贵州') a.intended_text = '广州';
    analyses.push(a);
  }
  const grouped = read('apps/mobile/src/__tests__/fixtures/workspaceTimingControls.json').find(c => c.id === '40357072');
  // The timing-only control has no graph. Attach the already frozen, owned
  // numeric projection for this exact group; do not synthesize a character split.
  const groupRow = corpus.find(r => r.id === '40357072:雨伞');
  grouped.data.tone_graph = { raw: [], filtered: { segments: groupRow.segments.map(s => s.map(p =>
    ({ timestamp_seconds: p.t, normalized_semitones: p.st }))) } };
  analyses.push({ ...clone(fresh), id: 'saved:grouped-雨伞', alignment_reference_text: grouped.data.syllables.map(s => s.characters).join(''), data: grouped.data });
  return { rows: [...corpus, ...controls], context: expected, analyses };
}
function makeReport() {
  const input = inputs(), before = JSON.stringify(input);
  const result = replay(input);
  if (JSON.stringify(input) !== before) throw Error('Production replay mutated evidence');
  const reportRows = result.rows.map(r => ({ ...r, provenance: r.id.startsWith('constructed:') ? 'constructed_geometry' : 'frozen_corpus' }));
  const chunkRows = [];
  for (const a of result.analyses) for (const chunk of a.chunks) {
    const provenance = a.id === fresh.id ? 'fresh_saved_measurements' : a.id.startsWith('saved:') ? 'saved_grouped_measurements' : 'constructed_control';
    for (const e of chunk.constituents) reportRows.push({ id: `${a.id}:${e.unit.text}`, provenance,
      shape: e.shape, observed: e.observed, expected: e.expected, grade: e.grade, role: e.role,
      color: load('@/speech/learnerPitchGrade').pitchGradePresentation[e.grade.agreement].color });
    chunkRows.push({ id: `${a.id}:${chunk.text}`, provenance, grade: chunk.grade, color: chunk.color,
      expected: { label: chunk.constituents.map(e => `${e.unit.text}: ${e.expected.label}`).join('; ') },
      constituents: chunk.constituents.map(e => ({ text: e.unit.text, role: e.role, grade: e.grade.agreement })) });
  }
  const count = (rows, f) => rows.reduce((out, r) => { const k = f(r); out[k] = (out[k] ?? 0) + 1; return out; }, {});
  const original = result.rows.slice(0, corpus.length);
  const unresolved = original.filter(r => r.observed.tone !== 'UNCLEAR' && r.expected.tone === null);
  return { summary: {
    corpus_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, corpusPath))).digest('hex'),
    physical_fixture_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, 'apps/mobile/src/__tests__/fixtures/toneFeedbackPhysical.json'))).digest('hex'),
    corpus_units: corpus.length, clean_shapes: original.filter(r => r.shape.shape !== 'UNCLEAR').length,
    tone_likeness: count(original, r => r.observed.tone),
    trustworthy_families: count(original.filter(r => r.observed.evidence === 'trustworthy'), r => r.observed.tone),
    unavailable_evidence: original.filter(r => r.observed.evidence === 'unavailable').length,
    previous: { STRONG_MATCH: 0, PARTIAL_OR_WEAK: 5, CLEAR_DIFFERENCE: 3, UNAVAILABLE: 45 },
    current: count(original, r => r.grade.agreement),
    lexical_family_fallbacks: original.filter(r => r.expected.basis === 'lexical_family').map(r => ({ id: r.id, agreement: r.grade.agreement })),
    gray_reasons: count(original.filter(r => r.grade.agreement === 'UNAVAILABLE'), r => r.grade.reason),
    classifiable_but_context_unresolved: unresolved.map(r => r.id),
    lost_classifiable: original.filter(r => r.shape.shape !== 'UNCLEAR' && r.observed.tone === 'UNCLEAR').map(r => r.id),
    fresh_analysis_id: fresh.id, fresh_utterance_id: fresh.utterance_id,
  }, rows: reportRows, chunks: chunkRows };
}
function csv(rows) {
  const fields = ['identity', 'provenance', 'measured_shape', 'geometry', 'T1_fit', 'T2_fit', 'T3_fit', 'T4_fit', 'best', 'runner_up',
    'margin', 'tone_likeness', 'expected_context', 'agreement', 'color', 'gray_reason', 'chunk_role'];
  const quote = x => `"${String(x ?? '').replaceAll('"', '""')}"`;
  return [fields, ...rows.map(r => [r.id, r.provenance, r.shape?.shape ?? 'constituent aggregation',
    JSON.stringify(r.observed?.features ?? {}), ...['TONE_1', 'TONE_2', 'TONE_3', 'TONE_4'].map(t => r.observed?.fits[t]),
    r.observed?.best, r.observed?.runnerUp, r.observed?.margin, r.observed?.tone ?? 'not a single-tone unit',
    r.expected?.label ?? r.constituents?.map(c => `${c.text}: ${c.role}`).join('; '), r.grade.agreement, r.color,
    r.grade.agreement === 'UNAVAILABLE' ? r.grade.reason : '', r.role ?? ''])].map(row => row.map(quote).join(',')).join('\n') + '\n';
}
module.exports = { inputs, makeReport, csv };
if (require.main === module) {
  const report = makeReport();
  fs.writeFileSync(path.join(out, 'tone-feedback-results.json'), JSON.stringify(report, null, 2) + '\n');
  fs.writeFileSync(path.join(out, 'tone-feedback-matrix.csv'), csv([...report.rows, ...report.chunks]));
  console.log(JSON.stringify(report.summary, null, 2));
}
