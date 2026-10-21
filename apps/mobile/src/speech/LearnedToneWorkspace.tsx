import { useEffect, useState, type ReactNode } from 'react';
import { Pressable, Text, View } from 'react-native';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { ExactPlaybackButton, useCanonicalRecording } from '@/audio/ExactPlaybackButton';
import { stopAllPlayback } from '@/audio/session';
import { PitchPlot } from '@/components/PitchPlot';
import { colors } from '@/theme';

type Learned = NonNullable<PerceivedSpeechAnalysis['data']['dev_learned_tone']>;

export function toneRendering(data: Learned): { target: string; heard: string } {
  return {
    target: data.units.map(u => u.target_pinyin ?? '…').join(' '),
    // Keep neutral reading; a numbered abstention is explicitly unknown, never a match.
    heard: data.units.map(u => u.comparison.state === 'neutral'
      ? (u.target_pinyin ?? '…') : (u.heard_pinyin ?? '[unclear]')).join(' '),
  };
}

export function LearnedToneWorkspace({ analysis, phraseActions }: { analysis: PerceivedSpeechAnalysis; phraseActions?: ReactNode }) {
  const learned = analysis.data.dev_learned_tone!;
  const [selected, setSelected] = useState(0);
  const [debug, setDebug] = useState(false);
  const unit = learned.units[selected];
  const syllable = analysis.data.syllables[selected];
  const rendering = toneRendering(learned);
  const span = unit?.realization.azure_span;
  const display = analysis.data.tone_graph?.filtered ?? analysis.data.display_contour;
  const fetchRecording = useCanonicalRecording(analysis.utterance_id);
  useEffect(() => () => stopAllPlayback(), []);
  return <View testID="learned-tone-workspace" style={{ gap: 10 }}>
    <Text style={{ color: colors.secondary }}>Experimental tone realization</Text>
    <Text>{learned.expectation_basis === 'intended_target' ? 'Target' : 'Transcript reference'}: {learned.target_text}</Text>
    <Text testID="learned-target-rendering">{learned.target_mapping_resolved === false ? 'Transcript reading (target mapping unresolved)' : 'Target reading'}: {rendering.target}</Text>
    <Text testID="learned-heard-rendering">Heard-tone rendering: {rendering.heard}</Text>
    <Text style={{ color: colors.secondary }}>Tone rendering uses the same syllables, not lexical ASR. Unclear tones are not errors; neutral syllables keep their contextual reading.</Text>
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
      {learned.units.map((u, i) => <Pressable key={u.index} accessibilityRole="button"
        accessibilityLabel={`Inspect ${u.characters}, ${u.realization.prediction ?? 'unclear'}`}
        accessibilityState={{ selected: selected === i }} onPress={() => { stopAllPlayback(); setSelected(i); }}
        style={{ padding: 10, borderWidth: 1, borderColor: selected === i ? colors.text : colors.secondary, borderRadius: 8 }}>
        <Text style={{ fontSize: 24 }}>{u.characters}</Text>
        <Text>{u.comparison.state === 'neutral' ? 'Neutral' : u.realization.prediction ? `${u.realization.prediction}-like` : 'Unclear'}</Text>
      </Pressable>)}
      {phraseActions}
    </View>
    {display && <PitchPlot user={[]} display={display} durationSeconds={analysis.data.duration_seconds}
      regions={analysis.data.syllables.flatMap(s => s.start_seconds != null && s.end_seconds != null
        ? [{ label: s.characters, start_seconds: s.start_seconds, end_seconds: s.end_seconds }] : [])} />}
    {unit && <View testID="learned-selected-detail" style={{ gap: 8 }}>
      <Text>{unit.characters} · {unit.target_pinyin ?? 'Reading unresolved'} · lexical {unit.lexical_tone === 0 ? 'neutral' : unit.lexical_tone == null ? 'unresolved' : `T${unit.lexical_tone}`}</Text>
      <Text>Expected surface: {unit.expected_surface_tone === 0 ? 'neutral' : unit.expected_surface_tone == null ? 'unresolved' : `T${unit.expected_surface_tone}`}</Text>
      {span && <ExactPlaybackButton utteranceId={analysis.utterance_id} text={unit.characters}
        start={span[0]!} end={span[1]!} fetchRecording={fetchRecording} />}
      {display && span && <PitchPlot user={[]} display={{ ...display, segments: (display.segments ?? []).map(segment => segment.filter(p => p.timestamp_seconds >= span[0]! && p.timestamp_seconds < span[1]!)) }}
        startSeconds={span[0]!} durationSeconds={span[1]!} />}
      {unit.expected_surface_tone != null && unit.expected_surface_tone > 0 && <Text>
        Expected contour (schematic): {({ 1: 'high level ─', 2: 'rising ↗', 3: 'low / dipping ↘↗', 4: 'falling ↘' } as Record<number, string>)[unit.expected_surface_tone]}
      </Text>}
      <Text testID="learned-comparison">{unit.comparison.message}</Text>
      {unit.comparison.explanation && <Text>{unit.comparison.explanation}</Text>}
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: debug }} onPress={() => setDebug(!debug)}>
        <Text style={{ color: colors.secondary }}>Dev evidence {debug ? '−' : '+'}</Text>
      </Pressable>
      {debug && <Text selectable testID="learned-debug">{JSON.stringify({ unit, f0: syllable?.observed_contour,
        eligibility: syllable?.pitch_eligibility, timings_ms: learned.timings_ms, runtime: learned.runtime }, null, 2)}</Text>}
    </View>}
  </View>;
}
