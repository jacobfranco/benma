import { useCallback, useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import type { ContextualInterpretationRun, ConversationTurn, PerceptionRun } from '@/api/types';
import { useAssistantPlayback } from '@/audio/useAssistantPlayback';
import { Body, Button, Card, ErrorMessage, Heading, Screen } from '@/components/Ui';
import { SpeechControls } from '@/speech/SpeechControls';
import { SpeechEvidence } from '@/speech/SpeechEvidence';
import { useSpeechTurn } from '@/speech/useSpeechTurn';
import type { SpeechAnalysis } from '@/speech/workflow';
import { requestTurnSpeech } from '@/freeTalk/workflow';
import { reconcileTurns } from '@/freeTalk/state';
import { colors } from '@/theme';

const downloadAudio = (path: string) => api.downloadAudioFile(path);

export default function ConversationScreen() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [analyses, setAnalyses] = useState<Record<string, SpeechAnalysis>>({});
  const [meanings, setMeanings] = useState<Record<string, ContextualInterpretationRun>>({});
  const [perceptions, setPerceptions] = useState<PerceptionRun[]>([]);
  const [initializationError, setInitializationError] = useState<string | null>(null);
  const [voices, setVoices] = useState<Record<string, 'preparing' | 'failed'>>({});
  const playback = useAssistantPlayback(downloadAudio);
  const initialization = useRef<Promise<void> | null>(null);
  const mounted = useRef(true);
  const activity = useRef(0);
  const speechRequests = useRef(new Set<string>());

  const initialize = useCallback(() => {
    if (initialization.current) return;
    setInitializationError(null);
    initialization.current = api.createConversation().then((conversation) => {
      if (mounted.current) setConversationId(conversation.id);
    }).catch(() => {
      initialization.current = null;
      if (mounted.current) setInitializationError('Conversation unavailable. Try again.');
    });
  }, []);
  useEffect(() => {
    mounted.current = true;
    initialize();
    return () => { mounted.current = false; };
  }, [initialize]);

  const prepareVoice = async (assistant: ConversationTurn, startedAt?: number) => {
    const generation = assistant.assistant_generation_run_id;
    if (!generation || speechRequests.current.has(assistant.id)) return;
    const requestedActivity = activity.current;
    speechRequests.current.add(assistant.id);
    setVoices((current) => ({ ...current, [assistant.id]: 'preparing' }));
    try {
      const speech = await requestTurnSpeech(api, assistant);
      if (!mounted.current) return;
      setTurns((current) => current.map((turn) => turn.id === assistant.id ? { ...turn, assistant_speech: speech } : turn));
      setVoices((current) => { const next = { ...current }; delete next[assistant.id]; return next; });
      if (speech.status === 'succeeded' && speech.audio_url && requestedActivity === activity.current) {
        await playback.play({ id: speech.id, url: speech.audio_url,
          ...(startedAt !== undefined ? { turnStartedAt: startedAt } : {}) });
      }
    } catch {
      if (mounted.current) setVoices((current) => ({ ...current, [assistant.id]: 'failed' }));
    } finally { speechRequests.current.delete(assistant.id); }
  };

  const speechTurn = useSpeechTurn({
    mode: conversationId ? { responseMode: 'conversation', conversationId } : null,
    beforeRecording: () => { activity.current++; playback.stop(); },
    onAnalysis: (analysis) => setAnalyses((current) => ({ ...current, [analysis.perceptionId ?? analysis.utteranceId]: analysis })),
    onInterpretation: (interpretation) => setMeanings((current) => ({ ...current, [interpretation.perception_run_id]: interpretation })),
    onPerception: (perception) => setPerceptions((current) =>
      current.some((item) => item.id === perception.id) ? current : [...current, perception]),
    onResult: (result, startedAt) => {
      if (!result.conversation) return;
      const { assistant_turn: assistant, ...user } = result.conversation;
      setTurns((current) => reconcileTurns(current, [user, assistant]));
      void prepareVoice(assistant, startedAt);
    },
    onResponseFailure: async () => {
      setMeanings({});
      if (!conversationId) return;
      try {
        const persisted = await api.listConversationTurns(conversationId);
        if (mounted.current) setTurns(persisted);
      } catch { /* Keep heard text and the last authoritative history available. */ }
    },
  });
  const provisional = perceptions.filter((perception) => !turns.some((turn) => turn.perception_run_id === perception.id));
  const rows = [
    ...turns.map((turn, index) => ({
      key: turn.role === 'assistant' ? `reply-${turns[index - 1]?.perception_run_id ?? turn.id}` : turn.perception_run_id ?? turn.id,
      turn, pendingReply: false,
      perception: perceptions.find((item) => item.id === turn.perception_run_id),
    })),
    ...provisional.flatMap((perception) => [
      { key: perception.id, turn: undefined, perception, pendingReply: false },
      { key: `reply-${perception.id}`, turn: undefined, perception, pendingReply: true },
    ]),
  ];
  return <Screen>
    <Heading>Conversation</Heading>
    <Body>Speak Mandarin, learn from what Benma heard, and keep talking.</Body>
    {!conversationId && !initializationError && <Body>Starting conversation…</Body>}
    <ErrorMessage message={initializationError} />
    {initializationError && <Button label="Retry starting conversation" onPress={initialize} />}
    <View accessibilityLabel="Conversation" style={{ gap: 12 }}>
      {rows.map(({ key, turn, perception, pendingReply }) => pendingReply
        ? <Card key={key} style={styles.assistantCard}>
            <Text style={styles.speaker}>BENMA</Text>
            <Text style={styles.pending}>{speechTurn.error ? 'Response unavailable. You can keep talking.' : 'Preparing response…'}</Text>
          </Card>
        : !turn || turn.role === 'user'
        ? <SpeechEvidence compact key={key} heard={perception?.transcript ?? turn?.perceived_text ?? ''}
            synthetic={perception?.normalized_result?.evidence_status === 'synthetic_replay'}
            decision={turn?.interpretation_decision ?? meanings[key]?.decision}
            understood={turn ? turn.resolved_text : meanings[key]?.inferred_text}
            analysis={analyses[perception?.id ?? turn?.perception_run_id ?? '']}
            recordingUrl={`/v1/utterances/${perception?.utterance_id ?? turn?.utterance_id}/audio`}
             />
        : <Card key={key} style={styles.assistantCard}>
            <Text style={styles.speaker}>BENMA</Text>
            <Text selectable style={styles.text}>{turn.assistant_text}</Text>
            {voices[turn.id] === 'preparing' ? <Body>Preparing voice…</Body> :
              turn.assistant_speech?.status === 'succeeded' && turn.assistant_speech.audio_url ?
                <Button secondary disabled={speechTurn.busy}
                  label={playback.activeId === turn.assistant_speech.id && playback.isPlaying ? 'Pause response' : 'Play response'}
                  onPress={() => { activity.current++; playback.toggle({ id: turn.assistant_speech!.id, url: turn.assistant_speech!.audio_url! }); }} /> : <>
                  <Body>Audio unavailable. You can keep talking.</Body>
                  <Button secondary disabled={speechTurn.busy} label="Prepare voice" onPress={() => void prepareVoice(turn)} />
                </>}
          </Card>)}

    </View>
    <SpeechControls turn={speechTurn} disabled={!conversationId} />
    <ErrorMessage message={playback.error} />
  </Screen>;
}
const styles = StyleSheet.create({
  assistantCard: { minHeight: 128 },
  pending: { color: colors.secondary, fontSize: 15, lineHeight: 23 },
  speaker: { color: colors.secondary, fontSize: 12, fontWeight: '700' },
  text: { color: colors.text, fontSize: 23, lineHeight: 34 },
});
