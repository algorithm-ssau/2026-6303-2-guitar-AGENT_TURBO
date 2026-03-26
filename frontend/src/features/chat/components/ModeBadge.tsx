import React from 'react';

interface ModeBadgeProps {
  mode?: 'search' | 'consultation';
}

/**
 * Бейдж режима работы агента
 * search → зелёный "Поиск"
 * consultation → синий "Консультация"
 */
export const ModeBadge: React.FC<ModeBadgeProps> = ({ mode }) => {
  if (!mode) return null;

  const isSearch = mode === 'search';

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: '10px',
        fontSize: '11px',
        fontWeight: 'bold',
        marginLeft: '6px',
        backgroundColor: isSearch ? '#d4edda' : '#cce5ff',
        color: isSearch ? '#155724' : '#004085',
      }}
    >
      {isSearch ? 'Поиск' : 'Консультация'}
    </span>
  );
};
