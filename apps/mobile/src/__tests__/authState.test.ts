import { authReducer, type AuthState } from '@/auth/AuthProvider';

describe('authentication session state', () => {
  const loading: AuthState = { phase: 'loading', token: null, error: null };

  it('restores a secure token into signed-in state', () => {
    expect(authReducer(loading, { type: 'RESTORED', token: 'opaque-token' })).toEqual({
      phase: 'signed_in',
      token: 'opaque-token',
      error: null,
    });
  });

  it('clears session state on sign out', () => {
    const signedIn: AuthState = { phase: 'signed_in', token: 'opaque-token', error: null };
    expect(authReducer(signedIn, { type: 'SIGNED_OUT' })).toEqual({
      phase: 'signed_out',
      token: null,
      error: null,
    });
  });

  it('keeps sign-in failures out of token state', () => {
    expect(authReducer(loading, { type: 'FAILED', message: 'disabled' })).toEqual({
      phase: 'signed_out',
      token: null,
      error: 'disabled',
    });
  });
});
