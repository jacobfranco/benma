import { fetch } from 'expo/fetch';

import type { AudioDownload } from './audioData';

export const mediaFetch = fetch;
export async function readAudioResponse(response: Response): Promise<AudioDownload> {
  return { bytes: await response.bytes(), contentType: response.headers?.get('Content-Type') ?? null };
}
