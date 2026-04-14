import React from 'react';
import { Session } from '../types';
import './Sidebar.css';

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
    <>
      {/* Overlay для мобильных */}
      {isOpen && <div className="sidebar-overlay" onClick={onToggle} />}
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Кнопка нового чата */}
        <div className="sidebar-header">
          <button className="sidebar-new-chat-btn" onClick={onNewChat}>
            + Новый чат
          </button>
        </div>

        {/* Список сессий */}
        <div className="sidebar-sessions">
          {sessions.length === 0 && (
            <div className="sidebar-empty">Нет сохранённых чатов</div>
          )}
          {sessions.map((session) => {
            const isActive = session.id === currentSessionId;
            return (
              <div
                key={session.id}
                className={`sidebar-session ${isActive ? 'sidebar-session-active' : ''}`}
                onClick={() => onSelectSession(session.id)}
              >
                <div className="sidebar-session-title">
                  {session.title}
                </div>
                <button
                  className="sidebar-session-delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
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
          <div className="sidebar-footer">
            <button className="sidebar-clear-btn" onClick={onClearHistory}>
              Очистить всё
            </button>
          </div>
        )}
      </aside>
    </>
  );
};
