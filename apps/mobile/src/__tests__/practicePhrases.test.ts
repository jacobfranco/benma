import { choosePracticePhrase, practicePhrases } from '@/speech/practicePhrases';

it('keeps a reviewable, unique bank of short phrases', () => {
  expect(practicePhrases.length).toBe(60);
  expect(new Set(practicePhrases).size).toBe(practicePhrases.length);
  expect(practicePhrases.every(phrase => phrase.length >= 3 && phrase.length <= 12)).toBe(true);
});

it('uses injected randomness and avoids the previous choice without retries', () => {
  const random = jest.fn().mockReturnValue(0);
  expect(choosePracticePhrase(undefined, random)).toBe(practicePhrases[0]);
  expect(choosePracticePhrase(practicePhrases[0], random)).toBe(practicePhrases[1]);
  expect(choosePracticePhrase(undefined, () => 0.9999)).toBe(practicePhrases.at(-1));
  expect(random).toHaveBeenCalledTimes(2);
});
