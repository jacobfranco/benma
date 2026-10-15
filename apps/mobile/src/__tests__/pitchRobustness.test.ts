import type { PerceivedSpeechAnalysis } from '@/api/types';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { pronunciationChunks } from '@/speech/pronunciationChunks';
import { unitShape } from '@/speech/pitchShapeEvidence';
import { classifyToneLikeness } from '@/speech/toneLikeness';

const physical = require('./fixtures/pitchRobustnessPhysical.json') as PerceivedSpeechAnalysis[];
const evaluate = (a: PerceivedSpeechAnalysis) => pronunciationChunks(a.data).map(c => gradeChunkPitch(a, c));
it('keeps newest human families, accepts confident shallow T3, and preserves the original primary fall', () => {
  const before = JSON.stringify(physical), chunks = evaluate(physical[1]!);
  const units = chunks.flatMap(c => c.constituents);
  expect(units.map(c => [c.observed.tone, c.observed.strength, c.grade.agreement])).toEqual([
    ['TONE_3', 'weak', 'STRONG_MATCH'], ['TONE_4', 'full', 'CLEAR_DIFFERENCE'],
    ['TONE_3', 'weak', 'STRONG_MATCH'], ['TONE_4', 'full', 'STRONG_MATCH'],
    ['UNCLEAR', 'unavailable', 'UNAVAILABLE'],
  ]);
  expect(units[0]!.observed.fits.TONE_3).toBeCloseTo(.8782118593, 8);
  expect(units[2]!.observed.fits.TONE_3).toBeCloseTo(.8218233405, 8);
  expect(units[3]!.pitch.segments.map(s => s.length)).toEqual([14]);
  expect(units[3]!.unit.members[0]!.pitch_eligibility?.state).toBe('sufficient');
  expect(units[4]!.role).toBe('neutral_unreliable_nonveto');
  expect(chunks[3]!.grade.agreement).toBe('STRONG_MATCH');
  const raw = physical[1]!.data.tone_graph!.raw!;
  const rejected = raw.filter(p => p.exclusion_reasons?.includes('candidate_supported_ambiguous_branch'));
  expect(rejected).toHaveLength(7);
  expect(rejected.every(p => p.tracker_f0_hz! > 0 && p.selected_f0_hz == null && !p.retained)).toBe(true);
  expect(raw.filter(p => p.retained).every(p => p.selected_f0_hz === p.tracker_f0_hz)).toBe(true);
  expect(JSON.stringify(physical)).toBe(before);
});
it('requires the explicit candidate certificate; other exclusions cannot retire a raw corruption veto', () => {
  for (const reason of ['low_frequency_contamination', 'persistent_background_periodicity', 'below_energy_gate', 'terminal_octave_ambiguity_no_supported_alternative']) {
    const a = JSON.parse(JSON.stringify(physical[1])) as PerceivedSpeechAnalysis;
    a.data.tone_graph!.raw!.forEach(p => {
      if (p.exclusion_reasons?.includes('candidate_supported_ambiguous_branch')) p.exclusion_reasons = [reason];
    });
    expect(evaluate(a)[3]!.grade.agreement).toBe('UNAVAILABLE');
  }
});
it('rejects washer branches without creating low/high families or positive neutral credit', () => {
  const chunks = evaluate(physical[0]!);
  expect(chunks.every(c => c.grade.agreement === 'UNAVAILABLE')).toBe(true);
  expect(chunks.flatMap(c => c.constituents).every(c => c.observed.decision === 'UNAVAILABLE')).toBe(true);
  expect(chunks[3]!.constituents[1]!.role).toBe('neutral_unreliable_nonveto');
});
it('keeps new physical families under deletion, timing perturbation, transposition and target changes', () => {
  for (const a of physical) {
    const baseline = evaluate(a);
    for (const u of baseline.flatMap(c => c.constituents)) {
      const p = u.pitch.segments.flat();
      for (const [probe, segments] of [u.pitch.segments.map(s => s.filter(q => q !== p[0])),
        u.pitch.segments.map(s => s.filter(q => q !== p.at(-1))),
        u.pitch.segments.map(s => s.filter((_, i) => i % 10 !== 9)),
        u.pitch.segments.map(s => s.map((q, i) => ({ ...q, timestamp_seconds: q.timestamp_seconds + (i % 2 ? .002 : 0) }))),
        ...[-24, 24].map(shift => u.pitch.segments.map(s => s.map(q => ({ ...q, normalized_semitones: q.normalized_semitones + shift }))))].entries()) {
        const result = classifyToneLikeness(unitShape(a.data, u.unit, segments), segments);
        if (a === physical[1] && u.unit.text === '这' && probe === 2) {
          // Removing another tenth point inside the classifier compounds this
          // external thinning. Keep the existing conservative structural veto.
          expect(result).toMatchObject({ decision: 'UNAVAILABLE', reason: 'unstable_measurement_support' });
        } else expect(result.tone).toBe(u.observed.tone);
      }
    }
    const changed = JSON.parse(JSON.stringify(a)) as PerceivedSpeechAnalysis;
    changed.data.syllables.forEach(s => { s.characters = '字'; s.lexical_tone = 1; s.expected_surface_tone = 4; });
    expect(evaluate(changed).flatMap(c => c.constituents).map(c => c.observed))
      .toEqual(baseline.flatMap(c => c.constituents).map(c => c.observed));
  }
});
