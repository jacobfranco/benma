import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, TextInput, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { Body, Button, Card, ErrorMessage, Heading, Screen } from '@/components/Ui';
import { colors } from '@/theme';

export default function HomeScreen() {
  const { state, signIn, signOut } = useAuth();
  const [phone, setPhone] = useState('+1');

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
            placeholder="+1 202 555 0123"
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
      <Heading>Practice what was actually said.</Heading>
      <Body>
        Benma keeps provider perception, pronunciation evidence, and your later correction separate.
      </Body>
      <Card>
        <Heading>What did I say?</Heading>
        <Body>Record arbitrary Mandarin. No intended sentence or context is sent to perception.</Body>
        <Button label="Open perception" onPress={() => router.push('/perception')} />
      </Card>
      <Card>
        <Heading>Pronunciation</Heading>
        <Body>Enter a known target, record attempts, and inspect only supported evaluator evidence.</Body>
        <Button label="Open pronunciation" onPress={() => router.push('/pronunciation')} />
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
