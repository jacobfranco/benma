// Nonzero, nonconstant PCM samples expose shifts, padding, and altered amplitudes.
export function canonicalWave(frames = 16000) {
  const bytes = new Uint8Array(44 + frames * 2), view = new DataView(bytes.buffer);
  const tag = (text: string, at: number) => bytes.set(Array.from(text, c => c.charCodeAt(0)), at);
  tag('RIFF', 0); view.setUint32(4, bytes.length - 8, true); tag('WAVEfmt ', 8);
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, 16000, true); view.setUint32(28, 32000, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true); tag('data', 36);
  view.setUint32(40, frames * 2, true);
  for (let i = 0; i < frames; i++) view.setInt16(44 + i * 2, (i % 1000) - 500, true);
  return bytes;
}
