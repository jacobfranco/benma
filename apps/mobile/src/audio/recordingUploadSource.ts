import { fetch as expoFetch } from 'expo/fetch';
import { File } from 'expo-file-system';

import type { RecordingUploadSource } from '@/audio/recordingUploadSource.types';

// Native default. Metro resolves recordingUploadSource.web.ts in the browser.
export async function createRecordingUploadSource(
  uri: string, _mimeHint: string,
): Promise<RecordingUploadSource> {
  const body = new FormData();
  // SDK 57 requires a real Expo File, not a React Native { uri, name, type } part.
  body.append('file', new File(uri));
  return { body, fetch: expoFetch, release: () => {} };
}
