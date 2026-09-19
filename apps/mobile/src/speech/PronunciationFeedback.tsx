import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import type { PronunciationResult, DisplayContour } from '@/api/types';
import { PlaybackButton } from '@/audio/PlaybackButton';
import { PitchPlot, type PitchPoint } from '@/components/PitchPlot';
import { SyllableComparison, lexicalShapes } from '@/speech/SyllableComparison';
import { Body, Chinese, FixtureBanner, Pinyin } from '@/components/Ui';

function map(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? value as Record<string, unknown> : {};
}
const points = (value: unknown) => Array.isArray(value) ? value as PitchPoint[] : [];

export function PronunciationFeedback({ result }: { result: PronunciationResult }) {
  const [details, setDetails] = useState(false);
  const assessment = map(result.assessment?.normalized_result);
  const accuracy = assessment.pronunciation_score;
  const invalid = map(result.overall_evidence.recording_quality).status === 'invalid_for_interpretation';
  const regions = result.syllables.flatMap((syllable) => {
    const timing = map(syllable.timing);
    return typeof timing.start_seconds === 'number' && typeof timing.end_seconds === 'number'
      ? [{ label: syllable.characters, start_seconds: timing.start_seconds, end_seconds: timing.end_seconds }] : [];
  });
  return <View style={{ gap: 12 }}>
    {map(result.assessment?.normalized_result).evidence_status === 'synthetic_replay' && <FixtureBanner />}
    <Body>Target phrase</Body>
    <Chinese>{result.target.text}</Chinese>
    <Pinyin>{result.target.display_pinyin}</Pinyin>
    <Body>Experimental pronunciation analysis</Body>
    {!invalid && typeof accuracy === 'number' && Number.isFinite(accuracy) &&
      <Body>{`Pronunciation accuracy vs target: ${Math.round(accuracy)} (experimental)`}</Body>}
    <SyllableComparison syllables={result.syllables.map(s => ({
      index: s.syllable_index, characters: s.characters,
      pinyin: result.target.display_pinyin.split(' ')[s.syllable_index] ?? s.pinyin,
      lexical_tone: s.lexical_tone as 0 | 1 | 2 | 3 | 4 | null,
      expected_tone: (lexicalShapes[s.lexical_tone ?? -1] ?? []).map((height, i, values) => ({ position: i/(values.length-1), height })),
      expected_surface_tone: s.expected_surface_tone,
      expected_surface_shape: (lexicalShapes[s.expected_surface_tone ?? -1] ?? []).map((height, i, values) => ({ position: i/(values.length-1), height })),
      display_contour: s.display_contour, observed_contour: s.observed_contour,
      start_seconds: typeof s.timing?.start_seconds === 'number' ? s.timing.start_seconds : null,
      end_seconds: typeof s.timing?.end_seconds === 'number' ? s.timing.end_seconds : null,
    }))} />
    {invalid && <Body>Recording issue. Try a quieter, clearer recording.</Body>}
    {result.reference_audio?.audio_url && <PlaybackButton label="▶ Reference" uri={result.reference_audio.audio_url} />}
    <PlaybackButton label="▶ Mine" uri={result.recording_audio_url} />
    <Pressable accessibilityRole="button" accessibilityState={{ expanded: details }} onPress={() => setDetails(value => !value)}>
      <Body>{details ? 'Less detail' : 'More detail'}</Body>
    </Pressable>
    {details && <View style={{ gap: 10 }}>
      <Body>Whole utterance</Body>
      <PitchPlot reference={points(map(result.reference_audio?.acoustic_result).mobile_f0)}
        referenceDisplay={map(result.reference_audio?.acoustic_result).display_contour as DisplayContour | undefined}
        display={result.display_contour} regions={regions} user={points(map(result.acoustic?.normalized_result).mobile_f0)} />
      <Body>Expected here uses connected-speech rules; Mine is an approximate acoustic shape. Dictionary tones stay separate from the provider’s target-relative assessment.</Body>
      {!invalid && result.syllables.map(syllable => <View key={syllable.syllable_index} style={{ gap: 4 }}>
        <Chinese>{syllable.characters}</Chinese><Pinyin>{syllable.pinyin}</Pinyin>
        <Text>Expected surface {syllable.expected_surface_tone === 0 ? 'neutral tone' : `tone ${syllable.expected_surface_tone ?? 'unresolved'}`}</Text>
        <Text selectable>{String(map(syllable.interpretation).message ?? 'Could not evaluate this syllable reliably.')}</Text>
      </View>)}
    </View>}

  </View>;
}
