import React, { useState, useMemo } from 'react';
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
  onScroll?: (e: React.UIEvent<HTMLDivElement>) => void;
  isLoadingMore?: boolean;
}

/**
 * Сайдбар с историей чатов — по дизайну из mockup.html
 * Тёмная тема, hover-эффекты, поиск, анимации, CSS-классы из design system
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
  onScroll,
  isLoadingMore,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredSessionId, setHoveredSessionId] = useState<number | null>(null);

  // Фильтрация сессий по заголовку (регистронезависимо)
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const query = searchQuery.toLowerCase();
    return sessions.filter((s) => s.title.toLowerCase().includes(query));
  }, [sessions, searchQuery]);

  return (
    <>
      {/* Overlay для мобильных */}
      {isOpen && <div className="sidebar-overlay" onClick={onToggle} />}
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Заголовок */}
        <div className="sidebar-logo">GUITAR AI</div>

        {/* Кнопка нового чата */}
        <div className="sidebar-header">
          <button className="sidebar-new-chat-btn" onClick={onNewChat}>
            ✚ Новый чат
          </button>
        </div>

        {/* Поле поиска по истории */}
        <div className="sidebar-search">
          <input
            type="text"
            className="sidebar-search-input"
            placeholder="Поиск чатов..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Метка "История запросов" */}
        <div className="sidebar-label">История запросов</div>

        {/* Список сессий */}
        <div className="sidebar-sessions" onScroll={onScroll}>
          {filteredSessions.length === 0 && (
            <div className="sidebar-empty">
              {searchQuery ? 'Ничего не найдено' : 'Нет сохранённых чатов'}
            </div>
          )}
          {filteredSessions.map((session) => {
            const isActive = session.id === currentSessionId;
            const isHovered = hoveredSessionId === session.id;
            return (
              <div
                key={session.id}
                className={`sidebar-session ${isActive ? 'sidebar-session-active' : ''} ${isHovered && !isActive ? 'sidebar-session-hover' : ''}`}
                onClick={() => onSelectSession(session.id)}
                onMouseEnter={() => setHoveredSessionId(session.id)}
                onMouseLeave={() => setHoveredSessionId(null)}
              >
                <div className="sidebar-session-title">
                  {session.title}
                </div>
                <button
                  className={`sidebar-session-delete ${isHovered ? 'sidebar-session-delete-visible' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm('Удалить этот чат?')) {
                      onDeleteSession(session.id);
                    }
                  }}
                  title="Удалить чат"
                >
                  ✕
                </button>
              </div>
            );
          })}

          {/* Индикатор загрузки при подгрузке сессий */}
          {isLoadingMore && (
            <div className="sidebar-loading">Загрузка...</div>
          )}
        </div>

        {/* Кнопка очистить всё */}
        {sessions.length > 0 && (
          <div className="sidebar-footer">
            <button
              className="sidebar-clear-btn"
              onClick={() => {
                if (window.confirm('Удалить всю историю?')) {
                  onClearHistory();
                }
              }}
            >
              🗑 Очистить всё
            </button>
          </div>
        )}
      </aside>
    </>
  );
};
