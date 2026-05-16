import React, { useState } from 'react';
import './AuthScreen.css';

interface AuthScreenProps {
  onLogin: (login: string, password: string) => Promise<void>;
  onRegister: (login: string, password: string) => Promise<void>;
}

const LOGIN_RE = /^[A-Za-z0-9_-]{3,32}$/;

function validate(login: string, password: string): string | null {
  if (!LOGIN_RE.test(login)) {
    return 'Логин: 3-32 символа, латинские буквы, цифры, _ или -';
  }
  if (password.length < 3) {
    return 'Пароль должен быть не короче 3 символов';
  }
  return null;
}

export const AuthScreen: React.FC<AuthScreenProps> = ({ onLogin, onRegister }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextLogin = login.trim();
    const validationError = validate(nextLogin, password);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      if (mode === 'login') {
        await onLogin(nextLogin, password);
      } else {
        await onRegister(nextLogin, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить вход');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <main className="auth-panel">
        <div className="auth-brand">GUITAR AI</div>
        <div className="auth-tabs" role="tablist" aria-label="Режим авторизации">
          <button
            type="button"
            className={`auth-tab ${mode === 'login' ? 'auth-tab-active' : ''}`}
            onClick={() => {
              setMode('login');
              setError(null);
            }}
          >
            Вход
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'register' ? 'auth-tab-active' : ''}`}
            onClick={() => {
              setMode('register');
              setError(null);
            }}
          >
            Регистрация
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-field">
            <span>Логин</span>
            <input
              value={login}
              onChange={(event) => setLogin(event.target.value)}
              autoComplete="username"
              placeholder="admin"
              disabled={isSubmitting}
            />
          </label>
          <label className="auth-field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              placeholder="admin"
              disabled={isSubmitting}
            />
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Проверяем...' : mode === 'login' ? 'Войти' : 'Создать аккаунт'}
          </button>
        </form>
      </main>
    </div>
  );
};
