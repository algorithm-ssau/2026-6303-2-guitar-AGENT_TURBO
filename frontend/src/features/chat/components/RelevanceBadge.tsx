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
            return { text: 'Лучшее совпадение', color: '#28a745', bgColor: '#d4edda' };
        }
        if (pos <= 3) {
            return { text: 'Отличный вариант', color: '#17a2b8', bgColor: '#d1ecf1' };
        }
        return { text: 'Подходит', color: '#6c757d', bgColor: '#e2e3e5' };
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
                border: `1px solid ${color}`,
            }}
        >
            {text}
        </span>
    );
};
