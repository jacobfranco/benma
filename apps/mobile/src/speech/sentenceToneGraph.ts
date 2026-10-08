import type { PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import type { PitchPoint, PitchXLayout } from '@/components/PitchPlot';

type Data = PerceivedSpeechAnalysis['data'];
export function hasTiming(s: PerceivedSyllable): s is PerceivedSyllable & { start_seconds: number; end_seconds: number } {
  return Number.isFinite(s.start_seconds) && Number.isFinite(s.end_seconds) && s.start_seconds! >= 0 && s.end_seconds! > s.start_seconds!;
}
export const toneName = (tone: number) => tone === 0 ? 'Neutral' : `T${tone}`;
export function toneReference(s: PerceivedSyllable) {
  if (s.reading_source === 'unresolved' || !s.pinyin || s.lexical_tone == null) {
    return { label: '?', lexicalFallback: false, description: 'Reading unresolved' };
  }
  if (s.expected_surface_tone != null) {
    return { label: s.expected_surface_tone === 0 ? 'N' : toneName(s.expected_surface_tone), lexicalFallback: false,
      description: `Reference tone: ${toneName(s.expected_surface_tone)}` };
  }
  return { label: `${toneName(s.lexical_tone)}*`, lexicalFallback: true,
    description: `Lexical ${toneName(s.lexical_tone)} · contextual realization unresolved` };
}
export const expectedLabel = (s: PerceivedSyllable) => toneReference(s).description;
type TimedSyllable = PerceivedSyllable & { start_seconds: number; end_seconds: number };
function sampleOwner(timed: TimedSyllable[], timestamp: number): TimedSyllable | undefined {
  // The timing validator tolerates up to 1 ms overlap. In that case the later
  // start owns the sample; equal starts break ties by perceived index. No retiming.
  let owner: TimedSyllable | undefined;
  for (const unit of timed) {
    if (unit.start_seconds <= timestamp && timestamp < unit.end_seconds &&
        (!owner || unit.start_seconds > owner.start_seconds ||
          unit.start_seconds === owner.start_seconds && unit.index > owner.index)) owner = unit;
  }
  return owner;
}
export function pitchSignal(data: Data, start = 0, end = data.duration_seconds, unitIndex?: number): string {
  const timed = data.syllables.filter(hasTiming);
  const unit = timed.find(s => s.index === unitIndex);
  const frames = data.tone_graph?.raw.filter(p => p.timestamp_seconds >= start && p.timestamp_seconds < end &&
    (!unit || sampleOwner(timed, p.timestamp_seconds) === unit));
  if (!frames) return 'Pitch signal: Unavailable';
  const retained = frames.filter(p => p.retained).length;
  // Descriptive display flags only; these never select/reject F0 or grade a tone.
  if (retained < 5) return 'Pitch signal: Not enough';
  return retained / frames.length >= .8 ? 'Pitch signal: Clear' : 'Pitch signal: Limited';
}

// Backend groups carry exact source offsets and whole-word timing only.
export function timingGroups(data: Data) {
  if (data.alignment_status === 'synthetic') return [];
  return (data.timing_groups ?? []).filter(g => {
    const members = data.syllables.filter(s => s.character_start >= g.character_start && s.character_end <= g.character_end);
    return Number.isFinite(g.start_seconds) && Number.isFinite(g.end_seconds) && g.start_seconds >= 0 &&
      g.end_seconds > g.start_seconds && g.end_seconds <= data.duration_seconds && members.length > 1 &&
      members[0]!.character_start === g.character_start && members.at(-1)!.character_end === g.character_end &&
      members.map(s => s.characters).join('') === g.text && members.every(s => !hasTiming(s));
  });
}
export function timingGroupFor(data: Data, s: PerceivedSyllable) {
  return timingGroups(data).find(g => g.character_start <= s.character_start && g.character_end >= s.character_end);
}

// Display units, never seconds. Every accepted interval is half-open, including
// the final unit. Its endpoint remains in elapsed-time detail, but has no cell owner.
export const PAUSE_SECONDS = .3;
export const PAUSE_WIDTH = .2;
// Symmetric plot inset; local timing still includes unvoiced onsets and offsets.
export const CELL_PLOT_INSET = .12;
export function normalizedMine(data: Data): PitchXLayout {
  const timed = data.alignment_status === 'synthetic' ? [] : data.syllables.filter(hasTiming);
  const source = data.tone_graph?.mine ?? data.display_contour;
  const segments: PitchXLayout['segments'] = [], regions: PitchXLayout['regions'] = [], pauses: number[] = [];
  let cursor = 0;
  for (const [i, syllable] of data.syllables.entries()) {
    const previous = data.syllables[i - 1];
    // An untimed intervening character is not evidence of silence.
    // Nanosecond tolerance only avoids floating-point subtraction turning 0.30
    // into 0.29999999999999993; it is not an acoustic threshold adjustment.
    if (data.alignment_status !== 'synthetic' && previous && hasTiming(previous) && hasTiming(syllable) && previous.index + 1 === syllable.index &&
        syllable.start_seconds - previous.end_seconds + 1e-9 >= PAUSE_SECONDS) {
      pauses.push(cursor + PAUSE_WIDTH / 2);
      cursor += PAUSE_WIDTH;
    }
    regions.push({ index: syllable.index, label: syllable.characters, start: cursor, end: cursor + 1 });
    // Identity owns a cell even when acoustic timing is absent. Never partition it.
    if (!hasTiming(syllable) || data.alignment_status === 'synthetic') { cursor++; continue; }
    for (const segment of source?.segments ?? []) {
      const owned = segment.filter(p => sampleOwner(timed, p.timestamp_seconds) === syllable);
      if (owned.length) segments.push(owned.map(p => ({ ...p,
        position: cursor + CELL_PLOT_INSET + (1 - 2 * CELL_PLOT_INSET) *
          (p.timestamp_seconds - syllable.start_seconds) / (syllable.end_seconds - syllable.start_seconds) })));
    }
    cursor++;
  }
  const groups = timingGroups(data);
  const evidenceRegions = regions.filter(r => !groups.some(g => {
    const s = data.syllables.find(s => s.index === r.index)!;
    return g.character_start <= s.character_start && g.character_end >= s.character_end;
  }));
  for (const group of groups) {
    const members = data.syllables.filter(s => group.character_start <= s.character_start && s.character_end <= group.character_end);
    const left = regions.find(r => r.index === members[0]!.index)!.start;
    const right = regions.find(r => r.index === members.at(-1)!.index)!.end;
    evidenceRegions.push({ index: members[0]!.index, label: group.text, start: left, end: right });
    for (const segment of source?.segments ?? []) {
      const owned = segment.filter(p => group.start_seconds <= p.timestamp_seconds && p.timestamp_seconds < group.end_seconds);
      if (owned.length) segments.push(owned.map(p => ({ ...p,
        position: left + CELL_PLOT_INSET + (right - left - 2 * CELL_PLOT_INSET) *
          (p.timestamp_seconds - group.start_seconds) / (group.end_seconds - group.start_seconds) })));
    }
  }
  return { segments, regions, evidenceRegions, pauses, extent: Math.max(1, cursor) };
}
export function graphWidth(viewport: number, duration: number, units: number, shortestUnit?: number): number {
  const readableUnits = shortestUnit && shortestUnit > 0 ? duration / shortestUnit * 48 : 0;
  return Math.max(viewport, Math.min(6000, Math.max(duration * 140, units * 64, readableUnits)));
}
export function rawPitch(data: Data): { retained: PitchPoint[]; rejected: PitchPoint[] } {
  const frames = data.tone_graph?.raw ?? [];
  const rates = frames.map(p => p.tracker_f0_hz ?? p.f0_hz).filter((p): p is number => p != null && p > 0).sort((a, b) => a - b);
  const mid = Math.floor(rates.length / 2);
  const median = rates.length ? (rates.length % 2 ? rates[mid]! : (rates[mid-1]! + rates[mid]!) / 2) : null;
  const baseline = data.tone_graph?.filtered.baseline_hz ?? median;
  const point = (p: typeof frames[number]): PitchPoint => {
    const hz = p.tracker_f0_hz ?? p.f0_hz;
    return { timestamp_seconds: p.timestamp_seconds,
      normalized_semitones: hz && baseline ? 12 * Math.log2(hz / baseline) : null };
  };
  return { retained: frames.filter(p => p.retained).map(point), rejected: frames.filter(p => !p.retained).map(point) };
}
