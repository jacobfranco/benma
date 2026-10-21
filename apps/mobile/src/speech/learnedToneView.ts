import type { PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { gradeLearnerPitch, pitchExpectation, pitchGrade, pitchGradePresentation, type LearnerPitchGrade, type PitchExpectation } from '@/speech/learnerPitchGrade';
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

export type ContextualToneExplanation = {
  rule: string; title: string; dictionary: string; spoken: string; explanation: string;
  heard: string;
};

// A rule ID comes from the linguistic resolver, never from Hanzi or pinyin parsing.
// Unknown future IDs keep the same contract and show only the supplied expectation.
export function contextualToneExplanation(data: Data, s: PerceivedSyllable): ContextualToneExplanation | null {
  const unit = learnedUnit(data, s);
  const expected = workspaceExpectation(data, s);
  const tones = expected.acceptableTones ?? (expected.tone ? [expected.tone] : []);
  if (!unit?.contextual_rule || expected.basis === 'unresolved' || !tones.length ||
      unit.lexical_tone == null || tones.every(t => t === unit.lexical_tone)) return null;
  const sandhi = unit.contextual_rule === 'third_tone_sandhi';
  const alternatives = tones.length > 1;
  return {
    rule: unit.contextual_rule,
    title: sandhi ? 'Third-tone sandhi' : 'Contextual pronunciation',
    dictionary: `Tone ${unit.lexical_tone}`,
    spoken: tones.map(t => `Tone ${t}`).join(' or '),
    explanation: sandhi ? alternatives
      ? 'Tone 2 or Tone 3 can be acceptable here, depending on phrasing.'
      : 'Before another third tone, this dictionary Tone 3 changes to a rising Tone-2-like realization.'
      : 'The spoken tone in this context can differ from the dictionary tone.',
    heard: unit.realization.status === 'ok' && unit.realization.prediction
      ? `Tone ${unit.realization.prediction.slice(-1)}` : 'Not enough evidence',
  };
}

export function workspaceExpectation(data: Data, s: PerceivedSyllable): PitchExpectation {
  const learned = learnedToneEvidence(data);
  if (!learned) return pitchExpectation(s, data.syllables);
  const unit = learnedUnit(data, s);
  const unknown: PitchExpectation = { tone: null, basis: 'unresolved', label: 'Not yet gradable in context',
    coaching: null, reason: 'learned_expectation_unresolved' };
  if (!unit || learned.target_mapping_resolved === false || unit.expectation_resolution === 'unresolved') return unknown;
  const neutral = unit.expected_neutral ?? unit.expected_surface_tone === 0;
  const tones = unit.acceptable_surface_tones ?? (unit.expected_surface_tone ? [unit.expected_surface_tone] : []);
  if (neutral) return { tone: 0, basis: 'neutral', label: 'Neutral', coaching: null, reason: unit.surface_rule ?? 'neutral' };
  if (!tones.length || tones.some(t => ![1, 2, 3, 4].includes(t))) return unknown;
  if (tones.length > 1) return { tone: null, acceptableTones: tones, basis: 'acceptable_alternatives',
    label: tones.map(t => `Tone ${t}`).join(' or '), coaching: null, reason: unit.surface_rule ?? 'surface_alternatives' };
  return { ...pitchExpectation({ ...s, pinyin: unit.target_pinyin, reading_source: 'phrase', lexical_tone: null,
    expected_surface_tone: tones[0] as 1 | 2 | 3 | 4, surface_rule: unit.surface_rule }), acceptableTones: tones };
}

export function toneRendering(data: Learned, members?: readonly PerceivedSyllable[]) {
  const units = members ? members.map(s => data.units.find(u => u.index === s.index && u.characters === s.characters)) : data.units;
  return {
    referenceLabel: data.target_mapping_resolved === false || data.expectation_basis === 'perceived_text' ? 'Transcript reading' : 'Target reading',
    target: units.map(u => u?.target_pinyin ?? '…').join(' '),
    // Neutral is a contextual reading, not a prediction from the numbered-tone model.
    heard: units.map(u => u?.comparison.state === 'neutral' ? u.target_pinyin ?? '…'
      : u?.realization.status === 'ok' && u.realization.prediction ? u.heard_pinyin ?? '[unclear]' : '[unclear]').join(' '),
  };
}

export function workspaceGradePresentation(grade: LearnerPitchGrade) {
  const presentation = pitchGradePresentation[grade.agreement];
  if (!grade.reason.startsWith('learned_')) return presentation;
  return { ...presentation, label: grade.agreement === 'STRONG_MATCH' ? grade.message
    : grade.agreement === 'UNAVAILABLE' ? grade.reason === 'learned_expectation_unresolved' ? 'Not yet gradable' : 'Not enough evidence'
      : grade.message };
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
    const here = contextualToneExplanation(analysis.data, e.unit.members[0]!) ? ' here' : '';
    const usable = e.hasPitch && unit?.realization.status === 'ok' && !!unit.realization.prediction;
    const neutral = expected.basis === 'neutral' && unit?.comparison.state === 'neutral';
    const observed: WorkspaceFeedback['constituents'][number]['observed'] = {
      tone: usable && !neutral ? `TONE_${unit.realization.prediction!.slice(1)}` as ToneFamily : 'UNCLEAR',
      reason: unit?.realization.reason ?? 'learned_realization', variant: 'learned',
    };
    let grade = pitchGrade('UNAVAILABLE', 'learned_insufficient', 'Not enough evidence');
    const role = neutral ? e.role : 'grade_bearing';
    if (neutral) grade = e.role === 'neutral_measured_accepted' &&
      unit.realization.reason === 'neutral_outside_four_tone_model'
      ? pitchGrade('STRONG_MATCH', 'learned_neutral_correct', 'Correct · Neutral')
      : pitchGrade('UNAVAILABLE', 'learned_neutral_unavailable', 'Not enough evidence for neutral tone');
    else if (usable && expected.basis === 'unresolved') grade = pitchGrade('UNAVAILABLE', 'learned_expectation_unresolved',
      `Heard Tone ${unit.realization.prediction!.slice(1)}. Benma can't reliably grade this tone in context yet.`);
    else if (usable) {
      const heard = Number(unit.realization.prediction!.slice(1));
      const acceptable = expected.acceptableTones ?? (expected.tone ? [expected.tone] : []);
      // Learned family membership is primary. No F0 shape, probability threshold,
      // deterministic disagreement or perturbation check can veto this match.
      if (acceptable.includes(heard)) grade = pitchGrade('STRONG_MATCH', 'learned_agreement', `Correct · Tone ${heard}${here}`);
      else {
        // Reuse the existing conservative red policy only to corroborate an
        // incompatible learned family. A different F0 winner cannot confirm it.
        const corroboration = gradeLearnerPitch(e.observed, { ...expected, tone: acceptable[0] ?? null }, e.hasPitch);
        const decisive = e.observed.tone === observed.tone && corroboration.agreement === 'CLEAR_DIFFERENCE';
        const message = `Expected ${acceptable.map(t => `Tone ${t}`).join(' or ')}${here} · heard Tone ${heard}`;
        const movement = heard === 4 ? 'fell' : heard === 2 ? 'rose' : null;
        const target = expected.tone === 2 ? 'rise' : expected.tone === 4 ? 'fall' : null;
        grade = pitchGrade(decisive ? 'CLEAR_DIFFERENCE' : 'PARTIAL_OR_WEAK',
          decisive ? 'learned_corroborated_difference' : 'learned_difference', message,
          decisive && movement && target ? `Your pitch ${movement} here; this syllable should ${target} in this context.`
            : unit.comparison.explanation ?? null);
      }
    }
    if (e.unit.grouped) grade = pitchGrade('UNAVAILABLE', 'grouped_timing', 'Separate tone judgments are unavailable for this timing group.');
    return { ...e, observed, expected, grade, role };
  });
  const bearing = constituents.filter(e => e.role === 'grade_bearing');
  const exact = !!analysis.utterance_id && ['succeeded', 'partial'].includes(analysis.status) &&
    analysis.data.evidence_status === 'recorded_audio' && chunk.timingStatus === 'timed' &&
    chunk.start != null && chunk.end != null && chunk.start >= 0 && chunk.end <= analysis.data.duration_seconds;
  const correct = constituents.filter(e => e.grade.agreement === 'STRONG_MATCH');
  const allCorrect = correct.length === constituents.length;
  const summary = correct.map(e => e.expected.basis === 'neutral' ? 'neutral'
    : `Tone ${e.observed.tone.slice(-1)}${contextualToneExplanation(analysis.data, e.unit.members[0]!) ? ' here' : ''}`).join(' + ');
  const grade = !exact || !bearing.length
    ? pitchGrade('UNAVAILABLE', 'learned_missing_timing', 'Not enough evidence')
    : bearing.find(e => e.grade.agreement === 'CLEAR_DIFFERENCE')?.grade
      ?? bearing.find(e => e.grade.agreement === 'UNAVAILABLE')?.grade
      ?? bearing.find(e => e.grade.agreement === 'PARTIAL_OR_WEAK')?.grade
      ?? (constituents.length === 1 ? constituents[0]!.grade
        : pitchGrade('STRONG_MATCH', 'learned_chunk_agreement', allCorrect
          ? `Correct · ${summary}` : `Correct where measured · ${summary}`));
  return { grade, constituents, hasNeutralNonVeto: constituents.some(e => e.role !== 'grade_bearing') };
}
