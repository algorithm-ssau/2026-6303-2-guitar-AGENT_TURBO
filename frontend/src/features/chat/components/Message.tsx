import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
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
  const [copied, setCopied] = useState(false);

  const formattedTime = message.timestamp.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const isConsultation = !message.mode || message.mode === 'consultation';
  const showContent = isConsultation || !message.results || message.results.length === 0;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            {isUser ? '👤 Вы' : '🤖 Агент'}
            {!isUser && message.mode && <ModeBadge mode={message.mode} />}
          </div>
          {!isUser && isConsultation && (
            <button
              onClick={handleCopy}
              style={{
                background: 'none',
                border: 'none',
                color: '#6c757d',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              {copied ? '✅ Скопировано!' : '📋 Копировать'}
            </button>
          )}
        </div>

        {/* Для consultation mode или fallback показываем content */}
        {showContent && (
          <div style={{ fontSize: '14px', lineHeight: '1.5' }}>
            {(!isUser && isConsultation) ? (
              <ReactMarkdown
                components={{
                  code(props) {
                    const { children, className, node, ...rest } = props;
                    return (
                      <code
                        {...rest}
                        style={{
                          backgroundColor: '#2b2b2b',
                          color: '#f8f9fa',
                          padding: '2px 4px',
                          borderRadius: '4px',
                          fontFamily: 'monospace'
                        }}
                      >
                        {children}
                      </code>
                    );
                  },
                  a(props) {
                    const { children, node, ...rest } = props;
                    return (
                      <a {...rest} style={{ color: '#007bff', textDecoration: 'underline' }}>
                        {children}
                      </a>
                    );
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              message.content
            )}
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
