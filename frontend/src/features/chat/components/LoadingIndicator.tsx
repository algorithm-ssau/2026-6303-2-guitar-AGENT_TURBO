import React from 'react';

interface LoadingIndicatorProps {
  title?: string;
  description?: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  title = 'Загрузка чата',
  description = 'Подтягиваем сообщения и состояние сессии...',
}) => {
  return (
    <div
      style={{
        minHeight: '240px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '14px',
        color: 'var(--text-dim)',
        textAlign: 'center',
      }}
    >
      <div
        aria-hidden="true"
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          border: '3px solid color-mix(in srgb, var(--border) 80%, transparent)',
          borderTopColor: 'var(--accent)',
          animation: 'spin 0.9s linear infinite',
        }}
      />
      <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>{title}</div>
      <div style={{ fontSize: '13px', maxWidth: '320px' }}>{description}</div>
    </div>
  );
};
