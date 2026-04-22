import React from 'react';

export interface StatusIndicatorProps {
  status: string | null;
  isLoading: boolean;
  mode?: 'search' | 'consultation';
  showSkeletons?: boolean;
}

/**
 * Живой индикатор статуса поиска
 * Показывает текущий этап обработки с анимированными точками
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, isLoading }) => {
  // При isLoading=false — не рендерится
  if (!isLoading) {
    return null;
  }

  // При isLoading=true и status=null — показываем "Подключение..."
  if (!status) {
    return (
      <div
        style={{
          padding: '16px',
          textAlign: 'center',
          color: 'var(--text-dim)',
        }}
      >
        <div style={{ display: 'inline-block', marginBottom: '8px' }}>
          🤖
        </div>
        <div style={{ fontSize: '14px' }}>
          Подключение
          <span className="status-dots">...</span>
        </div>
        <div
          style={{
            width: '200px',
            height: '4px',
            backgroundColor: 'var(--surface-hover)',
            borderRadius: '2px',
            margin: '12px auto 0',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: '50%',
              height: '100%',
              backgroundColor: 'var(--success)',
              animation: 'loading 1s ease-in-out infinite',
            }}
          />
        </div>
      </div>
    );
  }

  // При isLoading=true и status не null — показываем текст статуса
  return (
    <div
      style={{
        padding: '16px',
        textAlign: 'center',
        color: 'var(--text-dim)',
      }}
    >
      <div style={{ display: 'inline-block', marginBottom: '8px' }}>
        🤖
      </div>
      <div style={{ fontSize: '14px' }}>
        {status}
        <span className="status-dots">...</span>
      </div>
      <div
        style={{
          width: '200px',
          height: '4px',
          backgroundColor: 'var(--surface-hover)',
          borderRadius: '2px',
          margin: '12px auto 0',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: '50%',
            height: '100%',
            backgroundColor: 'var(--success)',
            animation: 'loading 1s ease-in-out infinite',
          }}
        />
      </div>
    </div>
  );
};
