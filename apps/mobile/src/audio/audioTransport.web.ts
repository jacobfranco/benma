import type { AudioDownload } from './audioData';

export const mediaFetch: typeof globalThis.fetch = (input, init) => globalThis.fetch(input, init);
export async function readAudioResponse(response: Response): Promise<AudioDownload> {
  const blob = await response.blob();
  return { blob, bytes: new Uint8Array(await blob.arrayBuffer()), contentType: blob.type || null };
}
