import React, { useRef, useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
import { StatusIndicator } from './StatusIndicator';
import { ErrorMessage } from './ErrorMessage';
import { EmptyResults } from './EmptyResults';
import { Sidebar } from './Sidebar';
import { useChat } from '../hooks/useChat';
import { SkeletonCard } from './SkeletonCard';

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
    <div style={{ display: 'flex', height: '100vh' }}>
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
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#f5f5f5',
          minWidth: 0,
        }}
      >
        {/* Header */}
        <header
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '60px',
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            fontSize: '20px',
            fontWeight: 'bold',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          <button
            onClick={() => setSidebarOpen(prev => !prev)}
            style={{
              position: 'absolute',
              left: '16px',
              background: 'transparent',
              border: 'none',
              color: '#ffffff',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
            title={sidebarOpen ? 'Скрыть сайдбар' : 'Показать сайдбар'}
          >
            ☰
          </button>
          🎸 Guitar Agent
          {connectionMessage && (
            <span style={{ marginLeft: '12px', fontSize: '12px', opacity: 0.8 }}>
              ({connectionMessage})
            </span>
          )}
        </header>

        {/* Область сообщений */}
        <main
          style={{
            flex: 1,
            overflowY: 'auto',
            backgroundColor: '#ffffff',
          }}
        >
          <MessageList messages={messages} />

          {messages.length > 0 &&
            messages[messages.length - 1].role === 'agent' &&
            messages[messages.length - 1].mode === 'search' &&
            (!messages[messages.length - 1].results || messages[messages.length - 1].results?.length === 0) && (
              <EmptyResults />
            )}

          {/* Скелетоны при ожидании search-результатов */}
          {isLoading && !status && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '12px',
              padding: '16px',
            }}>
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

        <style>{`
          @keyframes loading {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(300%); }
          }
        `}</style>
      </div>

    </div>
  );
};
