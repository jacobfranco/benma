import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { PerceivedReadings, PerceivedSpeechAnalysis, PerceivedSyllable } from '@/api/types';
import { PitchPlot } from '@/components/PitchPlot';
import { SyllableComparison } from '@/speech/SyllableComparison';
import { colors } from '@/theme';

// Retain the lexical strip entry point for callers; the paired strip is primary.
export function SyllableToneStrip({ syllables }: { syllables: PerceivedSyllable[]; duration?: number }) {
  return <SyllableComparison syllables={syllables} />;
}
export function TranscriptFeedback({ analysis, readings, heard = '', failed = false, receivedAt, startedAt }: {
  readings?: PerceivedReadings | undefined;
  analysis?: PerceivedSpeechAnalysis | undefined; heard?: string; failed?: boolean; receivedAt?: number | undefined; startedAt?: number | undefined;
}) {
  const [details, setDetails] = useState(false);
  const painted = useRef<string | undefined>(undefined);
  const data = analysis?.data;
  const hasHan = /[\u3400-\u4dbf\u4e00-\u9fff]/.test(heard || analysis?.alignment_reference_text || '');
  const syllables = data?.syllables ?? readings?.syllables;
  useEffect(() => {
    if (!analysis || painted.current === analysis.id) return;
    const frame = requestAnimationFrame(() => {
      painted.current = analysis.id;
      if (__DEV__) {
        if (receivedAt !== undefined) console.info('[speech timing] analysis response to UI frame ms:', Date.now()-receivedAt);
        if (startedAt !== undefined) console.info('[speech timing] Stop to chart frame ms:', Date.now()-startedAt);
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [analysis, receivedAt, startedAt]);
  return <View testID="pronunciation-content" style={[styles.content, !hasHan && { minHeight: 0 }]}>
    {!hasHan ? <Text style={styles.secondary}>Pronunciation unavailable: no Chinese syllables could be resolved from what Benma heard.</Text> : <>
    <View style={styles.summary}><Text style={styles.secondary}>{data ? 'Expected here · acoustic shapes' : failed ? 'Analysis unavailable' : 'Analyzing speech…'}</Text></View>
    {syllables ? <SyllableComparison syllables={syllables} /> :
      failed ? <View style={styles.failure}><Text style={styles.secondary}>Speech analysis unavailable. You can keep speaking.</Text></View> :
        <SyllableComparison loading heard={heard} />}
    {(data?.unresolved_spans ?? readings?.unresolved_spans ?? []).map((span, index) => <Text key={index} style={styles.secondary}>{String(span.text)} · reading unresolved</Text>)}
    </>}
    <Pressable accessibilityLabel={details ? 'Less detail' : 'More detail'} accessibilityRole="button" accessibilityState={{ expanded: details, disabled: !data }}
      disabled={!data} onPress={() => setDetails(value => !value)} style={styles.detailsButton}>
      <Text style={[styles.detailLabel, !data && { opacity: 0 }]}>{details ? 'Less detail' : 'More detail'}</Text>
    </Pressable>
    {details && data && <View style={styles.details}>
      <Text style={styles.detailLabel}>Whole utterance</Text>
      <PitchPlot user={data.measured_pitch} display={data.display_contour} durationSeconds={data.duration_seconds} />
      <Text style={styles.secondary}>Expected here uses conservative connected-speech rules. Dictionary tones stay separate. Neutral tone has no fixed contour.</Text>
      <Text style={styles.secondary}>Mine shows an approximate acoustic shape, not a correctness score. Pitch is relative to this recording; gaps contain no reliable voiced pitch.</Text>
      {data.alignment_status !== 'aligned' && <Text style={styles.secondary}>Some syllable timing is unavailable. Individual voice contours need reliable alignment.</Text>}
      {data.syllables.map(s => <Text key={`tone-${s.index}`} style={styles.secondary}>{s.characters} · dictionary {s.lexical_tone ?? '?'} · expected here {s.expected_surface_tone ?? '?'} · {(s.observed_contour?.reason ?? 'timing unavailable').replaceAll('_', ' ')}</Text>)}
      {data.evidence_status === 'synthetic_replay' && <Text style={styles.secondary}>Development fixture; synthetic timing is not used to label your tone.</Text>}
      {data.quality_issues.length > 0 && <Text style={styles.secondary}>Recording quality limits the pitch evidence.</Text>}
      {data.syllables.filter(s => s.reading_source === 'unresolved').map(s =>
        <Text key={s.index} style={styles.secondary}>{s.characters}: {s.alternatives.join(' / ')} · reading unresolved</Text>)}
    </View>}
  </View>;
}
const styles = StyleSheet.create({
  content: { minHeight: 244, gap: 6 },
  summary: { height: 20 },
  secondary: { color: colors.secondary, fontSize: 12, lineHeight: 18 },
  detailLabel: { color: colors.primary, fontSize: 13, fontWeight: '600' },
  detailsButton: { height: 28, justifyContent: 'center', alignSelf: 'flex-start' },
  details: { gap: 10 },
  failure: { height: 184, justifyContent: 'center' },
});
