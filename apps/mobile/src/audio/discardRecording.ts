import type { AudioRecorder } from 'expo-audio';

export async function discardRecording(recorder: AudioRecorder): Promise<void> {
  if (recorder.getStatus().isRecording) await recorder.stop();
}
