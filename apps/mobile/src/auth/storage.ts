import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const SESSION_KEY = 'benma.auth.session-token';

export interface TokenStorage {
  get(): Promise<string | null>;
  set(value: string): Promise<void>;
  clear(): Promise<void>;
}

export const tokenStorage: TokenStorage = {
  async get() {
    if (Platform.OS === 'web') return globalThis.localStorage?.getItem(SESSION_KEY) ?? null;
    return SecureStore.getItemAsync(SESSION_KEY);
  },
  async set(value) {
    if (Platform.OS === 'web') globalThis.localStorage?.setItem(SESSION_KEY, value);
    else await SecureStore.setItemAsync(SESSION_KEY, value);
  },
  async clear() {
    if (Platform.OS === 'web') globalThis.localStorage?.removeItem(SESSION_KEY);
    else await SecureStore.deleteItemAsync(SESSION_KEY);
  },
};
