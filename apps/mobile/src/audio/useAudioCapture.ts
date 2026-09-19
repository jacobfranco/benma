import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from 'expo-audio';

import { beginRecording, endRecording, registerAudioReset } from '@/audio/session';
import { discardRecording } from '@/audio/discardRecording';
import { retainRecordingUri } from '@/audio/recordingUri';

export type PermissionState = 'checking' | 'granted' | 'denied';

export function useAudioCapture(
  { directory = 'document' }: { directory?: 'cache' | 'document' } = {},
) {
  const [permission, setPermission] = useState<PermissionState>('checking');
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const recordingOwner = useRef({});
  const recordingActive = useRef(false);
  const stopRequested = useRef(false);
  const lifecycleError = useRef<string | null>(null);
  const mounted = useRef(true);
  const releaseRecording = useRef<(() => void) | null>(null);
  const recorder = useAudioRecorder(
    { ...RecordingPresets.HIGH_QUALITY, directory },
    (status) => {
      if (status.hasError) {
        const message = status.error ?? 'Recording stopped with an audio encoder error';
        lifecycleError.current = message;
        recordingActive.current = false;
        endRecording(recordingOwner.current);
        setError(message);
      } else if (status.isFinished && recordingActive.current && !stopRequested.current) {
        const message = 'Recording stopped unexpectedly. Please record again.';
        lifecycleError.current = message;
        recordingActive.current = false;
        endRecording(recordingOwner.current);
        setError(message);
      }
    },
  );
  const recorderState = useAudioRecorderState(recorder, 200);

  const requestPermission = useCallback(async () => {
    const result = await AudioModule.requestRecordingPermissionsAsync();
    setPermission(result.granted ? 'granted' : 'denied');
    return result.granted;
  }, []);

  useEffect(() => {
    const message = (caught: unknown) =>
      setError(caught instanceof Error ? caught.message : 'Audio services are unavailable');
    void AudioModule.getRecordingPermissionsAsync()
      .then((result) => setPermission(result.granted ? 'granted' : 'denied'))
      .catch(message);
    void setAudioModeAsync({
      playsInSilentMode: true,
      allowsRecording: true,
      allowsBackgroundRecording: false,
      shouldPlayInBackground: false,
    }).catch(message);
  }, []);

  useEffect(() => {
    mounted.current = true;
    const owner = recordingOwner.current;
    const reset = () => {
      generation.current++;
      if (recordingActive.current && !stopRequested.current) void discardRecording(recorder).catch(() => {});
      recordingActive.current = false;
      endRecording(owner);
      releaseRecording.current?.();
      releaseRecording.current = null;
    };
    const unregister = registerAudioReset(reset);
    return () => {
      mounted.current = false;
      unregister();
      reset();
    };
  }, [recorder]);

  const start = useCallback(async () => {
    setError(null);
    lifecycleError.current = null;
    stopRequested.current = false;
    const requestedGeneration = generation.current;
    const granted = permission === 'granted' || (await requestPermission());
    if (!granted || !mounted.current || requestedGeneration !== generation.current) return false;
    try {
      beginRecording(recordingOwner.current);
      await recorder.prepareToRecordAsync();
      if (!mounted.current || requestedGeneration !== generation.current) {
        await discardRecording(recorder);
        endRecording(recordingOwner.current);
        return false;
      }
      recorder.record();
      if (!recorder.getStatus().isRecording) {
        throw new Error('Recording did not enter the active state');
      }
      recordingActive.current = true;
      return true;
    } catch (caught) {
      recordingActive.current = false;
      endRecording(recordingOwner.current);
      const message = caught instanceof Error ? caught.message : 'Recording could not start';
      setError(message);
      throw caught;
    }
  }, [permission, recorder, requestPermission]);

  const stop = useCallback(async () => {
    const requestedGeneration = generation.current;
    stopRequested.current = true;
    try {
      const finalStatus = recorder.getStatus();
      if (!finalStatus.isRecording) {
        throw new Error(
          lifecycleError.current ?? 'Recording stopped before it could be completed. Please try again.',
        );
      }
      await recorder.stop();
      recordingActive.current = false;
      endRecording(recordingOwner.current);
      const uri = recorder.uri;
      if (!uri) throw new Error('Recording completed without a file URI');
      const release = retainRecordingUri(uri);
      releaseRecording.current?.();
      const current = mounted.current && requestedGeneration === generation.current;
      releaseRecording.current = current ? release : null;
      if (!current) release();
      return { uri, durationMillis: finalStatus.durationMillis };
    } catch (caught) {
      recordingActive.current = false;
      endRecording(recordingOwner.current);
      const message = caught instanceof Error ? caught.message : 'Recording could not stop';
      setError(message);
      throw caught;
    } finally {
      stopRequested.current = false;
    }
  }, [recorder]);

  return {
    permission,
    requestPermission,
    start,
    stop,
    isRecording: recorderState.isRecording,
    durationMillis: recorderState.durationMillis,
    error: recorderState.mediaServicesDidReset
      ? 'Audio services were interrupted. Please record again.'
      : error,
  };
}
