import { useCallback, useEffect, useState } from 'react';
import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from 'expo-audio';

export type PermissionState = 'checking' | 'granted' | 'denied';

export function useAudioCapture() {
  const recorder = useAudioRecorder({ ...RecordingPresets.HIGH_QUALITY, directory: 'document' });
  const recorderState = useAudioRecorderState(recorder, 200);
  const [permission, setPermission] = useState<PermissionState>('checking');
  const [error, setError] = useState<string | null>(null);

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

  const start = useCallback(async () => {
    setError(null);
    const granted = permission === 'granted' || (await requestPermission());
    if (!granted) return false;
    try {
      await recorder.prepareToRecordAsync();
      recorder.record();
      return true;
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Recording could not start';
      setError(message);
      throw caught;
    }
  }, [permission, recorder, requestPermission]);

  const stop = useCallback(async () => {
    try {
      await recorder.stop();
      const uri = recorder.uri;
      if (!uri) throw new Error('Recording completed without a file URI');
      return { uri, durationMillis: recorderState.durationMillis };
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Recording could not stop';
      setError(message);
      throw caught;
    }
  }, [recorder, recorderState.durationMillis]);

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
