import React, { createContext, useContext, useEffect, useMemo, useReducer } from 'react';
import { authReducer, initialAuthState, type AuthState } from './authState';
import type { AuthService } from './types';

interface Ctx { service: AuthService; state: AuthState }
const AuthCtx = createContext<Ctx | null>(null);

export function AuthProvider({ service, children }: { service: AuthService; children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialAuthState);

  useEffect(() => {
    let alive = true;
    service.getSession().then((u) => alive && dispatch({ type: 'session', user: u }), () => alive && dispatch({ type: 'signedOut' }));
    const off = service.onChange((u) => alive && dispatch({ type: 'session', user: u }));
    return () => { alive = false; off(); };
  }, [service]);

  const value = useMemo(() => ({ service, state }), [service, state]);
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): Ctx {
  const c = useContext(AuthCtx);
  if (!c) throw new Error('useAuth outside AuthProvider');
  return c;
}
