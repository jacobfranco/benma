import { useCallback, useEffect, useRef, useState } from 'react';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { Directory, File, Paths } from 'expo-file-system';

import { audioExtension, cacheFileName, validateAudio, type AudioDownload, type CachedAudioSource } from './audioData';

import { playbackAllowed, registerPlayback, stopAllPlayback } from '@/audio/session';
export type { AudioDownload, CachedAudioSource } from './audioData';

const PLAYBACK_ERROR = 'Benma’s audio could not be played. You can try again.';
const CACHE_DIRECTORY = 'protected-audio';
let nextCacheSlot = 0;
let initializedCache = false;

interface PendingPlayback {
  id: string;
  loadStartedAt: number;
  turnStartedAt?: number;
}

interface CachedSpeech {
  file: File;
  slot: number;
}

function speechCacheDirectory(slot: number): Directory {
  const root = new Directory(Paths.cache, CACHE_DIRECTORY);
  if (!root.exists) root.create({ idempotent: true, intermediates: true });
  if (!initializedCache) {
    // No previous process can still own a player. Remove obsolete private audio.
    for (const entry of root.list()) { try { entry.delete(); } catch { /* best effort */ } }
    const legacy = new Directory(Paths.cache, 'assistant-speech');
    try { if (legacy.exists) legacy.delete(); } catch { /* best effort migration cleanup */ }
    initializedCache = true;
  }
  const directory = new Directory(root, String(slot));
  if (!directory.exists) directory.create({ idempotent: true, intermediates: true });
  return directory;
}

async function validCachedFile(file: File, expected?: Uint8Array): Promise<boolean> {
  if (!file.exists || !file.size || file.size <= 12) return false;
  try {
    const bytes = await file.bytes();
    const extension = audioExtension(bytes);
    return extension !== null && file.uri.endsWith(`.${extension}`) && file.size === bytes.length &&
      (!expected || (bytes.length === expected.length && bytes.every((value, index) => value === expected[index])));
  } catch {
    return false;
  }
}

function removeOtherCachedSpeech(directory: Directory, keepUri: string): void {
  for (const entry of directory.list()) {
    if (entry.uri === keepUri) continue;
    try {
      entry.delete();
    } catch {
      // Cache cleanup must never make otherwise valid playback fail.
    }
  }
}

export function useCachedAudio(fetchAudio: (url: string) => Promise<Uint8Array | AudioDownload>) {
  // Keeping the shared iOS session active prevents Expo Audio's delayed pause cleanup from
  // deactivating a recorder or a newly loading player 100 ms later.
  const cacheSlot = useRef<number | null>(null);
  if (cacheSlot.current === null) cacheSlot.current = ++nextCacheSlot;
  const player = useAudioPlayer(null, { keepAudioSessionActive: true });
  const status = useAudioPlayerStatus(player);
  const activeId = useRef<string | null>(null);
  const activeUrl = useRef<string | null>(null);
  const pendingPlayback = useRef<PendingPlayback | null>(null);
  const inFlightCache = useRef(new Map<string, Promise<CachedSpeech>>());
  const loadTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const awaitingPlaying = useRef<PendingPlayback | null>(null);
  const clearLoadTimeout = useCallback(() => {
    if (loadTimeout.current) clearTimeout(loadTimeout.current);
    loadTimeout.current = null;
  }, []);
  const operation = useRef(0);
  const latestRequestedId = useRef<string | null>(null);
  const lastNativeError = useRef<string | null>(null);
  const [visibleId, setVisibleId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reportError = useCallback((caught: unknown, operation: string) => {
    clearLoadTimeout();
    pendingPlayback.current = null;
    awaitingPlaying.current = null;
    activeId.current = null; // A retry must replace the failed native source.
    // Do not print free-form exceptions: they may include protected URLs or tokens.
    // Extract only recognized native error classes and numeric OSStatus codes.
    const message = caught instanceof Error ? caught.message : '';
    const domain = /\b(AVFoundationErrorDomain|NSOSStatusErrorDomain|NSCocoaErrorDomain)\b/.exec(message)?.[1];
    const code = /\b(?:Code|OSStatus)\s*[=:]\s*(-?\d{1,10})\b/.exec(message)?.[1];
    const category = /null|convert|cast|record/i.test(message) ? 'source-contract'
      : /format|decode|corrupt/i.test(message) ? 'format' : 'unclassified';
    if (__DEV__) console.error('[audio playback] failed', { operation, category,
      ...(domain ? { domain } : {}), ...(code ? { code: Number(code) } : {}) });
    setError(PLAYBACK_ERROR);
  }, [clearLoadTimeout]);

  const cache = useCallback(
    async (source: CachedAudioSource): Promise<CachedSpeech> => {
      const existing = inFlightCache.current.get(source.url);
      if (existing) return existing;

      const promise = (async () => {
        const slot = cacheSlot.current!;
        const directory = speechCacheDirectory(slot);
        const name = cacheFileName(source);
        for (const extension of ['wav', 'm4a', 'webm']) {
          const file = new File(directory, `${name}.${extension}`);
          if (await validCachedFile(file)) return { file, slot };
          if (file.exists) file.delete();
        }

        const startedAt = Date.now();
        const downloaded = await fetchAudio(source.url);
        const { bytes, extension } = validateAudio(source, downloaded);
        const file = new File(directory, `${name}.${extension}`);
        file.write(bytes);
        if (!(await validCachedFile(file, bytes))) {
          if (file.exists) file.delete();
          throw new Error('Assistant speech could not be saved to the cache');
        }
        if (__DEV__) {
          console.info('[audio playback] cache verified', { extension, size: file.size, container: extension });
          console.info('[audio playback] audio download/cache ms:', Date.now() - startedAt);
        }
        return { file, slot };
      })();
      inFlightCache.current.set(source.url, promise);
      try {
        return await promise;
      } finally {
        if (inFlightCache.current.get(source.url) === promise) inFlightCache.current.delete(source.url);
      }
    },
    [fetchAudio],
  );

  useEffect(() => {
    if (!status.error) {
      lastNativeError.current = null;
      return;
    }
    pendingPlayback.current = null;
    if (lastNativeError.current === status.error) return;
    lastNativeError.current = status.error;
    reportError(new Error(status.error), 'native-status');
  }, [reportError, status.error]);

  useEffect(() => {
    // Subscribe directly: React can batch away the transient unloaded status on
    // a fast local replacement. Native readiness is the gate, not a render cycle.
    const subscription = player.addListener('playbackStatusUpdate', (loaded) => {
      if (loaded.error) {
        if (lastNativeError.current === loaded.error) return;
        lastNativeError.current = loaded.error;
        reportError(new Error(loaded.error), 'native-load');
        return;
      }
      const playing = awaitingPlaying.current;
      if (loaded.playing && playing) {
        awaitingPlaying.current = null;
        if (__DEV__ && playing.turnStartedAt !== undefined) {
          console.info('[speech timing] total to native playing ms:', Date.now() - playing.turnStartedAt);
        }
      }
      const pending = pendingPlayback.current;
      if (!playbackAllowed() || !pending || !loaded.isLoaded || !player.isLoaded || pending.id !== activeId.current) return;
      pendingPlayback.current = null;
      clearLoadTimeout();
      try {
        awaitingPlaying.current = pending;
        player.play();
        if (__DEV__) {
          console.info('[audio playback] native loaded:', true);
          console.info('[audio playback] local load-to-play request ms:', Date.now() - pending.loadStartedAt);
        }
      } catch (caught) { reportError(caught, 'play'); }
    });
    return () => subscription.remove();
  }, [clearLoadTimeout, player, reportError]);

  const play = useCallback(
    async (source: CachedAudioSource) => {
      if (!playbackAllowed()) return;
      setError(null);
      if (activeId.current === source.id && activeUrl.current === source.url && !status.error) {
        if (pendingPlayback.current || !player.isLoaded) return;
        stopAllPlayback();
        const replayOperation = ++operation.current;
        try {
          if (status.didJustFinish) await player.seekTo(0);
          if (replayOperation === operation.current) player.play();
        } catch (caught) {
          reportError(caught, 'replay');
        }
        return;
      }

      stopAllPlayback();
      const requestedOperation = ++operation.current;
      latestRequestedId.current = source.url;
      pendingPlayback.current = null;
      activeId.current = null;
      setVisibleId(null);
      player.pause();

      let step = 'download/cache';
      try {
        const cached = await cache(source);
        if (requestedOperation !== operation.current) {
          if ((latestRequestedId.current !== source.url || cached.slot !== cacheSlot.current) && cached.file.exists) cached.file.delete();
          return;
        }

        // Expo 57 iOS replace requires a non-null AudioSource record, despite
        // the JS AudioSource union accepting null. Replace the local source once.
        step = 'replace-local-source';
        lastNativeError.current = null;
        activeId.current = source.id;
        activeUrl.current = source.url;
        pendingPlayback.current = {
          id: source.id,
          loadStartedAt: Date.now(),
          ...(source.turnStartedAt !== undefined ? { turnStartedAt: source.turnStartedAt } : {}),
        };
        clearLoadTimeout();
        loadTimeout.current = setTimeout(() => {
          if (requestedOperation === operation.current && pendingPlayback.current) {
            reportError(new Error('Local load timed out'), 'load-timeout');
          }
        }, 15000);
        player.replace(cached.file.uri);
        removeOtherCachedSpeech(speechCacheDirectory(cacheSlot.current!), cached.file.uri);
        setVisibleId(source.id);
      } catch (caught) {
        if (requestedOperation === operation.current) reportError(caught, step);
      }
    },
    [cache, clearLoadTimeout, player, reportError, status.didJustFinish, status.error],
  );

  const toggle = useCallback(
    (source: CachedAudioSource) => {
      if (activeId.current === source.id && activeUrl.current === source.url && status.playing) {
        player.pause();
        return;
      }
      void play(source);
    },
    [play, player, status.playing],
  );

  const stop = useCallback(() => {
    operation.current += 1;
    latestRequestedId.current = null;
    pendingPlayback.current = null;
    awaitingPlaying.current = null;
    clearLoadTimeout();
    player.pause();
  }, [clearLoadTimeout, player]);

  useEffect(() => {
    const reset = () => {
      stop();
      activeId.current = null;
      activeUrl.current = null;
      setVisibleId(null);
      player.replace({}); // Valid native record with no URI detaches the current item.
      const directory = speechCacheDirectory(cacheSlot.current!);
      removeOtherCachedSpeech(directory, '');
      cacheSlot.current = ++nextCacheSlot;
      inFlightCache.current.clear();
    };
    const unregister = registerPlayback(stop, reset);
    return () => {
      unregister();
      operation.current += 1;
      latestRequestedId.current = null;
      pendingPlayback.current = null;
      clearLoadTimeout();
      awaitingPlaying.current = null;
      // useAudioPlayer disposes the native object on unmount; do not touch it here.
      removeOtherCachedSpeech(speechCacheDirectory(cacheSlot.current!), '');
    };
  }, [clearLoadTimeout, player, stop]);

  return {
    activeId: visibleId,
    error,
    isPlaying: status.playing,
    play,
    stop,
    toggle,
  };
}
