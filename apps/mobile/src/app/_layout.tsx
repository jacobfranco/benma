import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, AppState, Platform } from 'react-native';

import { AuthProvider, useAuth } from '@/auth/AuthProvider';
import { colors } from '@/theme';
import { stopAllPlayback } from '@/audio/session';

export default function RootLayout() {
  return <AuthProvider><AuthenticatedStack /></AuthProvider>;
}

function AuthenticatedStack() {
  const { state } = useAuth();
  useEffect(() => {
    const subscription = AppState.addEventListener('change', next => { if (next !== 'active') stopAllPlayback(); });
    const hidden = () => { if (document.hidden) stopAllPlayback(); };
    if (Platform.OS === 'web') document.addEventListener('visibilitychange', hidden);
    return () => {
      subscription.remove();
      if (Platform.OS === 'web') document.removeEventListener('visibilitychange', hidden);
      stopAllPlayback();
    };
  }, []);
  if (state.phase === 'loading') return <ActivityIndicator accessibilityLabel="Restoring session" />;
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenListeners={{ blur: () => stopAllPlayback() }}
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
