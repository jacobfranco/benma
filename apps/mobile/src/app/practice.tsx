import { useEffect, useRef, useState } from 'react';
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
  // Safe development trace: no transcript, audio, credentials or provider payloads.
  const trace = (event: string, targetId?: string) => {
    if (__DEV__) console.info('[practice mode]', { event, targetId: targetId ?? null });
  };
  useEffect(() => {
    if (__DEV__) console.info('[practice mode]', { event: 'enter' });
    return () => { if (__DEV__) console.info('[practice mode]', { event: 'leave' }); };
  }, []);
  const turn = useSpeechTurn({
    mode: target ? { responseMode: 'none', targetId: target.id } : withTarget ? null : { responseMode: 'none' },
    beforeRecording: () => trace('record', target?.id),
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
      trace('prepared', prepared.id);
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
    {!withTarget && !target && <Button secondary label="Add a target phrase"
      disabled={turn.busy || preparing}
      onPress={() => { turn.reset(); stopAllPlayback(); setWithTarget(true); trace('edit'); }} />}
    {withTarget || target ? <Card>
      <Body>{target ? 'Target active · every recording uses this phrase' : 'Prepare a target before recording'}</Body>
      {!target && <>
        <TextInput accessibilityLabel="Target phrase" editable={!turn.busy && !preparing}
          value={targetText} style={{ fontSize: 24, minHeight: 50 }}
          onChangeText={(text) => { setTargetText(text); }} />
        <Button label="Prepare target" disabled={!targetText.trim() || turn.busy || preparing}
          loading={preparing} onPress={() => void prepare()} />
      </>}
      {target && <>
        <Chinese>{target.text}</Chinese><Pinyin>{target.display_pinyin}</Pinyin>
        <Button secondary label="Change target" disabled={turn.busy || preparing} onPress={() => {
          turn.reset(); stopAllPlayback(); trace('change', target.id);
          setWithTarget(true); setTarget(null); setReference(null); setEditPinyin(false); setTargetError(null);
        }} />
        <Button secondary label="Edit pinyin" disabled={turn.busy || preparing} onPress={() => setEditPinyin((value) => !value)} />
        {editPinyin && <>
          <TextInput accessibilityLabel="Corrected numeric pinyin" value={pinyin} onChangeText={setPinyin} />
          <Button label="Use this reading" disabled={turn.busy || preparing} onPress={() => void prepare(true)} />
        </>}
        {target.pinyin_syllables.some(p => /[05]$/.test(p)) && <Body>Neutral tone has context-dependent pitch. Reference pronunciation is one natural realization, not a fixed expected contour.</Body>}
        {reference?.generation_config.evidence_status === 'synthetic_replay' && <FixtureBanner />}
        {reference?.status === 'succeeded' && reference.audio_url
          ? <PlaybackButton label="▶ Native reference" uri={reference.audio_url} disabled={turn.busy} />
          : !turn.busy && !preparing && <Button secondary label="Retry reference" onPress={() => void retryReference()} />}
        <Body>One example realization. Your target phrase guides the assessment.</Body>
      </>}
      <Button secondary label="Clear target · use free practice" disabled={turn.busy || preparing} onPress={() => {
        turn.reset(); stopAllPlayback(); trace('clear', target?.id);
        setTarget(null); setReference(null); setTargetText(''); setWithTarget(false);
        setEditPinyin(false); setTargetError(null);
      }} />
      <ErrorMessage message={targetError} />
    </Card> : <Body>Free practice: speak without a target phrase.</Body>}
    {entries.map(({ perception, pronunciation }) => <SpeechEvidence key={perception.id}
      heard={perception.transcript ?? ''}
      {...(perception.utterance_id ? { recordingUrl: `/v1/utterances/${perception.utterance_id}/audio` } : {})}
      synthetic={perception.normalized_result?.evidence_status === 'synthetic_replay'}
      pronunciation={(analyses[perception.id] ?? analyses[perception.utterance_id])?.pronunciation ?? pronunciation}
      analysis={(analyses[perception.id] ?? analyses[perception.utterance_id])} />)}
    {target && <Body>Recording for target: {target.text} {target.display_pinyin}</Body>}
    <SpeechControls turn={turn} disabled={preparing || (withTarget && !target)} />
  </Screen>;
}
