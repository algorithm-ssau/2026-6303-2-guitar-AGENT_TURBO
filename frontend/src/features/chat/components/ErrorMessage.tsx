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
        backgroundColor: '#f8d7da',
        color: '#721c24',
        borderRadius: '8px',
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
            backgroundColor: '#721c24',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
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
