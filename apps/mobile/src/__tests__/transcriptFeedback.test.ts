import React from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import { SpeechEvidence } from '@/speech/SpeechEvidence';
import { PitchPlot, pitchDots } from '@/components/PitchPlot';

const mockReplay = jest.fn();
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: (props: unknown) => { mockReplay(props); return null; } }));

it.each(['preserve', 'infer', 'clarify'] as const)('keeps the same measured chart and heard reference during %s', async (decision) => {
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, {
    heard: '周谋', decision, understood: decision === 'infer' ? '周末' : null,
    analysis: { utteranceId: 'u', state: 'ready', perceived: perceivedAnalysis },
    recordingUrl: '/v1/utterances/u/audio',
  })); });
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('Expected here · acoustic shapes');
  expect(tree).toContain('zhōu'); expect(tree).toContain('móu');
  expect(tree).not.toMatch(/accuracy|correctness|target required|mò/);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(0);
  expect(tree).not.toContain('Pitch is relative');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More detail' }).props.onPress());
  expect(renderer.root.findByType(PitchPlot).props.user).toEqual(perceivedAnalysis.data.measured_pitch);
  expect(tree.includes('What Benma understood')).toBe(decision === 'infer');
  expect(tree.includes('Meaning')).toBe(decision === 'clarify');
  expect(mockReplay).toHaveBeenCalledWith({ uri: '/v1/utterances/u/audio', label: '▶ Play mine' });
  await act(async () => renderer.unmount());
});

it('keeps raw pitch visible without alignment or resolved readings', async () => {
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, {
    heard: '行……', decision: 'clarify', analysis: { utteranceId: 'u', state: 'ready', perceived: {
      ...perceivedAnalysis, data: { ...perceivedAnalysis.data, alignment_status: 'unavailable',
        syllables: [{ ...perceivedAnalysis.data.syllables[0]!, characters: '行', pinyin: null,
          lexical_tone: null, expected_tone: [], reading_source: 'unresolved', alternatives: ['xing2', 'hang2'] }] },
    } },
  })); });
  expect(JSON.stringify(renderer.toJSON())).toContain('Reading unresolved');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More detail' }).props.onPress());
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('Relative pitch contour');
  expect(tree).toContain('timing is unavailable');
  expect(tree).toContain('reading unresolved');
  expect(tree).toContain('Meaning');
  await act(async () => renderer.unmount());
});

it('does not invent pitch in unvoiced spans and keeps the full recording time axis', () => {
  const dots = pitchDots([
    { timestamp_seconds: 0.5, normalized_semitones: 0 },
    { timestamp_seconds: 1, normalized_semitones: null },
    { timestamp_seconds: 2, normalized_semitones: null },
  ], 200, 100, 2);
  expect(dots).toHaveLength(1);
  expect(dots[0]!.x).toBe(50);
  expect(pitchDots([{ timestamp_seconds: NaN, normalized_semitones: 0 }], 200, 100)).toEqual([]);
});

it('pairs expected and observed shapes locally, with the overview collapsed', async () => {
  const analysis = { ...perceivedAnalysis, data: { ...perceivedAnalysis.data,
    syllables: [{ ...perceivedAnalysis.data.syllables[1]!,
      observed_contour: { classification: '4-like' as const, confidence: 'moderate' as const },
      display_contour: { segments: [[{ timestamp_seconds: .7, normalized_semitones: 2 },
        { timestamp_seconds: .72, normalized_semitones: 1 }]] },
    }],
  } };
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, {
    heard: '谋', analysis: { utteranceId: 'u', state: 'ready', perceived: analysis },
  })); });
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('Tone 2'); expect(tree).toContain('Tone 4-like');
  expect(tree).toContain('Expected lexical tone 2');
  expect(tree).not.toContain('Whole utterance');
  expect(tree).not.toContain('Connected speech');
  await act(async () => renderer.unmount());
});

it('shows surface expectations and measured Mine without overwriting the lexical reading', async () => {
  let renderer!: ReactTestRenderer;
  const syllable = { ...perceivedAnalysis.data.syllables[0]!, characters: '你', pinyin: 'nǐ',
    lexical_tone: 3 as const, expected_surface_tone: 2 as const,
    expected_surface_shape: [{ position: 0, height: .5 }, { position: 1, height: 1 }],
    observed_contour: { classification: '4-like' as const, confidence: 'moderate' as const } };
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, {
    heard: '你', analysis: { utteranceId: 'u', state: 'ready', perceived: {
      ...perceivedAnalysis, data: { ...perceivedAnalysis.data, syllables: [syllable] },
    } },
  })); });
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('nǐ'); expect(tree).toContain('Expected surface tone 2');
  expect(tree).toContain('Tone 4-like');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More detail' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('dictionary');
  expect(syllable.lexical_tone).toBe(3);
  await act(async () => renderer.unmount());
});

it('preserves a non-Han transcript in a compact fallback, without empty syllable cards', async () => {
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, { heard: 'Neal zaigan shima' })); });
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('Neal zaigan shima');
  expect(tree).toContain('Pronunciation unavailable');
  expect(tree).not.toContain('syllable-skeleton');
  expect(renderer.root.findByProps({ testID: 'pronunciation-section' }).props.style.minHeight).toBe(0);
  await act(async () => renderer.unmount());
});
