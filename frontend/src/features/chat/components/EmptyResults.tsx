import React from 'react';

/**
 * Компонент пустого состояния
 * Показывается когда поиск не дал результатов
 */
export const EmptyResults: React.FC = () => {
  return (
    <div
      style={{
        padding: '24px 16px',
        textAlign: 'center',
        backgroundColor: 'var(--bg-bubble-ai)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        margin: '16px',
      }}
    >
      <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎸</div>
      <div
        style={{
          fontSize: '16px',
          fontWeight: '600',
          color: 'var(--text-main)',
          marginBottom: '8px',
        }}
      >
        По вашему запросу ничего не найдено
      </div>
      <div
        style={{
          fontSize: '14px',
          color: 'var(--text-dim)',
        }}
      >
        Попробуйте расширить бюджет или изменить параметры
      </div>
    </div>
  );
};
