import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { IconAction, WorkspaceDialog } from '@/components/WorkspaceActions';
import type { ContextualToneExplanation } from '@/speech/learnedToneView';
import { colors } from '@/theme';

export function ContextualToneHelp({ explanation, characters }: {
  explanation: ContextualToneExplanation; characters: string;
}) {
  const [open, setOpen] = useState(false);
  return <>
    <IconAction label={`Why this tone here for ${characters}?`} icon="ⓘ" onPress={() => setOpen(true)} />
    {open && <WorkspaceDialog title={explanation.title} onClose={() => setOpen(false)}>
      <View style={styles.content} testID="contextual-tone-help">
        <Text style={styles.text}>Dictionary tone: {explanation.dictionary}</Text>
        <Text style={styles.text}>Spoken here: {explanation.spoken}</Text>
        <Text style={styles.text}>{explanation.explanation}</Text>
        <Text style={styles.text}>Heard: {explanation.heard}</Text>
        <Text style={styles.caption}>The pinyin keeps the dictionary tone mark.</Text>
      </View>
    </WorkspaceDialog>}
  </>;
}

const styles = StyleSheet.create({
  content: { gap: 10 },
  text: { color: colors.text, fontSize: 15, lineHeight: 22 },
  caption: { color: colors.secondary, fontSize: 13, lineHeight: 20 },
});
