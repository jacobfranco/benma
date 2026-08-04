import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { AuthProvider } from '@/auth/AuthProvider';
import { colors } from '@/theme';

export default function RootLayout() {
  return (
    <AuthProvider>
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
        <Stack.Screen name="perception" options={{ title: 'What did I say?' }} />
        <Stack.Screen name="pronunciation" options={{ title: 'Pronunciation' }} />
        <Stack.Screen name="history" options={{ title: 'History / Development' }} />
        <Stack.Screen name="calibration" options={{ title: 'Calibration Capture' }} />
      </Stack>
    </AuthProvider>
  );
}
