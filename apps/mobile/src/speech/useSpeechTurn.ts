import { useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';

import { api } from '@/api/client';
import type { ContextualInterpretationRun, PerceptionRun } from '@/api/types';
import { useAudioCapture } from '@/audio/useAudioCapture';
import { stopAllPlayback } from '@/audio/session';
import {
  logTiming, submitSpeech, SpeechSubmissionError, speechFailureLabels,
  type SpeechAnalysis, type SpeechCheckpoint, type SpeechMode, type SpeechStage, type SpeechSubmission,
} from '@/speech/workflow';

export function useSpeechTurn({ mode, onPerception, onResult, onAnalysis, onInterpretation, onResponseFailure, beforeRecording }: {
  mode: SpeechMode | null;
  onPerception: (perception: PerceptionRun) => void;
  onResult: (result: SpeechSubmission, startedAt: number) => void;
  onAnalysis?: (analysis: SpeechAnalysis) => void;
  onInterpretation?: (interpretation: ContextualInterpretationRun) => void;
  onResponseFailure?: () => Promise<void>;
  beforeRecording?: () => void;
}) {
  const capture = useAudioCapture({ directory: 'cache' });
  const [phase, setPhase] = useState<'idle' | 'recording' | 'processing'>('idle');
  const [stage, setStage] = useState<SpeechStage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryable, setRetryable] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const lock = useRef(false);
  const mounted = useRef(true);
  const recordedMode = useRef<SpeechMode | null>(null);
  const checkpoint = useRef<SpeechCheckpoint | null>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  const start = async () => {
    if (lock.current || !mode || phase === 'recording') return;
    lock.current = true;
    try {
      beforeRecording?.();
      stopAllPlayback();
      setError(null);
      setRetryable(false);
      checkpoint.current = null;
      recordedMode.current = mode;
      if (!(await capture.start())) {
        setPermissionDenied(true);
        setError('Microphone access is needed. Allow it in Settings and try again.');
        return;
      }
      setPermissionDenied(false);
      if (mounted.current) setPhase('recording');
    } catch { if (mounted.current) setError(speechFailureLabels.recording); }
    finally { lock.current = false; }
  };

  const submit = async (retry = false) => {
    if (lock.current || !mode || (!retry && phase !== 'recording')) return;
    lock.current = true;
    const startedAt = Date.now();
    setPhase('processing');
    setError(null);
    setRetryable(false);
    try {
      if (!retry) {
        setStage('stopping');
        const recording = await capture.stop();
        if (__DEV__) console.info('[speech timing] recording duration ms:', recording.durationMillis);
        checkpoint.current = { uri: recording.uri };
      }
      if (!checkpoint.current) throw new SpeechSubmissionError('recording');
      const result = await submitSpeech(api, recordedMode.current ?? mode, checkpoint.current,
        Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4',
        (next) => { if (!mounted.current) throw new Error('Screen closed'); setStage(next); },
        (perception) => { if (mounted.current) onPerception(perception); }, startedAt,
        (analysis) => { if (mounted.current) onAnalysis?.(analysis); },
        onInterpretation ? (interpretation) => {
          if (mounted.current) { onInterpretation(interpretation); logTiming('total time to meaning', startedAt); }
        } : undefined);
      if (mounted.current) onResult(result, startedAt);
      checkpoint.current = null;
    } catch (caught) {
      if (!mounted.current) return;
      const failure = caught instanceof SpeechSubmissionError ? caught.stage : 'recording';
      setError(speechFailureLabels[failure]);
      setRetryable(failure !== 'response' && failure !== 'recording');
      if (failure === 'response') await onResponseFailure?.();
    } finally {
      lock.current = false;
      if (mounted.current) { setPhase('idle'); setStage(null); }
      logTiming('submission completion', startedAt);
    }
  };
  return { phase, stage, error: capture.error ? speechFailureLabels.recording : error,
    retryable, permissionDenied, durationMillis: capture.durationMillis,
    start, stop: () => submit(), retry: () => submit(true), busy: phase !== 'idle',
    reset: () => {
      if (lock.current || phase !== 'idle') return;
      checkpoint.current = null; recordedMode.current = null;
      setRetryable(false); setError(null);
    },
  };
}
