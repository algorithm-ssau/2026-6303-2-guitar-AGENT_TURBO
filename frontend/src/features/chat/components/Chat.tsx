import React, { useRef, useEffect, useState } from 'react';
import { Sidebar } from './Sidebar';
import { ChatMain } from './ChatMain';
import { useChat } from '../hooks/useChat';
import { Theme } from '../../../shared/theme/useTheme';
import { Message } from '../types';
import { ConfirmDialog } from '../../../shared/components/ConfirmDialog';
import './Chat.css';

interface ChatProps {
  theme: Theme;
  authToken: string;
  currentUserLogin: string;
  onAuthExpired: () => void;
  onLogout: () => void;
  onToggleTheme: () => void;
}

/**
 * Главный компонент чата с сайдбаром истории
 */
export const Chat: React.FC<ChatProps> = ({
  theme,
  authToken,
  currentUserLogin,
  onAuthExpired,
  onLogout,
  onToggleTheme,
}) => {
  const {
    messages = [],
    isLoading = false,
    error = null,
    connectionStatus = 'connecting',
    status = null,
    sendMessage = () => {},
    sendAction = () => {},
    sessions = [],
    isLoadingSessions = false,
    latestLiveMessageId = null,
    currentSessionId = null,
    selectSession = () => {},
    newChat = () => {},
    deleteSession = () => {},
    clearHistory = () => {},
    loadMoreSessions = () => {},
    hasMoreSessions = false,
    isLoadingMoreSessions = false,
    isLoadingSessionMessages = false,
  } = useChat(authToken, onAuthExpired);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [revealedMessageId, setRevealedMessageId] = useState<string | null>(null);
  const [revealedContent, setRevealedContent] = useState('');
  const [showRevealedResults, setShowRevealedResults] = useState(false);
  const [pendingConfirm, setPendingConfirm] = useState<'logout' | 'clear-history' | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 768px)');
    const syncViewportState = () => {
      const mobile = mediaQuery.matches;
      setIsMobileViewport(mobile);
      setSidebarOpen(!mobile);
    };

    syncViewportState();
    mediaQuery.addEventListener('change', syncViewportState);

    return () => mediaQuery.removeEventListener('change', syncViewportState);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, revealedContent, showRevealedResults]);

  useEffect(() => {
    if (!latestLiveMessageId) {
      setRevealedMessageId(null);
      setRevealedContent('');
      setShowRevealedResults(false);
    }
  }, [latestLiveMessageId]);

  useEffect(() => {
    if (!latestLiveMessageId) {
      return;
    }

    const latestMessage = messages.find((message) => message.id === latestLiveMessageId);
    if (!latestMessage || latestMessage.role !== 'agent') {
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;
    let currentIndex = 0;
    const fullText = latestMessage.content || '';

    setRevealedMessageId(latestMessage.id);
    setRevealedContent('');
    setShowRevealedResults(false);

    const revealResults = () => {
      if (!cancelled) {
        setShowRevealedResults(true);
        timeoutId = setTimeout(() => {
          if (!cancelled) {
            setRevealedMessageId(null);
            setRevealedContent('');
            setShowRevealedResults(false);
          }
        }, 0);
      }
    };

    const tick = () => {
      if (cancelled) {
        return;
      }

      if (!fullText) {
        revealResults();
        return;
      }

      currentIndex = Math.min(fullText.length, currentIndex + Math.max(2, Math.ceil(fullText.length / 40)));
      setRevealedContent(fullText.slice(0, currentIndex));

      if (currentIndex >= fullText.length) {
        timeoutId = setTimeout(revealResults, latestMessage.mode === 'search' ? 180 : 0);
        return;
      }

      timeoutId = setTimeout(tick, 24);
    };

    timeoutId = setTimeout(tick, 120);

    return () => {
      cancelled = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [latestLiveMessageId, messages]);

  const handleSend = (content: string) => {
    sendMessage(content);
  };

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  const handleSelectSession = (id: number) => {
    selectSession(id);
    if (isMobileViewport) {
      setSidebarOpen(false);
    }
  };

  const handleNewChat = () => {
    newChat();
    if (isMobileViewport) {
      setSidebarOpen(false);
    }
  };

  const handleRequestLogout = () => {
    setPendingConfirm('logout');
  };

  const handleRequestClearHistory = () => {
    setPendingConfirm('clear-history');
  };

  const handleCancelConfirm = () => {
    setPendingConfirm(null);
  };

  const handleConfirmAction = () => {
    const action = pendingConfirm;
    setPendingConfirm(null);

    if (action === 'logout') {
      onLogout();
    }

    if (action === 'clear-history') {
      clearHistory();
    }
  };

  const handleRetry = () => {
    const lastUserMessage = messages.slice().reverse().find(m => m.role === 'user')?.content;
    if (lastUserMessage) {
      sendMessage(lastUserMessage);
    }
  };

  // Обработчик скролла сайдбара — подгрузка сессий при приближении к низу
  const handleSidebarScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const isNearBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 50;
    if (isNearBottom && hasMoreSessions && !isLoadingMoreSessions) {
      loadMoreSessions();
    }
  };

  const thinkingLabel = status || 'Думаю над ответом';
  const displayMessages = messages.map((message): Message => {
    if (message.id !== revealedMessageId || message.role !== 'agent') {
      return message;
    }

    return {
      ...message,
      content: revealedContent,
      results: showRevealedResults ? message.results : undefined,
      transient: { phase: 'revealing', status: null },
    };
  });

  if (isLoading) {
    displayMessages.push({
      id: 'pending-agent-message',
      role: 'agent',
      content: '',
      timestamp: new Date(),
      transient: {
        phase: 'thinking',
        status: thinkingLabel,
      },
    });
  }

  const canRetryLastMessage = Boolean(messages.slice().reverse().find((message) => message.role === 'user')?.content);

  return (
    <div className="chat-page">
      <div className="chat-layout">
        {/* Сайдбар истории — слева */}
        <Sidebar
          sessions={sessions}
          isLoadingSessions={isLoadingSessions}
          currentSessionId={currentSessionId}
          isOpen={sidebarOpen}
          theme={theme}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onDeleteSession={deleteSession}
          onClearHistory={handleRequestClearHistory}
          onToggleTheme={onToggleTheme}
          onLogout={handleRequestLogout}
          onToggle={handleToggleSidebar}
          onScroll={handleSidebarScroll}
          isLoadingMore={isLoadingMoreSessions}
        />

        <ChatMain
          displayMessages={displayMessages}
          connectionStatus={connectionStatus}
          error={error}
          isLoading={isLoading}
          isLoadingSessionMessages={isLoadingSessionMessages}
          canRetryLastMessage={canRetryLastMessage}
          sidebarOpen={sidebarOpen}
          currentUserLogin={currentUserLogin}
          onToggleSidebar={handleToggleSidebar}
          onNewChat={handleNewChat}
          onSend={handleSend}
          onRetry={handleRetry}
          onAction={sendAction}
          messagesEndRef={messagesEndRef}
        />
      </div>

      <ConfirmDialog
        isOpen={pendingConfirm !== null}
        title={pendingConfirm === 'clear-history' ? 'Очистить историю?' : 'Выйти из аккаунта?'}
        message={
          pendingConfirm === 'clear-history'
            ? 'Вы уверены, что хотите удалить всю историю чатов? Это действие нельзя отменить.'
            : 'Вы уверены, что хотите выйти? Текущий чат останется в истории.'
        }
        onCancel={handleCancelConfirm}
        onConfirm={handleConfirmAction}
      />
    </div>
  );
};
