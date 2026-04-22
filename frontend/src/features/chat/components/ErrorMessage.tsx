import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

/**
 * Компонент отображения ошибки
 * Показывает текст ошибки и опциональную кнопку повторной попытки
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div
      style={{
        padding: '16px',
        margin: '0 16px 16px',
        backgroundColor: 'var(--error-bg)',
        color: 'var(--error-text)',
        border: '1px solid var(--error-border)',
        borderRadius: '12px',
        fontSize: '14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
      }}
    >
      <span>⚠️ {message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--bg-bubble-ai)',
            color: 'var(--text-main)',
            border: '1px solid var(--error-border)',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: '500',
            whiteSpace: 'nowrap',
          }}
        >
          Попробовать снова
        </button>
      )}
    </div>
  );
};
