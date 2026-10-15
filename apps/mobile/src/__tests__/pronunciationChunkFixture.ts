import cases from './fixtures/pronunciationChunkCases.json';
import { perceivedAnalysis } from './perceivedFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';

type Data = PerceivedSpeechAnalysis['data'];
export function chunkCase(text: string) {
  return cases.find(c => c.text === text)! as unknown as {
    text: string; syllables: Data['syllables']; pronunciation_chunk_policy: string;
    pronunciation_chunk_candidates: NonNullable<Data['pronunciation_chunk_candidates']>;
  };
}
export function chunkAnalysis(text: string): PerceivedSpeechAnalysis {
  const fixture = chunkCase(text);
  const base = JSON.parse(JSON.stringify(perceivedAnalysis)) as PerceivedSpeechAnalysis;
  // Layout/projection-only timing, explicitly not a recorded physical take.
  return { ...base, alignment_reference_text: text, data: { ...base.data,
    ...fixture, duration_seconds: fixture.syllables.length * .4, timing_groups: [],
    syllables: fixture.syllables.map((s, i) => ({ ...s, start_seconds: i * .4, end_seconds: (i + 1) * .4 })),
  } };
}
export const physicalChunk = require('../../../../services/api/tests/fixtures/pitch_projection_89cee47e.json') as {
  data: Data;
  track: { evidence_id: string; frames: { timestamp_seconds: number; selected_f0_hz: number | null }[] };
};
export function physicalChunkAnalysis(): PerceivedSpeechAnalysis {
  const candidates = chunkCase('我想买这个');
  return { ...perceivedAnalysis, alignment_reference_text: candidates.text, data: { ...physicalChunk.data,
    pronunciation_chunk_policy: candidates.pronunciation_chunk_policy,
    pronunciation_chunk_candidates: candidates.pronunciation_chunk_candidates,
  } };
}
