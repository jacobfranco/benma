import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';

import { Button } from '@/components/Ui';

export function PlaybackButton({
  uri,
  label = 'Play recording',
  headers,
}: {
  uri: string;
  label?: string;
  headers?: Record<string, string> | undefined;
}) {
  const player = useAudioPlayer(headers ? { uri, headers } : uri);
  const status = useAudioPlayerStatus(player);

  const toggle = () => {
    if (status.playing) player.pause();
    else if (status.didJustFinish) void player.seekTo(0).then(() => player.play());
    else player.play();
  };

  return <Button secondary label={status.playing ? 'Pause' : label} onPress={toggle} />;
}
