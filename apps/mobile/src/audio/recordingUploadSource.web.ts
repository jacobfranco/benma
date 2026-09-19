import type { RecordingUploadSource } from '@/audio/recordingUploadSource.types';
import { retainRecordingUri } from '@/audio/recordingUri';

const extensions: Record<string, string> = {
  'audio/webm': 'webm', 'audio/mp4': 'm4a', 'audio/x-m4a': 'm4a',
  'audio/ogg': 'ogg', 'audio/wav': 'wav', 'audio/x-wav': 'wav',
  'audio/mpeg': 'mp3', 'audio/flac': 'flac',
};

async function inferMime(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.slice(0, 12).arrayBuffer());
  const text = (start: number, end: number) => String.fromCharCode(...bytes.slice(start, end));
  if (bytes[0] === 0x1a && bytes[1] === 0x45 && bytes[2] === 0xdf && bytes[3] === 0xa3) return 'audio/webm';
  if (text(4, 8) === 'ftyp') return 'audio/mp4';
  if (text(0, 4) === 'OggS') return 'audio/ogg';
  if (text(0, 4) === 'RIFF' && text(8, 12) === 'WAVE') return 'audio/wav';
  throw new Error('Unknown recording container');
}

export async function createRecordingUploadSource(
  uri: string, _mimeHint: string,
): Promise<RecordingUploadSource> {
  const release = retainRecordingUri(uri);
  let stage = 'fetch';
  try {
    // Expo Audio web returns an object URL. Never send API credentials to this fetch.
    if (!uri.startsWith('blob:')) throw new Error('Expected a browser recording');
    const response = await globalThis.fetch(uri);
    if (!response.ok) throw new Error('Recording unavailable');
    stage = 'blob';
    let blob = await response.blob();
    if (!blob.size) throw new Error('Recording is empty');
    stage = 'format';
    // The recorder hint may be WebM even when the browser falls back to MP4.
    // Preserve the actual MIME, including codec parameters, and the original bytes.
    if (!blob.type) blob = new Blob([blob], { type: await inferMime(blob) });
    const mime = blob.type.split(';')[0]!.trim().toLowerCase();
    const extension = extensions[mime];
    if (!extension) throw new Error('Unsupported recording MIME');
    stage = 'multipart';
    const body = new FormData();
    body.append('file', blob, `recording.${extension}`);
    if (__DEV__) console.info('[recording upload]', {
      platform: 'web', stage: 'ready', mime, bytes: blob.size, extension,
    });
    return { body, fetch: (input, init) => globalThis.fetch(input, init), release };
  } catch {
    release();
    if (__DEV__) console.info('[recording upload]', { platform: 'web', stage, failed: true });
    // Fetch errors can contain object URLs; only expose this stable upload message.
    throw new Error('Recording could not be prepared for upload. Try sending it again.');
  }
}
