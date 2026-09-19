export interface CachedAudioSource {
  id: string;
  url: string;
  turnStartedAt?: number;
}

export interface AudioDownload {
  bytes: Uint8Array;
  contentType: string | null;
  blob?: Blob;
}

export function cacheFileName(source: CachedAudioSource): string {
  // Only protected audio resource paths are accepted. The resource kind is part of
  // the identity, so reference/assistant IDs cannot collide. No URLs or auth metadata.
  const match = /^\/v1\/(assistant-speeches|reference-speech|utterances)\/([A-Za-z0-9_-]{1,128})\/audio$/.exec(source.url);
  if (!match) throw new Error('Invalid protected audio source');
  return `${match[1]}-${match[2]}`;
}

function isWave(bytes: Uint8Array): boolean {
  const header = (
    bytes.byteLength > 44 &&
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x41 &&
    bytes[10] === 0x56 &&
    bytes[11] === 0x45
  );
  if (!header) return false;
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const end = view.getUint32(4, true) + 8;
  if (end > bytes.length || end < 44) return false;
  let format = false, data = false;
  for (let offset = 12; offset + 8 <= end;) {
    const size = view.getUint32(offset + 4, true);
    if (offset + 8 + size > end) return false;
    const kind = String.fromCharCode(...bytes.slice(offset, offset + 4));
    if (kind === 'fmt ') format = size >= 16;
    if (kind === 'data') data = size > 0;
    offset += 8 + size + size % 2;
  }
  return format && data;
}

export function audioExtension(bytes: Uint8Array): 'wav' | 'm4a' | 'webm' | null {
  if (isWave(bytes)) return 'wav';
  if (bytes.length > 12 && String.fromCharCode(...bytes.slice(4, 8)) === 'ftyp') return 'm4a';
  if (bytes.length > 12 && bytes[0] === 0x1a && bytes[1] === 0x45 && bytes[2] === 0xdf && bytes[3] === 0xa3) return 'webm';
  return null;
}


export function validateAudio(source: CachedAudioSource, downloaded: Uint8Array | AudioDownload) {
  cacheFileName(source);
  const bytes = downloaded instanceof Uint8Array ? downloaded : downloaded.bytes;
  const contentType = downloaded instanceof Uint8Array ? null : downloaded.contentType?.split(';')[0]?.trim().toLowerCase();
  const extension = audioExtension(bytes);
  const declared = contentType && ({ 'audio/wav': 'wav', 'audio/x-wav': 'wav', 'audio/wave': 'wav',
    'audio/mp4': 'm4a', 'audio/m4a': 'm4a', 'audio/x-m4a': 'm4a', 'audio/webm': 'webm' } as Record<string, string>)[contentType];
  if (declared && declared !== extension) throw new Error('Audio format disagrees with content type');
  if (!extension || (!source.url.startsWith('/v1/utterances/') && extension !== 'wav')) {
    throw new Error('Downloaded audio format is invalid');
  }
  return { bytes, extension, mime: { wav: 'audio/wav', m4a: 'audio/mp4', webm: 'audio/webm' }[extension] };
}
