import { useCallback, useEffect, useRef, useState } from 'react';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';

import { api } from '@/api/client';
import { playbackAllowed, registerPlayback, stopAllPlayback } from '@/audio/session';
import { useCachedAudio } from '@/audio/useCachedAudio';
import { retainRecordingUri } from '@/audio/recordingUri';
import { Button, ErrorMessage } from '@/components/Ui';

const downloadAudio = (path: string) => api.downloadAudioFile(path);

export function ProtectedPlaybackButton({
  path, label, disabled = false,
}: { path: string; label: string; disabled?: boolean }) {
  const playback = useCachedAudio(downloadAudio);
  const source = { id: path, url: path };
  return <>
    <Button secondary disabled={disabled} label={playback.isPlaying ? 'Pause' : label}
      onPress={() => playback.toggle(source)} />
    <ErrorMessage message={playback.error} />
  </>;
}

function LocalPlaybackButton({ uri, label, disabled }: { uri: string; label: string; disabled: boolean }) {
  useEffect(() => retainRecordingUri(uri), [uri]);
  const player = useAudioPlayer(uri, { keepAudioSessionActive: true });
  const status = useAudioPlayerStatus(player);
  const operation = useRef(0);
  const [error, setError] = useState<string | null>(null);
  const stop = useCallback(() => { operation.current++; player.pause(); }, [player]);
  useEffect(() => registerPlayback(stop), [stop]);
  const toggle = async () => {
    if (status.playing) { player.pause(); return; }
    if (!playbackAllowed()) return;
    stopAllPlayback();
    const requestedOperation = ++operation.current;
    setError(null);
    try {
      if (status.didJustFinish) await player.seekTo(0);
      if (requestedOperation === operation.current && playbackAllowed()) player.play();
    } catch { setError('Recording audio unavailable. Try again.'); }
  };
  return <>
    <Button secondary disabled={disabled || !status.isLoaded} label={status.playing ? 'Pause' : label}
      onPress={() => void toggle()} />
    <ErrorMessage message={error} />
  </>;
}

export function PlaybackButton({ uri, label = 'Play recording', disabled = false }: { uri: string; label?: string; disabled?: boolean }) {
  return uri.startsWith('file:') || uri.startsWith('blob:')
    ? <LocalPlaybackButton uri={uri} label={label} disabled={disabled} />
    : <ProtectedPlaybackButton path={api.protectedAudioPath(uri)} label={label} disabled={disabled} />;
}
