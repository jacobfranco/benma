import fixtures from './fixtures/consistencyAcceptance.json';

import type { DisplayContour, ObservedContour } from '@/api/types';
import { contourGeometry } from '@/components/PitchPlot';
import { learnerGestureContour, LEARNER_GESTURE_METHOD } from '@/speech/learnerGestureContour';
import { learnerVerdict } from '@/speech/learnerVerdict';
import { normalizedDisplayContour } from '@/speech/normalizedDisplayContour';
import { primaryMineContour } from '@/speech/SyllableComparison';

const display: DisplayContour = { segments: [[0, 3, -3, 0].map((v,i) => ({ timestamp_seconds: i*.1, normalized_semitones: v }))] };
function observed(bins: number[]): ObservedContour {
  return { classification: '1-like', confidence: 'moderate', reason: 'acoustic_shape_only', features: {
    gap_count: 0, ...Object.fromEntries(bins.flatMap((v,i) => [[`bin_${i+1}_st`,v],[`bin_${i+1}_seconds`,i*.05]])),
  } };
}
const values = (d: DisplayContour) => d.segments!.flat().map(p=>p.normalized_semitones);
it.each([
  ['level', [0,.1,0,-.1,0]], ['rise', [-2,-1,0,1,2]], ['valley', [1,0,-1,0,1]],
  ['fall', [2,1,0,-1,-2]], ['weak rise', [0,.1,.2,.3,.4]],
])('preserves exact %s bin amplitude and geometry without local excursions', (_, bins) => {
  const o=observed(bins as number[]), snapshot=JSON.stringify({display,o});
  const gesture=learnerGestureContour(display,o)!;
  expect(values(gesture)).toEqual(bins);
  const normalized=normalizedDisplayContour(gesture,o)!;
  expect(Math.max(...values(normalized))-Math.min(...values(normalized))).toBeCloseTo(Math.max(...bins as number[])-Math.min(...bins as number[]));
  expect(normalized.maximum_semitones).toBe(4);
  for (const tone of [1,2,3,4]) {
    const syllable={display_contour:display,observed_contour:o,expected_surface_tone:tone};
    expect(primaryMineContour(syllable)).toEqual(gesture);
    const verdict=learnerVerdict(tone,o);
    for (const width of [52,520]) contourGeometry(normalized.segments!,width,38,[-4,4],0,1,true);
    expect(learnerVerdict(tone,o)).toBe(verdict);
  }
  expect(JSON.stringify({display,o})).toBe(snapshot);
  expect(values(display)).toContain(3); expect(values(display)).toContain(-3);
});
it('uses the actual stable core medians, never ordinary bins for the onset hypothesis',()=>{
  const row=fixtures.find(r=>r.target==='天')!;
  const o=row.observed as ObservedContour;
  const gesture=learnerGestureContour(row.display,o)!;
  expect(values(gesture)).toEqual([1,2,3,4,5].map(i=>o.features![`core_bin_${i}_st`]));
  expect(learnerVerdict(1,o)).toBe('close');
});
it('replays fresh level wiggle and keeps every detail excursion',()=>{
  const row=fixtures.find(r=>r.target==='妈')!, o=row.observed as ObservedContour;
  const before=JSON.stringify(row), gesture=primaryMineContour({display_contour:row.display,observed_contour:o})!;
  expect(gesture.method).toBe(LEARNER_GESTURE_METHOD);
  expect(Math.max(...values(gesture))-Math.min(...values(gesture))).toBeCloseTo(1.4543,4);
  expect(Math.max(...values(row.full))-Math.min(...values(row.full))).toBeGreaterThan(5);
  expect(row.full.segments.flat()).toHaveLength(58);
  expect(learnerVerdict(1,o)).toBe('matches');
  expect(JSON.stringify(row)).toBe(before);
});
it('bridges only the certified low-confidence short gap; details remain segmented',()=>{
  const row=fixtures.find(r=>r.observed.reason==='coherent_short_gap')!;
  const o=row.observed as ObservedContour, before=JSON.stringify(row);
  expect(learnerGestureContour(row.display,o)!.segments).toHaveLength(1);
  expect(normalizedDisplayContour(row.display,o)!.segments).toHaveLength(1);
  expect(row.full.segments).toHaveLength(2);
  expect(JSON.stringify(row)).toBe(before);
  for (const fault of ['certificate','reason','long','contradiction','extra','contamination']) {
    const d=JSON.parse(JSON.stringify(row.display)) as DisplayContour;
    const bad=JSON.parse(JSON.stringify(o)) as ObservedContour;
    if(fault==='certificate') bad.features!.coherent_short_gap=0;
    if(fault==='reason') bad.reason='fragmented_voicing';
    if(fault==='long') {bad.features!.longest_gap_seconds=.2;d.segments![1]!.forEach(p=>p.timestamp_seconds+=.2);}
    if(fault==='contradiction') d.segments![1]!.forEach((p,i)=>p.normalized_semitones=i*2);
    if(fault==='extra') bad.features!.gap_count=2;
    if(fault==='contamination') bad.features!.contaminated_fraction=.2;
    expect(learnerGestureContour(d,bad)).toBe(d);
    expect(normalizedDisplayContour(d,bad)!.segments).toHaveLength(2);
  }
});
it('fails back to measured data for legacy/missing summaries',()=>{
  const o=observed([0,1,2,3,4]); delete o.features!.bin_3_seconds;
  expect(learnerGestureContour(display,o)).toBe(display);
});
