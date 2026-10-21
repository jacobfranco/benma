import { Text } from 'react-native';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { learnedToneEvidence } from '@/speech/learnedToneView';
import { colors } from '@/theme';

// Mounted only inside the existing More details > Technical details affordance.
export function LearnedToneEvidence({ data }: { data: PerceivedSpeechAnalysis['data'] }) {
  const evidence = learnedToneEvidence(data);
  if (!evidence) return null;
  return <Text selectable testID="learned-debug" style={{ color: colors.secondary, fontSize: 12, lineHeight: 18 }}>
    Dev evidence{'\n'}{JSON.stringify(evidence, null, 2)}
  </Text>;
}
