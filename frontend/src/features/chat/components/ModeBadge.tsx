import React from 'react';

interface ModeBadgeProps {
  mode?: 'search' | 'consultation' | 'clarification';
}

/**
 * Бейдж режима работы агента
 * search → зелёный "Поиск"
 * consultation → синий "Консультация"
 * clarification → оранжевый "Уточнение"
 */
export const ModeBadge: React.FC<ModeBadgeProps> = ({ mode }) => {
  if (!mode) return null;

  const colorMap = {
    search: { bg: '#d4edda', text: '#155724', label: 'Поиск' },
    consultation: { bg: '#cce5ff', text: '#004085', label: 'Консультация' },
    clarification: { bg: '#fff3cd', text: '#856404', label: 'Уточнение' },
  };

  const colors = colorMap[mode];

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: '10px',
        fontSize: '11px',
        fontWeight: 'bold',
        marginLeft: '6px',
        backgroundColor: colors.bg,
        color: colors.text,
      }}
    >
      {colors.label}
    </span>
  );
};
