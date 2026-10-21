import type { PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { pitchExpectation, pitchGrade, pitchGradePresentation, type LearnerPitchGrade, type PitchExpectation } from '@/speech/learnerPitchGrade';
import type { PronunciationChunk } from '@/speech/pronunciationChunks';
import { pronunciationUnits } from '@/speech/pronunciationWorkspace';
import type { ToneFamily } from '@/speech/toneLikeness';

type Data = PerceivedSpeechAnalysis['data'];
type Learned = NonNullable<Data['dev_learned_tone']>;
type Unit = Learned['units'][number];
type Feedback = ReturnType<typeof gradeChunkPitch>;
type Constituent = Feedback['constituents'][number];
type WorkspaceFeedback = Omit<Feedback, 'constituents'> & {
  constituents: (Omit<Constituent, 'observed'> & {
    observed: Pick<Constituent['observed'], 'tone' | 'reason'> & { variant: string };
  })[];
};

export function learnedToneEvidence(data: Data): Learned | null {
  return __DEV__ ? data.dev_learned_tone ?? null : null;
}

// Join by saved identity, never array position or a target-derived timing span.
function learnedUnit(data: Data, s: PerceivedSyllable): Unit | undefined {
  return learnedToneEvidence(data)?.units.find(u => u.index === s.index && u.characters === s.characters);
}

export function workspaceExpectation(data: Data, s: PerceivedSyllable): PitchExpectation {
  const learned = learnedToneEvidence(data);
  if (!learned) return pitchExpectation(s, data.syllables);
  const unit = learnedUnit(data, s);
  if (!unit || learned.target_mapping_resolved === false || unit.expected_surface_tone == null || unit.comparison.state === 'unresolved') {
    return { tone: null, basis: 'unresolved', label: 'Expected tone unresolved', coaching: null, reason: 'learned_expectation_unresolved' };
  }
  // Only a resolved surface expectation may be compared. No lexical fallback.
  return pitchExpectation({ ...s, pinyin: unit.target_pinyin, lexical_tone: null,
    expected_surface_tone: unit.expected_surface_tone as 0 | 1 | 2 | 3 | 4,
    surface_rule: unit.surface_rule });
}

export function toneRendering(data: Learned, members?: readonly PerceivedSyllable[]) {
  const units = members ? members.map(s => data.units.find(u => u.index === s.index && u.characters === s.characters)) : data.units;
  return {
    referenceLabel: data.target_mapping_resolved === false || data.expectation_basis === 'perceived_text' ? 'Transcript reading' : 'Target reading',
    target: units.map(u => u?.target_pinyin ?? '…').join(' '),
    // Neutral is a contextual reading, not a numbered recognition or a match.
    heard: units.map(u => u?.comparison.state === 'neutral' ? u.target_pinyin ?? '…'
      : u?.realization.status === 'ok' && u.realization.prediction ? u.heard_pinyin ?? '[unclear]' : '[unclear]').join(' '),
  };
}

export function workspaceGradePresentation(grade: LearnerPitchGrade) {
  const presentation = pitchGradePresentation[grade.agreement];
  return grade.reason === 'learned_expectation_unresolved' || grade.reason === 'learned_neutral'
    ? { ...presentation, label: 'Pitch not judged' } : presentation;
}

export function workspaceChunkFeedback(analysis: PerceivedSpeechAnalysis, chunk: PronunciationChunk,
  units = pronunciationUnits(analysis.data)): WorkspaceFeedback {
  const original = gradeChunkPitch(analysis, chunk, units);
  if (!learnedToneEvidence(analysis.data)) return original;
  // Keep the established projections, measured shape and contextual neutral
  // support. Never reuse the deterministic numbered family/grade as learned output.
  const constituents = original.constituents.map(e => {
    const unit = !e.unit.grouped ? learnedUnit(analysis.data, e.unit.members[0]!) : undefined;
    const expected = workspaceExpectation(analysis.data, e.unit.members[0]!);
    const usable = e.hasPitch && unit?.realization.status === 'ok' && !!unit.realization.prediction;
    const neutral = expected.basis === 'neutral' && unit?.comparison.state === 'neutral';
    const observed: WorkspaceFeedback['constituents'][number]['observed'] = {
      tone: usable && !neutral ? `TONE_${unit.realization.prediction!.slice(1)}` as ToneFamily : 'UNCLEAR',
      reason: unit?.realization.reason ?? 'learned_realization', variant: 'learned',
    };
    let grade = pitchGrade('UNAVAILABLE', 'learned_insufficient', 'Tone unclear. No correction.');
    const role = neutral ? e.role : 'grade_bearing';
    if (neutral) grade = e.role === 'neutral_measured_accepted' ? e.grade
      : pitchGrade('UNAVAILABLE', 'learned_neutral', 'Neutral tone has no fixed pitch shape.');
    else if (usable && expected.basis === 'unresolved') grade = pitchGrade('UNAVAILABLE', 'learned_expectation_unresolved',
      'Expected pitch is unresolved in this context. No correction.');
    else if (usable && expected.basis === 'resolved_surface') {
      // Consume downstream comparison, not probability thresholds or argmax equality.
      // This contract supplies no decisive/stable error evidence: never emit red.
      if (unit.comparison.state === 'experimental_match') grade = pitchGrade('STRONG_MATCH', 'learned_agreement',
        'The heard tone fits the expected pitch. This is not a correctness score.', unit.comparison.explanation ?? null);
      if (unit.comparison.state === 'experimental_mismatch') grade = pitchGrade('PARTIAL_OR_WEAK', 'learned_difference',
        'The heard tone may differ from what is expected here, but a tone error is not clear.', unit.comparison.explanation ?? null);
    }
    if (e.unit.grouped) grade = pitchGrade('UNAVAILABLE', 'grouped_timing', 'Separate tone judgments are unavailable for this timing group.');
    return { ...e, observed, expected, grade, role };
  });
  const bearing = constituents.filter(e => e.role === 'grade_bearing');
  const exact = !!analysis.utterance_id && ['succeeded', 'partial'].includes(analysis.status) &&
    analysis.data.evidence_status === 'recorded_audio' && chunk.timingStatus === 'timed' &&
    chunk.start != null && chunk.end != null && chunk.start >= 0 && chunk.end <= analysis.data.duration_seconds;
  const grade = !exact || !bearing.length
    ? pitchGrade('UNAVAILABLE', 'missing_timing_playback_or_bearing', 'Pitch feedback is unavailable for this chunk.')
    : bearing.find(e => e.grade.agreement === 'UNAVAILABLE')?.grade
      ?? bearing.find(e => e.grade.agreement === 'PARTIAL_OR_WEAK')?.grade
      ?? (bearing.length === 1 ? bearing[0]!.grade
        : pitchGrade('STRONG_MATCH', 'learned_chunk_agreement', 'The pitch we could judge is reasonably acceptable here.'));
  return { grade, constituents, hasNeutralNonVeto: constituents.some(e => e.role !== 'grade_bearing') };
}
