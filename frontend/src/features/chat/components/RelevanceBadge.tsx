import React from 'react';

interface RelevanceBadgeProps {
    position: number;
}

/**
 * Компонент бейджа релевантности.
 * 
 * Позиция 1: зелёный бейдж "Лучшее совпадение"
 * Позиции 2-3: голубой бейдж "Отличный вариант"
 * Позиции 4-5: серый бейдж "Подходит"
 */
export const RelevanceBadge: React.FC<RelevanceBadgeProps> = ({ position }) => {
    const getBadgeConfig = (pos: number) => {
        if (pos === 1) {
            return { text: 'Лучшее совпадение', color: 'var(--success-text)', bgColor: 'var(--success-bg)' };
        }
        if (pos <= 3) {
            return { text: 'Отличный вариант', color: 'var(--info-text)', bgColor: 'var(--info-bg)' };
        }
        return { text: 'Подходит', color: 'var(--text-subtle)', bgColor: 'var(--surface-hover)' };
    };

    const { text, color, bgColor } = getBadgeConfig(position);

    return (
        <span
            className="relevance-badge"
            style={{
                display: 'inline-block',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '600',
                color: color,
                backgroundColor: bgColor,
                border: '1px solid var(--border)',
            }}
        >
            {text}
        </span>
    );
};
