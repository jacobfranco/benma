import { useState } from 'react';
import { Platform, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { errorMessage } from '@/api/errors';
import { PlaybackButton } from '@/audio/PlaybackButton';
import { useAudioCapture } from '@/audio/useAudioCapture';
import { Body, Button, Card, Chinese, ErrorMessage, Heading, Screen } from '@/components/Ui';
import { colors } from '@/theme';

interface CalibrationPrompt {
  id: string;
  target: string;
  requestedProduction: 'correct' | 'wrong tone' | 'wrong initial' | 'wrong final' | 'negative control';
  instruction: string;
}

const TARGETS = ['妈', '麻', '马', '骂', '买', '卖', '水', '睡', '生活', '睡觉'];

function prompts(): CalibrationPrompt[] {
  const categories: CalibrationPrompt['requestedProduction'][] = [
    'wrong tone',
    'wrong initial',
    'wrong final',
    'correct',
    'negative control',
  ];
  return categories.flatMap((category, categoryIndex) =>
    TARGETS.map((target, index) => ({
      id: `pilot-${categoryIndex + 1}-${index + 1}`,
      target,
      requestedProduction: category,
      instruction:
        category === 'correct'
          ? 'Produce the target naturally and clearly.'
          : category === 'negative control'
            ? 'Produce nonsense, very unclear speech, or silence as assigned in the session notes.'
            : `Deliberately produce exactly one ${category.replace('wrong ', '')} error.`,
    })),
  );
}

const PILOT_PROMPTS = prompts();

export default function CalibrationCaptureScreen() {
  const [index, setIndex] = useState(0);
  const [recording, setRecording] = useState<{ uri: string; durationMillis: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const capture = useAudioCapture();
  const prompt = PILOT_PROMPTS[index]!;

  if (!__DEV__) {
    return (
      <Screen>
        <Heading>Calibration capture unavailable</Heading>
        <Body>This internal evidence-collection route is disabled in production builds.</Body>
      </Screen>
    );
  }

  const start = async () => {
    setError(null);
    setRecording(null);
    try {
      await capture.start();
    } catch (caught) {
      setError(errorMessage(caught));
    }
  };

  const stop = async () => {
    try {
      setRecording(await capture.stop());
    } catch (caught) {
      setError(errorMessage(caught));
    }
  };

  const save = async () => {
    if (!recording) return;
    setSaving(true);
    setError(null);
    try {
      const target = await api.createTarget(prompt.target);
      const practice = await api.createPracticeSession('pronunciation', {
        development_calibration_capture: true,
        prompt_id: prompt.id,
        requested_production: prompt.requestedProduction,
        requested_production_is_ground_truth: false,
        evidence_requires_three_native_listener_annotations: true,
        research_exported: false,
      });
      const utterance = await api.uploadUtterance(
        recording.uri,
        Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4',
        practice.id,
      );
      const attempt = await api.createAttempt(utterance.id, target.id);
      setSaved((current) => [...current, attempt.id]);
      setRecording(null);
      setIndex((current) => Math.min(PILOT_PROMPTS.length - 1, current + 1));
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen>
      <Heading>Calibration capture</Heading>
      <Body>
        Development-only capture. Saving keeps production evidence; it does not export anything to
        the benchmark. The requested production is a recording instruction, not ground truth.
      </Body>
      <View style={styles.progressTrack}>
        <View style={[styles.progress, { width: `${(saved.length / PILOT_PROMPTS.length) * 100}%` }]} />
      </View>
      <Text style={styles.progressText}>
        {saved.length}/{PILOT_PROMPTS.length} captured this run
      </Text>
      <Card>
        <Text style={styles.promptId}>{prompt.id}</Text>
        <Chinese>{prompt.target}</Chinese>
        <Text style={styles.production}>{prompt.requestedProduction}</Text>
        <Body>{prompt.instruction}</Body>
        {capture.isRecording ? (
          <>
            <Text style={styles.timer}>{(capture.durationMillis / 1000).toFixed(1)}s</Text>
            <Button label="Stop" onPress={() => void stop()} />
          </>
        ) : (
          <Button label={recording ? 'Record again' : 'Record'} onPress={() => void start()} />
        )}
        {recording && (
          <>
            <PlaybackButton uri={recording.uri} label="Play capture" />
            <Button loading={saving} label="Save capture" onPress={() => void save()} />
          </>
        )}
        <ErrorMessage message={error ?? capture.error} />
      </Card>
      <Body>
        Export is a separate developer command and requires an explicit confirmation flag. Future
        public use requires a consent design.
      </Body>
    </Screen>
  );
}

const styles = StyleSheet.create({
  progressTrack: { height: 8, backgroundColor: colors.border, borderRadius: 4, overflow: 'hidden' },
  progress: { height: 8, backgroundColor: colors.primary },
  progressText: { color: colors.secondary, fontSize: 13 },
  promptId: { color: colors.secondary, fontSize: 11, fontWeight: '700', textTransform: 'uppercase' },
  production: { color: colors.reference, fontSize: 20, fontWeight: '800', textTransform: 'capitalize' },
  timer: { fontSize: 42, color: colors.text, fontVariant: ['tabular-nums'] },
});
