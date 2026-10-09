import { useCallback, useEffect, useRef, useState } from 'react';

import { api } from '@/api/client';
import { exactRecording } from '@/audio/exactRecording';
import { registerAudioReset } from '@/audio/session';
import { useCachedAudio } from '@/audio/useCachedAudio';
import { IconAction } from '@/components/WorkspaceActions';
import { ErrorMessage } from '@/components/Ui';

export function useCanonicalRecording(utteranceId: string) {
  const cached = useRef<Promise<Uint8Array> | null>(null);
  useEffect(() => {
    cached.current = null;
    const clear = () => { cached.current = null; };
    const unregister = registerAudioReset(clear);
    return () => { unregister(); clear(); };
  }, [utteranceId]);
  return useCallback(() => {
    if (!cached.current) {
      const pending = api.downloadCanonicalRecording(utteranceId).catch(error => {
        if (cached.current === pending) cached.current = null;
        throw error;
      });
      cached.current = pending;
    }
    return cached.current;
  }, [utteranceId]);
}

export function ExactPlaybackButton({ utteranceId, text, start, end, fetchRecording }: {
  utteranceId: string; text: string; start: number; end: number; fetchRecording: () => Promise<Uint8Array>;
}) {
  const [loading, setLoading] = useState(false);
  const fetchSegment = useCallback(async () => {
    setLoading(true);
    try { return { bytes: exactRecording(await fetchRecording(), start, end), contentType: 'audio/wav' }; }
    finally { setLoading(false); }
  }, [fetchRecording, start, end]);
  const playback = useCachedAudio(fetchSegment);
  return <>
    <IconAction loading={loading} icon={playback.isPlaying ? 'Ⅱ' : '▶'} label={playback.isPlaying ? `Pause my recording for ${text}` : `Play my recording for ${text}`}
      onPress={() => playback.toggle({ id: `${utteranceId}:${start}:${end}`, url: `/v1/utterances/${utteranceId}/audio` })} />
    <ErrorMessage message={playback.error} />
  </>;
}
