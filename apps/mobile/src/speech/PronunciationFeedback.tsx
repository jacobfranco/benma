import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { learnerVerdict } from '@/speech/learnerVerdict';
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
  const fixture = result.assessment?.provider === 'replay' || assessment.evidence_status === 'synthetic_replay';
  const liveAssessment = !fixture && result.assessment?.status === 'succeeded' && assessment.evidence_status === 'live_provider';
  const judged = result.syllables.some(s => learnerVerdict(s.expected_surface_tone, s.observed_contour) !== 'unclear');
  const invalid = map(result.overall_evidence.recording_quality).status === 'invalid_for_interpretation';
  const regions = result.syllables.flatMap((syllable) => {
    const timing = map(syllable.timing);
    return typeof timing.start_seconds === 'number' && typeof timing.end_seconds === 'number'
      ? [{ label: syllable.characters, start_seconds: timing.start_seconds, end_seconds: timing.end_seconds }] : [];
  });
  return <View style={{ gap: 12 }}>
    {fixture && <FixtureBanner message="Provider assessment is a development fixture. Tone feedback uses local recording evidence." />}
    <Body>Target phrase</Body>
    <Chinese>{result.target.text}</Chinese>
    <Pinyin>{result.target.display_pinyin}</Pinyin>
    <Body>Experimental pronunciation analysis</Body>
    <SyllableComparison gradeTarget syllables={result.syllables.map(s => ({
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
    {result.syllables.some(s => s.expected_surface_tone === 0) && <Body>Neutral tone has context-dependent pitch. Mine describes its shape, not correctness. A reference pronunciation is one natural realization.</Body>}
    {invalid && <Body>{judged ? 'Only part of the recording had clear pitch evidence.' : 'Try again with a steady recording.'}</Body>}
    {result.reference_audio?.audio_url && <PlaybackButton label="▶ Reference" uri={result.reference_audio.audio_url} />}
    <PlaybackButton label="▶ Mine" uri={result.recording_audio_url} />
    <Pressable accessibilityLabel={details ? 'Less detail' : 'More detail'} accessibilityRole="button" accessibilityState={{ expanded: details }} onPress={() => setDetails(value => !value)}>
      <Body>{details ? 'Less detail' : 'More detail'}</Body>
    </Pressable>
    {details && <View style={{ gap: 10 }}>
      {liveAssessment && !invalid && typeof accuracy === 'number' && Number.isFinite(accuracy) &&
      <Body>{`Pronunciation accuracy vs target: ${Math.round(accuracy)} (experimental)`}</Body>}
      {fixture && <Body>Developer detail: provider assessment is synthetic and excluded from learner evaluation.</Body>}
      <Text selectable>Target: {result.target.id} · {result.target.text} · {result.target.display_pinyin}</Text>
      <Body>Whole utterance · full contour including onset</Body>
      <PitchPlot reference={points(map(result.reference_audio?.acoustic_result).mobile_f0)}
        referenceDisplay={map(result.reference_audio?.acoustic_result).display_contour as DisplayContour | undefined}
        display={result.display_contour} regions={regions} user={points(map(result.acoustic?.normalized_result).mobile_f0)} />
      <Body>Raw measured pitch</Body>
      <PitchPlot user={points(map(result.acoustic?.normalized_result).f0 ?? map(result.acoustic?.normalized_result).mobile_f0)} />
      <Body>Mine summarizes the broad pitch evidence used for the tone judgment. Detail shows measured pitch over time, including gaps. Expected is a teaching example; exact overlap is not required.</Body>
      {result.syllables.map(syllable => <View key={syllable.syllable_index} style={{ gap: 4 }}>
        <Chinese>{syllable.characters}</Chinese><Pinyin>{syllable.pinyin}</Pinyin>
        <Text>Expected surface {syllable.expected_surface_tone === 0 ? 'neutral tone' : `tone ${syllable.expected_surface_tone ?? 'unresolved'}`}</Text>
        <Text>Observed shape: {syllable.observed_contour?.classification ?? 'unclear'}</Text>
        <Text>Evidence confidence: {syllable.observed_contour?.confidence ?? 'unavailable'}</Text>
        <Text>Reason: {syllable.observed_contour?.reason ?? 'unavailable'}</Text>
        <Text>Evidence interval: {String(syllable.observed_contour?.features?.evidence_start_seconds ?? syllable.timing?.start_seconds ?? '?')}–{String(syllable.observed_contour?.features?.evidence_end_seconds ?? syllable.timing?.end_seconds ?? '?')} s · gaps: {syllable.observed_contour?.features?.gap_count ?? '?'}</Text>
        <Text>Retained core: {syllable.observed_contour?.features?.first_reliable_core_seconds ?? '?'}–{syllable.observed_contour?.features?.last_reliable_core_seconds ?? '?'} s</Text>
        <Text>Recording quality: {invalid ? 'Partial' : String(map(result.overall_evidence.recording_quality).status ?? 'unavailable')}</Text>
        <Text>Reliable evidence: {syllable.observed_contour?.features?.retained_display_frames ?? '?'} frames / {Math.round((syllable.observed_contour?.features?.voiced_duration_seconds ?? 0)*1000)} ms</Text>
        {syllable.observed_contour?.features?.evidence_region_selected === 1 && <Text>Boundary evidence excluded: {syllable.observed_contour.features.excluded_onset_frames} onset / {syllable.observed_contour.features.excluded_terminal_frames} terminal frames</Text>}
        {liveAssessment && map(syllable.interpretation).observed_provider_tone != null &&
        <Text selectable>{`Provider detail: ${String(map(syllable.interpretation).message ?? '')}`}</Text>}
      </View>)}
    </View>}

  </View>;
}
