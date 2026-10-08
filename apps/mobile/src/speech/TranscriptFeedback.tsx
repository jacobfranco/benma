import { useEffect, useRef } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { PerceivedReadings, PerceivedSpeechAnalysis } from '@/api/types';
import { SentenceToneGraph } from '@/speech/SentenceToneGraph';
import { colors } from '@/theme';

export function TranscriptFeedback({ analysis, readings, heard = '', failed = false, receivedAt, startedAt }: {
  readings?: PerceivedReadings | undefined;
  analysis?: PerceivedSpeechAnalysis | undefined; heard?: string; failed?: boolean; receivedAt?: number | undefined; startedAt?: number | undefined;
}) {
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
    {data ? <SentenceToneGraph key={analysis!.id} data={data} /> : <>
      <Text style={styles.secondary}>{failed ? 'Speech analysis unavailable. You can keep speaking.' : 'Analyzing speech…'}</Text>
      {!syllables && !failed && <View testID="sentence-graph-placeholder" style={{ height: 230 }}><Text style={styles.secondary}>Pitch timeline loading…</Text></View>}
      {(syllables ?? []).map(s => <Text key={s.index} style={styles.secondary}>{s.characters} · {s.pinyin ?? 'Reading unresolved'}</Text>)}
    </>}
    {data?.evidence_status === 'synthetic_replay' && <Text style={styles.secondary}>Development fixture; synthetic timing is not used as perceived syllable timing.</Text>}
    </>}
  </View>;
}
const styles = StyleSheet.create({
  content: { minHeight: 244, gap: 6 },
  secondary: { color: colors.secondary, fontSize: 12, lineHeight: 18 },
});
