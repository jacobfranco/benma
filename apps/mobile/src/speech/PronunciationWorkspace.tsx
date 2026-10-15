import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { ExactPlaybackButton, useCanonicalRecording } from '@/audio/ExactPlaybackButton';
import { stopAllPlayback } from '@/audio/session';
import { PitchShapePlot } from '@/components/PitchShapePlot';
import { WorkspaceDialog } from '@/components/WorkspaceActions';
import { SentenceToneGraph } from '@/speech/SentenceToneGraph';
import { pitchFeedbackCopy } from '@/speech/pitchFeedback';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { pitchExpectation, pitchGradePresentation, type LearnerPitchGrade } from '@/speech/learnerPitchGrade';
import { shapeLabels } from '@/speech/pitchShape';
import { chunkPitch, chunkReading, defaultChunk, isTimedChunk, pronunciationChunks } from '@/speech/pronunciationChunks';
import { pronunciationUnits, unitPresentation } from '@/speech/pronunciationWorkspace';
import { expectedLabel } from '@/speech/sentenceToneGraph';
import { toneGestureMatch } from '@/speech/toneGestureMatch';
import { toneLikenessLabels } from '@/speech/toneLikeness';
import { colors } from '@/theme';

function PitchStatus({ grade, compact = false }: { grade: LearnerPitchGrade; compact?: boolean }) {
  const state = pitchGradePresentation[grade.agreement];
  return <Text accessibilityRole="text" accessibilityLabel={state.label}
    style={[styles.pitchStatus, { color: state.ink, backgroundColor: state.background }]}>{state.symbol}{compact ? '' : ` ${state.label}`}</Text>;
}

export function PronunciationWorkspace({ analysis, phraseActions }: { analysis: PerceivedSpeechAnalysis; phraseActions?: ReactNode }) {
  const { data } = analysis;
  const units = useMemo(() => pronunciationUnits(data), [data]);
  const chunks = useMemo(() => pronunciationChunks(data, units), [data, units]);
  const feedback = useMemo(() => new Map(chunks.map(chunk => [chunk.id, gradeChunkPitch(analysis, chunk, units)])), [analysis, chunks, units]);
  const [selectedId, setSelectedId] = useState(() => defaultChunk(chunks));
  const [details, setDetails] = useState(false);
  const [technical, setTechnical] = useState(false);
  const [constituentId, setConstituentId] = useState<string | null>(null);
  const selected = chunks.filter(isTimedChunk).find(c => c.id === selectedId);
  const contour = useMemo(() => selected ? chunkPitch(data, selected, units) : null, [data, selected, units]);
  const selectedFeedback = selected ? feedback.get(selected.id) : undefined;
  const evidence = selectedFeedback?.constituents ?? [];
  const single = selected?.constituents.length === 1 ? selected.constituents[0] : undefined;
  const inspected = evidence.find(e => e.unit.id === constituentId) ?? evidence[0];
  const hasPitch = evidence.some(e => e.hasPitch);
  const shape = single ? evidence[0]?.shape : undefined;
  const observedTone = single ? evidence[0]?.observed : undefined;
  const fetchRecording = useCanonicalRecording(analysis.utterance_id);
  useEffect(() => () => stopAllPlayback(), []);
  const observed = single && !single.grouped && single.eligibility?.state === 'sufficient'
    ? toneGestureMatch(single.members[0]!).observed_gesture : null;
  return <View style={styles.workspace} testID="pronunciation-workspace">
    {!!units.length && <View testID="perceived-sentence-overview" style={styles.sentence}>
      {chunks.map(chunk => {
        if (!isTimedChunk(chunk)) return <Text key={chunk.id} style={styles.untimed}>{chunk.text}</Text>;
        const unit = chunk.constituents.length === 1 ? chunk.constituents[0] : undefined;
        const grade = feedback.get(chunk.id)!.grade;
        return <Pressable key={chunk.id} testID={`pronunciation-unit-${chunk.members[0]!.index}`} accessibilityRole="button"
          {...(Platform.OS === 'web' ? { 'aria-pressed': chunk.id === selectedId } : {})}
          accessibilityLabel={`${chunk.text}, pronunciation chunk${unit?.grouped ? ', grouped timing' : ''}, ${pitchGradePresentation[grade.agreement].label}`}
          accessibilityState={{ selected: chunk.id === selectedId }}
          onPress={() => { stopAllPlayback(); setSelectedId(chunk.id); setConstituentId(null); }}
          style={[styles.unit, chunk.id === selectedId && styles.selected]}>
          <Text style={styles.character}>{chunk.text}</Text>
          <Text accessible={false} aria-hidden style={[styles.overviewStatus, { color: pitchGradePresentation[grade.agreement].ink }]}>{pitchGradePresentation[grade.agreement].symbol}</Text>
        </Pressable>;
      })}
      {phraseActions}
    </View>}
    {!units.length && <Text style={styles.caption}>Timing-specific feedback is unavailable. You can still play the whole recording.</Text>}
    {!!units.length && !selected && <Text style={styles.caption}>Tap a chunk to hear it and see its pitch.</Text>}
    {selected && <View testID="selected-pronunciation-detail" style={styles.detail}>
      <View style={styles.compactRow}>
        <View style={styles.compactIdentity}>
          <View style={styles.identity}>
            <Text style={styles.detailCharacter}>{selected.text}</Text>
            <ExactPlaybackButton key={selected.id} utteranceId={analysis.utterance_id} text={selected.text}
              start={selected.start} end={selected.end} fetchRecording={fetchRecording} />
          </View>
          <Text style={styles.reading}>{chunkReading(selected)}</Text>
        </View>
        {hasPitch && contour && <View style={styles.compactGraph}><PitchShapePlot display={contour} start={selected.start} end={selected.end}
          regions={selected.constituents.map(u => ({ label: u.text, start: u.start, end: u.end }))} /></View>}
      </View>
      {selectedFeedback && <View style={styles.feedbackRow}>
        {observedTone && !single?.grouped && hasPitch && <Text accessibilityRole="text" style={styles.gesture}>{toneLikenessLabels[observedTone.tone]}</Text>}
        <PitchStatus grade={selectedFeedback.grade} compact={!!observedTone && !single?.grouped && hasPitch} />
      </View>}
      {!hasPitch && <Text accessibilityRole="text" style={styles.caption}>{pitchFeedbackCopy.unavailable}</Text>}
      {hasPitch && selectedFeedback && ['PARTIAL_OR_WEAK', 'CLEAR_DIFFERENCE'].includes(selectedFeedback.grade.agreement) &&
        <Text accessibilityRole="text" style={styles.caption}>{selectedFeedback.grade.message}</Text>}
      {selectedFeedback?.grade.coaching && <Text accessibilityRole="text" style={styles.caption}>{selectedFeedback.grade.coaching}</Text>}
    </View>}
    <Pressable accessibilityRole="button" accessibilityLabel="More details"
      accessibilityState={{ expanded: details }} onPress={() => { stopAllPlayback(); setTechnical(false); setDetails(true); }} style={styles.link}>
      <Text style={styles.linkText}>More details ›</Text>
    </Pressable>
    {details && <WorkspaceDialog title="Full pitch details" onClose={() => setDetails(false)}>
      {selected && <View style={{ gap: 8 }}>
        <View style={styles.identity}>
          <Text style={styles.detailCharacter}>{selected.text}</Text>
          <Text style={styles.reading}>{chunkReading(selected)}</Text>
          <ExactPlaybackButton key={`details-${selected.id}`} utteranceId={analysis.utterance_id} text={selected.text}
            start={selected.start} end={selected.end} fetchRecording={fetchRecording} />
        </View>
        <Text style={styles.status}>Your pitch</Text>
        {hasPitch && contour ? <PitchShapePlot display={contour} start={selected.start} end={selected.end} height={152}
          regions={selected.constituents.map(u => ({ label: u.text, start: u.start, end: u.end }))} />
          : <Text style={styles.caption}>{pitchFeedbackCopy.unavailable}</Text>}
        {hasPitch && shape && !single?.grouped && <Text style={styles.reference}>Measured shape: {shapeLabels[shape.shape]}</Text>}
        {hasPitch && observedTone && !single?.grouped && <Text style={styles.gesture}>{toneLikenessLabels[observedTone.tone]}</Text>}
        <Text style={styles.status}>Expected here</Text>
        <Text style={styles.reference}>{selected.members.map(s => `${s.characters} · ${pitchExpectation(s, analysis.data.syllables).label}`).join('\n')}</Text>
        {selected.members.some(s => pitchExpectation(s).basis === 'lexical_family') &&
          <Text style={styles.caption}>Connected-speech realization may vary here.</Text>}
        <Text style={styles.status}>Feedback · pitch only</Text>
        {selectedFeedback && <><PitchStatus grade={selectedFeedback.grade} /><Text style={styles.caption}>{selectedFeedback.grade.message}</Text>
          {selectedFeedback.grade.coaching && <Text style={styles.caption}>{selectedFeedback.grade.coaching}</Text>}</>}
        {selectedFeedback?.hasNeutralNonVeto && <Text style={styles.caption}>A neutral syllable has no fixed contour. Supported neutral pitch can be accepted in this chunk; missing or unreliable neutral pitch does not count against it.</Text>}
        <Text style={styles.caption}>Colors describe pitch agreement, not consonants, vowels, or overall pronunciation. Each graph fits its spoken span; gaps stay empty.</Text>
        {single?.grouped && <Text style={styles.caption}>One accepted timing span. Separate character timing and playback are unavailable.</Text>}
      </View>}
      {selected && selected.constituents.length > 1 && inspected && <View style={styles.constituents}>
        <Text style={styles.status}>Constituent details</Text>
        <View style={styles.sentence}>
          {selected.constituents.map(unit => <Pressable key={unit.id} testID={`chunk-constituent-${unit.members[0]!.index}`}
            {...(Platform.OS === 'web' ? { 'aria-pressed': inspected.unit.id === unit.id } : {})}
            accessibilityRole="button" accessibilityLabel={`Inspect ${unit.text}, constituent timing unit`}
            accessibilityState={{ selected: inspected.unit.id === unit.id }}
            onPress={() => { stopAllPlayback(); setConstituentId(unit.id); }}
            style={[styles.unit, inspected.unit.id === unit.id && styles.selected]}>
            <Text style={styles.character}>{unit.text}</Text>
          </Pressable>)}
        </View>
        <View testID="selected-constituent-detail" style={styles.detail}>
          <View style={styles.identity}>
            <Text style={styles.detailCharacter}>{inspected.unit.text}</Text>
            <Text style={styles.reading}>{chunkReading(inspected.unit)}</Text>
            <ExactPlaybackButton key={inspected.unit.id} utteranceId={analysis.utterance_id} text={inspected.unit.text}
              start={inspected.unit.start} end={inspected.unit.end} fetchRecording={fetchRecording} />
          </View>
          <Text style={styles.caption}>{inspected.hasPitch ? 'Pitch available' : 'Pitch unavailable'}</Text>
          {inspected.hasPitch ? <PitchShapePlot display={inspected.pitch} start={inspected.unit.start} end={inspected.unit.end} height={120} />
            : <Text accessibilityRole="text" style={styles.caption}>{pitchFeedbackCopy.unavailable}</Text>}
          {inspected.hasPitch && inspected.expected.basis !== 'neutral' && <Text style={styles.gesture}>{toneLikenessLabels[inspected.observed.tone]}</Text>}
          {inspected.hasPitch && <Text style={styles.reference}>Measured shape: {shapeLabels[inspected.shape.shape]}</Text>}
          <Text style={styles.reference}>Expected here · {inspected.expected.label}</Text>
          {inspected.expected.coaching && <Text style={styles.caption}>{inspected.expected.coaching}</Text>}
          <PitchStatus grade={inspected.grade} />
          <Text style={styles.caption}>{inspected.role === 'neutral_unmeasured_nonveto' ? 'Neutral dependent; this does not veto the chunk’s pitch feedback.' : inspected.grade.message}</Text>
          {inspected.grade.coaching && <Text style={styles.caption}>{inspected.grade.coaching}</Text>}
        </View>
      </View>}
      <Pressable accessibilityRole="button" accessibilityLabel="Technical details" accessibilityState={{ expanded: technical }}
        onPress={() => setTechnical(!technical)} style={styles.link}><Text style={styles.linkText}>Technical details {technical ? '⌄' : '›'}</Text></Pressable>
      {technical && <View style={styles.constituents}>
        {selected && <View style={{ gap: 6 }}>
          <Text style={styles.caption}>{selected.start.toFixed(2)}–{selected.end.toFixed(2)} s · exact segment</Text>
          {single && <Text style={styles.gesture}>{observed && observed !== 'unclear'
            ? `Observed gesture: ${({ level: 'Mostly level', rising: 'Rising', falling: 'Falling', dipping: 'Dipping' } as const)[observed]} · experimental`
            : single.grouped ? 'Grouped phrase · gesture unavailable' : 'Gesture unavailable'}</Text>}
          {single && <Text style={styles.status}>{unitPresentation(single).label}</Text>}
          {single && <Text style={styles.caption}>{`Measurement evidence: ${single.eligibility?.state ?? 'insufficient'}`}</Text>}
          {single && <Text style={styles.caption}>{single.eligibility?.reasons?.join(' · ')}</Text>}
          {single?.members[0]?.pitch_projection && <Text style={styles.caption}>Pitch source: {single.members[0].pitch_projection.track_evidence_id}{'\n'}Source frame indices: {single.members[0].pitch_projection.frame_indices?.join(', ')}</Text>}
          <Text style={styles.caption}>Measurement quality describes acoustic support, not pronunciation correctness. This saved diagnostic gesture uses the older strict classifier.</Text>
          <Text style={styles.reference}>{selected.members.map(s => `${s.characters} · ${expectedLabel(s)}`).join('\n')}</Text>
          {selected.members.some(s => s.lexical_tone === 3) && <Text style={styles.caption}>Connected T3 can be low or dipping; a full dip and rise is not required.</Text>}
          {selected.members.some(s => s.expected_surface_tone === 0) && <Text style={styles.caption}>Neutral tone has no fixed pitch shape.</Text>}
        </View>}
        {shape && <Text style={styles.caption}>Shape method: retained-geometry-v1 · {shape.reason}{'\n'}{JSON.stringify(shape.features)}{'\n'}{JSON.stringify(shape.perturbations)}</Text>}
        {evidence.map(e => <Text key={e.unit.id} style={styles.caption}>{e.unit.text} · Tone likeness: {e.observed.reason} · {e.observed.variant}{'\n'}
          Grade: {e.grade.reason} · {e.role}{'\n'}Citation tone: {e.unit.members[0]?.lexical_tone ?? 'unresolved'} · Surface rule: {e.expected.reason}</Text>)}
        {selected && selected.constituents.length > 1 && inspected && <View>
          <Text style={styles.status}>{inspected.unit.text} · {unitPresentation(inspected.unit).label}</Text>
          <Text style={styles.caption}>{inspected.unit.start.toFixed(2)}–{inspected.unit.end.toFixed(2)} s · exact segment</Text>
          <Text style={styles.caption}>Measurement evidence: {inspected.unit.eligibility?.state ?? 'insufficient'}</Text>
          <Text style={styles.caption}>{inspected.unit.eligibility?.reasons?.join(' · ')}</Text>
        </View>}
        <SentenceToneGraph data={data} initialDetail />
      </View>}
    </WorkspaceDialog>}
  </View>;
}

const styles = StyleSheet.create({
  workspace: { gap: 4, minWidth: 0 },
  gesture: { color: colors.text, fontSize: 14 },
  feedbackRow: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8 },
  pitchStatus: { fontSize: 13, fontWeight: '600' },
  overviewStatus: { fontSize: 12, lineHeight: 12 },
  caption: { color: colors.secondary, fontSize: 12, lineHeight: 18 },
  sentence: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 4 },
  unit: { minWidth: 44, minHeight: 48, paddingHorizontal: 7, justifyContent: 'center', alignItems: 'center',
    borderRadius: 8, backgroundColor: colors.diagnostic, borderWidth: 2, borderColor: 'transparent', flexShrink: 0 },
  selected: { borderColor: colors.text, borderBottomWidth: 4 },
  character: { color: colors.text, fontSize: 24, lineHeight: 34 },
  untimed: { color: colors.secondary, fontSize: 24, lineHeight: 48 },
  detail: { gap: 4, paddingTop: 4 },
  constituents: { gap: 6 },
  compactRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  compactIdentity: { width: 100, gap: 2 },
  compactGraph: { flex: 1, minWidth: 0 },
  identity: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8 },
  detailCharacter: { color: colors.text, fontSize: 28, lineHeight: 38, fontWeight: '600' },
  reading: { color: colors.secondary, fontSize: 16, flexShrink: 1 },
  status: { color: colors.secondary, fontSize: 13, fontWeight: '600' },
  reference: { color: colors.secondary, fontSize: 12, lineHeight: 19 },
  link: { minHeight: 44, justifyContent: 'center' },
  linkText: { color: colors.primary, fontSize: 14, fontWeight: '600' },
});
