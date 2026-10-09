import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { PlaybackButton } from '@/audio/PlaybackButton';
import type { ConversationTurn, PronunciationResult } from '@/api/types';
import { Card, FixtureBanner } from '@/components/Ui';
import { TranscriptFeedback } from '@/speech/TranscriptFeedback';
import { pronunciationUnits } from '@/speech/pronunciationWorkspace';
import type { SpeechAnalysis } from '@/speech/workflow';
import { colors } from '@/theme';

// A textual comparison of two explicit server fields, never a pronunciation diagnosis.
export function changedWording(heard: string, understood: string): { heard: string; understood: string } {
  const a = Array.from(heard), b = Array.from(understood);
  let start = 0, endA = a.length, endB = b.length;
  while (start < endA && start < endB && a[start] === b[start]) start++;
  while (endA > start && endB > start && a[endA - 1] === b[endB - 1]) { endA--; endB--; }
  return { heard: a.slice(start, endA).join(''), understood: b.slice(start, endB).join('') };
}
const semanticText = (text: string) => text.replace(/[\p{P}\p{Z}\s]/gu, '');

export function SpeechEvidence({ heard, decision = null, understood = null,
  pronunciation, analysis, processing, recordingUrl, intendedText, synthetic = false, compact = false }: {
  compact?: boolean;
  heard: string;
  intendedText?: string | undefined;
  decision?: ConversationTurn['interpretation_decision'] | undefined;
  understood?: string | null | undefined;
  pronunciation?: PronunciationResult | undefined;
  analysis?: SpeechAnalysis | undefined;
  processing?: string;
  recordingUrl?: string;
  synthetic?: boolean;
}) {
  const [expanded, setExpanded] = useState(!compact);
  const inferred = decision === 'infer' && understood !== null && semanticText(heard) !== semanticText(understood);
  const targetText = intendedText ?? pronunciation?.target.text ?? analysis?.pronunciation?.target.text;
  const targetChange = targetText && semanticText(targetText) !== semanticText(heard)
    ? changedWording(semanticText(targetText), semanticText(heard)) : null;
  const change = inferred ? changedWording(heard, understood!) : null;
  // The completed strip is the heard sentence when it represents all lexical text.
  // Keep full text for loading, failed analyses and mixed/non-Han utterances.
  const stripText = analysis?.perceived?.data.syllables.map(s => s.characters).join('');
  const heardInStrip = expanded && !!analysis?.perceived && pronunciationUnits(analysis.perceived.data).length > 0 && !!stripText && semanticText(stripText) === semanticText(heard);

  const playback = recordingUrl ? <PlaybackButton compact uri={recordingUrl} label="Play my full recording" /> : null;
  return <Card style={!compact ? { padding: 12, gap: 6 } : undefined}>
    {compact && <Text style={styles.speaker}>YOU</Text>}
    {synthetic && <FixtureBanner />}
    {compact && <Text style={styles.label}>What Benma heard</Text>}
    {!heardInStrip && <View testID="perceived-phrase-row" style={{ flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 4 }}>
      <Text selectable style={[styles.text, { flexShrink: 1 }]}>{heard}</Text>{playback}
    </View>}
    {compact && <Pressable accessibilityRole="button" accessibilityLabel={expanded ? 'Hide pronunciation' : 'Explore pronunciation'}
      accessibilityState={{ expanded }} onPress={() => setExpanded(!expanded)} style={{ minHeight: 44, justifyContent: 'center' }}>
      <Text style={styles.feedback}>{expanded ? 'Hide pronunciation' : 'Explore pronunciation →'}</Text>
    </Pressable>}
    {expanded && <View testID="pronunciation-section" style={{ gap: 8 }}>
      <TranscriptFeedback heard={heard} analysis={analysis?.perceived} readings={analysis?.readings} failed={analysis?.state === 'failed'}
          phraseActions={heardInStrip ? playback : null} receivedAt={analysis?.receivedAt} startedAt={analysis?.startedAt} />
    </View>}
    {targetChange && <View testID="target-comparison">
      <Text style={styles.feedback}>{`Target difference: ${targetChange.heard || "∅"} → ${targetChange.understood || "∅"}`}</Text>
    </View>}
    {inferred && <>
      <Text style={styles.label}>What Benma understood</Text>
      <Text selectable style={styles.text}>{understood}</Text>
    </>}
    {change && <View>
      <Text style={styles.label}>Speech note</Text>
      <Text selectable style={styles.feedback}>{change.heard && change.understood
        ? `Benma heard “${change.heard}” where context suggested “${change.understood}”.`
        : 'Context suggested different wording. Compare the heard and understood text.'}</Text>
    </View>}
    {decision === 'clarify' && <View>
      <Text style={styles.label}>Meaning</Text>
      <Text style={styles.feedback}>Benma is unsure what you meant or how you intended to finish the thought.</Text>
    </View>}
    {processing && <Text accessibilityRole="text" style={styles.feedback}>{processing}</Text>}
  </Card>;
}

const styles = StyleSheet.create({
  speaker: { color: colors.secondary, fontWeight: '700', fontSize: 12 },
  label: { color: colors.secondary, fontWeight: '600', fontSize: 13 },
  text: { color: colors.text, fontSize: 23, lineHeight: 34 },
  feedback: { color: colors.secondary, fontSize: 15, lineHeight: 23 },
});
