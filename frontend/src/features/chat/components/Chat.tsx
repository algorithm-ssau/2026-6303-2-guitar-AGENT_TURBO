import React, { useRef, useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
import { ErrorMessage } from './ErrorMessage';
import { EmptyResults } from './EmptyResults';
import { Sidebar } from './Sidebar';
import { useChat } from '../hooks/useChat';
import { Theme } from '../../../shared/theme/useTheme';
import { Message } from '../types';
import './Chat.css';

interface ChatProps {
  theme: Theme;
  onToggleTheme: () => void;
}

/**
 * Главный компонент чата с сайдбаром истории
 */
export const Chat: React.FC<Partial<ChatProps>> = ({ theme = 'dark', onToggleTheme = () => {} }) => {
  const {
    messages = [],
    isLoading = false,
    error = null,
    connectionStatus = 'connecting',
    status = null,
    sendMessage = () => {},
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
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [revealedMessageId, setRevealedMessageId] = useState<string | null>(null);
  const [revealedContent, setRevealedContent] = useState('');
  const [showRevealedResults, setShowRevealedResults] = useState(false);
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

  const connectionMessage =
    connectionStatus === 'connecting' ? 'Подключение...' :
      connectionStatus === 'disconnected' ? 'Переподключение...' : null;

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

  const lastDisplayMessage = displayMessages[displayMessages.length - 1];

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
          onClearHistory={clearHistory}
          onToggleTheme={onToggleTheme}
          onToggle={handleToggleSidebar}
          onScroll={handleSidebarScroll}
          isLoadingMore={isLoadingMoreSessions}
        />

        {/* Основная область чата */}
        <div className="chat-main">
          <header className="chat-header">
            <div className="chat-header-group">
              <button
                className="chat-header-toggle"
                onClick={handleToggleSidebar}
                title={sidebarOpen ? 'Скрыть сайдбар' : 'Показать сайдбар'}
                aria-label={sidebarOpen ? 'Скрыть сайдбар' : 'Показать сайдбар'}
              >
                ☰
              </button>
              <div>
                <div className="chat-header-title">REVERB AGENT</div>
                {connectionMessage && (
                  <span className="chat-header-status">
                    {connectionMessage}
                  </span>
                )}
              </div>
            </div>

            <button className="chat-reset-button" onClick={handleNewChat}>
              ↻ Новый поиск
            </button>
          </header>

          <main className="chat-messages">
            {isLoadingSessionMessages ? (
              <div className="chat-history-skeleton" aria-hidden="true">
                <div className="chat-history-skeleton-message chat-history-skeleton-message-user" />
                <div className="chat-history-skeleton-message chat-history-skeleton-message-agent" />
                <div className="chat-history-skeleton-message chat-history-skeleton-message-agent chat-history-skeleton-message-wide" />
              </div>
            ) : (
              <>
                <MessageList messages={displayMessages} />

                {lastDisplayMessage &&
                  !lastDisplayMessage.transient &&
                  lastDisplayMessage.role === 'agent' &&
                  lastDisplayMessage.mode === 'search' &&
                  (!lastDisplayMessage.results || lastDisplayMessage.results.length === 0) && (
                    <EmptyResults />
                  )}

                {error && (
                  <ErrorMessage message={error} onRetry={handleRetry} />
                )}
              </>
            )}

            <div ref={messagesEndRef} />
          </main>

          <InputForm onSend={handleSend} disabled={isLoading || isLoadingSessionMessages} />
        </div>
      </div>
    </div>
  );
};
