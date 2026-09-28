import { contourGeometry, pitchDots, pitchSegments } from '@/components/PitchPlot';
import { primaryMineContour, unclearContourLabel } from '@/speech/SyllableComparison';

describe('pitch plot geometry', () => {
  it('omits unvoiced points instead of drawing a fake contour', () => {
    const dots = pitchDots(
      [
        { timestamp_seconds: 0, normalized_semitones: -2, voicing_probability: 0.8 },
        { timestamp_seconds: 0.1, normalized_semitones: null, voicing_probability: 0.1 },
        { timestamp_seconds: 0.2, normalized_semitones: 3, voicing_probability: 0.9 },
      ],
      200,
      100,
    );
    expect(dots).toHaveLength(2);
    expect(dots[0]?.x).toBe(0);
    expect(dots[1]?.x).toBe(200);
    expect(dots[1]!.y).toBeLessThan(dots[0]!.y);
  });

  it('returns no geometry for wholly uncertain pitch evidence', () => {
    expect(
      pitchDots([{ timestamp_seconds: 0.1, normalized_semitones: null }], 200, 100),
    ).toEqual([]);
  });
});

it('groups continuous samples into lines and keeps explicit and temporal gaps', () => {
  const points = [0, .01, .02, .25, .26].map(t => ({ timestamp_seconds: t, normalized_semitones: t }));
  expect(pitchSegments(points).map((s: unknown[]) => s.length)).toEqual([3, 2]);
  const withGap = [points[0]!, { timestamp_seconds: .005, normalized_semitones: null }, points[1]!];
  expect(pitchSegments(withGap).map((s: unknown[]) => s.length)).toEqual([1, 1]);
});

it('fits the usable syllable contour across its chart without changing timestamps or bridging gaps', () => {
  const segments = [[{ timestamp_seconds: .6, normalized_semitones: 0 },
    { timestamp_seconds: .7, normalized_semitones: 1 }],
  [{ timestamp_seconds: .9, normalized_semitones: 2 }, { timestamp_seconds: 1, normalized_semitones: 3 }]];
  const original = JSON.stringify(segments);
  const fitted = contourGeometry(segments, 100, 40, [-3, 4], 0, 1.5, true);
  expect(fitted).toHaveLength(2);
  expect(fitted[0]![0]!.x).toBe(0);
  expect(fitted[1]![1]!.x).toBe(100);
  expect(fitted[1]![0]!.x - fitted[0]![1]!.x).toBeCloseTo(50);
  expect(JSON.stringify(segments)).toBe(original);
  expect(contourGeometry(segments, 100, 40, [-3, 4], 0, 1.5)[0]![0]!.x).toBe(40);
});

it('keeps empty and single-point fitted contours finite', () => {
  expect(contourGeometry([], 100, 40, [-3, 3], 0, 1, true)).toEqual([]);
  expect(contourGeometry([[{ timestamp_seconds: .5, normalized_semitones: 0 }]], 100, 40, [-3, 3], 0, 1, true)[0]![0]!.x).toBe(0);
});

it.each([
  ['insufficient_voicing', 'Not enough clear voice'],
  ['tracker_instability', 'Pitch tracking was unstable'],
  ['ambiguous_shape', 'Shape was ambiguous'],
  ['low_frequency_contamination', 'Background sound interfered'],
])('explains unclear evidence for %s', (reason, label) => {
  expect(unclearContourLabel(reason)).toBe(label);
});


it('uses the classifier core, preserves gaps and timestamps, and fills the chart width', () => {
  const display = { segments: [[{ timestamp_seconds: .6, normalized_semitones: 3 },
    { timestamp_seconds: .63, normalized_semitones: 0 }, { timestamp_seconds: .7, normalized_semitones: .1 }],
  [{ timestamp_seconds: .8, normalized_semitones: 0 }, { timestamp_seconds: .9, normalized_semitones: -.1 }]] };
  const observed = { classification: '1-like' as const, reason: 'sustained_level_after_onset',
    features: { first_reliable_core_seconds: .63, last_reliable_core_seconds: .9 } };
  const before = JSON.stringify(display);
  const primary = primaryMineContour({ display_contour: display, observed_contour: observed })!;
  expect(primary.segments!.map(s => s.length)).toEqual([2, 2]);
  expect(primary.segments![0]![0]!.timestamp_seconds).toBe(.63);
  const geometry = contourGeometry(primary.segments!, 100, 40, [-3, 3], .5, 1, true);
  expect(geometry[0]![0]!.x).toBe(0);
  expect(geometry[1]![1]!.x).toBe(100);
  expect(JSON.stringify(display)).toBe(before);
  expect(primaryMineContour({ display_contour: display, observed_contour: { ...observed,
    reason: 'acoustic_shape_only' } })).toBe(display);
  expect(primaryMineContour({ display_contour: display, observed_contour: { ...observed,
    classification: 'unclear' } })).toBe(display);
});
