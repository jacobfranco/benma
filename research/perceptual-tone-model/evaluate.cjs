// Offline baseline adapter. Executes existing production functions; no new policy.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const { load, replay } = require('../../benchmark/pronunciation_v2/tone_feedback.cjs');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const read = p => JSON.parse(fs.readFileSync(path.resolve(root, p), 'utf8'));
const json = x => JSON.parse(JSON.stringify(x));
const manifestPath = path.join(__dirname, 'baseline-manifest.json');
function verifyBaseline() {
  const manifest = JSON.parse(fs.readFileSync(manifestPath));
  for (const [file, expected] of Object.entries(manifest.files))
    assert.equal(sha(fs.readFileSync(path.join(root, file))), expected, `Frozen baseline changed: ${file}`);
  return sha(fs.readFileSync(manifestPath));
}
const Ajv = require(path.join(root, 'apps/mobile/node_modules/ajv'));
const validate = new Ajv({ allErrors: true }).compile(read('research/perceptual-tone-model/dataset.schema.json'));
function evaluate(examples, baselineId) {
  const { learnerPitchEvidence, pitchGradePresentation } = load('@/speech/learnerPitchGrade');
  const seen = new Set(), sources = new Map(), speakers = new Map(), recordings = new Map();
  return examples.map(example => {
    assert(validate(example), JSON.stringify(validate.errors));
    assert(!seen.has(example.example_id), `Duplicate example_id: ${example.example_id}`);
    seen.add(example.example_id);
    if (['train', 'validation', 'test'].includes(example.partition)) {
      const previous = speakers.get(example.speaker_id);
      assert(!previous || previous === example.partition, 'Speaker leakage across partitions');
      speakers.set(example.speaker_id, example.partition);
    }
    const owner = recordings.get(example.audio.sha256);
    assert(owner === undefined || owner === example.speaker_id, 'Recording has inconsistent speaker identity');
    recordings.set(example.audio.sha256, example.speaker_id);
    const { source, target } = example;
    assert(target.start_seconds < target.end_seconds, 'Invalid target span');
    assert(example.context_window.start_seconds <= target.start_seconds &&
      example.context_window.end_seconds >= target.end_seconds, 'Context must contain target');
    const annotators = example.annotations.map(a => a.annotator_id);
    assert.equal(new Set(annotators).size, annotators.length, 'Duplicate annotator; preserve revisions separately');
    for (const [label, count] of Object.entries(example.disagreement.counts))
      assert.equal(example.annotations.filter(a => a.acceptability === label).length, count, 'Judgment counts differ');
    assert.equal(example.disagreement.status === 'unlabeled', annotators.length === 0, 'Invalid annotation status');
    if (!sources.has(source.path)) {
      const bytes = fs.readFileSync(path.resolve(root, source.path));
      sources.set(source.path, { value: JSON.parse(bytes), hash: sha(bytes) });
    }
    const saved = sources.get(source.path);
    assert.equal(saved.hash, source.sha256, 'Analysis source hash mismatch');
    let result, chunk = null, segments, eligibility, projection, syllable;
    if (source.kind === 'historical_row') {
      // Preserve the old 53-unit adapter, including its saved contextual fields.
      // Do not silently enrich context or split its grouped timing during freeze.
      const row = saved.value.find(r => r.id === source.row_id);
      assert(row, 'Missing historical row');
      assert.equal(row.recording, example.recording_id);
      const recording = read('docs/research/pronunciation-v2/2026-10-08-gesture-readability/projection-replay.json')
        .find(r => r.recording === row.recording);
      const unit = recording.units.find(u => u.text === row.text && u.start === row.start && u.end === row.end);
      assert.equal(recording.transcript, example.utterance);
      assert.equal(recording.utterance_id, example.utterance_id);
      assert.equal(recording.audio_sha256, example.audio.sha256);
      assert.deepEqual(unit.members, target.syllable_indices);
      assert.equal(unit.members[0], target.syllable_index);
      const context = read('docs/research/pronunciation-v2/2026-10-09-product-feedback/expected-context.json').units;
      result = replay({ rows: [row], context }).rows[0];
      syllable = context[row.id];
      assert.equal(row.text, target.syllable);
      assert.equal(row.start, target.start_seconds); assert.equal(row.end, target.end_seconds);
      assert.equal(row.grouped, target.unit_kind === 'timing_group');
      segments = row.segments;
      eligibility = row.eligibility;
      projection = { selected_frame_indices: segments.flat().map(p => p.index) };
    } else {
      const analysis = Array.isArray(saved.value)
        ? saved.value.find(a => a.id === source.analysis_id) : saved.value;
      assert(analysis && analysis.id === source.analysis_id, 'Missing analysis_id');
      assert.equal(analysis.utterance_id, example.utterance_id, 'Wrong recording analysis');
      assert.equal(analysis.alignment_reference_text, example.utterance);
      const before = JSON.stringify(analysis);
      const output = replay({ analyses: [analysis] }).analyses[0];
      const hits = output.chunks.flatMap(c => c.constituents.filter(u =>
        u.unit.members.some(s => s.index === target.syllable_index)).map(u => ({ c, u })));
      assert.equal(hits.length, 1, 'Target must resolve to one owned unit');
      result = hits[0].u;
      chunk = { text: hits[0].c.text, grade: hits[0].c.grade,
        color: pitchGradePresentation[hits[0].c.grade.agreement].color,
        constituent_role: result.role };
      assert.equal(result.unit.grouped, target.unit_kind === 'timing_group');
      assert.equal(result.unit.text, target.syllable);
      assert.deepEqual(json(result.unit.members.map(s => s.index)), target.syllable_indices);
      assert.equal(result.unit.members[0].index, target.syllable_index);
      assert.equal(result.unit.start, target.start_seconds); assert.equal(result.unit.end, target.end_seconds);
      syllable = result.unit.members[0];
      segments = result.pitch.segments;
      eligibility = syllable.pitch_eligibility ?? null;
      projection = syllable.pitch_projection ?? null;
      assert.equal(JSON.stringify(analysis), before, 'Replay mutated saved analysis');
    }
    assert.equal(syllable.lexical_tone ?? null, example.expected.lexical_tone);
    assert.equal(syllable.expected_surface_tone ?? null, example.expected.surface_tone);
    const evidence = learnerPitchEvidence(result.observed, result.expected);
    assert.deepEqual(json(evidence.acceptable), example.expected.acceptable_families);
    const b = {
      baseline_id: baselineId, evidence_reliability: result.observed.evidence,
      eligibility, structural_reliability: result.shape.structurallyUsable ?? null,
      observed_family: result.observed.tone, family_decision: result.observed.decision,
      family_scores: result.observed.fits, winner: evidence.winner,
      winner_support: evidence.support, runner_up: result.observed.runnerUp,
      runner_up_support: evidence.runnerUpSupport, acceptable_support: evidence.acceptableSupport,
      margins: { acoustic: result.observed.margin, acceptable: evidence.acceptableMargin,
        runner_up: evidence.runnerUpMargin }, clarity: evidence.clarity,
      probe_agreement: { agreeing: evidence.probeAgreement, total: evidence.probeCount,
        fraction: evidence.consensus, probes: result.observed.perturbations ?? {} },
      gesture_strength: result.observed.strength, learner_grade: result.grade,
      color: pitchGradePresentation[result.grade.agreement].color,
      coaching_message: result.grade.coaching, chunk,
      resolved_expectation: result.expected, shape: result.shape, acoustic: result.observed,
      duration_seconds: target.end_seconds - target.start_seconds,
      normalized_f0_segments: segments, projection,
    };
    const out = json({ ...example, deterministic: b });
    assert(validate(out), JSON.stringify(validate.errors));
    return out;
  });
}
module.exports = { evaluate, verifyBaseline, sha };
if (require.main === module) {
  const [input, output] = process.argv.slice(2);
  assert(input && output && process.argv.length === 4,
    'Usage: node research/perceptual-tone-model/evaluate.cjs INPUT.jsonl OUTPUT.jsonl');
  const baselineId = verifyBaseline();
  const examples = fs.readFileSync(input, 'utf8').split('\n').filter(s => s.trim()).map(s => JSON.parse(s));
  const rows = evaluate(examples, baselineId);
  // Refuse overwrite, including input/production evidence or checkpoint results.
  fs.writeFileSync(output, rows.map(r => JSON.stringify(r)).join('\n') + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ examples: rows.length, baseline_id: baselineId, output }));
}
