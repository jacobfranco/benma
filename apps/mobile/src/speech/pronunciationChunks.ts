import type { PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import { defaultUnit, pronunciationUnits, unitPitch, workspacePitch, type PronunciationUnit } from '@/speech/pronunciationWorkspace';
import { PAUSE_SECONDS } from '@/speech/sentenceToneGraph';

type Data = PerceivedSpeechAnalysis['data'];
type Candidate = NonNullable<Data['pronunciation_chunk_candidates']>[number];
export interface PronunciationChunk {
  id: string;
  text: string;
  members: PerceivedSyllable[];
  constituents: PronunciationUnit[];
  constituentUnitIds: string[];
  characterIndices: number[];
  reason: Candidate['reason'] | 'single_unit' | 'existing_timing_group' | 'untimed';
  linguisticReason?: Candidate['reason'];
  timingStatus: 'timed' | 'unavailable';
  start: number | null;
  end: number | null;
}
export type TimedPronunciationChunk = PronunciationChunk & { timingStatus: 'timed'; start: number; end: number };
export function isTimedChunk(chunk: PronunciationChunk): chunk is TimedPronunciationChunk {
  return chunk.timingStatus === 'timed' && chunk.start !== null && chunk.end !== null;
}

function makeChunk(members: PerceivedSyllable[], constituents: PronunciationUnit[], reason: PronunciationChunk['reason']): PronunciationChunk {
  const first = members[0]!, last = members.at(-1)!;
  const constituentUnitIds = constituents.map(u => u.id);
  return {
    id: `chunk:${JSON.stringify(constituentUnitIds.length ? constituentUnitIds : [`untimed:${first.index}:${first.character_start}:${last.character_end}`])}`,
    text: members.map(s => s.characters).join(''), members, constituents, constituentUnitIds,
    characterIndices: members.flatMap(s => Array.from({ length: s.character_end - s.character_start }, (_, i) => s.character_start + i)),
    reason, timingStatus: constituents.length ? 'timed' : 'unavailable',
    start: constituents[0]?.start ?? null, end: constituents.at(-1)?.end ?? null,
  };
}

// Partition identity first. A saved timing group is indivisible even when there
// is no linguistic candidate. Untimed syllables remain readable singleton chunks.
export function pronunciationChunks(data: Data, units = pronunciationUnits(data)): PronunciationChunk[] {
  const atoms = data.syllables.flatMap(s => {
    const unit = units.find(u => u.members.includes(s));
    if (unit && unit.members[0] !== s) return [];
    return [makeChunk(unit?.members ?? [s], unit ? [unit] : [],
      unit ? unit.grouped ? 'existing_timing_group' : 'single_unit' : 'untimed')];
  });
  // Older servers stay at truthful singletons/groups. Unknown future policies
  // cannot silently widen V1. Mandarin rules live only in the API.
  const candidates = data.pronunciation_chunk_policy === 'perceived-pronunciation-chunks-v1'
    ? data.pronunciation_chunk_candidates ?? [] : [];
  const result: PronunciationChunk[] = [];
  for (let i = 0; i < atoms.length;) {
    const atom = atoms[i]!;
    const candidate = candidates.find(c => c.character_start === atom.members[0]!.character_start);
    const parts: PronunciationChunk[] = [];
    if (candidate) {
      for (let j = i; j < atoms.length && atoms[j]!.members[0]!.character_start < candidate.character_end; j++) parts.push(atoms[j]!);
    }
    const members = parts.flatMap(p => p.members), constituents = parts.flatMap(p => p.constituents);
    const exact = candidate && candidate.character_end - candidate.character_start === 2 && members.length === 2 &&
      members.at(-1)?.character_end === candidate.character_end &&
      members.map(s => s.characters).join('') === candidate.text &&
      candidate.syllable_indices.length === members.length &&
      members.every((s, j) => s.index === candidate.syllable_indices[j] &&
        s.character_start === candidate.character_start + j && s.character_end === s.character_start + 1);
    const completeTiming = parts.length > 0 && parts.every(isTimedChunk) && constituents.every((unit, j) => {
      const previous = constituents[j - 1];
      // Reuse the production visible-pause marker (including its FP tolerance)
      // only to veto a merge. Reject reversed timing; never repair boundaries.
      return !previous || (unit.start >= previous.start && unit.end >= previous.end &&
        unit.start - previous.end + 1e-9 < PAUSE_SECONDS);
    });
    if (exact && completeTiming) {
      const chunk = makeChunk(members, constituents, constituents.length === 1 && constituents[0]!.grouped
        ? 'existing_timing_group' : candidate.reason);
      chunk.linguisticReason = candidate.reason;
      result.push(chunk);
      i += parts.length;
    } else { result.push(atom); i++; }
  }
  return result;
}

export function defaultChunk(chunks: PronunciationChunk[]): string | null {
  const unitId = defaultUnit(chunks.flatMap(c => c.constituents));
  return chunks.find(c => c.constituentUnitIds.includes(unitId ?? ''))?.id ?? null;
}

export function chunkReading(chunk: Pick<PronunciationChunk, 'members'>): string {
  return chunk.members.every(s => s.reading_source !== 'unresolved' && s.pinyin)
    ? chunk.members.map(s => s.pinyin).join('')
    : chunk.members.map(s => s.reading_source !== 'unresolved' && s.pinyin ? s.pinyin : 'Reading unresolved').join(' · ');
}

export function chunkEvidence(data: Data, chunk: PronunciationChunk, units = pronunciationUnits(data)) {
  return chunk.constituents.map(unit => {
    const pitch = unitPitch(data, unit, units);
    return { unit, pitch, hasPitch: pitch.segments.some(s => s.length > 0) };
  });
}

export function chunkPitch(data: Data, chunk: PronunciationChunk, units = pronunciationUnits(data)) {
  // Union existing ownership projections, never crop a new acoustic region.
  // Keeping constituent/source segments separate prevents bridging every gap,
  // including a touching boundary. Point objects and attempt scale are retained.
  const segments = chunkEvidence(data, chunk, units).flatMap(e => e.pitch.segments)
    .sort((a, b) => a[0]!.timestamp_seconds - b[0]!.timestamp_seconds);
  return { ...workspacePitch(data), segments };
}
