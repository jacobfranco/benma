import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { ExactPlaybackButton, useCanonicalRecording } from '@/audio/ExactPlaybackButton';
import { stopAllPlayback } from '@/audio/session';
import { PitchPlot } from '@/components/PitchPlot';
import { WorkspaceDialog } from '@/components/WorkspaceActions';
import { SentenceToneGraph } from '@/speech/SentenceToneGraph';
import { defaultUnit, pronunciationUnits, unitPitch, unitPresentation } from '@/speech/pronunciationWorkspace';
import { expectedLabel } from '@/speech/sentenceToneGraph';
import { toneGestureMatch } from '@/speech/toneGestureMatch';
import { colors } from '@/theme';

export function PronunciationWorkspace({ analysis, phraseActions }: { analysis: PerceivedSpeechAnalysis; phraseActions?: ReactNode }) {
  const { data } = analysis;
  const units = useMemo(() => pronunciationUnits(data), [data]);
  const [selectedId, setSelectedId] = useState(() => defaultUnit(units));
  const [details, setDetails] = useState(false);
  const selected = units.find(u => u.id === selectedId);
  const contour = useMemo(() => selected ? unitPitch(data, selected, units) : null, [data, selected, units]);
  const fetchRecording = useCanonicalRecording(analysis.utterance_id);
  useEffect(() => () => stopAllPlayback(), []);
  const observed = selected && !selected.grouped && selected.eligibility?.state === 'sufficient'
    ? toneGestureMatch(selected.members[0]!).observed_gesture : null;
  return <View style={styles.workspace} testID="pronunciation-workspace">
    {!!units.length && <View testID="perceived-sentence-overview" style={styles.sentence}>
      {data.syllables.map(s => {
        const unit = units.find(u => u.members.includes(s));
        if (unit && unit.members[0] !== s) return null;
        if (!unit) return <Text key={`untimed-${s.index}`} style={styles.untimed}>{s.characters}</Text>;
        const presentation = unitPresentation(unit);
        return <Pressable key={unit.id} testID={`pronunciation-unit-${s.index}`} accessibilityRole="button"
          accessibilityLabel={`${unit.text}, ${presentation.label}${unit.grouped ? ', grouped timing' : ''}`}
          accessibilityState={{ selected: unit.id === selectedId }}
          onPress={() => { stopAllPlayback(); setSelectedId(unit.id); }}
          style={[styles.unit, { backgroundColor: presentation.background }, unit.id === selectedId && styles.selected]}>
          <Text style={styles.character}>{unit.text}</Text>
        </Pressable>;
      })}
      {phraseActions}
    </View>}
    {!units.length && <Text style={styles.caption}>Timing-specific feedback is unavailable. You can still play the whole recording.</Text>}
    {!!units.length && !selected && <Text style={styles.caption}>Not enough trustworthy pitch evidence to choose a unit. Tap any timed unit to hear it and inspect its measurements.</Text>}
    {selected && <View testID="selected-pronunciation-detail" style={styles.detail}>
      <View style={styles.identity}>
        <Text style={styles.detailCharacter}>{selected.text}</Text>
        <Text style={styles.reading}>{selected.members.map(s => s.reading_source !== 'unresolved' && s.pinyin ? s.pinyin : 'Reading unresolved').join(' · ')}</Text>
        <ExactPlaybackButton key={selected.id} utteranceId={analysis.utterance_id} text={selected.text}
          start={selected.start} end={selected.end} fetchRecording={fetchRecording} />
      </View>
      <PitchPlot user={[]} display={contour} startSeconds={selected.start} durationSeconds={selected.end}
        fixedDisplayDomain showPoints showMineLabel={false} plotHeight={104} />
      <Text style={styles.gesture}>{observed && observed !== 'unclear'
        ? `${({ level: 'Mostly level', rising: 'Rising', falling: 'Falling', dipping: 'Dipping' } as const)[observed]} · experimental`
        : selected.grouped ? 'Grouped phrase · gesture unavailable' : 'Gesture unavailable'}</Text>
      <Text style={styles.status}>{unitPresentation(selected).label}</Text>
      {selected.eligibility?.state === 'unstable' && <Text style={styles.caption}>Some pitch measurements disagree.</Text>}
      {selected.eligibility?.state === 'incomplete' && <Text style={styles.caption}>Part of the pitch measurement is missing.</Text>}
    </View>}
    <Pressable accessibilityRole="button" accessibilityLabel="More details"
      accessibilityState={{ expanded: details }} onPress={() => { stopAllPlayback(); setDetails(true); }} style={styles.link}>
      <Text style={styles.linkText}>More details ›</Text>
    </Pressable>
    {details && <WorkspaceDialog title="Full pitch details" onClose={() => setDetails(false)}>
      {selected && <View style={{ gap: 6 }}>
        <Text style={styles.detailCharacter}>{selected.text}</Text>
        <Text style={styles.caption}>{selected.start.toFixed(2)}–{selected.end.toFixed(2)} s · exact segment</Text>
        <Text style={styles.caption}>{`Measurement evidence: ${selected.eligibility?.state ?? 'insufficient'}`}</Text>
        <Text style={styles.caption}>{selected.eligibility?.reasons?.join(' · ')}</Text>
        <Text style={styles.caption}>Measurement quality describes acoustic support, not pronunciation correctness. Gesture descriptions are experimental and withheld when support is mixed or limited.</Text>
        <Text style={styles.reference}>{selected.members.map(s => `${s.characters} · ${expectedLabel(s)}`).join('\n')}</Text>
        {selected.members.some(s => s.lexical_tone === 3) && <Text style={styles.caption}>Connected T3 can be low or dipping; a full dip and rise is not required.</Text>}
        {selected.members.some(s => s.expected_surface_tone === 0) && <Text style={styles.caption}>Neutral tone has no fixed pitch shape.</Text>}
      </View>}
      <SentenceToneGraph data={data} initialDetail />
    </WorkspaceDialog>}
  </View>;
}

const styles = StyleSheet.create({
  workspace: { gap: 4, minWidth: 0 },
  gesture: { color: colors.text, fontSize: 14 },
  caption: { color: colors.secondary, fontSize: 12, lineHeight: 18 },
  sentence: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 4 },
  unit: { minWidth: 44, minHeight: 48, paddingHorizontal: 7, justifyContent: 'center', alignItems: 'center',
    borderRadius: 8, backgroundColor: colors.diagnostic, borderWidth: 2, borderColor: 'transparent', flexShrink: 0 },
  selected: { borderColor: colors.text, borderBottomWidth: 4 },
  character: { color: colors.text, fontSize: 24, lineHeight: 34 },
  untimed: { color: colors.secondary, fontSize: 24, lineHeight: 48 },
  detail: { gap: 4, paddingTop: 4 },
  identity: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8 },
  detailCharacter: { color: colors.text, fontSize: 28, lineHeight: 38, fontWeight: '600' },
  reading: { color: colors.secondary, fontSize: 16, flexShrink: 1 },
  status: { color: colors.secondary, fontSize: 13, fontWeight: '600' },
  reference: { color: colors.secondary, fontSize: 12, lineHeight: 19 },
  link: { minHeight: 44, justifyContent: 'center' },
  linkText: { color: colors.primary, fontSize: 14, fontWeight: '600' },
});
