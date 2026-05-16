import { useCallback, useEffect, useState } from 'react';
import { AuthUser, fetchMe, login as apiLogin, register as apiRegister } from './api';

const TOKEN_STORAGE_KEY = 'guitar-agent-token';

export interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isCheckingAuth: boolean;
  authError: string | null;
  login: (loginValue: string, password: string) => Promise<void>;
  register: (loginValue: string, password: string) => Promise<void>;
  logout: () => void;
}

export function useAuth(): AuthState {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(Boolean(token));
  const [authError, setAuthError] = useState<string | null>(null);

  const persistAuth = useCallback((nextToken: string, nextUser: AuthUser) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, nextToken);
    setToken(nextToken);
    setUser(nextUser);
    setAuthError(null);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
    setAuthError(null);
    setIsCheckingAuth(false);
  }, []);

  useEffect(() => {
    if (!token) {
      setIsCheckingAuth(false);
      return;
    }

    let cancelled = false;
    setIsCheckingAuth(true);
    fetchMe(token)
      .then((currentUser) => {
        if (!cancelled) {
          setUser(currentUser);
          setAuthError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          logout();
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsCheckingAuth(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [logout, token]);

  const login = useCallback(async (loginValue: string, password: string) => {
    setAuthError(null);
    const response = await apiLogin(loginValue, password);
    persistAuth(response.token, response.user);
  }, [persistAuth]);

  const register = useCallback(async (loginValue: string, password: string) => {
    setAuthError(null);
    const response = await apiRegister(loginValue, password);
    persistAuth(response.token, response.user);
  }, [persistAuth]);

  return {
    token,
    user,
    isCheckingAuth,
    authError,
    login,
    register,
    logout,
  };
}
