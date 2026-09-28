import type { PropsWithChildren, ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '@/theme';

export function Screen({ children }: PropsWithChildren): ReactNode {
  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

export function Card({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Heading({ children }: PropsWithChildren) {
  return <Text style={styles.heading}>{children}</Text>;
}

export function Chinese({ children }: PropsWithChildren) {
  return <Text selectable style={styles.chinese}>{children}</Text>;
}

export function Pinyin({ children }: PropsWithChildren) {
  return <Text selectable style={styles.pinyin}>{children}</Text>;
}

export function Body({ children }: PropsWithChildren) {
  return <Text selectable style={styles.body}>{children}</Text>;
}

export function ErrorMessage({ message }: { message: string | null }) {
  return message ? <Text style={styles.error}>{message}</Text> : null;
}

export function FixtureBanner({ message = 'Development fixture — not real speech evaluation.' }: { message?: string }) {
  return (
    <View style={styles.fixture} accessibilityRole="alert">
      <Text style={styles.fixtureText}>{message}</Text>
    </View>
  );
}

export function Button({
  label,
  onPress,
  disabled = false,
  loading = false,
  secondary = false,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  secondary?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondaryButton,
        pressed && styles.pressed,
        (disabled || loading) && styles.disabled,
      ]}
    >
      {loading && <ActivityIndicator color={secondary ? colors.primary : '#fff'} />}
      <Text style={[styles.buttonText, secondary && styles.secondaryButtonText]}>{label}</Text>
    </Pressable>
  );
}

export function EvidencePanel({
  title = 'Advanced evidence',
  children,
}: PropsWithChildren<{ title?: string }>) {
  return (
    <Card style={styles.evidence}>
      <Text style={styles.evidenceTitle}>{title}</Text>
      {children}
    </Card>
  );
}

export function EvidenceRow({ label, value }: { label: string; value: unknown }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <View style={styles.evidenceRow}>
      <Text style={styles.evidenceLabel}>{label}</Text>
      <Text selectable style={styles.evidenceValue}>
        {typeof value === 'string' ? value : JSON.stringify(value)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  screen: { padding: 20, paddingBottom: 48, gap: 16,
    ...(Platform.OS === 'web' ? { width: '100%', maxWidth: 900, alignSelf: 'center' } as const : {}) },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 14,
    padding: 18,
    gap: 12,
  },
  heading: { color: colors.text, fontSize: 30, fontWeight: '700', letterSpacing: -0.5 },
  chinese: { color: colors.text, fontSize: 34, lineHeight: 45, fontWeight: '600' },
  pinyin: { color: colors.secondary, fontSize: 20, lineHeight: 28 },
  body: { color: colors.secondary, fontSize: 16, lineHeight: 24 },
  error: { color: colors.danger, fontSize: 15, lineHeight: 21 },
  button: {
    flexDirection: 'row',
    gap: 10,
    minHeight: 52,
    borderRadius: 12,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
  },
  secondaryButton: { backgroundColor: 'transparent', borderColor: colors.primary, borderWidth: 1 },
  pressed: { backgroundColor: colors.primaryPressed },
  disabled: { opacity: 0.45 },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  secondaryButtonText: { color: colors.primary },
  fixture: { borderRadius: 10, padding: 12, backgroundColor: colors.warningBackground },
  fixtureText: { color: colors.warningText, fontWeight: '700', lineHeight: 20 },
  evidence: { backgroundColor: colors.diagnostic },
  evidenceTitle: { color: colors.text, fontWeight: '700', fontSize: 16 },
  evidenceRow: { gap: 2 },
  evidenceLabel: { color: colors.secondary, fontSize: 12, textTransform: 'uppercase' },
  evidenceValue: { color: colors.text, fontSize: 13, fontFamily: 'monospace' },
});
