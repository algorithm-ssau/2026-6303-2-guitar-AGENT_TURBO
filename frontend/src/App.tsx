import { Chat } from './features/chat';
import { useTheme } from './shared/theme/useTheme';

function App() {
  const { theme, toggleTheme } = useTheme();

  return <Chat theme={theme} onToggleTheme={toggleTheme} />;
}

export default App;
