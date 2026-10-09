import { useCallback, useEffect, useState } from 'react';

import { retainRecordingUri } from './recordingUri';
import { playbackAllowed, registerPlayback, stopAllPlayback } from './session';
import { useBrowserPlayer } from './useBrowserPlayer';
import { useCachedAudio } from './useCachedAudio';

import { Button, ErrorMessage } from '@/components/Ui';
import { IconAction } from '@/components/WorkspaceActions';
import { api } from '@/api/client';

const downloadAudio = (path: string) => api.downloadAudioFile(path);
export function ProtectedPlaybackButton({ path, label, disabled = false, compact = false }: {
  path: string; label: string; disabled?: boolean; compact?: boolean;
}) {
  const [loading, setLoading] = useState(false);
  const fetchAudio = useCallback(async (path: string) => {
    setLoading(true);
    try { return await downloadAudio(path); } finally { setLoading(false); }
  }, []);
  const playback = useCachedAudio(fetchAudio);
  return <>
    {compact ? <IconAction disabled={disabled} loading={loading} icon={playback.isPlaying ? 'Ⅱ' : '▶'}
      label={playback.isPlaying ? `Pause: ${label}` : label} onPress={() => playback.toggle({ id: path, url: path })} />
      : <Button secondary disabled={disabled} label={playback.isPlaying ? 'Pause' : label}
        onPress={() => playback.toggle({ id: path, url: path })} />}
    <ErrorMessage message={playback.error} />
  </>;
}
function LocalPlaybackButton({ uri, label, disabled, compact }: { uri: string; label: string; disabled: boolean; compact: boolean }) {
  const { get, stop, detach, play, isPlaying, error } = useBrowserPlayer();
  useEffect(() => {
    const release = retainRecordingUri(uri);
    get().src = uri;
    const reset = () => { detach(); release(); };
    const unregister = registerPlayback(stop, reset);
    return () => { unregister(); reset(); };
  }, [detach, get, stop, uri]);
  const toggle = () => {
    if (isPlaying) stop();
    else if (playbackAllowed()) { stopAllPlayback(); void play(); }
  };
  return <>
    {compact ? <IconAction disabled={disabled} icon={isPlaying ? 'Ⅱ' : '▶'}
      label={isPlaying ? `Pause: ${label}` : label} onPress={toggle} />
      : <Button secondary disabled={disabled} label={isPlaying ? 'Pause' : label} onPress={toggle} />}
    <ErrorMessage message={error} />
  </>;
}
export function PlaybackButton({ uri, label = 'Play recording', disabled = false, compact = false }: {
  uri: string; label?: string; disabled?: boolean; compact?: boolean;
}) {
  return uri.startsWith('blob:')
    ? <LocalPlaybackButton uri={uri} label={label} disabled={disabled} compact={compact} />
    : <ProtectedPlaybackButton path={api.protectedAudioPath(uri)} label={label} disabled={disabled} compact={compact} />;
}
