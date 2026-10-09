import type { PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import { pitchSegments } from '@/components/PitchPlot';
import { hasTiming, timingGroups } from '@/speech/sentenceToneGraph';
import { colors } from '@/theme';

type Data = PerceivedSpeechAnalysis['data'];
export type PitchAgreement = 'STRONG_MATCH' | 'PARTIAL_OR_FLEXIBLE' | 'CLEAR_DIFFERENCE' | 'UNAVAILABLE';
export const agreementLabels: Record<PitchAgreement, string> = {
  STRONG_MATCH: 'Strong pitch match', PARTIAL_OR_FLEXIBLE: 'Partial pitch match',
  CLEAR_DIFFERENCE: 'Pitch differs', UNAVAILABLE: 'Pitch comparison unavailable',
};
export interface PronunciationUnit {
  id: string; text: string; members: PerceivedSyllable[];
  start: number; end: number; grouped: boolean;
  eligibility: PerceivedSyllable['pitch_eligibility'];
  agreement: PitchAgreement;
}

// Presentation only. toneGestureMatch deliberately abstains for every current
// policy. Do not reinterpret its uncertain result as a weak positive (amber).
export function pitchAgreement(): PitchAgreement { return 'UNAVAILABLE'; }

// One presentation seam for a future approved comparison policy. Current output
// is neutral and names evidence availability, never pronunciation correctness.
export function unitPresentation(unit: PronunciationUnit) {
  const labels = { sufficient: 'Measurement: clear', incomplete: 'Measurement: mixed',
    unstable: 'Measurement: mixed', insufficient: 'Measurement: limited' };
  return { label: unit.agreement === 'UNAVAILABLE'
    ? labels[unit.eligibility?.state ?? 'insufficient'] : agreementLabels[unit.agreement],
  background: colors.diagnostic, foreground: colors.secondary };
}

export function pronunciationUnits(data: Data): PronunciationUnit[] {
  if (!['aligned', 'partial'].includes(data.alignment_status) || data.evidence_status !== 'recorded_audio') return [];
  const groups = timingGroups(data);
  return data.syllables.flatMap(s => {
    const group = groups.find(g => g.character_start <= s.character_start && g.character_end >= s.character_end);
    if (group && group.character_start !== s.character_start) return [];
    if (!group && (!hasTiming(s) || s.end_seconds > data.duration_seconds)) return [];
    const evidence = group ?? s;
    return [{ id: `${evidence.timing_evidence_id ?? data.timing_evidence_id ?? 'saved'}:${evidence.character_start}:${evidence.character_end}:${evidence.start_seconds}:${evidence.end_seconds}`,
      text: group?.text ?? s.characters,
      members: group ? data.syllables.filter(m => m.character_start >= group.character_start && m.character_end <= group.character_end) : [s],
      start: evidence.start_seconds!, end: evidence.end_seconds!, grouped: !!group,
      eligibility: evidence.pitch_eligibility, agreement: pitchAgreement() }];
  });
}

export function defaultUnit(units: PronunciationUnit[]): string | null {
  return (units.find(u => u.agreement === 'PARTIAL_OR_FLEXIBLE' || u.agreement === 'CLEAR_DIFFERENCE') ??
    units.find(u => u.eligibility?.state === 'sufficient') ?? units[0])?.id ?? null;
}

// Retained measurements, not the smoothed Mine contour. No recentering or local
// scaling: every unit uses the same domain from this entire saved attempt.
export function workspacePitch(data: Data) {
  const source = data.tone_graph?.filtered;
  const segments = source?.segments ?? pitchSegments(data.measured_pitch).map(segment => segment.map(p => ({
    timestamp_seconds: p.timestamp_seconds!, normalized_semitones: p.normalized_semitones!,
  })));
  const values = segments.flat().map(p => p.normalized_semitones).filter(Number.isFinite);
  return { ...source, segments, minimum_semitones: Math.min(-3, ...values.map(v => v - 1)),
    maximum_semitones: Math.max(3, ...values.map(v => v + 1)) };
}
export function unitPitch(data: Data, unit: PronunciationUnit, units = pronunciationUnits(data)) {
  const source = workspacePitch(data);
  const segments: typeof source.segments = [];
  for (const segment of source.segments) {
    let current: typeof segment = [];
    for (const p of segment) {
      // Preserve the existing later-start ownership rule for accepted tiny overlaps.
      const owner = units.filter(u => u.start <= p.timestamp_seconds && p.timestamp_seconds < u.end)
        .sort((a, b) => b.start - a.start || b.members[0]!.index - a.members[0]!.index)[0];
      if (owner?.id === unit.id) current.push(p);
      else { if (current.length) segments.push(current); current = []; }
    }
    if (current.length) segments.push(current);
  }
  return { ...source, segments };
}
