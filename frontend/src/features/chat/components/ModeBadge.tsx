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
    search: { bg: 'var(--success-bg)', text: 'var(--success-text)', label: 'Поиск' },
    consultation: { bg: 'var(--info-bg)', text: 'var(--info-text)', label: 'Консультация' },
    clarification: { bg: 'var(--warning-bg)', text: 'var(--warning-text)', label: 'Уточнение' },
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
