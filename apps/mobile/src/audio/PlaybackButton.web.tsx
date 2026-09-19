import { useEffect } from 'react';

import { retainRecordingUri } from './recordingUri';
import { playbackAllowed, registerPlayback, stopAllPlayback } from './session';
import { useBrowserPlayer } from './useBrowserPlayer';
import { useCachedAudio } from './useCachedAudio';

import { Button, ErrorMessage } from '@/components/Ui';
import { api } from '@/api/client';

const downloadAudio = (path: string) => api.downloadAudioFile(path);
export function ProtectedPlaybackButton({ path, label, disabled = false }: { path: string; label: string; disabled?: boolean }) {
  const playback = useCachedAudio(downloadAudio);
  return <>
    <Button secondary disabled={disabled} label={playback.isPlaying ? 'Pause' : label}
      onPress={() => playback.toggle({ id: path, url: path })} />
    <ErrorMessage message={playback.error} />
  </>;
}
function LocalPlaybackButton({ uri, label, disabled }: { uri: string; label: string; disabled: boolean }) {
  const { get, stop, detach, play, isPlaying, error } = useBrowserPlayer();
  useEffect(() => {
    const release = retainRecordingUri(uri);
    get().src = uri;
    const reset = () => { detach(); release(); };
    const unregister = registerPlayback(stop, reset);
    return () => { unregister(); reset(); };
  }, [detach, get, stop, uri]);
  return <>
    <Button secondary disabled={disabled} label={isPlaying ? 'Pause' : label} onPress={() => {
      if (isPlaying) stop();
      else if (playbackAllowed()) { stopAllPlayback(); void play(); }
    }} />
    <ErrorMessage message={error} />
  </>;
}
export function PlaybackButton({ uri, label = 'Play recording', disabled = false }: { uri: string; label?: string; disabled?: boolean }) {
  return uri.startsWith('blob:')
    ? <LocalPlaybackButton uri={uri} label={label} disabled={disabled} />
    : <ProtectedPlaybackButton path={api.protectedAudioPath(uri)} label={label} disabled={disabled} />;
}
