import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
} from 'react';

import { api } from '@/api/client';
import { tokenStorage } from '@/auth/storage';

export type AuthState =
  | { phase: 'loading'; token: null; error: null }
  | { phase: 'signed_out'; token: null; error: string | null }
  | { phase: 'signing_in'; token: null; error: null }
  | { phase: 'signed_in'; token: string; error: null };

type AuthAction =
  | { type: 'RESTORED'; token: string | null }
  | { type: 'SIGN_IN' }
  | { type: 'SIGNED_IN'; token: string }
  | { type: 'FAILED'; message: string }
  | { type: 'SIGNED_OUT' };

export function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'RESTORED':
      return action.token
        ? { phase: 'signed_in', token: action.token, error: null }
        : { phase: 'signed_out', token: null, error: null };
    case 'SIGN_IN':
      return { phase: 'signing_in', token: null, error: null };
    case 'SIGNED_IN':
      return { phase: 'signed_in', token: action.token, error: null };
    case 'FAILED':
      return { phase: 'signed_out', token: null, error: action.message };
    case 'SIGNED_OUT':
      return { phase: 'signed_out', token: null, error: null };
    default:
      return state;
  }
}

interface AuthContextValue {
  state: AuthState;
  signIn(phoneNumber: string): Promise<void>;
  signOut(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(authReducer, {
    phase: 'loading',
    token: null,
    error: null,
  });

  useEffect(() => {
    void tokenStorage.get().then((token) => {
      api.setToken(token);
      dispatch({ type: 'RESTORED', token });
    });
  }, []);

  const signIn = useCallback(async (phoneNumber: string) => {
    dispatch({ type: 'SIGN_IN' });
    try {
      const session = await api.devAuth(phoneNumber);
      await tokenStorage.set(session.token);
      api.setToken(session.token);
      dispatch({ type: 'SIGNED_IN', token: session.token });
    } catch (error) {
      dispatch({ type: 'FAILED', message: error instanceof Error ? error.message : 'Sign-in failed' });
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api.revokeSession();
    } finally {
      api.setToken(null);
      await tokenStorage.clear();
      dispatch({ type: 'SIGNED_OUT' });
    }
  }, []);

  const value = useMemo(() => ({ state, signIn, signOut }), [signIn, signOut, state]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
