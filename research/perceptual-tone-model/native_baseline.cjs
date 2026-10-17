// Research adapter to frozen acoustic functions; accepts saved acoustic evidence.
// Corpus examples without that evidence abstain. No synthetic F0 or target input.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { load } = require('../../benchmark/pronunciation_v2/tone_feedback.cjs');
const { verifyBaseline } = require('./evaluate.cjs');

function classify(row) {
  if (!row.segments) return { prediction: null, reason: 'missing_saved_benma_acoustics' };
  if (row.grouped) return { prediction: null, reason: 'grouped_timing' };
  const segments = row.segments.map(s => s.map(p => {
    assert(Number.isFinite(p.t) && Number.isFinite(p.st), 'Invalid saved acoustic point');
    return { timestamp_seconds: p.t, normalized_semitones: p.st };
  }));
  const flags = row.segments.flat().filter(p => row.flagged_indices?.includes(p.index)).map(p => p.t);
  const { classifyPitchShape } = load('@/speech/pitchShape');
  const { classifyToneLikeness } = load('@/speech/toneLikeness');
  const shape = classifyPitchShape(segments, flags, !!row.flagged_indices?.length);
  const observed = classifyToneLikeness(shape, segments);
  return {
    prediction: observed.decision === 'NUMBERED' ? observed.tone.replace('TONE_', 'T') : null,
    reason: observed.reason, family_decision: observed.decision,
    observed_family: observed.tone, support_not_probabilities: observed.fits,
    neutral_output_supported: false,
  };
}

module.exports = { classify };
if (require.main === module) {
  const [input, output] = process.argv.slice(2);
  assert(input && output && process.argv.length === 4, 'Usage: node native_baseline.cjs SAVED_ROWS.json OUTPUT.json');
  const baseline = verifyBaseline();
  const rows = JSON.parse(fs.readFileSync(input));
  const result = rows.map(row => ({ id: row.id, recording: row.recording, text: row.text,
    start: row.start, end: row.end, ...classify(row) }));
  fs.writeFileSync(output, JSON.stringify({ baseline, rows: result }, null, 2) + '\n', { flag: 'wx' });
}
