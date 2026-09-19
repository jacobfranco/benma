import * as SecureStore from 'expo-secure-store';
import React from 'react';
import { Platform, TextInput } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { api } from '@/api/client';
import HomeScreen from '@/app/index';
import { AuthProvider } from '@/auth/AuthProvider';
import { DEVELOPMENT_PHONE_NUMBER } from '@/auth/development';

jest.mock('expo-router', () => ({ router: { push: jest.fn() } }));
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const webStorage = { getItem: jest.fn(), setItem: jest.fn(), removeItem: jest.fn() };
const originalLocalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');

beforeAll(() => {
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: webStorage });
});

afterAll(() => {
  if (originalLocalStorage) Object.defineProperty(globalThis, 'localStorage', originalLocalStorage);
  else Reflect.deleteProperty(globalThis, 'localStorage');
});

describe.each(['web', 'ios', 'android'] as const)('%s development sign-in', (platform) => {
  let renderer: ReactTestRenderer | undefined;
  let fetchMock: jest.SpiedFunction<typeof fetch>;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.replaceProperty(Platform, 'OS', platform);
    webStorage.getItem.mockReturnValue(null);
    jest.mocked(SecureStore.getItemAsync).mockResolvedValue(null);
    jest.mocked(SecureStore.setItemAsync).mockResolvedValue();
    api.setToken(null);
    fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers(),
      json: async () => ({ token: 'development-session', account_id: 'development-account' }),
    } as Response);
  });

  afterEach(async () => {
    await act(async () => renderer?.unmount());
    renderer = undefined;
    api.setToken(null);
    jest.restoreAllMocks();
  });

  async function mount() {
    await act(async () => {
      renderer = create(React.createElement(AuthProvider, null, React.createElement(HomeScreen)));
    });
    return renderer!;
  }

  async function continueWithDevelopment(screen: ReactTestRenderer) {
    await act(async () => {
      screen.root.findByProps({ accessibilityLabel: 'Continue with development account' }).props.onPress();
    });
  }

  it('sends a complete shared phone number with one click and saves the session', async () => {
    const screen = await mount();
    expect(screen.root.findByType(TextInput).props.value).toBe(DEVELOPMENT_PHONE_NUMBER);
    expect(fetchMock).not.toHaveBeenCalled();

    await continueWithDevelopment(screen);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe(`${api.baseUrl}/v1/dev/auth`);
    expect(init?.method).toBe('POST');
    expect(new Headers(init?.headers).get('Content-Type')).toBe('application/json');
    const payload = JSON.parse(String(init?.body));
    expect(payload).toEqual({ phone_number: DEVELOPMENT_PHONE_NUMBER });
    expect(payload.phone_number).toMatch(/^\+[1-9]\d{6,14}$/);
    expect(screen.root.findByProps({ accessibilityLabel: 'Open Conversation' })).toBeTruthy();
    if (platform === 'web') {
      expect(webStorage.setItem).toHaveBeenCalledWith(expect.any(String), 'development-session');
      expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
    } else {
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(expect.any(String), 'development-session');
      expect(webStorage.setItem).not.toHaveBeenCalled();
    }
  });

  it('still submits an explicitly edited development identity', async () => {
    const screen = await mount();
    const editedPhone = '+442079460123';
    await act(async () => screen.root.findByType(TextInput).props.onChangeText(editedPhone));

    await continueWithDevelopment(screen);

    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({ phone_number: editedPhone });
  });

  it('restores an existing session without signing into the default identity', async () => {
    webStorage.getItem.mockReturnValue('existing-session');
    jest.mocked(SecureStore.getItemAsync).mockResolvedValue('existing-session');
    const screen = await mount();

    expect(screen.root.findAllByType(TextInput)).toHaveLength(0);
    expect(screen.root.findByProps({ accessibilityLabel: 'Open Conversation' })).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
    await api.me();
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get('Authorization')).toBe('Bearer existing-session');
  });
});
