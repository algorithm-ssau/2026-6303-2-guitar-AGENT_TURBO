import React from 'react';
import './SkeletonCard.css';

interface SkeletonCardProps {
    count?: number;
}

/**
 * Анимированный скелетон карточки гитары
 * Повторяет форму GuitarCard: картинка-прямоугольник, 2 строки текста, цена
 */
export const SkeletonCard: React.FC<SkeletonCardProps> = ({ count = 1 }) => {
    const skeletons = Array.from({ length: count }, (_, i) => i);

    return (
        <>
            {skeletons.map((index) => (
                <div key={index} className="skeleton-card">
                    <div className="skeleton-card__image" />
                    <div className="skeleton-card__title" />
                    <div className="skeleton-card__title skeleton-card__title--line2" />
                    <div className="skeleton-card__price" />
                </div>
            ))}
        </>
    );
};
