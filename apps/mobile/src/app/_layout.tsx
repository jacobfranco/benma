import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator } from 'react-native';

import { AuthProvider, useAuth } from '@/auth/AuthProvider';
import { colors } from '@/theme';

export default function RootLayout() {
  return <AuthProvider><AuthenticatedStack /></AuthProvider>;
}

function AuthenticatedStack() {
  const { state } = useAuth();
  if (state.phase === 'loading') return <ActivityIndicator accessibilityLabel="Restoring session" />;
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.background },
          headerShadowVisible: false,
          headerTintColor: colors.primary,
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Benma' }} />
        <Stack.Protected guard={state.phase === 'signed_in'}>
        <Stack.Screen name="conversation" options={{ title: 'Conversation' }} />
        <Stack.Screen name="practice" options={{ title: 'Practice' }} />
        <Stack.Screen name="free-talk" options={{ title: 'Conversation' }} />
        <Stack.Screen name="perception" options={{ title: 'What did I say?' }} />
        <Stack.Screen name="pronunciation" options={{ title: 'Pronunciation' }} />
        <Stack.Screen name="history" options={{ title: 'History / Development' }} />
        <Stack.Screen name="calibration" options={{ title: 'Calibration Capture' }} />
        </Stack.Protected>
      </Stack>
    </>
  );
}
