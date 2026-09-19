import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, TextInput, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { DEVELOPMENT_PHONE_NUMBER } from '@/auth/development';
import { Body, Button, Card, ErrorMessage, Heading, Screen } from '@/components/Ui';
import { colors } from '@/theme';

export default function HomeScreen() {
  const { state, signIn, signOut } = useAuth();
  const [phone, setPhone] = useState(DEVELOPMENT_PHONE_NUMBER);

  if (state.phase === 'loading') {
    return (
      <Screen>
        <ActivityIndicator color={colors.primary} />
      </Screen>
    );
  }

  if (state.phase !== 'signed_in') {
    return (
      <Screen>
        <Heading>Benma</Heading>
        <Body>Development access for the truth-preserving Mandarin speech foundation.</Body>
        <Card>
          <Body>Phone number (international format)</Body>
          <TextInput
            accessibilityLabel="Phone number"
            autoComplete="tel"
            keyboardType="phone-pad"
            onChangeText={setPhone}
            placeholder={DEVELOPMENT_PHONE_NUMBER}
            style={styles.input}
            value={phone}
          />
          <ErrorMessage message={state.error} />
          <Button
            label="Continue with development account"
            loading={state.phase === 'signing_in'}
            onPress={() => void signIn(phone)}
          />
        </Card>
      </Screen>
    );
  }

  return (
    <Screen>
      <Heading>Speak Mandarin with Benma.</Heading>
      <Body>Talk freely or take time to practice a phrase.</Body>
      <Card>
        <Heading>Conversation</Heading>
        <Body>Speak, see what Benma heard, and hear a reply.</Body>
        <Button label="Open Conversation" onPress={() => router.push('/conversation')} />
      </Card>
      <Card>
        <Heading>Practice</Heading>
        <Body>See your tone contour, or practice a target phrase.</Body>
        <Button label="Open Practice" onPress={() => router.push('/practice')} />
      </Card>
      <View style={styles.secondaryActions}>
        {__DEV__ && (
          <Button
            secondary
            label="Calibration capture (development)"
            onPress={() => router.push('/calibration')}
          />
        )}
        <Button secondary label="History / Development" onPress={() => router.push('/history')} />
        <Button secondary label="Sign out" onPress={() => void signOut()} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  input: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    minHeight: 50,
    fontSize: 18,
    color: colors.text,
    backgroundColor: '#fff',
  },
  secondaryActions: { gap: 10 },
});
