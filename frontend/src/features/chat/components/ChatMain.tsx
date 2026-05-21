import React from 'react';
import { MessageList } from './MessageList';
import { InputForm } from './InputForm';
import { ErrorMessage } from './ErrorMessage';
import { EmptyResults } from './EmptyResults';
import { LoadingIndicator } from './LoadingIndicator';
import { Message } from '../types';

interface ChatMainProps {
  displayMessages: Message[];
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  error: string | null;
  isLoading: boolean;
  isLoadingSessionMessages: boolean;
  canRetryLastMessage: boolean;
  sidebarOpen: boolean;
  currentUserLogin: string;
  onToggleSidebar: () => void;
  onNewChat: () => void;
  onSend: (text: string) => void;
  onRetry: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

export const ChatMain: React.FC<ChatMainProps> = ({
  displayMessages,
  connectionStatus,
  error,
  isLoading,
  isLoadingSessionMessages,
  canRetryLastMessage,
  sidebarOpen,
  currentUserLogin,
  onToggleSidebar,
  onNewChat,
  onSend,
  onRetry,
  messagesEndRef,
}) => {
  const connectionMessage =
    connectionStatus === 'connecting' ? 'Подключение...' :
      connectionStatus === 'disconnected' ? 'Переподключение...' : null;

  const lastDisplayMessage = displayMessages[displayMessages.length - 1];

  return (
    <div className="chat-main">
      <header className="chat-header">
        <div className="chat-header-group">
          <button
            className="chat-header-toggle"
            onClick={onToggleSidebar}
            title={sidebarOpen ? 'Скрыть сайдбар' : 'Показать сайдбар'}
            aria-label={sidebarOpen ? 'Скрыть сайдбар' : 'Показать сайдбар'}
          >
            ☰
          </button>
          <div>
            <div className="chat-header-title">REVERB AGENT</div>
            {connectionMessage && (
              <span className="chat-header-status">
                {connectionMessage}
              </span>
            )}
          </div>
        </div>

        <div className="chat-header-actions">
          <span className="chat-current-user">{currentUserLogin}</span>
          <button className="chat-reset-button" onClick={onNewChat}>
            ↻ Новый поиск
          </button>
        </div>
      </header>

      <main className="chat-messages">
        <div className="chat-content-shell">
          {isLoadingSessionMessages ? (
            <LoadingIndicator />
          ) : (
            <>
              <MessageList messages={displayMessages} />

              {lastDisplayMessage &&
                !lastDisplayMessage.transient &&
                lastDisplayMessage.role === 'agent' &&
                lastDisplayMessage.mode === 'search' &&
                (!lastDisplayMessage.results || lastDisplayMessage.results.length === 0) && (
                  <EmptyResults />
                )}

              {error && (
                <ErrorMessage message={error} onRetry={canRetryLastMessage ? onRetry : undefined} />
              )}
            </>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <InputForm onSend={onSend} disabled={isLoading || isLoadingSessionMessages} />
    </div>
  );
};
