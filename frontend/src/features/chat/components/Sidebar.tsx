import React from 'react';
import { Session } from '../types';

interface SidebarProps {
  sessions: Session[];
  currentSessionId: number | null;
  isOpen: boolean;
  onSelectSession: (id: number) => void;
  onNewChat: () => void;
  onDeleteSession: (id: number) => void;
  onClearHistory: () => void;
  onToggle: () => void;
}

/**
 * Сайдбар с историей чатов
 */
export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  isOpen,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onClearHistory,
  onToggle,
}) => {
  return (
    <aside
      style={{
        width: isOpen ? '280px' : '0px',
        minWidth: isOpen ? '280px' : '0px',
        height: '100vh',
        backgroundColor: '#1a1a2e',
        color: '#e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        borderRight: isOpen ? '1px solid #2a2a4a' : 'none',
        overflow: 'hidden',
        transition: 'width 0.2s ease, min-width 0.2s ease',
      }}
    >
      {/* Кнопка нового чата */}
      <div style={{ padding: '16px' }}>
        <button
          onClick={onNewChat}
          style={{
            width: '100%',
            padding: '10px 16px',
            backgroundColor: '#3a3a5c',
            color: '#ffffff',
            border: '1px solid #4a4a6a',
            borderRadius: '8px',
            fontSize: '14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          + Новый чат
        </button>
      </div>

      {/* Список сессий */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 8px',
        }}
      >
        {sessions.length === 0 && (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              fontSize: '13px',
              opacity: 0.5,
            }}
          >
            Нет сохранённых чатов
          </div>
        )}
        {sessions.map((session) => {
          const isActive = session.id === currentSessionId;
          return (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              style={{
                padding: '10px 12px',
                marginBottom: '2px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: isActive ? '#3a3a5c' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '8px',
              }}
            >
              <div
                style={{
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontSize: '13px',
                }}
              >
                {session.title}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#888',
                  cursor: 'pointer',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '14px',
                  flexShrink: 0,
                }}
                title="Удалить чат"
              >
                x
              </button>
            </div>
          );
        })}
      </div>

      {/* Кнопка очистить всё */}
      {sessions.length > 0 && (
        <div style={{ padding: '12px 16px', borderTop: '1px solid #2a2a4a' }}>
          <button
            onClick={onClearHistory}
            style={{
              width: '100%',
              padding: '8px',
              background: 'transparent',
              border: '1px solid #4a4a6a',
              color: '#888',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            Очистить всё
          </button>
        </div>
      )}
    </aside>
  );
};
