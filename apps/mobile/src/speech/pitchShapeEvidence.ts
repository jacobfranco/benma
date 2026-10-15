import { pitchExpectation } from '@/speech/learnerPitchGrade';
import type { PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import { classifyPitchShape, type ShapePoint, type ShapeResult } from '@/speech/pitchShape';
import type { PronunciationUnit } from '@/speech/pronunciationWorkspace';

export function unitShape(data: PerceivedSpeechAnalysis['data'], unit: PronunciationUnit,
  segments: readonly (readonly ShapePoint[])[]): ShapeResult {
  if (unit.grouped) return { shape: 'UNCLEAR', reason: 'grouped_timing', features: {}, perturbations: {} };
  const raw = (data.tone_graph?.raw ?? []).filter(p => p.timestamp_seconds >= unit.start && p.timestamp_seconds < unit.end &&
    // Only the audio-only candidate proof can retire a raw branch veto. Other
    // rejection (including background noise) never makes remaining pitch safe.
    !(p.selected_f0_hz == null && !p.retained && p.exclusion_reasons?.includes('candidate_supported_ambiguous_branch')) &&
    (p.tracker_f0_hz ?? p.f0_hz ?? 0) > 0);
  const flagged = raw.slice(1).flatMap((p, i) => {
    const previous = raw[i]!;
    return p.timestamp_seconds - previous.timestamp_seconds <= .12 &&
      Math.abs(12 * Math.log2((p.tracker_f0_hz ?? p.f0_hz)! / (previous.tracker_f0_hz ?? previous.f0_hz)!)) > 6
      ? [previous.timestamp_seconds, p.timestamp_seconds] : [];
  });
  return classifyPitchShape(segments, flagged);
}

// Share the primary learner expectation; a family fallback is not an exact
// surface prediction. Callers can also display pitchExpectation(s).coaching.
export function expectedShapeLabel(s: PerceivedSyllable): string {
  const expected = pitchExpectation(s);
  if (expected.basis !== 'resolved_surface' && expected.basis !== 'neutral') return expected.label;
  return ({ 0: 'Flexible · neutral tone', 1: 'Level', 2: 'Rising',
    3: 'Low or dipping · a full rise is optional', 4: 'Falling' } as Record<number, string>)[expected.tone!]!;
}
