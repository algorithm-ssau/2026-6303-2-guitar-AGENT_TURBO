import React, { useState, useMemo } from 'react';
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
  onScroll?: (e: React.UIEvent<HTMLDivElement>) => void;
  isLoadingMore?: boolean;
}

/**
 * Сайдбар с историей чатов — по дизайну из mockup.html
 * Тёмная тема, hover-эффекты, поиск, анимации
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
    <aside
      style={{
        width: isOpen ? '280px' : '0px',
        minWidth: isOpen ? '280px' : '0px',
        height: '100vh',
        backgroundColor: '#141414',
        color: '#ececec',
        display: 'flex',
        flexDirection: 'column',
        borderRight: isOpen ? '1px solid #2a2a2a' : 'none',
        overflow: 'hidden',
        transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        fontFamily: '"Inter", -apple-system, sans-serif',
      }}
    >
      {/* Заголовок */}
      <div
        style={{
          padding: '24px 24px 0',
          fontWeight: 900,
          fontSize: '22px',
          color: '#4d88ff',
          letterSpacing: '-1px',
          marginBottom: '20px',
        }}
      >
        GUITAR AI
      </div>

      {/* Кнопка нового чата — accent style из мокапа */}
      <div style={{ padding: '0 24px 16px' }}>
        <button
          onClick={onNewChat}
          style={{
            width: '100%',
            padding: '12px 24px',
            backgroundColor: '#4d88ff',
            color: '#ffffff',
            border: 'none',
            borderRadius: '12px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            transition: 'background 0.2s, transform 0.2s, box-shadow 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#3d78ef';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 5px 15px rgba(77, 136, 255, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#4d88ff';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          ✚ Новый чат
        </button>
      </div>

      {/* Поле поиска по истории */}
      <div style={{ padding: '0 24px 16px' }}>
        <input
          type="text"
          placeholder="Поиск чатов..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '14px 18px',
            borderRadius: '14px',
            border: '1px solid #2a2a2a',
            backgroundColor: '#1a1a1a',
            color: '#ececec',
            outline: 'none',
            fontSize: '15px',
            transition: 'border-color 0.2s, box-shadow 0.2s',
            boxSizing: 'border-box',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = '#4d88ff';
            e.currentTarget.style.boxShadow = '0 0 0 3px rgba(77, 136, 255, 0.15)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = '#2a2a2a';
            e.currentTarget.style.boxShadow = 'none';
          }}
        />
      </div>

      {/* Метка "История запросов" */}
      <div
        style={{
          padding: '0 24px',
          fontSize: '11px',
          color: '#999999',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          fontWeight: 700,
          marginBottom: '10px',
        }}
      >
        История запросов
      </div>

      {/* Список сессий */}
      <div
        onScroll={onScroll}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 16px',
        }}
      >
        {filteredSessions.length === 0 && (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              fontSize: '13px',
              color: '#999999',
            }}
          >
            {searchQuery ? 'Ничего не найдено' : 'Нет сохранённых чатов'}
          </div>
        )}
        {filteredSessions.map((session) => {
          const isActive = session.id === currentSessionId;
          const isHovered = hoveredSessionId === session.id;

          return (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              onMouseEnter={() => setHoveredSessionId(session.id)}
              onMouseLeave={() => setHoveredSessionId(null)}
              style={{
                padding: '12px',
                marginBottom: '10px',
                borderRadius: '12px',
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '8px',
                // Активная сессия — подсвеченный фон
                backgroundColor: isActive ? '#1a1a1a' : 'transparent',
                border: isActive ? '1px solid #2a2a2a' : '1px solid transparent',
                color: isActive ? '#4d88ff' : '#999999',
                fontWeight: isActive ? 600 : 400,
                // Hover-эффекция на неактивных сессиях
                ...(isHovered && !isActive
                  ? {
                      backgroundColor: '#1e1e1e',
                      color: '#ececec',
                    }
                  : {}),
                transition: 'background-color 0.2s, color 0.2s, border-color 0.2s',
              }}
            >
              <div
                style={{
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {session.title}
              </div>
              {/* Кнопка удаления — появляется только при hover */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm('Удалить этот чат?')) {
                    onDeleteSession(session.id);
                  }
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#999999',
                  cursor: 'pointer',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '14px',
                  flexShrink: 0,
                  // Появляется только при hover
                  opacity: isHovered ? 1 : 0,
                  transition: 'opacity 0.2s',
                  lineHeight: 1,
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
          <div
            style={{
              padding: '12px',
              textAlign: 'center',
              fontSize: '13px',
              color: '#999999',
            }}
          >
            Загрузка...
          </div>
        )}
      </div>

      {/* Кнопка очистить всё */}
      {sessions.length > 0 && (
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #2a2a2a',
          }}
        >
          <button
            onClick={() => {
              if (window.confirm('Удалить всю историю?')) {
                onClearHistory();
              }
            }}
            style={{
              width: '100%',
              padding: '12px',
              background: 'transparent',
              border: '1px solid #2a2a2a',
              color: '#999999',
              borderRadius: '12px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'border-color 0.2s, color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#4d88ff';
              e.currentTarget.style.color = '#4d88ff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#2a2a2a';
              e.currentTarget.style.color = '#999999';
            }}
          >
            🗑 Очистить всё
          </button>
        </div>
      )}
    </aside>
  );
};
