import { useCallback, useEffect, useRef, useState } from 'react';

import { cacheFileName, validateAudio, type AudioDownload, type CachedAudioSource } from './audioData';
import { playbackAllowed, registerPlayback, stopAllPlayback } from './session';
import { useBrowserPlayer } from './useBrowserPlayer';
export type { AudioDownload, CachedAudioSource } from './audioData';

// Bound retained media across a long conversation, even when older cards stay mounted.
// Eviction detaches the owning player before revocation; replay of evicted media refetches.
const retained = new Map<object, () => void>();
const MAX_RETAINED_PLAYERS = 12;
function touch(owner: object, dispose: () => void) {
  retained.delete(owner);
  retained.set(owner, dispose);
  while (retained.size > MAX_RETAINED_PLAYERS) retained.values().next().value!();
}

export function useCachedAudio(fetchAudio: (url: string) => Promise<Uint8Array | AudioDownload>) {
  const { get, stop: stopPlayer, detach, play: playPlayer, isPlaying, error, setError, needsInteraction } = useBrowserPlayer();
  const owner = useRef({});
  const operation = useRef(0);
  const active = useRef<{ source: CachedAudioSource; uri: string } | null>(null);
  const pending = useRef(new Map<string, Promise<Uint8Array | AudioDownload>>());
  const [activeId, setActiveId] = useState<string | null>(null);
  const stop = useCallback(() => { operation.current++; stopPlayer(); }, [stopPlayer]);
  const reset = useCallback(() => {
    stop();
    detach();
    if (active.current) URL.revokeObjectURL(active.current.uri);
    active.current = null;
    pending.current.clear();
    retained.delete(owner.current);
    setActiveId(null);
    setError(null);
  }, [detach, setError, stop]);
  useEffect(() => {
    const unregister = registerPlayback(stop, reset);
    return () => { unregister(); reset(); };
  }, [reset, stop]);

  const play = useCallback(async (source: CachedAudioSource) => {
    if (!playbackAllowed()) return;
    stopAllPlayback();
    const current = ++operation.current;
    setError(null);
    try {
      cacheFileName(source);
      if (active.current?.source.url !== source.url) {
        let download = pending.current.get(source.url);
        if (!download) {
          download = fetchAudio(source.url);
          pending.current.set(source.url, download);
        }
        let downloaded: Uint8Array | AudioDownload;
        try { downloaded = await download; }
        finally { if (pending.current.get(source.url) === download) pending.current.delete(source.url); }
        if (current !== operation.current || !playbackAllowed()) return;
        const { bytes, mime } = validateAudio(source, downloaded);
        const blob = !(downloaded instanceof Uint8Array) && downloaded.blob?.type
          ? downloaded.blob : new Blob([new Uint8Array(bytes)], { type: mime });
        const uri = URL.createObjectURL(blob);
        detach();
        if (active.current) URL.revokeObjectURL(active.current.uri);
        active.current = { source, uri };
        get().src = uri;
      }
      setActiveId(source.id);
      touch(owner.current, reset);
      await playPlayer();
    } catch {
      if (current === operation.current) setError('Audio unavailable. Try playing it again.');
    }
  }, [detach, fetchAudio, get, playPlayer, reset, setError]);
  const toggle = useCallback((source: CachedAudioSource) => {
    if (active.current?.source.url === source.url && isPlaying) stop();
    else void play(source);
  }, [isPlaying, play, stop]);
  return { activeId, error, isPlaying, needsInteraction, play, stop, toggle };
}
