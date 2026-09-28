import rows from './fixtures/finalNarrowAcceptance.json';

import type { ObservedContour } from '@/api/types';
import { learnerVerdict } from '@/speech/learnerVerdict';

it.each(rows)('derives the existing verdict semantics for persisted $target', row => {
  const observed = row.observed as ObservedContour;
  const before = JSON.stringify(observed);
  expect(learnerVerdict(row.expected, observed)).toBe(row.verdict);
  if (observed.confidence === 'low') {
    expect(learnerVerdict(2, observed)).toBe('unclear');
    expect(learnerVerdict(0, observed)).toBe('unclear');
  }
  expect(JSON.stringify(observed)).toBe(before);
});
it('requires the acoustic certificate before accepting a discontinuous gap', () => {
  const observed = rows.find(row => row.target === '骂')!.observed as ObservedContour;
  for (const changed of [
    { ...observed, reason: 'acoustic_shape_only' },
    { ...observed, features: { ...observed.features, coherent_short_gap: 0 } },
    { ...observed, features: { ...observed.features, gap_count: 2 } },
    { ...observed, features: { ...observed.features, contaminated_fraction: .2 } },
    { ...observed, features: { ...observed.features, tracker_instability_rejected: 1 } },
  ]) expect(learnerVerdict(4, changed)).toBe('unclear');
});
