import { Text } from 'react-native';

import { Button, ErrorMessage } from '@/components/Ui';
import type { useSpeechTurn } from '@/speech/useSpeechTurn';
import { speechStageLabels } from '@/speech/workflow';

export function SpeechControls({ turn, disabled = false }: {
  turn: ReturnType<typeof useSpeechTurn>; disabled?: boolean;
}) {
  return <>
    {turn.phase === 'recording' ? <>
      <Text>{(turn.durationMillis / 1000).toFixed(1)}s</Text>
      <Button label="Stop recording" onPress={() => void turn.stop()} />
    </> : turn.phase === 'processing' && turn.stage ?
      <Button disabled loading label={speechStageLabels[turn.stage]} onPress={() => {}} /> :
      <Button disabled={disabled} label={turn.permissionDenied ? 'Try microphone again' : 'Tap to speak'}
        onPress={() => void turn.start()} />}
    {turn.retryable && <Button secondary label="Retry" onPress={() => void turn.retry()} />}
    <ErrorMessage message={turn.error} />
  </>;
}
