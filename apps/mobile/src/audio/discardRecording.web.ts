import type { AudioRecorder } from 'expo-audio';

import { retainRecordingUri } from './recordingUri';

export async function discardRecording(recorder: AudioRecorder): Promise<void> {
  const status = recorder.getStatus();
  if (!status.canRecord && !status.isRecording) return;
  // Expo has no public release() for a prepared web recorder. A stop releases its tracks.
  if (!status.isRecording) recorder.record();
  await recorder.stop();
  if (recorder.uri) retainRecordingUri(recorder.uri)();
}
