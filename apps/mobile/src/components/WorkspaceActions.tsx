import type { PropsWithChildren } from 'react';
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { colors } from '@/theme';

export function IconAction({ label, icon, onPress, disabled = false, loading = false }: {
  label: string; icon: string; onPress: () => void; disabled?: boolean; loading?: boolean;
}) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label}
    accessibilityState={{ disabled: disabled || loading, busy: loading }}
    disabled={disabled || loading} onPress={onPress}
    style={({ pressed }) => [styles.icon, (disabled || loading) && styles.disabled, pressed && styles.pressed]}>
    {loading ? <ActivityIndicator size="small" color={colors.secondary} />
      : <Text accessible={false} style={styles.glyph}>{icon}</Text>}
  </Pressable>;
}

// Native back and web Escape/focus containment are handled by the shared Modal.
// Mount only while open so hidden graphs, controls and playback do not persist.
export function WorkspaceDialog({ title, onClose, children }: PropsWithChildren<{ title: string; onClose: () => void }>) {
  return <Modal accessibilityLabel={title} transparent animationType="fade" onRequestClose={onClose} visible>
    <View style={styles.backdrop}>
      <View accessibilityViewIsModal style={styles.dialog}>
        <View style={styles.header}>
          <Text accessibilityRole="header" style={styles.title}>{title}</Text>
          <IconAction label={`Close ${title}`} icon="×" onPress={onClose} />
        </View>
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>{children}</ScrollView>
      </View>
    </View>
  </Modal>;
}
const styles = StyleSheet.create({
  icon: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 10 },
  glyph: { fontSize: 22, color: colors.primary },
  disabled: { opacity: .45 }, pressed: { backgroundColor: colors.diagnostic },
  backdrop: { flex: 1, justifyContent: 'center', padding: 16, backgroundColor: 'rgba(0,0,0,0.35)' },
  dialog: { width: '100%', maxWidth: 760, maxHeight: '90%', alignSelf: 'center', backgroundColor: colors.surface, borderRadius: 16 },
  header: { flexDirection: 'row', alignItems: 'center', paddingLeft: 16, paddingRight: 8, paddingVertical: 6 },
  title: { flex: 1, color: colors.text, fontSize: 18, fontWeight: '600' },
  content: { padding: 16, paddingTop: 4, gap: 12 },
});
