import React from 'react';
import { Message } from '../types';
import { MessageItem } from './Message';

interface MessageListProps {
  messages: Message[];
}

/**
 * Компонент списка сообщений
 * Рендерит все сообщения в чате
 */
export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#6c757d',
          textAlign: 'center',
          padding: '20px',
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎸</div>
        <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>
          Добро пожаловать в Guitar Agent!
        </div>
        <div style={{ fontSize: '14px', marginBottom: '16px' }}>
          Опишите желаемый звук и бюджет — я найду<br />
          подходящие варианты на Reverb.
        </div>
        <div
          style={{
            fontSize: '13px',
            backgroundColor: '#f8f9fa',
            padding: '12px 16px',
            borderRadius: '8px',
          }}
        >
          Пример: "Хочу телекастер с ярким звуком, до $600"
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '16px' }}>
      {messages.map((message, index) => (
        <MessageItem key={message.id} message={message} previousMessage={index > 0 ? messages[index - 1] : undefined}  />
      ))}
    </div>
  );
};
