import React, { useRef, useEffect } from 'react';
import { Message } from '../types';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
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
    currentStatus,
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

  // Текст статуса в зависимости от состояния
  const statusText = currentStatus || (isLoading ? 'Агент обрабатывает запрос...' : null);

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

        {/* Индикатор загрузки / статуса */}
        {(isLoading || statusText) && (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              color: '#6c757d',
            }}
          >
            <div style={{ display: 'inline-block', marginBottom: '8px' }}>
              🤖
            </div>
            <div style={{ fontSize: '14px' }}>
              {statusText || 'Агент подбирает гитары...'}
            </div>
            <div
              style={{
                width: '200px',
                height: '4px',
                backgroundColor: '#e9ecef',
                borderRadius: '2px',
                margin: '12px auto 0',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: '50%',
                  height: '100%',
                  backgroundColor: '#28a745',
                  animation: 'loading 1s ease-in-out infinite',
                }}
              />
            </div>
          </div>
        )}

        {/* Сообщение об ошибке */}
        {error && (
          <div
            style={{
              padding: '16px',
              margin: '0 16px 16px',
              backgroundColor: '#f8d7da',
              color: '#721c24',
              borderRadius: '8px',
              fontSize: '14px',
            }}
          >
            ⚠️ {error}
          </div>
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
      `}</style>
    </div>
  );
};
