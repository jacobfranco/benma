import { pitchDots, pitchSegments } from '@/components/PitchPlot';

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
