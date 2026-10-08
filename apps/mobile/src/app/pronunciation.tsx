import { useReducer, useRef, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api/client';
import { errorMessage } from '@/api/errors';
import type { PronunciationResult, PronunciationTarget, ReferenceSpeech } from '@/api/types';
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
import { PitchPlot, type PitchPoint } from '@/components/PitchPlot';
import { colors } from '@/theme';

type JsonMap = Record<string, unknown>;

function asMap(value: unknown): JsonMap | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as JsonMap) : null;
}

function pitchPoints(value: unknown): PitchPoint[] {
  return Array.isArray(value) ? (value as PitchPoint[]) : [];
}

function toneLabel(value: number | null | undefined): string {
  return value === 0 ? 'Neutral tone' : value ? `Tone ${value}` : 'Unresolved';
}

function providerIsSynthetic(result: PronunciationResult): boolean {
  const normalized = asMap(result.assessment?.normalized_result);
  return normalized?.evidence_status === 'synthetic_replay';
}

export default function PronunciationScreen() {
  const [targetText, setTargetText] = useState('生活');
  const [target, setTarget] = useState<PronunciationTarget | null>(null);
  const [reference, setReference] = useState<ReferenceSpeech | null>(null);
  const [referenceLoading, setReferenceLoading] = useState(false);
  const [targetError, setTargetError] = useState<string | null>(null);
  const [showCorrection, setShowCorrection] = useState(false);
  const [correctedPinyin, setCorrectedPinyin] = useState('');
  const [history, setHistory] = useState<PronunciationResult[]>([]);
  const [comparison, setComparison] = useState<string[]>([]);
  const [advanced, setAdvanced] = useState(false);
  const [state, dispatch] = useReducer(
    (current: WorkflowState<PronunciationResult>, action: WorkflowAction<PronunciationResult>) =>
      workflowReducer(current, action),
    initialWorkflowState<PronunciationResult>(),
  );
  const capture = useAudioCapture();
  const sessionId = useRef<string | null>(null);
  const pendingAttemptId = useRef<string | null>(null);

  const loadReference = async (prepared: PronunciationTarget, force = false) => {
    setReferenceLoading(true);
    try {
      setReference(await api.createReferenceSpeech(prepared.id, force));
    } catch (error) {
      setReference(null);
      setTargetError(errorMessage(error));
    } finally {
      setReferenceLoading(false);
    }
  };

  const resolveTarget = async () => {
    setTargetError(null);
    setReference(null);
    try {
      const prepared = await api.createTarget(targetText.trim());
      setTarget(prepared);
      setCorrectedPinyin(prepared.pinyin_syllables.join(' '));
      setHistory(await api.listPronunciationAttempts(prepared.id));
      dispatch({ type: 'RESET' });
      pendingAttemptId.current = null;
      await loadReference(prepared);
    } catch (error) {
      setTargetError(errorMessage(error));
    }
  };

  const saveCorrection = async () => {
    if (!target) return;
    setTargetError(null);
    try {
      const corrected = await api.correctTargetPinyin(target.id, correctedPinyin);
      setTarget(corrected);
      setShowCorrection(false);
      setHistory([]);
      setComparison([]);
      dispatch({ type: 'RESET' });
      pendingAttemptId.current = null;
      await loadReference(corrected);
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

  const analyze = async (rerun = false) => {
    if (!state.utteranceId || !target) return;
    dispatch({ type: state.phase === 'failure' ? 'RETRY_ANALYSIS' : 'ANALYZE' });
    try {
      const attempt = pendingAttemptId.current
        ? await api.getAttempt(pendingAttemptId.current)
        : await api.createAttempt(state.utteranceId, target.id);
      pendingAttemptId.current = attempt.id;
      const result = await api.analyzePronunciation(attempt.id, rerun);
      dispatch({ type: 'SUCCEEDED', result });
      setHistory(await api.listPronunciationAttempts(target.id));
    } catch (error) {
      dispatch({ type: 'FAILED', message: errorMessage(error) });
    }
  };

  const retryRecording = () => {
    pendingAttemptId.current = null;
    dispatch({ type: 'RESET' });
    void start();
  };

  const toggleComparison = (attemptId: string) => {
    setComparison((current) => {
      if (current.includes(attemptId)) return current.filter((value) => value !== attemptId);
      return current.length < 2 ? [...current, attemptId] : [current[1]!, attemptId];
    });
  };

  const result = state.result;
  const acoustic = asMap(result?.acoustic?.normalized_result);
  const referenceAcoustic = asMap(result?.reference_audio?.acoustic_result ?? reference?.acoustic_result);
  const userPitch = pitchPoints(acoustic?.mobile_f0);
  const referencePitch = pitchPoints(referenceAcoustic?.mobile_f0);
  const regions =
    result?.syllables.flatMap((syllable) => {
      const timing = asMap(syllable.timing);
      return typeof timing?.start_seconds === 'number' && typeof timing.end_seconds === 'number'
        ? [
            {
              label: syllable.characters,
              start_seconds: timing.start_seconds,
              end_seconds: timing.end_seconds,
            },
          ]
        : [];
    }) ?? [];
  const compared = comparison
    .map((id) => history.find((item) => item.attempt.id === id))
    .filter((item): item is PronunciationResult => Boolean(item));

  return (
    <Screen>
      <Heading>Pronunciation lab</Heading>
      <Body>Listen, record, inspect the evidence, then compare what you hear.</Body>

      <Card>
        <Text style={styles.label}>Mandarin target</Text>
        <TextInput
          accessibilityLabel="Pronunciation target"
          onChangeText={setTargetText}
          style={styles.targetInput}
          value={targetText}
        />
        <Button
          disabled={!targetText.trim()}
          label="Prepare target"
          onPress={() => void resolveTarget()}
        />
        <ErrorMessage message={targetError} />
      </Card>

      {target && (
        <Card>
          <View style={styles.targetHeader}>
            <View style={styles.targetIdentity}>
              <Chinese>{target.text}</Chinese>
              <Pinyin>{target.display_pinyin}</Pinyin>
            </View>
            <Pressable
              accessibilityRole="button"
              onPress={() => setShowCorrection((value) => !value)}
            >
              <Text style={styles.link}>Edit pinyin</Text>
            </Pressable>
          </View>
          <Text style={styles.provenance}>
            {target.pinyin_source === 'user-corrected' ? 'Your corrected reading' : 'Generated reading'}
          </Text>
          {showCorrection && (
            <View style={styles.correction}>
              <Body>Use numeric pinyin, one syllable per character (for example: sheng1 huo2).</Body>
              <TextInput
                accessibilityLabel="Corrected numeric pinyin"
                autoCapitalize="none"
                onChangeText={setCorrectedPinyin}
                style={styles.pinyinInput}
                value={correctedPinyin}
              />
              <Button label="Use this reading" onPress={() => void saveCorrection()} />
            </View>
          )}

          {referenceLoading ? (
            <Button disabled loading label="Preparing reference" onPress={() => {}} />
          ) : reference?.status === 'succeeded' && reference.audio_url ? (
            <>
              {reference.generation_config.evidence_status === 'synthetic_replay' && <FixtureBanner />}
              <PlaybackButton
                label="▶ Native reference"
                uri={api.absoluteUrl(reference.audio_url)}
              />
              <Text style={styles.caption}>One example realization—not a grading template.</Text>
            </>
          ) : (
            <View style={styles.referenceFailure}>
              <Body>Reference audio is unavailable. You can still record and analyze.</Body>
              <Button
                secondary
                label="Retry reference"
                onPress={() => void loadReference(target, true)}
              />
            </View>
          )}

          <View style={styles.recordingSection}>
            {state.phase === 'recording' ? (
              <>
                <Text style={styles.timer}>{(capture.durationMillis / 1000).toFixed(1)}s</Text>
                <Button label="Stop recording" onPress={() => void stop()} />
              </>
            ) : state.phase === 'idle' || state.phase === 'permission_required' ? (
              <Button label="Record attempt" onPress={() => void start()} />
            ) : null}
            {state.recordingUri && (
              <PlaybackButton uri={state.recordingUri} label="▶ Play mine" />
            )}
            {state.phase === 'recorded' && (
              <>
                <Button label="Keep and upload" onPress={() => void upload()} />
                <Button secondary label="Record again" onPress={retryRecording} />
              </>
            )}
            {state.phase === 'uploading' && (
              <Button disabled loading label="Saving attempt" onPress={() => {}} />
            )}
            {state.phase === 'uploaded' && (
              <Button label="Analyze attempt" onPress={() => void analyze()} />
            )}
            {state.phase === 'analyzing' && (
              <Button disabled loading label="Analyzing evidence" onPress={() => {}} />
            )}
            {state.phase === 'failure' && state.utteranceId && (
              <Button label="Retry analysis" onPress={() => void analyze(true)} />
            )}
            {state.phase === 'failure' && !state.utteranceId && (
              <Button label="Record again" onPress={retryRecording} />
            )}
            <ErrorMessage message={capture.error ?? state.error} />
          </View>
        </Card>
      )}

      {result && (
        <>
          <Card>
            {providerIsSynthetic(result) && <FixtureBanner />}
            <View style={styles.resultHeader}>
              <View>
                <Text style={styles.eyebrow}>LATEST ATTEMPT</Text>
                <Chinese>{result.target.text}</Chinese>
              </View>
              <Text style={styles.experimental}>Experimental analysis</Text>
            </View>
            {asMap(result.overall_evidence.recording_quality)?.status ===
              'invalid_for_interpretation' && (
              <View style={styles.qualityWarning}>
                <Text style={styles.warningTitle}>Recording issue</Text>
                <Body>Pronunciation interpretation was suppressed. Try a quieter, clearer recording.</Body>
              </View>
            )}
            <View style={styles.syllableGrid}>
              {result.syllables.map((syllable) => {
                return (
                  <View key={syllable.syllable_index} style={styles.syllableCard}>
                    <Chinese>{syllable.characters}</Chinese>
                    <Pinyin>{syllable.pinyin}</Pinyin>
                    <Text style={styles.expected}>
                      Reference {toneLabel(syllable.expected_surface_tone)}
                    </Text>
                    <Body>Tone comparison is unavailable. Reference pronunciation is not a grade.</Body>
                    {syllable.surface_tone_reason.map((rule, index) => (
                      <Text key={index} style={styles.ruleReason}>
                        {String(rule.type).replaceAll('_', ' ').toLocaleLowerCase()}
                      </Text>
                    ))}
                  </View>
                );
              })}
            </View>
            <View style={styles.abButtons}>
              {result.reference_audio?.audio_url && (
                <PlaybackButton
                  label="▶ Reference"
                  uri={api.absoluteUrl(result.reference_audio.audio_url)}
                />
              )}
              <PlaybackButton
                label="▶ Mine"
                uri={api.absoluteUrl(result.recording_audio_url)}
              />
            </View>
            <PitchPlot reference={referencePitch} regions={regions} user={userPitch} />
            <Button secondary label="Record another attempt" onPress={retryRecording} />
          </Card>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={advanced ? 'Hide advanced evidence' : 'Show advanced evidence'}
            onPress={() => setAdvanced((value) => !value)}
            style={styles.advancedToggle}
          >
            <Text style={styles.link}>{advanced ? 'Hide advanced evidence' : 'Show advanced evidence'}</Text>
          </Pressable>
          {advanced && (
            <EvidencePanel title="Experimental diagnostics">
              <Body>Uncalibrated provider and historical interpretation data. These are not pronunciation grades.</Body>
              <EvidenceRow label="Capability policy" value={result.capability_policy} />
              <EvidenceRow label="Provider" value={result.assessment?.provider} />
              <EvidenceRow label="Provider evidence" value={result.assessment?.normalized_result} />
              <EvidenceRow
                label="Acoustic algorithm"
                value={result.acoustic && `${result.acoustic.algorithm} ${result.acoustic.algorithm_version}`}
              />
              <EvidenceRow label="Acoustic normalization" value={acoustic?.normalization} />
              <EvidenceRow label="Alignment" value={result.alignment} />
              <EvidenceRow label="Interpretation" value={result.interpretation} />
              <EvidenceRow label="Pipeline" value={result.overall_evidence} />
            </EvidencePanel>
          )}
        </>
      )}

      {history.length > 0 && (
        <Card>
          <Heading>Attempt history</Heading>
          <Body>Attempts stay separate. Select two for an evidence-only A/B comparison.</Body>
          {history.map((attempt, index) => {
            const selected = comparison.includes(attempt.attempt.id);
            const attemptAcoustic = asMap(attempt.acoustic?.normalized_result);
            return (
              <View key={attempt.attempt.id} style={styles.attempt}>
                <View style={styles.attemptHeader}>
                  <View>
                    <Text style={styles.attemptTitle}>Attempt {index + 1}</Text>
                    <Text style={styles.caption}>{new Date(attempt.attempt.created_at).toLocaleString()}</Text>
                  </View>
                  <Pressable
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: selected }}
                    onPress={() => toggleComparison(attempt.attempt.id)}
                    style={[styles.compareChip, selected && styles.compareChipSelected]}
                  >
                    <Text style={[styles.compareText, selected && styles.compareTextSelected]}>
                      {selected ? 'Selected' : 'Compare'}
                    </Text>
                  </Pressable>
                </View>
                <PlaybackButton
                  label={`▶ Play attempt ${index + 1}`}
                  uri={api.absoluteUrl(attempt.recording_audio_url)}
                />
                <PitchPlot compact user={pitchPoints(attemptAcoustic?.mobile_f0)} />
              </View>
            );
          })}
        </Card>
      )}

      {compared.length === 2 && (
        <Card>
          <Heading>A/B comparison</Heading>
          <Body>No improvement percentage is calculated. Listen and compare the evidence directly.</Body>
          {compared.map((attempt) => (
            <View key={attempt.attempt.id} style={styles.compareAttempt}>
              <Text style={styles.attemptTitle}>
                Attempt {history.findIndex((item) => item.attempt.id === attempt.attempt.id) + 1}
              </Text>
              <PlaybackButton
                label="▶ Play"
                uri={api.absoluteUrl(attempt.recording_audio_url)}
              />
              {attempt.syllables.map((syllable) => (
                <Text key={syllable.syllable_index} style={styles.comparisonEvidence}>
                  {syllable.characters}: tone comparison unavailable
                </Text>
              ))}
            </View>
          ))}
        </Card>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: { color: colors.secondary, fontSize: 13, fontWeight: '700', textTransform: 'uppercase' },
  targetInput: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    minHeight: 58,
    paddingHorizontal: 14,
    color: colors.text,
    fontSize: 30,
  },
  pinyinInput: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    minHeight: 48,
    paddingHorizontal: 12,
    color: colors.text,
    fontSize: 17,
  },
  targetHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  targetIdentity: { flex: 1 },
  provenance: { color: colors.secondary, fontSize: 12 },
  link: { color: colors.primary, fontSize: 15, fontWeight: '700' },
  correction: { borderTopColor: colors.border, borderTopWidth: 1, paddingTop: 12, gap: 10 },
  caption: { color: colors.secondary, fontSize: 12, lineHeight: 17 },
  referenceFailure: { gap: 10 },
  recordingSection: { borderTopColor: colors.border, borderTopWidth: 1, paddingTop: 14, gap: 10 },
  timer: { fontSize: 42, color: colors.text, fontVariant: ['tabular-nums'] },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  eyebrow: { color: colors.secondary, fontSize: 11, fontWeight: '800', letterSpacing: 1.2 },
  experimental: { color: colors.reference, fontSize: 12, fontWeight: '700', maxWidth: 110 },
  qualityWarning: { backgroundColor: colors.warningBackground, padding: 12, borderRadius: 10, gap: 4 },
  warningTitle: { color: colors.warningText, fontWeight: '800' },
  syllableGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  syllableCard: {
    flexGrow: 1,
    flexBasis: 145,
    borderColor: colors.border,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 12,
    padding: 13,
    gap: 3,
    backgroundColor: colors.plotBackground,
  },
  expected: { color: colors.text, fontSize: 13, fontWeight: '700' },
  ruleReason: { color: colors.secondary, fontSize: 11, textTransform: 'capitalize' },
  abButtons: { gap: 8 },
  advancedToggle: { alignItems: 'center', padding: 8 },
  attempt: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 14, gap: 9 },
  attemptHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  attemptTitle: { color: colors.text, fontSize: 17, fontWeight: '800' },
  compareChip: {
    borderColor: colors.primary,
    borderWidth: 1,
    borderRadius: 18,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  compareChipSelected: { backgroundColor: colors.primary },
  compareText: { color: colors.primary, fontWeight: '700', fontSize: 12 },
  compareTextSelected: { color: '#fff' },
  compareAttempt: { borderTopColor: colors.border, borderTopWidth: 1, paddingTop: 12, gap: 8 },
  comparisonEvidence: { color: colors.secondary, fontSize: 14, lineHeight: 20 },
});
