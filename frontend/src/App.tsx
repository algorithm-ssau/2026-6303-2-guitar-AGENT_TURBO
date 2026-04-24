import { Chat } from './features/chat';
import { ToastContainer } from './shared/hooks/useToast';
import { useTheme } from './shared/theme/useTheme';

function App() {
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      <Chat theme={theme} onToggleTheme={toggleTheme} />
      <ToastContainer />
    </>
  );
}

export default App;
