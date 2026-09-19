// Only imported by web adapters. No DOM objects are created during module evaluation.
import { useCallback, useEffect, useRef, useState } from 'react';

export function useBrowserPlayer() {
  const element = useRef<HTMLAudioElement | null>(null);
  const operation = useRef(0);
  const [isPlaying, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsInteraction, setNeedsInteraction] = useState(false);
  const get = useCallback(() => {
    if (!element.current) {
      const audio = new Audio();
      audio.preload = 'auto';
      audio.onplaying = () => setPlaying(true);
      audio.onpause = audio.onended = () => setPlaying(false);
      audio.onerror = () => { setPlaying(false); setError('Audio unavailable. Try playing it again.'); };
      element.current = audio;
    }
    return element.current;
  }, []);
  const stop = useCallback(() => {
    operation.current++;
    element.current?.pause();
    setPlaying(false);
  }, []);
  const detach = useCallback(() => {
    stop();
    if (element.current) {
      element.current.removeAttribute('src');
      element.current.load();
    }
  }, [stop]);
  const play = useCallback(async () => {
    const audio = get();
    const current = ++operation.current;
    setError(null);
    setNeedsInteraction(false);
    try {
      if (audio.ended) audio.currentTime = 0;
      // Invoke within the click stack on replay; observe the browser's actual result.
      await audio.play();
    } catch (caught) {
      if (current !== operation.current) return;
      if (caught instanceof Error && caught.name === 'NotAllowedError') setNeedsInteraction(true);
      else if (!(caught instanceof Error && caught.name === 'AbortError')) setError('Audio unavailable. Try playing it again.');
    }
  }, [get]);
  useEffect(() => () => {
    operation.current++;
    const audio = element.current;
    if (!audio) return;
    audio.onplaying = audio.onpause = audio.onended = audio.onerror = null;
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    element.current = null;
  }, []);
  return { get, stop, detach, play, isPlaying, error, setError, needsInteraction };
}
