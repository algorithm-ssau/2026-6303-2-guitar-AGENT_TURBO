import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types';
import { ModeBadge } from './ModeBadge';
import { ResultsList } from './ResultsList';
import { SearchParamsPanel } from './SearchParamsPanel';
import './Message.css';

interface MessageProps {
  message: Message;
  previousMessage?: Message;
}

/**
 * Компонент одного сообщения в чате
 * Отображает сообщение от пользователя или агента
 */
export const MessageItem: React.FC<MessageProps> = ({ message, previousMessage }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const isThinking = message.transient?.phase === 'thinking';
  const showThinkingState = !isUser && isThinking;

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
          padding: '14px 20px',
          borderRadius: '20px',
          backgroundColor: isUser ? 'var(--bg-bubble-user)' : 'var(--bg-bubble-ai)',
          color: isUser ? 'var(--message-user-text)' : 'var(--message-ai-text)',
          border: isUser ? 'none' : '1px solid var(--border)',
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
          {!isUser && isConsultation && !message.transient && (
            <button
              onClick={handleCopy}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              {copied ? '✅ Скопировано!' : '📋 Копировать'}
            </button>
          )}
        </div>

        {showThinkingState && (
          <div className="message-thinking-body">
            <div className="message-thinking-title">
              Думаю над ответом
              <span className="message-thinking-dots">
                <span />
                <span />
                <span />
              </span>
            </div>
            <div className="message-thinking-status">{message.transient?.status || 'Собираю ответ...'}</div>
          </div>
        )}

        {!showThinkingState && showContent && (
          <div style={{ fontSize: '14px', lineHeight: '1.5' }}>
            {!isUser && isConsultation ? (
              <ReactMarkdown
                components={{
                  code(props) {
                    const { children, className, node, ...rest } = props;
                    return (
                      <code
                        {...rest}
                        style={{
                          backgroundColor: 'var(--code-bg)',
                          color: 'var(--text-main)',
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
                      <a {...rest} style={{ color: 'var(--link)', textDecoration: 'underline' }}>
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

        {!isUser && message.mode === 'search' && previousMessage?.parsedParams && (
          <SearchParamsPanel params={previousMessage.parsedParams} />
        )}

        {message.mode === 'search' && message.results && message.results.length > 0 && (
          <ResultsList results={message.results} />
        )}
        {!message.transient && (
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
        )}
      </div>
    </div>
  );
};
