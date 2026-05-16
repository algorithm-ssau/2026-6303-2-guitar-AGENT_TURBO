import { AuthScreen, useAuth } from './features/auth';
import { Chat } from './features/chat';
import { ToastContainer } from './shared/hooks/useToast';
import { useTheme } from './shared/theme/useTheme';

function App() {
  const { theme, toggleTheme } = useTheme();
  const { token, user, isCheckingAuth, login, register, logout } = useAuth();

  if (isCheckingAuth) {
    return <div className="auth-page">Проверяем сессию...</div>;
  }

  return (
    <>
      {token && user ? (
        <Chat
          theme={theme}
          authToken={token}
          currentUserLogin={user.login}
          onAuthExpired={logout}
          onLogout={logout}
          onToggleTheme={toggleTheme}
        />
      ) : (
        <AuthScreen onLogin={login} onRegister={register} />
      )}
      <ToastContainer />
    </>
  );
}

export default App;
