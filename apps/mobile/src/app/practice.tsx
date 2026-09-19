import { useRef, useState } from 'react';
import { TextInput } from 'react-native';

import { api } from '@/api/client';
import type { PerceptionRun, PronunciationResult, PronunciationTarget, ReferenceSpeech } from '@/api/types';
import { PlaybackButton } from '@/audio/PlaybackButton';
import { stopAllPlayback } from '@/audio/session';
import { Body, Button, Card, Chinese, ErrorMessage, FixtureBanner, Heading, Pinyin, Screen } from '@/components/Ui';
import { SpeechControls } from '@/speech/SpeechControls';
import { SpeechEvidence } from '@/speech/SpeechEvidence';
import { useSpeechTurn } from '@/speech/useSpeechTurn';
import type { SpeechAnalysis } from '@/speech/workflow';

interface PracticeEntry { perception: PerceptionRun; pronunciation?: PronunciationResult }

export default function PracticeScreen() {
  const [withTarget, setWithTarget] = useState(false);
  const [targetText, setTargetText] = useState('');
  const [target, setTarget] = useState<PronunciationTarget | null>(null);
  const [reference, setReference] = useState<ReferenceSpeech | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [targetError, setTargetError] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<Record<string, SpeechAnalysis>>({});
  const [entries, setEntries] = useState<PracticeEntry[]>([]);
  const [editPinyin, setEditPinyin] = useState(false);
  const [pinyin, setPinyin] = useState('');
  const preparationLock = useRef(false);
  const turn = useSpeechTurn({
    mode: withTarget ? target ? { responseMode: 'none', targetId: target.id } : null : { responseMode: 'none' },
    onAnalysis: (analysis) => setAnalyses((current) => ({ ...current, [analysis.perceptionId ?? analysis.utteranceId]: analysis })),
    onPerception: (perception) => setEntries((current) => current.some((entry) => entry.perception.id === perception.id)
      ? current : [...current, { perception }]),
    onResult: (result) => setEntries((current) => current.map((entry) => entry.perception.id === result.perception.id
      ? { perception: result.perception, ...(result.pronunciation ? { pronunciation: result.pronunciation } : {}) } : entry)),
  });

  const prepare = async (correctReading = false) => {
    if (preparationLock.current || turn.busy) return;
    turn.reset();
    preparationLock.current = true;
    setPreparing(true);
    setTargetError(null);
    stopAllPlayback();
    try {
      const prepared = correctReading && target
        ? await api.correctTargetPinyin(target.id, pinyin)
        : await api.createTarget(targetText.trim());
      setTarget(prepared);
      setPinyin(prepared.pinyin_syllables.join(' '));
      setEditPinyin(false);
      setReference(null);
      try { setReference(await api.createReferenceSpeech(prepared.id)); }
      catch { setTargetError('Reference audio unavailable. You can still practice.'); }
    } catch { setTargetError('Could not prepare that target phrase. Try again.'); }
    finally { preparationLock.current = false; setPreparing(false); }
  };
  const retryReference = async () => {
    if (!target || preparationLock.current) return;
    preparationLock.current = true;
    setPreparing(true);
    setTargetError(null);
    try { setReference(await api.createReferenceSpeech(target.id, true)); }
    catch { setTargetError('Reference audio unavailable. You can still practice.'); }
    finally { preparationLock.current = false; setPreparing(false); }
  };
  return <Screen>
    <Heading>Practice</Heading>
    <Body>Listen to your speech and try again at your own pace.</Body>
    <Button secondary disabled={turn.busy || preparing}
      label={withTarget ? 'Use free practice' : 'Add a target phrase'}
      onPress={() => { turn.reset(); stopAllPlayback(); setWithTarget((value) => !value); }} />
    {withTarget ? <Card>
      <Body>Target phrase</Body>
      <TextInput accessibilityLabel="Target phrase" editable={!turn.busy && !preparing}
        value={targetText} style={{ fontSize: 24, minHeight: 50 }}
        onChangeText={(text) => { turn.reset(); stopAllPlayback(); setTargetText(text); setTarget(null); setReference(null); }} />
      <Button label="Prepare target" disabled={!targetText.trim() || turn.busy || preparing}
        loading={preparing} onPress={() => void prepare()} />
      {target && <>
        <Chinese>{target.text}</Chinese><Pinyin>{target.display_pinyin}</Pinyin>
        <Button secondary label="Edit pinyin" disabled={turn.busy || preparing} onPress={() => setEditPinyin((value) => !value)} />
        {editPinyin && <>
          <TextInput accessibilityLabel="Corrected numeric pinyin" value={pinyin} onChangeText={setPinyin} />
          <Button label="Use this reading" disabled={turn.busy || preparing} onPress={() => void prepare(true)} />
        </>}
        {reference?.generation_config.evidence_status === 'synthetic_replay' && <FixtureBanner />}
        {reference?.status === 'succeeded' && reference.audio_url
          ? <PlaybackButton label="▶ Native reference" uri={reference.audio_url} disabled={turn.busy} />
          : !turn.busy && !preparing && <Button secondary label="Retry reference" onPress={() => void retryReference()} />}
        <Body>One example realization. Your target phrase guides the assessment.</Body>
      </>}
      <ErrorMessage message={targetError} />
    </Card> : <Body>Free practice: speak without a target phrase.</Body>}
    {entries.map(({ perception, pronunciation }) => <SpeechEvidence key={perception.id}
      heard={perception.transcript ?? ''}
      {...(perception.utterance_id ? { recordingUrl: `/v1/utterances/${perception.utterance_id}/audio` } : {})}
      synthetic={perception.normalized_result?.evidence_status === 'synthetic_replay'}
      pronunciation={(analyses[perception.id] ?? analyses[perception.utterance_id])?.pronunciation ?? pronunciation}
      analysis={(analyses[perception.id] ?? analyses[perception.utterance_id])} />)}
    <SpeechControls turn={turn} disabled={preparing || (withTarget && !target)} />
  </Screen>;
}
