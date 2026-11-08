// Pure auth state machine (FR-A01). Kept free of React so it can be unit-tested.
import type { AuthUser } from './types';

export type AuthState =
  | { status: 'loading'; user: null }
  | { status: 'signedOut'; user: null }
  | { status: 'signedIn'; user: AuthUser };

export type AuthAction =
  | { type: 'session'; user: AuthUser | null }
  | { type: 'signedOut' };

export const initialAuthState: AuthState = { status: 'loading', user: null };

export function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'session':
      if (action.user) {
        if (state.status === 'signedIn' && state.user.id === action.user.id && state.user.email === action.user.email) return state;
        return { status: 'signedIn', user: action.user };
      }
      return state.status === 'signedOut' ? state : { status: 'signedOut', user: null };
    case 'signedOut':
      return state.status === 'signedOut' ? state : { status: 'signedOut', user: null };
    default:
      return state;
  }
}
