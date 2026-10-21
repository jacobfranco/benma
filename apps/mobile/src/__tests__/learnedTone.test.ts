import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';
import { copy, replacePitch } from './toneFeedbackFixture';
import { physicalChunkAnalysis } from './pronunciationChunkFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { ExactPlaybackButton } from '@/audio/ExactPlaybackButton';
import { registerPlayback } from '@/audio/session';
import { PitchPlot } from '@/components/PitchPlot';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { contextualToneExplanation, learnedToneEvidence, toneRendering, workspaceChunkFeedback, workspaceExpectation } from '@/speech/learnedToneView';
import { pronunciationChunks } from '@/speech/pronunciationChunks';
import { PronunciationWorkspace } from '@/speech/PronunciationWorkspace';
import { ContextualToneHelp } from '@/speech/ContextualToneHelp';
import { submitSpeech, type SpeechCheckpoint, type SpeechWorkflowApi } from '@/speech/workflow';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));

function withLearned(base = perceivedAnalysis): PerceivedSpeechAnalysis {
  return { ...base, data: { ...base.data, dev_learned_tone: {
    expectation_basis: 'intended_target', target_text: base.alignment_reference_text, timings_ms: {}, runtime: { load_count: 1 },
    units: base.data.syllables.map(s => ({ index: s.index, characters: s.characters, target_pinyin: s.pinyin,
      lexical_tone: s.lexical_tone ?? null, expected_surface_tone: s.expected_surface_tone ?? null, surface_rule: s.surface_rule ?? null,
      heard_pinyin: s.pinyin, realization: { status: 'ok', prediction: 'T4', confidence: .999, azure_span: [s.start_seconds!, s.end_seconds!] },
      comparison: { state: s.expected_surface_tone === 0 ? 'neutral' : s.expected_surface_tone == null ? 'unresolved' : 'experimental_mismatch',
        correction: false, message: 'Experimental backend comparison' },
    })),
  } } };
}
function firstFeedback(value: PerceivedSpeechAnalysis) {
  return workspaceChunkFeedback(value, pronunciationChunks(value.data)[0]!);
}
let renderer: ReactTestRenderer;
async function mount(value = withLearned()) {
  await act(async () => { renderer = create(React.createElement(PronunciationWorkspace, {
    analysis: value, phraseActions: React.createElement(Text, { testID: 'phrase-action' }, 'Phrase action'),
  })); });
}
async function press(label: string) {
  await act(async () => renderer.root.findByProps({ accessibilityLabel: label }).props.onPress());
}
async function select(index: number) {
  await act(async () => renderer.root.findByProps({ testID: `pronunciation-unit-${index}` }).props.onPress());
}
afterEach(async () => { if (renderer) await act(async () => renderer.unmount()); });

it('restores compact chart styling, phrase actions, exact playback, selection and collapsed details', async () => {
  const value = withLearned();
  const before = JSON.stringify(value);
  await mount(value);
  expect(renderer.root.findByProps({ testID: 'pronunciation-workspace' })).toBeTruthy();
  expect(renderer.root.findAllByProps({ testID: 'learned-tone-workspace' })).toHaveLength(0);
  expect(renderer.root.findByProps({ testID: 'phrase-action' })).toBeTruthy();
  const chart = renderer.root.findByType(PitchPlot).props;
  expect(chart).toMatchObject({ showAxes: false, showPoints: true, plotHeight: 96, showMineLabel: false,
    startSeconds: 0, durationSeconds: .6 });
  expect(chart.display.segments).toEqual(perceivedAnalysis.data.tone_graph!.filtered.segments!.slice(0, 1));
  const button = renderer.root.findByProps({ testID: 'pronunciation-unit-0' });
  expect(StyleSheet.flatten(button.props.style)).toMatchObject({ minWidth: 44, minHeight: 48, borderBottomWidth: 4 });
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ start: 0, end: .6, text: '周' });
  const stop = jest.fn(), unregister = registerPlayback(stop);
  await select(1);
  expect(stop).toHaveBeenCalledTimes(1);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ start: .6, end: 1.2, text: '谋' });
  expect(renderer.root.findByType(PitchPlot).props.display.segments).toEqual(perceivedAnalysis.data.tone_graph!.filtered.segments!.slice(1));
  expect(JSON.stringify(renderer.toJSON())).toContain('Heard Tone 4');
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Experimental tone realization|Dev evidence|confidence|HuBERT|accuracy|99.9/);
  unregister();
  expect(JSON.stringify(value)).toBe(before);
});

it('uses learned family membership and never turns raw confidence alone into red', () => {
  const value = withLearned();
  const unit = value.data.dev_learned_tone!.units[0]!;
  for (const confidence of [.26, .999]) {
    unit.realization.confidence = confidence;
    expect(firstFeedback(value).grade.agreement).toBe('PARTIAL_OR_WEAK');
  }
  // A stale saved comparison cannot override the actual acceptable-family set.
  unit.comparison.state = 'experimental_match';
  expect(firstFeedback(value).grade.agreement).toBe('PARTIAL_OR_WEAK');
  unit.expected_surface_tone = 4;
  expect(firstFeedback(value).grade.agreement).toBe('STRONG_MATCH');
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('TONE_4');
});

it('keeps unresolved surface expectation gray despite a lexical fallback or claimed match', async () => {
  const value = withLearned();
  const unit = value.data.dev_learned_tone!.units[0]!;
  unit.expected_surface_tone = null;
  unit.comparison.state = 'experimental_match';
  expect(workspaceExpectation(value.data, value.data.syllables[0]!)).toMatchObject({ tone: null, basis: 'unresolved' });
  expect(firstFeedback(value).grade).toMatchObject({ agreement: 'UNAVAILABLE', coaching: null });
  await mount(value);
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('Heard Tone 4');
  expect(tree).toContain("can't reliably grade");
  expect(renderer.root.findByProps({ testID: 'selected-pronunciation-detail' }).findAllByType(Text)
    .map(n => n.props.children).join(' ')).not.toMatch(/Pitch acceptable|Pitch differs|Pitch may be off/);
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-0' }).props.accessibilityLabel).toContain('Not yet gradable');
});

it('keeps abstention gray with playable audio and measured pitch, never a deterministic fallback', async () => {
  const value = withLearned();
  const unit = value.data.dev_learned_tone!.units[0]!;
  unit.realization = { status: 'abstained', reason: 'continuity_guard', prediction: 'T4' };
  unit.comparison.state = 'insufficient';
  expect(firstFeedback(value).grade.agreement).toBe('UNAVAILABLE');
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('UNCLEAR');
  expect(toneRendering(value.data.dev_learned_tone!).heard).toContain('[unclear]');
  await mount(value);
  expect(renderer.root.findByType(PitchPlot)).toBeTruthy();
  expect(renderer.root.findByType(ExactPlaybackButton)).toBeTruthy();
  expect(JSON.stringify(renderer.toJSON())).toContain('Not enough evidence');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Heard Tone 4');
});

it('preserves contextual neutral non-veto in the original 这个 chunk and constituent interaction', async () => {
  const value = withLearned(physicalChunkAnalysis());
  const neutral = value.data.dev_learned_tone!.units[4]!;
  neutral.realization = { status: 'abstained', reason: 'neutral_out_of_scope' };
  const chunk = pronunciationChunks(value.data).find(c => c.text === '这个')!;
  const feedback = workspaceChunkFeedback(value, chunk);
  expect(feedback.hasNeutralNonVeto).toBe(true);
  expect(feedback.constituents[1]!.grade.agreement).toBe('UNAVAILABLE');
  expect(feedback.grade.agreement).toBe('STRONG_MATCH');
  expect(feedback.grade.message).toBe('Correct where measured · Tone 4');
  expect(toneRendering(value.data.dev_learned_tone!).heard).toMatch(/ge$/);
  await mount(value); await select(3);
  expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('这个');
  await press('More details');
  await act(async () => renderer.root.findByProps({ testID: 'chunk-constituent-4' }).props.onPress());
  const detail = renderer.root.findByProps({ testID: 'selected-constituent-detail' });
  expect(detail.findByType(ExactPlaybackButton).props).toMatchObject({ text: '个', start: 2.74, end: 3.04 });
  expect(detail.findAllByType(Text).map(n => n.props.children).join(' ')).not.toContain('Heard Tone 4');
});

it('places target/heard readings in More details and dev evidence only in Technical details', async () => {
  const value = withLearned();
  value.data.dev_learned_tone!.units[0]!.heard_pinyin = 'zhòu';
  await mount(value);
  expect(renderer.root.findAllByProps({ testID: 'learned-target-rendering' })).toHaveLength(0);
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  await press('More details');
  expect(JSON.stringify(renderer.root.findByProps({ testID: 'learned-target-rendering' }).props.children)).toContain('zhōu');
  expect(JSON.stringify(renderer.root.findByProps({ testID: 'learned-heard-rendering' }).props.children)).toContain('zhòu');
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  expect(renderer.root.findAllByType(PitchPlot).some(p => p.props.plotHeight === 152)).toBe(true);
  expect(JSON.stringify(renderer.toJSON())).toContain('Tone 1 — level');
  await press('Technical details');
  expect(renderer.root.findByProps({ testID: 'learned-debug' })).toBeTruthy();
  await press('Close Full pitch details');
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  await press('More details');
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
});

it('fails closed for missing/misordered identities and unresolved target mappings without mutating data', () => {
  const value = withLearned();
  value.data.dev_learned_tone!.units.reverse();
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('TONE_4');
  value.data.dev_learned_tone!.target_mapping_resolved = false;
  expect(firstFeedback(value).grade.agreement).toBe('UNAVAILABLE');
  expect(toneRendering(value.data.dev_learned_tone!).referenceLabel).toBe('Transcript reading');
  value.data.dev_learned_tone!.units = [];
  const before = JSON.stringify(value);
  expect(firstFeedback(value).grade.agreement).toBe('UNAVAILABLE');
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('UNCLEAR');
  expect(JSON.stringify(value)).toBe(before);
});

it('preserves feature-off grading and ignores learned payloads in production', () => {
  const chunk = pronunciationChunks(perceivedAnalysis.data)[0]!;
  expect(workspaceChunkFeedback(perceivedAnalysis, chunk)).toEqual(gradeChunkPitch(perceivedAnalysis, chunk));
  const previous = __DEV__;
  try {
    Object.assign(globalThis, { __DEV__: false });
    const value = withLearned();
    expect(learnedToneEvidence(value.data)).toBeNull();
    expect(workspaceChunkFeedback(value, chunk)).toEqual(gradeChunkPitch(value, chunk));
  } finally { Object.assign(globalThis, { __DEV__: previous }); }
});

it.each([true, false])('preserves the prepared-target workflow with the learned dev flag=%s', async enabled => {
  const previous = process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE;
  process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE = String(enabled);
  const client = {
    uploadUtterance: jest.fn().mockResolvedValue({ id: 'u' }),
    createPerception: jest.fn().mockResolvedValue({ id: 'p', transcript: '我想买这个' }),
    createAttempt: jest.fn().mockResolvedValue({ id: 'a' }),
    analyzePronunciation: jest.fn(), addConversationUserTurn: jest.fn(),
    analyzePerceivedSpeech: jest.fn().mockResolvedValue(perceivedAnalysis),
  } as unknown as jest.Mocked<SpeechWorkflowApi>;
  const checkpoint: SpeechCheckpoint = { uri: 'file:///recording.wav' };
  try {
    await submitSpeech(client, { responseMode: 'none', targetId: 't' }, checkpoint, 'audio/wav', () => {}, () => {});
    await Promise.all([checkpoint.analysis, checkpoint.targetAnalysis]);
    expect(client.createPerception).toHaveBeenCalledWith('u');
    expect(client.createAttempt).toHaveBeenCalledWith('u', 't');
    expect(client.analyzePerceivedSpeech).toHaveBeenCalledTimes(1);
    if (enabled) {
      expect(client.analyzePerceivedSpeech).toHaveBeenCalledWith('p', 't');
      expect(client.analyzePronunciation).not.toHaveBeenCalled();
    } else {
      expect(client.analyzePerceivedSpeech).toHaveBeenCalledWith('p');
      expect(client.analyzePronunciation).toHaveBeenCalledWith('a');
    }
  } finally {
    if (previous === undefined) delete process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE;
    else process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE = previous;
  }
});


const gradingCase = require('../../../../services/api/tests/fixtures/learner_grading_physical.json') as {
  units: { characters: string; lexical_tone: number; acceptable_surface_tones: number[];
    heard_tone: 'T1' | 'T2' | 'T3' | 'T4' | null; expected_neutral?: boolean; grade: string }[];
};
function gradingAcceptance() {
  const value = copy(withLearned(physicalChunkAnalysis()));
  value.data.dev_learned_tone!.units.forEach((unit, i) => {
    const fixture = gradingCase.units[i]!;
    unit.acceptable_surface_tones = fixture.acceptable_surface_tones;
    unit.expected_neutral = fixture.expected_neutral ?? false;
    unit.expectation_resolution = unit.expected_neutral ? 'neutral' : unit.acceptable_surface_tones.length > 1 ? 'alternatives' : 'exact';
    unit.expected_surface_tone = unit.expected_neutral ? 0 : unit.acceptable_surface_tones.length === 1 ? unit.acceptable_surface_tones[0]! : null;
    unit.realization = fixture.heard_tone ? { status: 'ok', prediction: fixture.heard_tone, confidence: .26 }
      : { status: 'abstained', reason: 'neutral_outside_four_tone_model' };
    // Controlled F0, not the original physical audio. In particular, the two
    // learned T3 matches must survive a strong falling deterministic T4 contour.
    replacePitch(value, i, x => -4 * x);
  });
  return value;
}
function allFeedback(value: PerceivedSpeechAnalysis) {
  return pronunciationChunks(value.data).map(c => workspaceChunkFeedback(value, c));
}
it('grades the reported physical families generically and explains T4 plus neutral', async () => {
  const value = gradingAcceptance();
  const feedback = allFeedback(value);
  expect(feedback.flatMap(f => f.constituents.map(e => e.grade.agreement))).toEqual(gradingCase.units.map(u => u.grade));
  expect(feedback[1]!.grade).toMatchObject({ message: 'Expected Tone 2 · heard Tone 4',
    coaching: 'Your pitch fell here; this syllable should rise in this context.' });
  expect(feedback[3]!.grade.message).toBe('Correct · Tone 4 + neutral');
  expect(feedback[0]!.constituents[0]!.expected).toMatchObject({ tone: null, acceptableTones: [2, 3] });
  await mount(value);
  for (const i of [0, 2, 3]) {
    await select(i);
    expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Most like|Pitch acceptable|unresolved in this context/);
  }
  expect(JSON.stringify(renderer.toJSON())).toContain('Correct · Tone 4 + neutral');
  await press('More details'); await press('Technical details');
  const debug = JSON.stringify(renderer.root.findByProps({ testID: 'learned-debug' }).props.children);
  expect(debug).toContain('acceptable_surface_tones');
  expect(debug).toContain('expected_neutral');
  expect(debug).toContain('expectation_resolution');
  expect(JSON.stringify(renderer.toJSON())).toContain('learned_neutral_correct');
});

it.each(['T2', 'T3'] as const)('accepts either licensed first-syllable family %s without an F0 veto', heard => {
  const value = gradingAcceptance();
  value.data.dev_learned_tone!.units[0]!.realization.prediction = heard;
  expect(allFeedback(value)[0]!.grade.agreement).toBe('STRONG_MATCH');
});

it('keeps uncorroborated or conflicting-F0 learned mismatches amber', () => {
  const value = gradingAcceptance();
  for (const contour of [(x: number) => .2 * x, (x: number) => 4 * x]) {
    replacePitch(value, 1, contour);
    expect(allFeedback(value)[1]!.grade.agreement).toBe('PARTIAL_OR_WEAK');
  }
});

it('preserves abstention and neutral validity failures, without falsely confirming a whole compound', () => {
  const value = gradingAcceptance();
  value.data.dev_learned_tone!.units[2]!.realization.status = 'abstained';
  expect(allFeedback(value)[2]!.grade.agreement).toBe('UNAVAILABLE');
  value.data.dev_learned_tone!.units[4]!.realization.reason = 'ambiguous_interrupted_voiced_envelope';
  const compound = allFeedback(value)[3]!;
  expect(compound.constituents[1]!.grade.agreement).toBe('UNAVAILABLE');
  expect(compound.grade.message).toBe('Correct where measured · Tone 4');
  value.data.dev_learned_tone!.units[3]!.realization.status = 'abstained';
  expect(allFeedback(value)[3]!.grade.agreement).toBe('UNAVAILABLE');
});

it('surfaces a decisive compound concern even when its neutral member is unavailable', () => {
  const value = gradingAcceptance();
  const unit = value.data.dev_learned_tone!.units[3]!;
  unit.realization.prediction = 'T2';
  replacePitch(value, 3, x => 4 * x);
  replacePitch(value, 4);
  expect(allFeedback(value)[3]!.grade.agreement).toBe('CLEAR_DIFFERENCE');
});

function contextualAcceptance() {
  const value = gradingAcceptance();
  value.data.dev_learned_tone!.units.slice(0, 2).forEach(u => { u.contextual_rule = 'third_tone_sandhi'; });
  return value;
}
it('explains the changed tone from the primary UI and preserves dictionary pinyin', async () => {
  const value = contextualAcceptance();
  const unit = value.data.dev_learned_tone!.units[1]!;
  unit.realization.prediction = 'T2';
  unit.heard_pinyin = 'xiáng';
  const before = JSON.stringify(value);
  expect(allFeedback(value)[1]!.grade.message).toBe('Correct · Tone 2 here');
  await mount(value); await select(1);
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  await press('Why this tone here for 想?');
  const help = renderer.root.findByProps({ testID: 'contextual-tone-help' });
  const text = help.findAllByType(Text).map(n => n.props.children.flat?.().join('') ?? n.props.children).join('\n');
  expect(text).toContain('Dictionary tone: Tone 3');
  expect(text).toContain('Spoken here: Tone 2');
  expect(text).toContain('Heard: Tone 2');
  expect(text).toContain('Before another third tone');
  await press('Close Third-tone sandhi');
  expect(renderer.root.findAllByProps({ testID: 'contextual-tone-help' })).toHaveLength(0);
  expect(toneRendering(value.data.dev_learned_tone!).target).toContain('xiǎng');
  expect(toneRendering(value.data.dev_learned_tone!).target).not.toContain('xiáng');
  expect(JSON.stringify(renderer.toJSON())).toContain('xiǎng');
  expect(JSON.stringify(value)).toBe(before);
});

it('explains alternatives without claiming one universal triple pattern', async () => {
  const value = contextualAcceptance();
  const explanation = contextualToneExplanation(value.data, value.data.syllables[0]!)!;
  expect(explanation.spoken).toBe('Tone 2 or Tone 3');
  expect(explanation.explanation).toContain('depending on phrasing');
  await mount(value); await select(0); await press('Why this tone here for 我?');
  expect(JSON.stringify(renderer.toJSON())).toContain('Tone 2 or Tone 3');
  await press('Close Third-tone sandhi');
  await press('More details'); await press('Technical details');
  const debug = renderer.root.findByProps({ testID: 'learned-debug' }).props.children;
  const units = JSON.parse(debug[2]).units;
  expect(units[0].acceptable_surface_tones).toEqual([2, 3]);
  expect(units[0].contextual_rule).toBe('third_tone_sandhi');
});

it('uses contextual mismatch copy without changing severity', () => {
  const value = contextualAcceptance();
  value.data.dev_learned_tone!.units[1]!.realization.prediction = 'T3';
  expect(allFeedback(value)[1]!.grade).toMatchObject({ message: 'Expected Tone 2 here · heard Tone 3', agreement: 'PARTIAL_OR_WEAK' });
});

it('shows no helper for unchanged tones, neutral, absent metadata or unresolved mapping', async () => {
  const value = contextualAcceptance();
  for (const i of [2, 3, 4]) expect(contextualToneExplanation(value.data, value.data.syllables[i]!)).toBeNull();
  expect(allFeedback(value)[2]!.grade.message).toBe('Correct · Tone 3');
  expect(allFeedback(value)[3]!.grade.message).toBe('Correct · Tone 4 + neutral');
  await mount(value); await select(2);
  expect(renderer.root.findAllByType(ContextualToneHelp)).toHaveLength(0);
  // Even a supplied ID does not make unchanged lexical/surface tones contextual.
  value.data.dev_learned_tone!.units[2]!.contextual_rule = 'third_tone_sandhi';
  expect(contextualToneExplanation(value.data, value.data.syllables[2]!)).toBeNull();
  delete value.data.dev_learned_tone!.units[1]!.contextual_rule;
  expect(contextualToneExplanation(value.data, value.data.syllables[1]!)).toBeNull();
  value.data.dev_learned_tone!.target_mapping_resolved = false;
  expect(contextualToneExplanation(value.data, value.data.syllables[0]!)).toBeNull();
});

it('uses resolver IDs independently of Hanzi and accepts a future ID without new component types', async () => {
  const value = contextualAcceptance();
  const unit = value.data.dev_learned_tone!.units[1]!;
  const s = value.data.syllables[1]!;
  unit.characters = s.characters = '乙';
  expect(contextualToneExplanation(value.data, s)!.title).toBe('Third-tone sandhi');
  unit.contextual_rule = 'future_context_rule';
  const explanation = contextualToneExplanation(value.data, s)!;
  expect(explanation.title).toBe('Contextual pronunciation');
  expect(explanation.spoken).toBe('Tone 2');
  await act(async () => { renderer = create(React.createElement(ContextualToneHelp, { explanation, characters: s.characters })); });
  await press('Why this tone here for 乙?');
  expect(JSON.stringify(renderer.toJSON())).toContain('Contextual pronunciation');
});

it('keeps feature-off feedback unchanged and hides contextual helpers', async () => {
  const value = contextualAcceptance();
  delete value.data.dev_learned_tone;
  expect(contextualToneExplanation(value.data, value.data.syllables[1]!)).toBeNull();
  expect(firstFeedback(value)).toEqual(gradeChunkPitch(value, pronunciationChunks(value.data)[0]!));
  await mount(value); await select(1);
  expect(renderer.root.findAllByType(ContextualToneHelp)).toHaveLength(0);
});
