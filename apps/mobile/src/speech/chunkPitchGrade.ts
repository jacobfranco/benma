import type { PerceivedSpeechAnalysis } from '@/api/types';
import { gradeLearnerPitch, pitchExpectation, pitchGrade, type LearnerPitchGrade } from '@/speech/learnerPitchGrade';
import { unitShape } from '@/speech/pitchShapeEvidence';
import { chunkEvidence, isTimedChunk, type PronunciationChunk } from '@/speech/pronunciationChunks';
import { pronunciationUnits } from '@/speech/pronunciationWorkspace';
import { classifyToneLikeness } from '@/speech/toneLikeness';

export type ConstituentPitchRole = 'grade_bearing' | 'neutral_unmeasured_nonveto' | 'neutral_measured_accepted' | 'neutral_unreliable_nonveto';
export function gradeChunkPitch(analysis: PerceivedSpeechAnalysis, chunk: PronunciationChunk,
  units = pronunciationUnits(analysis.data)) {
  const { data } = analysis;
  const exactPlayback = !!analysis.utterance_id && ['succeeded', 'partial'].includes(analysis.status) &&
    data.evidence_status === 'recorded_audio' && isTimedChunk(chunk) && chunk.start >= 0 && chunk.end <= data.duration_seconds;
  const recognized = data.pronunciation_chunk_policy === 'perceived-pronunciation-chunks-v1' && !!chunk.linguisticReason &&
    chunk.constituents.length > 1 && chunk.constituents.every((u, i) => !u.grouped && u.members.length === 1 &&
      (i === 0 || u.start >= chunk.constituents[i - 1]!.end));
  const constituents = chunkEvidence(data, chunk, units).map(evidence => {
    const { unit, pitch, hasPitch } = evidence;
    const shape = unitShape(data, unit, pitch.segments);
    const observed = classifyToneLikeness(shape, pitch.segments);
    const expected = pitchExpectation(unit.members[0]!, data.syllables);
    let grade = gradeLearnerPitch(observed, expected, hasPitch);
    let role: ConstituentPitchRole = 'grade_bearing';
    const neutral = exactPlayback && recognized && expected.tone === 0 && unit.members[0]!.reading_source !== 'unresolved' &&
      unit.start >= chunk.start! && unit.end <= chunk.end! && unit.end > unit.start &&
      chunk.constituents.some(other => other.id !== unit.id && (pitchExpectation(other.members[0]!).tone ?? 0) > 0);
    // A neutral dependent has no numbered-tone target. Positive acceptance needs
    // structural support, including deletion checks, but not a canonical family.
    if (neutral && !hasPitch) role = 'neutral_unmeasured_nonveto';
    if (neutral && hasPitch && shape.structurallyUsable) {
      role = 'neutral_measured_accepted';
      grade = pitchGrade('STRONG_MATCH', 'supported_contextual_neutral', 'Neutral syllable plausibly realized in this chunk.');
    }
    if (neutral && hasPitch && !shape.structurallyUsable) {
      role = 'neutral_unreliable_nonveto';
      grade = pitchGrade('UNAVAILABLE', 'unreliable_contextual_neutral', 'Neutral pitch could not be judged reliably; this does not veto the chunk’s pitch feedback.');
    }
    if (unit.grouped) grade = pitchGrade('UNAVAILABLE', 'grouped_timing', 'Separate tone judgments are unavailable for this timing group.');
    return { ...evidence, shape, observed, expected, grade, role };
  });
  let grade: LearnerPitchGrade;
  const bearing = constituents.filter(c => c.role === 'grade_bearing');
  const different = bearing.find(c => c.grade.agreement === 'CLEAR_DIFFERENCE');
  const unavailable = bearing.find(c => c.grade.agreement === 'UNAVAILABLE');
  const partial = bearing.find(c => c.grade.agreement === 'PARTIAL_OR_WEAK');
  if (!exactPlayback || !bearing.length) grade = pitchGrade('UNAVAILABLE', 'missing_timing_playback_or_bearing', 'Pitch feedback is unavailable for this chunk.');
  else if (different) grade = different.grade;
  else if (unavailable) grade = unavailable.grade;
  else if (partial) grade = partial.grade;
  else if (constituents.length === 1) grade = bearing[0]!.grade;
  else grade = pitchGrade('STRONG_MATCH', 'all_grade_bearing_pitch_matches', 'The pitch we could judge is reasonably acceptable here.',
    bearing.length === 1 ? bearing[0]!.grade.coaching :
      bearing.filter(c => c.grade.coaching).map(c => `${c.unit.text}: ${c.grade.coaching}`).join(' ') || null);
  return { grade, constituents, hasNeutralNonVeto: constituents.some(c => c.role !== 'grade_bearing') };
}
