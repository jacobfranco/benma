import { useReducer, useRef, useState } from 'react';
import { Platform, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import { errorMessage } from '@/api/errors';
import type { PerceptionRun, UserCorrection } from '@/api/types';
import { PlaybackButton } from '@/audio/PlaybackButton';
import { useAudioCapture } from '@/audio/useAudioCapture';
import {
  initialWorkflowState,
  workflowReducer,
  type WorkflowAction,
  type WorkflowState,
} from '@/audio/workflowMachine';
import {
  Body,
  Button,
  Card,
  Chinese,
  ErrorMessage,
  EvidencePanel,
  EvidenceRow,
  FixtureBanner,
  Heading,
  Screen,
} from '@/components/Ui';
import { colors } from '@/theme';

export default function PerceptionScreen() {
  const [state, dispatch] = useReducer(
    (current: WorkflowState<PerceptionRun>, action: WorkflowAction<PerceptionRun>) =>
      workflowReducer(current, action),
    initialWorkflowState<PerceptionRun>(),
  );
  const capture = useAudioCapture();
  const sessionId = useRef<string | null>(null);
  const [intendedText, setIntendedText] = useState('');
  const [correction, setCorrection] = useState<UserCorrection | null>(null);
  const [correctionError, setCorrectionError] = useState<string | null>(null);

  const start = async () => {
    try {
      if (!(await capture.start())) {
        dispatch({ type: 'PERMISSION_REQUIRED' });
        return;
      }
      setCorrection(null);
      setIntendedText('');
      dispatch({ type: 'START_RECORDING' });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const stop = async () => {
    try {
      const recording = await capture.stop();
      dispatch({ type: 'RECORDED', ...recording });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const upload = async () => {
    if (!state.recordingUri) return;
    dispatch({ type: 'UPLOAD' });
    try {
      if (!sessionId.current) {
        sessionId.current = (await api.createPracticeSession('perception_test')).id;
      }
      const mimeType = Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4';
      const utterance = await api.uploadUtterance(
        state.recordingUri,
        mimeType,
        sessionId.current,
      );
      dispatch({ type: 'UPLOADED', utteranceId: utterance.id });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const analyze = async () => {
    if (!state.utteranceId) return;
    dispatch({ type: state.phase === 'failure' ? 'RETRY_ANALYSIS' : 'ANALYZE' });
    try {
      const result = await api.createPerception(state.utteranceId);
      dispatch({ type: 'SUCCEEDED', result });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const submitCorrection = async () => {
    if (!state.utteranceId || !state.result || !intendedText.trim()) return;
    setCorrectionError(null);
    try {
      setCorrection(
        await api.createCorrection(state.utteranceId, state.result.id, intendedText.trim()),
      );
    } catch (error) {
      setCorrectionError(errorMessage(error));
    }
  };

  const replay = state.recordingUri ? <PlaybackButton uri={state.recordingUri} /> : null;
  const synthetic = state.result?.normalized_result?.evidence_status === 'synthetic_replay';

  return (
    <Screen>
      <Heading>What did I say?</Heading>
      <Body>Record arbitrary Mandarin. Benma sends only canonical audio and a Mandarin language hint.</Body>
      <Card>
        <Body>Recording state: {state.phase}</Body>
        {state.phase === 'recording' ? (
          <>
            <Text style={styles.timer}>{Math.round(capture.durationMillis / 1000)}s</Text>
            <Button label="Stop" onPress={() => void stop()} />
          </>
        ) : state.phase === 'idle' || state.phase === 'permission_required' ? (
          <Button label="Record" onPress={() => void start()} />
        ) : null}
        {replay}
        {state.phase === 'recorded' && (
          <>
            <Button label="Upload recording" onPress={() => void upload()} />
            <Button secondary label="Retry recording" onPress={() => void start()} />
          </>
        )}
        {state.phase === 'uploading' && <Button disabled loading label="Uploading" onPress={() => {}} />}
        {state.phase === 'uploaded' && <Button label="Analyze" onPress={() => void analyze()} />}
        {state.phase === 'analyzing' && <Button disabled loading label="Analyzing" onPress={() => {}} />}
        {state.phase === 'failure' && state.utteranceId && (
          <Button label="Retry analysis" onPress={() => void analyze()} />
        )}
        {state.phase === 'failure' && !state.utteranceId && (
          <Button label="Retry recording" onPress={() => void start()} />
        )}
        <ErrorMessage message={capture.error ?? state.error} />
      </Card>

      {state.result && (
        <Card>
          {synthetic && <FixtureBanner />}
          <Body>What Benma heard:</Body>
          <Chinese>{state.result.transcript ?? 'No transcript returned'}</Chinese>
          {correction ? (
            <View style={styles.correction}>
              <Body>What you meant:</Body>
              <Chinese>{correction.intended_text}</Chinese>
            </View>
          ) : (
            <>
              <Body>What were you actually trying to say? (optional)</Body>
              <TextInput
                accessibilityLabel="What you meant"
                multiline
                onChangeText={setIntendedText}
                placeholder="我明天想去北京。"
                style={styles.input}
                value={intendedText}
              />
              <Button
                secondary
                disabled={!intendedText.trim()}
                label="Save what I meant"
                onPress={() => void submitCorrection()}
              />
              <ErrorMessage message={correctionError} />
            </>
          )}
        </Card>
      )}

      {state.result && (
        <EvidencePanel>
          <EvidenceRow label="Utterance ID" value={state.utteranceId} />
          <EvidenceRow label="Audio duration" value={`${state.durationMillis} ms`} />
          <EvidenceRow label="Provider" value={`${state.result.provider} / ${state.result.product}`} />
          <EvidenceRow label="Adapter" value={state.result.adapter_version} />
          <EvidenceRow label="Run ID" value={state.result.id} />
          <EvidenceRow label="Latency" value={`${state.result.latency_ms ?? 'unknown'} ms`} />
          <EvidenceRow label="Status" value={state.result.status} />
          <EvidenceRow label="Normalized result" value={state.result.normalized_result} />
        </EvidencePanel>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  timer: { fontSize: 40, color: colors.text, fontVariant: ['tabular-nums'] },
  input: {
    minHeight: 90,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    color: colors.text,
    fontSize: 20,
    textAlignVertical: 'top',
  },
  correction: { gap: 8, borderTopColor: colors.border, borderTopWidth: 1, paddingTop: 14 },
});
