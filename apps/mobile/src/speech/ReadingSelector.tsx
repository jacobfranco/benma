import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import type { PronunciationTarget } from '@/api/types';
import { Body, Button, ErrorMessage } from '@/components/Ui';
import { WorkspaceDialog } from '@/components/WorkspaceActions';
import { colors } from '@/theme';

// Candidates are lexical dictionary/context results, never surface tone options.
export const readingChoices = (target: PronunciationTarget) => target.pinyin_syllables.map((_, index) =>
  [...new Set(target.pinyin_alternatives?.[index] ?? [])]);

export function ReadingSelector({ target, busy, error, onSave, onClose }: {
  target: PronunciationTarget; busy: boolean; error: string | null; onSave: (reading: string) => void; onClose: () => void;
}) {
  const [selected, setSelected] = useState(target.pinyin_syllables);
  return <WorkspaceDialog title="Edit reading" onClose={onClose}>
    <Body>Choose a lexical reading. Contextual tone changes are handled separately.</Body>
    {readingChoices(target).map((options, index) => options.length > 1 && <View key={index} style={{ gap: 4 }}>
      <Text style={{ color: colors.text, fontSize: 24 }}>{target.text[index]}</Text>
      <View accessibilityRole="radiogroup" style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
        {options.map(option => <Pressable key={option} accessibilityRole="radio" accessibilityLabel={`${target.text[index]}: ${option}`}
          accessibilityState={{ checked: selected[index] === option, disabled: busy }} disabled={busy}
          onPress={() => setSelected(current => current.map((value, i) => i === index ? option : value))}
          style={{ minWidth: 44, minHeight: 44, padding: 12, borderRadius: 8, borderWidth: 1,
            borderColor: selected[index] === option ? colors.text : colors.border, backgroundColor: colors.diagnostic }}>
          <Text style={{ color: colors.text }}>{option}</Text>
        </Pressable>)}
      </View>
    </View>)}
    <ErrorMessage message={error} />
    <Button label="Use this reading" loading={busy} onPress={() => onSave(selected.join(' '))} />
  </WorkspaceDialog>;
}
