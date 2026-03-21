import React, { useState, useRef, useEffect } from 'react';
import { Message, ChatState } from '../types';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
import { sendMessage } from '../api';

/**
 * Главный компонент чата
 * Управляет состоянием и рендерингом всего интерфейса
 */
export const Chat: React.FC = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  /**
   * Отправка сообщения с вызовом API
   */
  const handleSend = async (content: string) => {
    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, newUserMessage],
      isLoading: true,
      error: null,
    }));

    try {
      const response = await sendMessage(content);
      
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: response.reply,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, agentMessage],
        isLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Неизвестная ошибка',
      }));
    }
  };

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
      </header>

      {/* Область сообщений */}
      <main
        style={{
          flex: 1,
          overflowY: 'auto',
          backgroundColor: '#ffffff',
        }}
      >
        <MessageList messages={state.messages} />
        
        {/* Индикатор загрузки */}
        {state.isLoading && (
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
            <div style={{ fontSize: '14px' }}>Агент подбирает гитары...</div>
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
        {state.error && (
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
            ⚠️ {state.error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Форма ввода */}
      <InputForm onSend={handleSend} disabled={state.isLoading} />

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
