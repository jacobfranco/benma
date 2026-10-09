import { useCallback, useEffect, useRef, useState } from 'react';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';

import { api } from '@/api/client';
import { playbackAllowed, registerPlayback, stopAllPlayback } from '@/audio/session';
import { useCachedAudio } from '@/audio/useCachedAudio';
import { retainRecordingUri } from '@/audio/recordingUri';
import { IconAction } from '@/components/WorkspaceActions';
import { Button, ErrorMessage } from '@/components/Ui';

const downloadAudio = (path: string) => api.downloadAudioFile(path);

export function ProtectedPlaybackButton({
  path, label, disabled = false, compact = false,
}: { path: string; label: string; disabled?: boolean; compact?: boolean }) {
  const [loading, setLoading] = useState(false);
  const fetchAudio = useCallback(async (path: string) => {
    setLoading(true);
    try { return await downloadAudio(path); } finally { setLoading(false); }
  }, []);
  const playback = useCachedAudio(fetchAudio);
  const source = { id: path, url: path };
  return <>
    {compact ? <IconAction disabled={disabled} loading={loading} icon={playback.isPlaying ? 'Ⅱ' : '▶'}
      label={playback.isPlaying ? `Pause: ${label}` : label} onPress={() => playback.toggle(source)} />
      : <Button secondary disabled={disabled} label={playback.isPlaying ? 'Pause' : label}
        onPress={() => playback.toggle(source)} />}
    <ErrorMessage message={playback.error} />
  </>;
}

function LocalPlaybackButton({ uri, label, disabled, compact }: { uri: string; label: string; disabled: boolean; compact: boolean }) {
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
    {compact ? <IconAction disabled={disabled || !status.isLoaded} icon={status.playing ? 'Ⅱ' : '▶'}
      label={status.playing ? `Pause: ${label}` : label} onPress={() => void toggle()} />
      : <Button secondary disabled={disabled || !status.isLoaded} label={status.playing ? 'Pause' : label}
        onPress={() => void toggle()} />}
    <ErrorMessage message={error} />
  </>;
}

export function PlaybackButton({ uri, label = 'Play recording', disabled = false, compact = false }: { uri: string; label?: string; disabled?: boolean; compact?: boolean }) {
  return uri.startsWith('file:') || uri.startsWith('blob:')
    ? <LocalPlaybackButton uri={uri} label={label} disabled={disabled} compact={compact} />
    : <ProtectedPlaybackButton path={api.protectedAudioPath(uri)} label={label} disabled={disabled} compact={compact} />;
}
