import React, { createContext, useContext, useMemo, useState, useCallback } from 'react';

const AuthContext = createContext({
  token: null,
  user: null,
  expiresAt: null,
  setAuth: () => {},
  logout: () => {},
});

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState({
    token: null,
    user: null,
    expiresAt: null,
  });

  const setAuth = useCallback(({ token, user, expiresAt }) => {
    setAuthState({
      token: token ?? null,
      user: user ?? null,
      expiresAt: expiresAt ?? null,
    });
  }, []);

  const logout = useCallback(() => {
    setAuthState({
      token: null,
      user: null,
      expiresAt: null,
    });
  }, []);

  const value = useMemo(
    () => ({
      token: authState.token,
      user: authState.user,
      expiresAt: authState.expiresAt,
      setAuth,
      logout,
    }),
    [authState, logout, setAuth],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
