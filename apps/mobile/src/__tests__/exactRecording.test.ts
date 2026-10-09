import { canonicalWave } from './canonicalWave';

import { exactRecording } from '@/audio/exactRecording';
it.each([[.125, .25], [-.1, .1], [.9, 2], [0, 1], [.10001, .19001]])('plays exactly the clamped PCM window %s–%s without context', (start, end) => {
  const bytes = canonicalWave(), before = new Uint8Array(bytes), segment = exactRecording(bytes, start, end);
  const first = Math.max(0, Math.round(start * 16000)), last = Math.min(16000, Math.round(end * 16000));
  expect(segment.subarray(44)).toEqual(bytes.subarray(44 + first * 2, 44 + last * 2));
  expect(segment.length).toBe(44 + (last - first) * 2);
  expect(bytes).toEqual(before);
});
it.each([[1, 2], [0, 0], [.4, .2], [NaN, .5], [0, Infinity]])('rejects empty or invalid window %s–%s', (start, end) => {
  expect(() => exactRecording(canonicalWave(), start, end)).toThrow();
});
it('rejects malformed, truncated or noncanonical original audio instead of guessing timing', () => {
  const bytes = canonicalWave();
  expect(() => exactRecording(bytes.subarray(0, 100), 0, .1)).toThrow();
  new DataView(bytes.buffer).setUint32(24, 24000, true);
  expect(() => exactRecording(bytes, 0, .1)).toThrow();
});
