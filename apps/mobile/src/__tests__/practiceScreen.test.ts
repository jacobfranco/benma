import React from 'react';
import { Text } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import { registerPlayback } from '@/audio/session';
import { api } from '@/api/client';
import PracticeScreen from '@/app/practice';
import { SpeechEvidence, changedWording } from '@/speech/SpeechEvidence';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));

const mockCapture = {
  start: jest.fn().mockResolvedValue(true),
  stop: jest.fn().mockResolvedValue({ uri: 'file:///speech.m4a', durationMillis: 1200 }),
  error: null, durationMillis: 1200,
};
jest.mock('@/audio/useAudioCapture', () => ({ useAudioCapture: () => mockCapture }));
const mockPlayback = jest.fn();
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: (props: unknown) => { mockPlayback(props); return null; } }));

let renderer: ReactTestRenderer;
async function press(label: string) {
  await act(async () => { renderer.root.findByProps({ accessibilityLabel: label }).props.onPress(); });
}
async function record() { await press('New Attempt'); await press('Stop recording'); }
beforeEach(async () => {
  jest.restoreAllMocks(); jest.clearAllMocks();
  jest.spyOn(console, 'info').mockImplementation(() => {});
  jest.spyOn(api, 'uploadUtterance').mockResolvedValue({ id: 'utterance' } as never);
  jest.spyOn(api, 'createPerception').mockResolvedValue({ id: 'perception', utterance_id: 'utterance', transcript: '你好。' } as never);
  jest.spyOn(api, 'analyzePerceivedSpeech').mockResolvedValue(perceivedAnalysis);
  jest.spyOn(api, 'createConversation'); jest.spyOn(api, 'addConversationUserTurn');
  jest.spyOn(api, 'createAttempt').mockResolvedValue({ id: 'attempt' } as never);
  jest.spyOn(api, 'analyzePronunciation').mockResolvedValue({
    attempt: { id: 'attempt' }, target: { text: '你好', display_pinyin: 'nǐ hǎo' },
    assessment: { status: 'succeeded', normalized_result: { pronunciation_score: 79, evidence_status: 'live_provider' } },
    syllables: [], overall_evidence: {}, recording_audio_url: '/v1/utterances/utterance/audio',
  } as never);
  jest.spyOn(api, 'createTarget').mockResolvedValue({ id: 'target', text: '你好', display_pinyin: 'nǐ hǎo', pinyin_syllables: ['ni3', 'hao3'] } as never);
  jest.spyOn(api, 'createReferenceSpeech').mockResolvedValue({ id: 'ref', status: 'succeeded', audio_url: '/v1/reference-speech/ref/audio', generation_config: {} } as never);
  await act(async () => { renderer = create(React.createElement(PracticeScreen)); });
});
afterEach(async () => { await act(async () => renderer.unmount()); });

it('free Practice shows heard speech without a reply or target-relative score', async () => {
  await record();
  const rendered = JSON.stringify(renderer.toJSON());
  expect(rendered).toContain('你好。');
  expect(rendered).not.toContain('What Benma heard');
  expect(rendered).not.toContain('Your pitch');
  expect(rendered).not.toContain('target phrase is needed');
  const visibleText = renderer.root.findAllByType(Text).map((node) => node.props.children).flat().join(' ');
  expect(visibleText).not.toMatch(/BENMA|\d+%|accuracy score/);
  expect(api.createConversation).not.toHaveBeenCalled();
  expect(api.addConversationUserTurn).not.toHaveBeenCalled();
  expect(api.createAttempt).not.toHaveBeenCalled();
  expect(api.analyzePronunciation).not.toHaveBeenCalled();
});
it('target Practice prepares a reference, then invokes existing known-target assessment', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  expect(api.createTarget).toHaveBeenCalledWith('你好');
  expect(api.createReferenceSpeech).toHaveBeenCalledWith('target');
  expect(mockPlayback).toHaveBeenCalledWith({ compact: true, label: 'Play native reference for 你好', uri: '/v1/reference-speech/ref/audio', disabled: false });
  await record();
  expect(api.createPerception).toHaveBeenCalledWith('utterance');
  expect(api.createAttempt).toHaveBeenCalledWith('utterance', 'target');
  expect(api.analyzePronunciation).toHaveBeenCalledWith('attempt');
  expect(api.addConversationUserTurn).not.toHaveBeenCalled();
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Your pitch');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pronunciation accuracy vs target: 79 (experimental)');
  await press('More details');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pronunciation accuracy vs target: 79 (experimental)');
  expect(api.analyzePerceivedSpeech).toHaveBeenCalled();
});
it.each(['preserve', 'infer', 'clarify'] as const)('renders %s evidence distinctly with selectable Mandarin', async (decision) => {
  await act(async () => renderer.update(React.createElement(SpeechEvidence, {
    heard: '今天聊周谋。', decision, understood: decision === 'infer' ? '今天聊周末。' : decision === 'preserve' ? '今天聊周谋。' : null,
  })));
  const rendered = JSON.stringify(renderer.toJSON());
  expect(renderer.root.findByProps({ children: '今天聊周谋。' }).props.selectable).toBe(true);
  if (decision === 'infer') {
    expect(rendered).toContain('What Benma understood');
    expect(rendered).toContain('Benma heard');
    expect(rendered).not.toContain('pronounced');
  } else {
    expect(rendered).not.toContain('What Benma understood');
    if (decision === 'clarify') expect(rendered).toContain('unsure');
  }
});
it('describes exact changed characters without assigning pronunciation blame', () => {
  expect(changedWording('今天聊周谋。', '今天聊周末。')).toEqual({ heard: '谋', understood: '末' });
});

it('keeps the prepared reference mounted but disabled during recording so replay retains its cache', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  mockPlayback.mockClear();
  await press('New Attempt');
  expect(mockPlayback).toHaveBeenCalledWith({
    compact: true, label: 'Play native reference for 你好', uri: '/v1/reference-speech/ref/audio', disabled: true,
  });
  await press('Stop recording');
  expect(mockPlayback).toHaveBeenCalledWith({
    compact: true, label: 'Play native reference for 你好', uri: '/v1/reference-speech/ref/audio', disabled: false,
  });
});

it('an incomplete CLARIFY utterance retains conservative speech feedback and separate unresolved meaning', async () => {
  await act(async () => renderer.update(React.createElement(SpeechEvidence, {
    heard: '你好，今天我……', decision: 'clarify', understood: null,
    recordingUrl: '/v1/utterances/u/audio',
    analysis: { utteranceId: 'u', state: 'ready', perceived: perceivedAnalysis },
  })));
  const rendered = JSON.stringify(renderer.toJSON());
  expect(rendered).toContain('你好，今天我……');
  expect(rendered).not.toContain('Your pitch');
  expect(rendered).toContain('perceived-sentence-overview');
  expect(rendered).toContain('Meaning');
  expect(rendered).toContain('unsure');
  expect(rendered).not.toMatch(/trailing off|accuracy|target phrase is needed/i);
  expect(mockPlayback).toHaveBeenCalledWith({ uri: '/v1/utterances/u/audio', compact: true, label: 'Play my full recording' });
});

it('optional target-analysis failure leaves heard speech and the next recording available', async () => {
  jest.spyOn(api, 'analyzePronunciation').mockRejectedValue(new Error('analysis failed'));
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  await record();
  expect(JSON.stringify(renderer.toJSON())).toContain('你好。');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Your pitch');
  await press('New Attempt');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Stop recording' })).toBeTruthy();
});

it('retains one prepared target through three completed turns and rerenders; changes explicitly', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  for (let i = 0; i < 3; i++) {
    await record();
    await act(async () => renderer.update(React.createElement(PracticeScreen)));
    expect(JSON.stringify(renderer.toJSON())).toContain('Target');
  }
  expect(api.createAttempt).toHaveBeenCalledTimes(3);
  expect(jest.mocked(api.createAttempt).mock.calls.map(call => call[1])).toEqual(['target', 'target', 'target']);
  expect(api.analyzePerceivedSpeech).toHaveBeenCalled();
  await press('Change target');
  expect(renderer.root.findByProps({ accessibilityLabel: 'New Attempt' }).props.disabled).toBe(true);
  await press('Close Change target');
  await press('Clear target');
  await record();
  expect(api.analyzePerceivedSpeech).toHaveBeenCalledTimes(4);
});

it('changing 嘛 to 麻 records against the visible new target and retains it for repeats', async () => {
  jest.mocked(api.createTarget)
    .mockResolvedValueOnce({ id: 'neutral', text: '嘛', display_pinyin: 'ma', pinyin_syllables: ['ma5'] } as never)
    .mockResolvedValueOnce({ id: 'rising', text: '麻', display_pinyin: 'má', pinyin_syllables: ['ma2'] } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('嘛'));
  await press('Prepare target');
  await record();
  expect(api.createAttempt).toHaveBeenLastCalledWith('utterance', 'neutral');
  await press('Change target');
  expect(renderer.root.findByProps({ accessibilityLabel: 'New Attempt' }).props.disabled).toBe(true);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('麻'));
  await press('Prepare target');
  expect(api.createTarget).toHaveBeenLastCalledWith('麻');
  expect(renderer.root.findByProps({ children: '麻' })).toBeTruthy();
  for (let i = 0; i < 2; i++) {
    await record();
    expect(api.createAttempt).toHaveBeenLastCalledWith('utterance', 'rising');
  }
  expect(jest.mocked(api.createAttempt).mock.calls.map(call => call[1])).toEqual(['neutral', 'rising', 'rising']);
});

it('keeps the recorded target snapshot and perceived graph independent of legacy attempt data', async () => {
  jest.mocked(api.analyzePronunciation).mockResolvedValue({
    attempt: { id: 'attempt' }, target: { id: 'persisted-neutral', text: '嘛', display_pinyin: 'ma' },
    syllables: [], overall_evidence: {}, recording_audio_url: '/v1/utterances/utterance/audio',
  } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  await record();
  expect(api.createAttempt).toHaveBeenCalledWith('utterance', 'target');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('嘛');
  await press('More details');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('persisted-neutral');
});

it.each(['synthetic_replay', 'unknown'])('never presents a %s provider score as real assessment', async evidence_status => {
  jest.mocked(api.analyzePronunciation).mockResolvedValue({
    attempt: { id: 'attempt' }, target: { text: '妈', display_pinyin: 'mā' },
    assessment: { normalized_result: { pronunciation_score: 79, evidence_status } },
    syllables: [{ syllable_index: 0, characters: '妈', expected_surface_tone: 1,
      observed_contour: { classification: '1-like', confidence: 'moderate', reason: 'acoustic_shape_only' } }],
    overall_evidence: {}, recording_audio_url: '/v1/utterances/utterance/audio',
  } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('妈'));
  await press('Prepare target'); await record();
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pitch signal: Limited');
  await press('More details');
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).not.toContain('Pronunciation accuracy vs target: 79');
  expect(tree).not.toMatch(/Good ·|Tone 1 ✓|Yours sounded|Correct|Perfect/);
});

it.each([false, true])('no speech leaves Practice ready to rerecord, with prepared target=%s intact', async withTarget => {
  if (withTarget) {
    await press('Add a target phrase');
    await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
    await press('Prepare target');
  }
  jest.mocked(api.uploadUtterance).mockRejectedValueOnce({ code: 'no_speech' });
  await record();
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain("Didn't catch any speech. Try again.");
  expect(tree).not.toContain('What Benma heard'); expect(tree).not.toContain('Your pitch');
  expect(api.createPerception).not.toHaveBeenCalled(); expect(api.createAttempt).not.toHaveBeenCalled();
  expect(api.analyzePerceivedSpeech).not.toHaveBeenCalled(); expect(api.analyzePronunciation).not.toHaveBeenCalled();
  expect(renderer.root.findByProps({ accessibilityLabel: 'New Attempt' }).props.disabled).toBe(false);
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'Retry' })).toHaveLength(0);
  await record();
  expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(1);
  if (withTarget) expect(api.createAttempt).toHaveBeenCalledWith('utterance', 'target');
});

it('re-record replaces the workspace; history reopens an earlier attempt and marks the current one', async () => {
  for (let i = 1; i <= 3; i++) {
    jest.mocked(api.createPerception).mockResolvedValueOnce({ id: `p${i}`, utterance_id: `u${i}`, transcript: `第${i}次` } as never);
    jest.mocked(api.analyzePerceivedSpeech).mockResolvedValueOnce({ ...perceivedAnalysis, id: `a${i}`, perception_run_id: `p${i}`, utterance_id: `u${i}` });
    await record();
    expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(1);
    expect(renderer.root.findByType(SpeechEvidence).props.heard).toBe(`第${i}次`);
    expect(renderer.root.findByProps({ accessibilityLabel: 'New Attempt' })).toBeTruthy();
  }
  await press('History');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Open attempt 3' }).props.accessibilityState.selected).toBe(true);
  expect(renderer.root.findByProps({ accessibilityLabel: 'Open attempt 1' })).toBeTruthy();
  await press('Open attempt 1');
  expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(1);
  expect(renderer.root.findByType(SpeechEvidence).props.heard).toBe('第1次');
  expect(renderer.root.findByType(SpeechEvidence).props.analysis.perceived.id).toBe('a1');
  await press('History');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Open attempt 1' }).props.accessibilityState.selected).toBe(true);
});

it('New Attempt clears active graphs immediately, stops playback, and preserves target/history', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target'); await record();
  const stop = jest.fn(), unregister = registerPlayback(stop);
  await press('New Attempt');
  expect(stop).toHaveBeenCalled();
  expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(0);
  expect(renderer.root.findAllByProps({ testID: 'selected-pronunciation-detail' })).toHaveLength(0);
  expect(renderer.root.findByProps({ children: '你好' })).toBeTruthy();
  jest.mocked(api.uploadUtterance).mockRejectedValueOnce({ code: 'no_speech' });
  await press('Stop recording');
  expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(0);
  await press('History'); await press('Open attempt 1');
  expect(renderer.root.findByType(SpeechEvidence).props.heard).toBe('你好。');
  unregister();
});

it('Clear target removes attempts and ignores analysis arriving from the old exercise', async () => {
  let finish!: (value: typeof perceivedAnalysis) => void;
  jest.mocked(api.analyzePerceivedSpeech).mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target'); await record();
  await press('Clear target');
  await act(async () => finish(perceivedAnalysis));
  expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(0);
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'History' })).toHaveLength(0);
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'Clear target' })).toHaveLength(0);
  expect(JSON.stringify(renderer.toJSON())).toContain('Free Practice');
  await record();
  expect(renderer.root.findByType(SpeechEvidence).props.intendedText).toBeUndefined();
  expect(api.createAttempt).toHaveBeenCalledTimes(1);
});

it('offers only provided lexical readings, preserves raw perception and omits single-reading edits', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'Edit reading' })).toHaveLength(0);
  const target = { id: 'polyphone', text: '行', display_pinyin: 'xíng', pinyin_syllables: ['xing2'], pinyin_alternatives: [['xing2', 'hang2']] };
  jest.mocked(api.createTarget).mockResolvedValueOnce(target as never);
  jest.spyOn(api, 'correctTargetPinyin').mockResolvedValueOnce({ ...target, id: 'revision', pinyin_syllables: ['hang2'], display_pinyin: 'háng' } as never);
  await press('Change target');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('行'));
  await press('Prepare target'); await record();
  const raw = renderer.root.findByType(SpeechEvidence).props.heard;
  await press('Edit reading');
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'Corrected numeric pinyin' })).toHaveLength(0);
  expect([...new Set(renderer.root.findAllByProps({ accessibilityRole: 'radio' }).map(n => n.props.accessibilityLabel))]).toEqual(['行: xing2', '行: hang2']);
  await press('行: hang2'); await press('Use this reading');
  expect(api.correctTargetPinyin).toHaveBeenCalledWith('polyphone', 'hang2');
  expect(renderer.root.findByType(SpeechEvidence).props.heard).toBe(raw);
  expect(renderer.root.findByType(SpeechEvidence).props.intendedText).toBe('行');
});

it.each([500, 10000])('a %sms no-speech response at perception cannot create a learner attempt', async duration => {
  mockCapture.durationMillis = duration;
  mockCapture.stop.mockResolvedValueOnce({ uri: 'file:///silence.m4a', durationMillis: duration });
  jest.mocked(api.createPerception).mockRejectedValueOnce({ code: 'no_speech' });
  await record();
  expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(0);
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'History' })).toHaveLength(0);
  expect(api.createAttempt).not.toHaveBeenCalled();
  expect(api.analyzePerceivedSpeech).not.toHaveBeenCalled();
});

it('valid short speech has no client duration cutoff', async () => {
  mockCapture.stop.mockResolvedValueOnce({ uri: 'file:///short.m4a', durationMillis: 350 });
  jest.mocked(api.createPerception).mockResolvedValueOnce({ id: 'short', utterance_id: 'utterance', transcript: '好' } as never);
  await record();
  expect(renderer.root.findByType(SpeechEvidence).props.heard).toBe('好');
});

it('keeps 广州 target distinct from 贵州 perception, readings and both playback identities', async () => {
  const evidence = { ...perceivedAnalysis, utterance_id: 'utterance', alignment_reference_text: '贵州',
    data: { ...perceivedAnalysis.data, syllables: perceivedAnalysis.data.syllables.map((s, index) => ({ ...s,
      characters: ['贵', '州'][index]!, pinyin: ['guì', 'zhōu'][index]!, lexical_tone: index === 0 ? 4 as const : 1 as const,
    })) } };
  const saved = JSON.stringify(evidence);
  jest.mocked(api.createPerception).mockResolvedValueOnce({ id: 'perception', utterance_id: 'utterance', transcript: '贵州' } as never);
  jest.mocked(api.analyzePerceivedSpeech).mockResolvedValueOnce(evidence);
  jest.mocked(api.createTarget).mockResolvedValueOnce({ id: 'guangzhou', text: '广州', display_pinyin: 'guǎng zhōu',
    pinyin_syllables: ['guang3', 'zhou1'], pinyin_alternatives: [['guang3'], ['zhou1']] } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('广州'));
  await press('Prepare target'); await record();
  expect(renderer.root.findByProps({ children: '广州' })).toBeTruthy();
  expect(renderer.root.findByType(SpeechEvidence).props).toMatchObject({ heard: '贵州', intendedText: '广州' });
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-0' }).props.accessibilityLabel).toContain('贵');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Play my recording for 贵' })).toBeTruthy();
  expect(mockPlayback).toHaveBeenCalledWith({ compact: true, label: 'Play my full recording', uri: '/v1/utterances/utterance/audio' });
  expect(mockPlayback).toHaveBeenCalledWith({ compact: true, label: 'Play native reference for 广州', uri: '/v1/reference-speech/ref/audio', disabled: false });
  expect(JSON.stringify(evidence)).toBe(saved);
});
