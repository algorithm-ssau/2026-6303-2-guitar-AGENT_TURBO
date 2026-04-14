import React, { useRef, useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
import { StatusIndicator } from './StatusIndicator';
import { ErrorMessage } from './ErrorMessage';
import { EmptyResults } from './EmptyResults';
import { Sidebar } from './Sidebar';
import { useChat } from '../hooks/useChat';
import { SkeletonCard } from './SkeletonCard';
import './Chat.css';

/**
 * Главный компонент чата с сайдбаром истории
 */
export const Chat: React.FC = () => {
  const {
    messages,
    isLoading,
    error,
    connectionStatus,
    status,
    sendMessage,
    sessions,
    currentSessionId,
    selectSession,
    newChat,
    deleteSession,
    clearHistory,
    loadMoreSessions,
    hasMoreSessions,
    isLoadingMoreSessions,
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (content: string) => {
    sendMessage(content);
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

  return (
    <div className="chat-layout">
      {/* Сайдбар истории — слева */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        isOpen={sidebarOpen}
        onSelectSession={selectSession}
        onNewChat={newChat}
        onDeleteSession={deleteSession}
        onClearHistory={clearHistory}
        onToggle={() => setSidebarOpen(prev => !prev)}
        onScroll={handleSidebarScroll}
        isLoadingMore={isLoadingMoreSessions}
      />

      {/* Основная область чата */}
      <div className="chat-main">
        {/* Header */}
        <header className="chat-header">
          <button
            className="chat-header-toggle"
            onClick={() => setSidebarOpen(prev => !prev)}
            title={sidebarOpen ? 'Скрыть сайдбар' : 'Показать сайдбар'}
          >
            ☰
          </button>
          🎸 Guitar Agent
          {connectionMessage && (
            <span className="chat-header-status">
              ({connectionMessage})
            </span>
          )}
        </header>

        {/* Область сообщений */}
        <main className="chat-messages">
          <MessageList messages={messages} />

          {messages.length > 0 &&
            messages[messages.length - 1].role === 'agent' &&
            messages[messages.length - 1].mode === 'search' &&
            (!messages[messages.length - 1].results || messages[messages.length - 1].results?.length === 0) && (
              <EmptyResults />
            )}

          {/* Скелетоны при ожидании search-результатов */}
          {isLoading && !status && (
            <div className="chat-skeleton-grid">
              <SkeletonCard count={3} />
            </div>
          )}

          <StatusIndicator status={status} isLoading={isLoading} />

          {error && (
            <ErrorMessage message={error} onRetry={handleRetry} />
          )}

          <div ref={messagesEndRef} />
        </main>

        {/* Форма ввода */}
        <InputForm onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  );
};
