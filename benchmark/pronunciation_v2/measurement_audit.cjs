// Read-only pipeline audit of a saved analysis or diagnostic snapshot. No providers.
// node benchmark/pronunciation_v2/measurement_audit.cjs [--summary] saved.json ...
// With no paths, read an analysis (or array of analyses) from stdin.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { load } = require('./tone_feedback.cjs');
const { pronunciationUnits, unitPitch, workspacePitch } = load('@/speech/pronunciationWorkspace');
const { pronunciationChunks, chunkPitch } = load('@/speech/pronunciationChunks');
const { unitShape } = load('@/speech/pitchShapeEvidence');
const { shapeDisplay } = load('@/speech/pitchShapeDisplay');
const { normalizedGeometry } = load('@/components/PitchPlot');
const { classifyToneLikeness } = load('@/speech/toneLikeness');

const interval = points => points.length ? [points[0].timestamp_seconds, points.at(-1).timestamp_seconds] : null;
function audit(input) {
  const before = JSON.stringify(input);
  const data = input.data ?? input.analysis?.result;
  assert(data, 'Expected analysis.data or snapshot.analysis.result');
  const units = pronunciationUnits(data), chunks = pronunciationChunks(data, units);
  const source = workspacePitch(data), raw = data.tone_graph?.raw ?? [];
  const track = input.track ?? input.acoustic?.result?.utterance_pitch_track ?? input.acoustic?.normalized_result?.utterance_pitch_track;
  if (track) {
    assert.equal(data.pitch_track_evidence_id, track.evidence_id);
    assert.equal(raw.length, track.frames.length);
    for (const p of raw) {
      const f = track.frames[p.source_frame_index];
      assert.equal(p.timestamp_seconds, f.timestamp_seconds);
      assert.equal(p.tracker_f0_hz, f.raw_f0_hz);
      assert.equal(p.selected_f0_hz, f.selected_f0_hz);
      assert.equal(p.retained, f.selected_f0_hz !== null);
      assert.deepEqual(p.exclusion_reasons, f.exclusion_reasons);
    }
  }
  const byTime = new Map(raw.map((p, i) => [p.timestamp_seconds, { ...p, raw_index: i }]));
  const sourceByTime = new Map();
  source.segments.forEach((segment, segmentId) => segment.forEach((p, pointIndex) => {
    assert(!sourceByTime.has(p.timestamp_seconds), 'Duplicate global retained timestamp');
    sourceByTime.set(p.timestamp_seconds, { segment_id: segmentId, point_index: pointIndex, ...p });
    const frame = byTime.get(p.timestamp_seconds);
    if (raw.length) assert(frame?.retained, 'Displayed sample absent from retained raw evidence');
    if (track) {
      const original = track.frames[frame.source_frame_index];
      assert.equal(original.timestamp_seconds, p.timestamp_seconds);
      assert.equal(original.selected_f0_hz, frame.selected_f0_hz);
      assert(Math.abs(p.normalized_semitones - 12 * Math.log2(original.selected_f0_hz / track.baseline_hz)) < 1e-9);
    }
  }));
  if (raw.length) assert.deepEqual([...sourceByTime.keys()], raw.filter(p => p.retained).map(p => p.timestamp_seconds));
  const ownedTimes = new Set();
  const reports = units.map(unit => {
    const segments = unitPitch(data, unit, units).segments;
    const points = segments.flat();
    const { domain, layout } = shapeDisplay(segments, unit.start, unit.end);
    const coordinates = normalizedGeometry(layout, 1, 1, domain);
    const shape = unitShape(data, unit, segments);
    const tone = classifyToneLikeness(shape, segments);
    points.forEach((p, i) => {
      assert(unit.start <= p.timestamp_seconds && p.timestamp_seconds < unit.end, 'Sample outside accepted interval');
      assert(!ownedTimes.has(p.timestamp_seconds), 'Double ownership');
      assert(!i || points[i - 1].timestamp_seconds < p.timestamp_seconds, 'Nonmonotonic source order');
      assert.equal(sourceByTime.get(p.timestamp_seconds)?.normalized_semitones, p.normalized_semitones);
      ownedTimes.add(p.timestamp_seconds);
    });
    assert.equal(layout.segments.length, segments.length, 'Projection changed segment separation');
    const inSpan = raw.filter(p => unit.start <= p.timestamp_seconds && p.timestamp_seconds < unit.end);
    const chunk = chunks.find(c => c.constituentUnitIds.includes(unit.id));
    const timing = (data.timing_evidence?.units ?? []).filter(t => unit.members.some(s => s.index === t.syllable_index));
    const words = data.timing_evidence?.provider_timing?.NBest?.[0]?.Words ?? [];
    const providerWords = [...new Set(timing.map(t => t.provider_word_index))].flatMap(i => words[i] ? [{
      index: i, text: words[i].Word, start: words[i].Offset / 1e7, end: (words[i].Offset + words[i].Duration) / 1e7,
      timebase: 'recording_global_seconds',
    }] : []);
    return {
      unit: unit.text, reading: unit.members.map(s => s.pinyin), grouped: unit.grouped,
      aligned_interval: [unit.start, unit.end], timing_source: unit.members.map(s => s.timing_source),
      provider_words: providerWords,
      chunk: chunk ? { text: chunk.text, interval: [chunk.start, chunk.end] } : null,
      source_sample_count: inSpan.length,
      raw_voiced_count: inSpan.filter(p => (p.tracker_f0_hz ?? p.f0_hz ?? 0) > 0).length,
      retained_in_aligned_span: inSpan.filter(p => p.retained).length,
      retained_count: points.length, owned_interval: interval(points), segment_count: segments.length,
      // Keep null tracker observations and rejection reasons: a missing gesture
      // must be distinguishable from valid F0 removed by selection or ownership.
      raw_samples: inSpan,
      removed_samples: inSpan.filter(p => !p.retained).map(p => ({ timestamp_seconds: p.timestamp_seconds,
        source_frame_index: p.source_frame_index, reasons: p.exclusion_reasons })),
      retained_segments: segments.map(s => s.map(p => sourceByTime.get(p.timestamp_seconds))),
      classification_input: segments,
      graph: { domain, segments: layout.segments.map((s, i) => s.map((p, j) => ({ ...p, ...coordinates[i][j] }))) },
      classification: { shape: shape.shape, shape_reason: shape.reason, family: tone.tone, family_reason: tone.reason },
    };
  });
  for (const t of sourceByTime.keys()) {
    assert.equal(ownedTimes.has(t), units.some(u => u.start <= t && t < u.end), 'Unexplained ownership gap');
  }
  const chunkReports = chunks.filter(c => c.timingStatus === 'timed').map(chunk => {
    const segments = chunkPitch(data, chunk, units).segments;
    const expected = chunk.constituents.flatMap(u => unitPitch(data, u, units).segments)
      .sort((a, b) => a[0].timestamp_seconds - b[0].timestamp_seconds);
    assert.equal(JSON.stringify(segments), JSON.stringify(expected), 'Chunk changed constituent ownership');
    return { text: chunk.text, interval: [chunk.start, chunk.end], retained_count: segments.flat().length,
      segments, constituents: chunk.constituents.map(u => u.text) };
  });
  assert.equal(JSON.stringify(input), before, 'Projection or classification mutated saved evidence');
  return { id: input.id ?? input.analysis?.id, boundary_policy: '[start, end), including final unit; later start wins accepted overlaps',
    timebase: 'recording_global_seconds; no rounding, padding or chunk offset added',
    global: { raw_count: raw.length, retained_count: sourceByTime.size,
      unowned_retained_timestamps: [...sourceByTime.keys()].filter(t => !ownedTimes.has(t)) },
    units: reports, chunks: chunkReports };
}
function summary(report) {
  return { ...report, units: report.units.map(({ raw_samples, removed_samples, retained_segments, classification_input, graph, ...unit }) => unit),
    chunks: report.chunks.map(({ segments, ...chunk }) => chunk) };
}
module.exports = { audit, summary };
if (require.main === module) {
  const files = process.argv.slice(2).filter(p => p !== '--summary');
  const input = files.length ? files.map(p => JSON.parse(fs.readFileSync(p))) : JSON.parse(fs.readFileSync(0, 'utf8'));
  const reports = (Array.isArray(input) ? input : [input]).map(audit);
  process.stdout.write(JSON.stringify(process.argv.includes('--summary') ? reports.map(summary) : reports, null, 2) + '\n');
}
