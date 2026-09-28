import acceptance from './fixtures/learnerAcceptance.json';
import architectureAcceptance from './fixtures/architectureAcceptance.json';

import type { ObservedContour } from '@/api/types';
import { learnerVerdict } from '@/speech/learnerVerdict';
import { normalizedDisplayContour } from '@/speech/normalizedDisplayContour';
import { contourGeometry } from '@/components/PitchPlot';
import { primaryMineContour } from '@/speech/SyllableComparison';

const observed: ObservedContour = { classification: '1-like', confidence: 'moderate', reason: 'acoustic_shape_only',
  features: { contaminated_fraction: 0, discontinuous_gap_count: 0, tracker_instability_rejected: 0 } };
it.each([1,2,3,4])('matches Tone %s with moderate evidence', tone => {
  expect(learnerVerdict(tone, { ...observed, classification: `${tone}-like` as NonNullable<ObservedContour['classification']> })).toBe('matches');
});
it('reserves different for trustworthy conflicts, close for weak agreement', () => {
  expect(learnerVerdict(2, { ...observed, classification: '4-like', confidence: 'high' })).toBe('different');
  expect(learnerVerdict(2, { ...observed, classification: '4-like', confidence: 'low' })).toBe('unclear');
  expect(learnerVerdict(1, { ...observed, confidence: 'low' })).toBe('close');
  expect(learnerVerdict(3, { ...observed, reason: 'tracker_instability' })).toBe('unclear');
  expect(learnerVerdict(0, { ...observed, classification: '2-like' })).toBe('unclear');
});
it.each(acceptance)('replays persisted $text target and classification', row => {
  expect(row.target_id).toBe(row.attempt_target_id);
  expect(learnerVerdict(row.expected, row.observed as ObservedContour)).toBe(row.expected === 0 ? 'unclear' : 'matches');
});
const cases = [
  ['level', [0,.1,0,.1,0]], ['rise', [-2,-1,0,1,2]], ['dip', [2,0,-2,0,2]],
  ['fall', [2,1,0,-1,-2]], ['jitter level', [0,.2,-.1,.2,0]], ['jitter rise', [-2,-.8,-1,1,2]],
  ['weak rise', [0,.1,.2,.3,.4]], ['shallow fall', [.4,.3,.2,.1,0]],
] as const;
it.each(cases)('normalizes %s without changing evidence or verdict', (_, values) => {
  for (const padding of [.05, 2]) {
    const display = { segments: [values.map((v,i) => ({ timestamp_seconds: padding+i*.01, normalized_semitones: v }))] };
    const before = JSON.stringify({ display, observed });
    const normalized = normalizedDisplayContour(display, observed)!;
    const geometry = contourGeometry(normalized.segments!, 100, 40, [-4,4], 0, 8, true);
    expect(geometry[0]![0]!.x).toBe(0); expect(geometry[0]!.at(-1)!.x).toBe(100);
    const cleaned = normalized.segments![0]!;
    expect(cleaned.at(-1)!.normalized_semitones-cleaned[0]!.normalized_semitones).toBeCloseTo(values.at(-1)!-values[0]!);
    expect(normalized.maximum_semitones).toBe(4);
    expect(JSON.stringify({ display, observed })).toBe(before);
    expect(learnerVerdict(1, observed)).toBe('matches');
  }
});
it('bridges only bounded coherent gaps with safe endpoints', () => {
  const make = (gap: number, jump = 0) => ({ segments: [
    [{ timestamp_seconds: .2, normalized_semitones: 0 }, { timestamp_seconds: .21, normalized_semitones: .1 }],
    [{ timestamp_seconds: .21+gap, normalized_semitones: .1+jump }, { timestamp_seconds: .22+gap, normalized_semitones: .2+jump }],
  ] });
  expect(normalizedDisplayContour(make(.04), observed)!.segments).toHaveLength(1);
  expect(normalizedDisplayContour(make(.2), observed)!.segments).toHaveLength(2);
  expect(normalizedDisplayContour(make(.04, 3), observed)!.segments).toHaveLength(2);
  expect(normalizedDisplayContour(make(.04), { ...observed, confidence: 'low' })!.segments).toHaveLength(2);
  expect(normalizedDisplayContour(make(.04), { ...observed, features: {} })!.segments).toHaveLength(2);
});

it('shows only the selected evidence while preserving raw/full display and verdict', () => {
  const display = { segments: [[0,1,2,3,4].map(i => ({ timestamp_seconds: i*.1, normalized_semitones: i === 0 ? -12 : 0 }))] };
  const measured = { ...observed, features: { ...observed.features, evidence_region_selected: 1,
    evidence_start_seconds: .1, evidence_end_seconds: .4, whole_span_tracker_instability_rejected: 1 } };
  const snapshot = JSON.stringify({ display, measured });
  expect(primaryMineContour({ display_contour: display, observed_contour: measured })!.segments![0]!.map(p => p.timestamp_seconds)).toEqual([.1,.2,.30000000000000004]);
  expect(learnerVerdict(1, measured)).toBe('matches');
  expect(JSON.stringify({ display, measured })).toBe(snapshot);
});

it('recomputes the four newest persisted phone verdicts without provider scores', () => {
  const expected: Record<string, string> = { '妈': 'matches', '马': 'unclear', '骂': 'unclear', '嘛': 'unclear' };
  for (const result of architectureAcceptance) {
    const syllable = result.syllables[0]!;
    expect(learnerVerdict(syllable.expected_surface_tone, syllable.observed_contour as ObservedContour)).toBe(expected[result.target.text]);
    expect(result.assessment.normalized_result.pronunciation_score).toBe(79);
  }
  const measured = architectureAcceptance.find(r => r.target.text === '妈')!.syllables[0]!.observed_contour as ObservedContour;
  const snapshot = JSON.stringify(measured);
  expect(learnerVerdict(1, measured)).toBe('matches');
  for (const tone of [2,3,4]) expect(learnerVerdict(tone, measured)).toBe('different');
  expect(JSON.stringify(measured)).toBe(snapshot);
});
