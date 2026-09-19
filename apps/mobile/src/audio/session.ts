// All foreground players yield the shared native session before a microphone starts.
const players = new Set<() => void>();
const resets = new Set<() => void>();

export function registerPlayback(stop: () => void, reset = stop): () => void {
  players.add(stop);
  resets.add(reset);
  return () => { players.delete(stop); resets.delete(reset); };
}

export function stopAllPlayback(): void {
  for (const stop of players) { try { stop(); } catch { /* A disposed player cannot block recording. */ } }
}

export function resetAudioSession(): void {
  for (const reset of resets) { try { reset(); } catch { /* Cleanup cannot block auth or other owners. */ } }
  recordings.clear();
}

export function registerAudioReset(reset: () => void): () => void {
  resets.add(reset);
  return () => { resets.delete(reset); };
}

const recordings = new Set<object>();
export function beginRecording(owner: object): void {
  stopAllPlayback();
  recordings.add(owner);
}
export function endRecording(owner: object): void { recordings.delete(owner); }
export function playbackAllowed(): boolean { return recordings.size === 0; }
