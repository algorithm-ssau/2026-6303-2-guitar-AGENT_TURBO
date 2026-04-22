import React from 'react';
import { Message } from '../types';
import { MessageItem } from './Message';
import './Message.css';

interface MessageListProps {
  messages: Message[];
}

/**
 * Компонент списка сообщений
 * Рендерит все сообщения в чате
 */
export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const hasPersistentMessages = messages.some((message) => !message.transient);

  if (!hasPersistentMessages && messages.length === 0) {
    return (
      <div className="message-list-empty">
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎸</div>
        <div className="message-list-empty-title">
          Добро пожаловать в Guitar Agent!
        </div>
        <div className="message-list-empty-subtitle">
          Опишите желаемый звук и бюджет — я найду<br />
          подходящие варианты на Reverb.
        </div>
        <div className="message-list-empty-example">
          Пример: "Хочу телекастер с ярким звуком, до $600"
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <MessageItem key={message.id} message={message} previousMessage={index > 0 ? messages[index - 1] : undefined} />
      ))}
    </div>
  );
};
