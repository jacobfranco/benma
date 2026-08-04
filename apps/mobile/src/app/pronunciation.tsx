import { useReducer, useRef, useState } from 'react';
import { Platform, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import { errorMessage } from '@/api/errors';
import type {
  AssessmentRun,
  PronunciationAttempt,
  PronunciationTarget,
} from '@/api/types';
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
  Pinyin,
  Screen,
} from '@/components/Ui';
import { colors } from '@/theme';

interface AttemptResult {
  attempt: PronunciationAttempt;
  assessment: AssessmentRun;
}

interface LocalAttempt extends AttemptResult {
  uri: string;
  durationMillis: number;
}

export default function PronunciationScreen() {
  const [targetText, setTargetText] = useState('生活');
  const [target, setTarget] = useState<PronunciationTarget | null>(null);
  const [targetError, setTargetError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState<LocalAttempt[]>([]);
  const [state, dispatch] = useReducer(
    (current: WorkflowState<AttemptResult>, action: WorkflowAction<AttemptResult>) =>
      workflowReducer(current, action),
    initialWorkflowState<AttemptResult>(),
  );
  const capture = useAudioCapture();
  const sessionId = useRef<string | null>(null);
  const pendingAttemptId = useRef<string | null>(null);

  const resolveTarget = async () => {
    setTargetError(null);
    try {
      setTarget(await api.createTarget(targetText.trim()));
    } catch (error) {
      setTargetError(errorMessage(error));
    }
  };

  const start = async () => {
    try {
      if (!(await capture.start())) {
        dispatch({ type: 'PERMISSION_REQUIRED' });
        return;
      }
      dispatch({ type: 'START_RECORDING' });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const stop = async () => {
    try {
      dispatch({ type: 'RECORDED', ...(await capture.stop()) });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const upload = async () => {
    if (!state.recordingUri || !target) return;
    dispatch({ type: 'UPLOAD' });
    try {
      if (!sessionId.current) {
        sessionId.current = (await api.createPracticeSession('pronunciation')).id;
      }
      const utterance = await api.uploadUtterance(
        state.recordingUri,
        Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4',
        sessionId.current,
      );
      pendingAttemptId.current = null;
      dispatch({ type: 'UPLOADED', utteranceId: utterance.id });
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const assess = async () => {
    if (!state.utteranceId || !state.recordingUri || !target) return;
    dispatch({ type: state.phase === 'failure' ? 'RETRY_ANALYSIS' : 'ANALYZE' });
    try {
      const attempt = pendingAttemptId.current
        ? await api.getAttempt(pendingAttemptId.current)
        : await api.createAttempt(state.utteranceId, target.id);
      pendingAttemptId.current = attempt.id;
      const assessment = await api.createAssessment(attempt.id);
      const result = { attempt, assessment };
      dispatch({ type: 'SUCCEEDED', result });
      setAttempts((current) => [
        ...current,
        {
          ...result,
          uri: state.recordingUri!,
          durationMillis: state.durationMillis,
        },
      ]);
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const retryRecording = () => {
    pendingAttemptId.current = null;
    dispatch({ type: 'RESET' });
    void start();
  };

  const evidence = state.result?.assessment.normalized_result;
  const unsupportedTones = evidence?.unsupported_capabilities?.some((item) =>
    item.toLocaleLowerCase().includes('tone'),
  );

  return (
    <Screen>
      <Heading>Pronunciation</Heading>
      <Body>Characters are the target. Generated pinyin is provisional and keeps its provenance.</Body>
      <Card>
        <Body>Chinese word or phrase</Body>
        <TextInput
          accessibilityLabel="Pronunciation target"
          onChangeText={setTargetText}
          style={styles.targetInput}
          value={targetText}
        />
        <Button disabled={!targetText.trim()} label="Prepare target" onPress={() => void resolveTarget()} />
        <ErrorMessage message={targetError} />
      </Card>

      {target && (
        <Card>
          <Chinese>{target.text}</Chinese>
          <Pinyin>{target.display_pinyin}</Pinyin>
          <Body>Automatic pinyin — polyphonic readings may need correction in a future pass.</Body>
          <Body>Recording state: {state.phase}</Body>
          {state.phase === 'recording' ? (
            <>
              <Text style={styles.timer}>{Math.round(capture.durationMillis / 1000)}s</Text>
              <Button label="Stop" onPress={() => void stop()} />
            </>
          ) : state.phase === 'idle' || state.phase === 'permission_required' ? (
            <Button label="Record attempt" onPress={() => void start()} />
          ) : null}
          {state.recordingUri && <PlaybackButton uri={state.recordingUri} />}
          {state.phase === 'recorded' && (
            <>
              <Button label="Upload attempt" onPress={() => void upload()} />
              <Button secondary label="Retry recording" onPress={retryRecording} />
            </>
          )}
          {state.phase === 'uploading' && <Button disabled loading label="Uploading" onPress={() => {}} />}
          {state.phase === 'uploaded' && <Button label="Assess attempt" onPress={() => void assess()} />}
          {state.phase === 'analyzing' && <Button disabled loading label="Assessing" onPress={() => {}} />}
          {state.phase === 'failure' && state.utteranceId && (
            <Button label="Retry assessment" onPress={() => void assess()} />
          )}
          {state.phase === 'failure' && !state.utteranceId && (
            <Button label="Retry recording" onPress={retryRecording} />
          )}
          <ErrorMessage message={capture.error ?? state.error} />
        </Card>
      )}

      {state.result && evidence && (
        <Card>
          {evidence.evidence_status === 'synthetic_replay' && <FixtureBanner />}
          <Chinese>{target?.text}</Chinese>
          <Pinyin>{target?.display_pinyin}</Pinyin>
          <EvidenceRow label="Provider score" value={evidence.overall_score} />
          <EvidenceRow label="Pronunciation score" value={evidence.pronunciation_score} />
          {unsupportedTones && <Body>Tone detection unavailable from this evaluator.</Body>}
          {evidence.syllables?.map((syllable, index) => (
            <View key={`${syllable.text ?? 'syllable'}-${index}`} style={styles.syllable}>
              <Chinese>{syllable.text ?? `Syllable ${index + 1}`}</Chinese>
              <Pinyin>{syllable.pinyin}</Pinyin>
              <EvidenceRow label="Pronunciation score" value={syllable.pronunciation_score} />
              <EvidenceRow label="Detected tone" value={syllable.detected_tone} />
              <EvidenceRow label="Reference tone" value={syllable.reference_tone} />
              <EvidenceRow label="Tone score" value={syllable.tone_score} />
              <EvidenceRow label="Phones" value={syllable.phones} />
              <EvidenceRow label="Provider errors" value={syllable.provider_errors} />
            </View>
          ))}
          <Button secondary label="Try again" onPress={retryRecording} />
        </Card>
      )}

      {attempts.length > 0 && (
        <Card>
          <Heading>Attempts this session</Heading>
          {attempts.map((attempt, index) => (
            <View key={attempt.attempt.id} style={styles.attempt}>
              <Body>Attempt {index + 1}</Body>
              <PlaybackButton uri={attempt.uri} label={`Play attempt ${index + 1}`} />
              <EvidenceRow
                label="Provider score"
                value={attempt.assessment.normalized_result?.overall_score}
              />
            </View>
          ))}
        </Card>
      )}

      {state.result && (
        <EvidencePanel>
          <EvidenceRow label="Utterance ID" value={state.utteranceId} />
          <EvidenceRow label="Attempt ID" value={state.result.attempt.id} />
          <EvidenceRow label="Run ID" value={state.result.assessment.id} />
          <EvidenceRow
            label="Provider"
            value={`${state.result.assessment.provider} / ${state.result.assessment.product}`}
          />
          <EvidenceRow label="Latency" value={`${state.result.assessment.latency_ms ?? 'unknown'} ms`} />
          <EvidenceRow label="Status" value={state.result.assessment.status} />
          <EvidenceRow label="Target snapshot" value={state.result.assessment.target_snapshot} />
          <EvidenceRow label="Normalized result" value={state.result.assessment.normalized_result} />
        </EvidencePanel>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  targetInput: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    minHeight: 56,
    paddingHorizontal: 14,
    color: colors.text,
    fontSize: 28,
  },
  timer: { fontSize: 40, color: colors.text, fontVariant: ['tabular-nums'] },
  syllable: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 12, gap: 6 },
  attempt: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 12, gap: 8 },
});
