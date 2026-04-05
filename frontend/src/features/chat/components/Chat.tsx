import React, { useRef, useEffect } from 'react';
import { Message } from '../types';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
import { StatusIndicator } from './StatusIndicator';
import { ErrorMessage } from './ErrorMessage';
import { EmptyResults } from './EmptyResults';
import { useChat } from '../hooks/useChat';

/**
 * Главный компонент чата
 * Управляет состоянием и рендерингом всего интерфейса
 */
export const Chat: React.FC = () => {
  const {
    messages,
    isLoading,
    error,
    connectionStatus,
    status,
    sendMessage,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Отправка сообщения
   */
  const handleSend = (content: string) => {
    sendMessage(content);
  };

  const handleRetry = () => {
    const lastUserMessage = messages.slice().reverse().find(m => m.role === 'user')?.content;
    if (lastUserMessage) {
      sendMessage(lastUserMessage);
    }
  };

  // Сообщение о статусе соединения
  const connectionMessage =
    connectionStatus === 'connecting' ? 'Подключение...' :
      connectionStatus === 'disconnected' ? 'Переподключение...' : null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: '#f5f5f5',
      }}
    >
      {/* Header */}
      <header
        style={{
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

        {/* Индикатор статуса */}
        <StatusIndicator status={status} isLoading={isLoading} />

        {/* Сообщение об ошибке */}
        {error && (
          <ErrorMessage message={error} onRetry={handleRetry} />
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Форма ввода */}
      <InputForm onSend={handleSend} disabled={isLoading} />

      {/* CSS-анимация для лоадера */}
      <style>{`
        @keyframes loading {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
        .status-dots {
          animation: 'dots 1.5s steps(4, end) infinite';
        }
        @keyframes dots {
          0%, 20% { content: ''; }
          40% { content: '.'; }
          60% { content: '..'; }
          80%, 100% { content: '...'; }
        }
      `}</style>
    </div>
  );
};
