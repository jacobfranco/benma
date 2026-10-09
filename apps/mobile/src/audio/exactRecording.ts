// Canonical PCM only. Original uploads can have a different decoder time origin.
// One temporary selected segment is required by Expo Audio's file-based player;
// no polling timer is used to guess when to stop a short syllable.
export function exactRecording(bytes: Uint8Array, start: number, end: number): Uint8Array {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = (at: number) => String.fromCharCode(...bytes.slice(at, at + 4));
  if (bytes.length < 44 || tag(0) !== 'RIFF' || tag(8) !== 'WAVE') throw new Error('Canonical WAV required');
  let rate = 0, block = 0, dataStart = 0, dataSize = 0;
  const limit = view.getUint32(4, true) + 8;
  if (limit > bytes.length) throw new Error('Truncated WAV');
  for (let at = 12; at + 8 <= limit;) {
    const size = view.getUint32(at + 4, true);
    if (at + 8 + size > limit) throw new Error('Truncated WAV chunk');
    if (tag(at) === 'fmt ') {
      if (size < 16 || view.getUint16(at + 8, true) !== 1 || view.getUint16(at + 10, true) !== 1 ||
        view.getUint16(at + 22, true) !== 16) throw new Error('Canonical mono PCM16 required');
      rate = view.getUint32(at + 12, true); block = view.getUint16(at + 20, true);
    }
    if (tag(at) === 'data') { dataStart = at + 8; dataSize = size; }
    at += 8 + size + size % 2;
  }
  if (rate !== 16000 || block !== 2 || !dataStart || dataSize % block || !Number.isFinite(start) ||
    !Number.isFinite(end) || end <= start) throw new Error('Invalid canonical segment');
  const frames = dataSize / block;
  // Nearest PCM sample, bounded by actual audio length; never add padding.
  const first = Math.min(frames, Math.max(0, Math.round(start * rate)));
  const last = Math.min(frames, Math.max(0, Math.round(end * rate)));
  if (last <= first) throw new Error('Empty segment');
  const size = (last - first) * block, result = new Uint8Array(44 + size);
  const out = new DataView(result.buffer);
  const write = (text: string, at: number) => result.set(Array.from(text, c => c.charCodeAt(0)), at);
  write('RIFF', 0); out.setUint32(4, 36 + size, true); write('WAVEfmt ', 8);
  out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 1, true);
  out.setUint32(24, rate, true); out.setUint32(28, rate * block, true);
  out.setUint16(32, block, true); out.setUint16(34, 16, true); write('data', 36); out.setUint32(40, size, true);
  result.set(bytes.subarray(dataStart + first * block, dataStart + last * block), 44);
  return result;
}
