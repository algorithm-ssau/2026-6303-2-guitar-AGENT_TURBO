import React from 'react';
import { Message } from '../types';
import { ModeBadge } from './ModeBadge';
import { ResultsList } from './ResultsList';
import { SearchStatus } from './SearchStatus';

interface MessageProps {
  message: Message;
}

/**
 * Компонент одного сообщения в чате
 * Отображает сообщение от пользователя или агента
 */
export const MessageItem: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  const formattedTime = message.timestamp.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
        width: '100%',
      }}
    >
      <div
        style={{
          maxWidth: isUser ? '70%' : '90%',
          padding: '12px 16px',
          borderRadius: '12px',
          backgroundColor: isUser ? '#007bff' : '#e9ecef',
          color: isUser ? '#ffffff' : '#212529',
          borderBottomRightRadius: isUser ? '4px' : '12px',
          borderBottomLeftRadius: isUser ? '12px' : '4px',
        }}
      >
        <div
          style={{
            fontSize: '12px',
            fontWeight: 'bold',
            marginBottom: '4px',
            opacity: 0.8,
          }}
        >
          {isUser ? '👤 Вы' : '🤖 Агент'}
          {!isUser && message.mode && <ModeBadge mode={message.mode} />}
        </div>

        {/* Для consultation mode или fallback показываем content */}
        {(!message.mode || message.mode === 'consultation' || !message.results || message.results.length === 0) && (
          <div style={{ fontSize: '14px', lineHeight: '1.5' }}>
            {message.content}
          </div>
        )}

        {/* Отображаем список результатов */}
        {message.mode === 'search' && message.results && message.results.length > 0 && (
          <ResultsList results={message.results} />
        )}
        <div
          style={{
            fontSize: '11px',
            marginTop: '8px',
            opacity: 0.7,
            textAlign: 'right',
          }}
        >
          {formattedTime}
        </div>
      </div>
    </div>
  );
};
