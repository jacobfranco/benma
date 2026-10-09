import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import type { PerceptionRun, PronunciationResult, PronunciationTarget, ReferenceSpeech } from '@/api/types';
import { PlaybackButton } from '@/audio/PlaybackButton';
import { stopAllPlayback } from '@/audio/session';
import { Body, Button, Card, ErrorMessage, FixtureBanner, Screen } from '@/components/Ui';
import { IconAction, WorkspaceDialog } from '@/components/WorkspaceActions';
import { ReadingSelector, readingChoices } from '@/speech/ReadingSelector';
import { SpeechControls } from '@/speech/SpeechControls';
import { SpeechEvidence } from '@/speech/SpeechEvidence';
import { useSpeechTurn } from '@/speech/useSpeechTurn';
import type { SpeechAnalysis } from '@/speech/workflow';
import { colors } from '@/theme';

interface PracticeEntry { perception: PerceptionRun; pronunciation?: PronunciationResult; intendedText?: string }

export default function PracticeScreen() {
  const [targetText, setTargetText] = useState('');
  const [target, setTarget] = useState<PronunciationTarget | null>(null);
  const [reference, setReference] = useState<ReferenceSpeech | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [targetError, setTargetError] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<Record<string, SpeechAnalysis>>({});
  const [entries, setEntries] = useState<PracticeEntry[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [dialog, setDialog] = useState<'target' | 'reading' | 'history' | null>(null);
  const currentEntry = entries.find(entry => entry.perception.id === activeId);
  const preparationLock = useRef(false);
  const session = useRef(0);
  const generation = session.current;
  useEffect(() => () => stopAllPlayback(), []);
  const turn = useSpeechTurn({
    mode: dialog === 'target' || preparing ? null : target ? { responseMode: 'none', targetId: target.id } : { responseMode: 'none' },
    beforeRecording: () => { setActiveId(null); setDialog(null); },
    onAnalysis: analysis => {
      if (generation !== session.current) return;
      setAnalyses(current => ({ ...current, [analysis.perceptionId ?? analysis.utteranceId]: analysis }));
    },
    onPerception: perception => {
      if (generation !== session.current) return;
      stopAllPlayback(); setActiveId(perception.id); setDialog(null);
      setEntries(current => current.some(entry => entry.perception.id === perception.id)
        ? current : [...current, { perception, ...(target ? { intendedText: target.text } : {}) }]);
    },
    onResult: result => {
      if (generation !== session.current) return;
      setEntries(current => current.map(entry => entry.perception.id === result.perception.id
        ? { ...entry, perception: result.perception, ...(result.pronunciation ? { pronunciation: result.pronunciation } : {}) } : entry));
    },
  });
  const clearAttempts = () => {
    session.current++; setEntries([]); setAnalyses({}); setActiveId(null); stopAllPlayback();
  };
  const open = (next: typeof dialog) => { turn.reset(); stopAllPlayback(); setDialog(next); };
  const clear = () => {
    if (turn.busy || preparationLock.current) return;
    turn.reset(); clearAttempts(); setTarget(null); setReference(null); setTargetText(''); setTargetError(null); setDialog(null);
  };
  const prepare = async (reading?: string) => {
    if (preparationLock.current || turn.busy) return;
    turn.reset(); preparationLock.current = true; setPreparing(true); setTargetError(null); stopAllPlayback();
    try {
      const prepared = reading && target ? await api.correctTargetPinyin(target.id, reading) : await api.createTarget(targetText.trim());
      if (!reading) clearAttempts();
      setTarget(prepared); setDialog(null); setReference(null);
      try { setReference(await api.createReferenceSpeech(prepared.id)); }
      catch { setTargetError('Reference audio unavailable. You can still practice.'); }
    } catch { setTargetError('Could not prepare that target phrase. Try again.'); }
    finally { preparationLock.current = false; setPreparing(false); }
  };
  const retryReference = async () => {
    if (!target || preparationLock.current) return;
    preparationLock.current = true; setPreparing(true); setTargetError(null);
    try { setReference(await api.createReferenceSpeech(target.id, true)); }
    catch { setTargetError('Reference audio unavailable. You can still practice.'); }
    finally { preparationLock.current = false; setPreparing(false); }
  };
  return <Screen compact footer={<SpeechControls turn={turn} recordLabel="New Attempt" disabled={preparing || dialog !== null} />}>
    {target ? <Card style={styles.target}>
      <Text style={styles.label}>Target</Text>
      <View style={styles.row}>
        <Text selectable style={styles.phrase}>{target.text}</Text>
        <View style={styles.actions}>
          {reference?.status === 'succeeded' && reference.audio_url
            ? <PlaybackButton compact label={`Play native reference for ${target.text}`} uri={reference.audio_url} disabled={turn.busy || preparing} />
            : <IconAction icon="▷" label="Retry reference" loading={preparing} disabled={turn.busy} onPress={() => void retryReference()} />}
          <IconAction icon="✎" label="Change target" disabled={turn.busy || preparing}
            onPress={() => { setTargetText(target.text); open('target'); }} />
          <IconAction icon="×" label="Clear target" disabled={turn.busy || preparing} onPress={clear} />
        </View>
      </View>
      <View style={styles.row}>
        <Text style={styles.reading}>{target.display_pinyin}</Text>
        {readingChoices(target).some(options => options.length > 1) && <IconAction icon="✎" label="Edit reading"
          disabled={turn.busy || preparing} onPress={() => open('reading')} />}
      </View>
      {reference?.generation_config.evidence_status === 'synthetic_replay' && <FixtureBanner />}
      {!dialog && <ErrorMessage message={targetError} />}
    </Card> : <View style={styles.row}>
      <Text style={styles.label}>Free Practice</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Add a target phrase" disabled={turn.busy || preparing}
        onPress={() => open('target')} style={styles.link}><Text style={styles.linkText}>Add target</Text></Pressable>
    </View>}
    {!!entries.length && <View style={styles.row}>
      <Text style={styles.label}>{currentEntry ? `Attempt ${entries.indexOf(currentEntry) + 1} of ${entries.length}` : 'Ready for a new attempt'}</Text>
      <IconAction icon="↶" label="History" disabled={turn.busy || preparing} onPress={() => open('history')} />
    </View>}
    {currentEntry && <SpeechEvidence key={currentEntry.perception.id}
      heard={currentEntry.perception.transcript ?? ''} intendedText={currentEntry.intendedText}
      recordingUrl={`/v1/utterances/${currentEntry.perception.utterance_id}/audio`}
      synthetic={currentEntry.perception.normalized_result?.evidence_status === 'synthetic_replay'}
      pronunciation={(analyses[currentEntry.perception.id] ?? analyses[currentEntry.perception.utterance_id])?.pronunciation ?? currentEntry.pronunciation}
      analysis={analyses[currentEntry.perception.id] ?? analyses[currentEntry.perception.utterance_id]} />}
    {dialog === 'target' && <WorkspaceDialog title="Change target" onClose={() => { if (!preparing) setDialog(null); }}>
      <TextInput accessibilityLabel="Target phrase" autoFocus editable={!preparing} value={targetText}
        style={styles.input} onChangeText={setTargetText} />
      <Button label="Prepare target" disabled={!targetText.trim()} loading={preparing} onPress={() => void prepare()} />
      <ErrorMessage message={targetError} />
    </WorkspaceDialog>}
    {dialog === 'reading' && target && <ReadingSelector target={target} busy={preparing} error={targetError}
      onSave={reading => void prepare(reading)} onClose={() => { if (!preparing) setDialog(null); }} />}
    {dialog === 'history' && <WorkspaceDialog title="History" onClose={() => setDialog(null)}>
      <Body>Attempts in this session</Body>
      {[...entries].reverse().map(entry => <Pressable key={entry.perception.id} accessibilityRole="button"
        accessibilityLabel={`Open attempt ${entries.indexOf(entry) + 1}`} accessibilityState={{ selected: entry === currentEntry }}
        onPress={() => { stopAllPlayback(); setActiveId(entry.perception.id); setDialog(null); }} style={styles.historyRow}>
        <Text style={styles.label}>{`Attempt ${entries.indexOf(entry) + 1}${entry === currentEntry ? ' · Current' : ''}`}</Text>
        <Text style={styles.reading}>{entry.perception.transcript}</Text>
      </Pressable>)}
    </WorkspaceDialog>}
  </Screen>;
}
const styles = StyleSheet.create({
  target: { padding: 12, gap: 2 },
  row: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 4 },
  actions: { flexDirection: 'row', alignItems: 'center' },
  phrase: { color: colors.text, fontSize: 24, lineHeight: 34, flexShrink: 1 },
  reading: { color: colors.secondary, fontSize: 15, lineHeight: 22, flexShrink: 1 },
  label: { color: colors.secondary, fontSize: 12, fontWeight: '600' },
  link: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 8 },
  linkText: { color: colors.primary, fontSize: 14 },
  input: { fontSize: 24, minHeight: 50, color: colors.text },
  historyRow: { minHeight: 48, padding: 8, borderRadius: 8, backgroundColor: colors.diagnostic, gap: 4 },
});
