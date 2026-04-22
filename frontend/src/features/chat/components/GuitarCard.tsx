import React from 'react';
import { GuitarResult } from '../types';
import { RelevanceBadge } from './RelevanceBadge';

interface GuitarCardProps {
    result: GuitarResult;
    priceMin?: number;
    priceMax?: number;
    position?: number;
}

/**
 * Определяет цвет цены на основе бюджета
 * - Зелёный: цена в бюджете (≤ priceMax)
 * - Жёлтый: превышает до 20%
 * - Красный: превышает более 20%
 */
const getPriceColor = (price: number, priceMax?: number): string => {
    if (priceMax === undefined || priceMax === null) {
        return 'var(--success)';
    }

    if (price <= priceMax) {
        return 'var(--success)';
    }

    const threshold20Percent = priceMax * 1.2;

    if (price <= threshold20Percent) {
        return 'var(--warning)';
    }

    return 'var(--danger)';
};

/** Форматируем цену: "$499" вместо "499 USD" */
const formatPrice = (price: number, currency: string | undefined): string => {
    if (currency === 'USD') {
        return `$${price}`;
    }
    return `${price} ${currency || 'USD'}`;
};

export const GuitarCard: React.FC<GuitarCardProps> = ({ result, priceMin, priceMax, position }) => {
    const [imageError, setImageError] = React.useState(false);
    const hasImage = result.imageUrl && !imageError;
    const priceColor = getPriceColor(result.price ?? 0, priceMax);

    // Карточка дороже бюджета более чем на 20% — приглушённый стиль
    const isOverBudget = priceMax !== undefined && priceMax !== null
        && result.price !== undefined
        && result.price > priceMax * 1.2;

    return (
        <div
            className="guitar-card-wrapper"
            style={{
                position: 'relative',
                opacity: isOverBudget ? 0.6 : 1,
                transition: 'opacity 0.2s',
            }}
        >
            {/* Номер позиции и бейдж релевантности */}
            {position !== undefined && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px',
                }}>
                    <span style={{
                        fontSize: '16px',
                        fontWeight: 'bold',
                        color: 'var(--text-dim)',
                    }}>
                        #{position}
                    </span>
                    <RelevanceBadge position={position} />
                </div>
            )}

            <a
                href={result.listingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="guitar-card"
                style={{
                    display: 'block',
                    textDecoration: 'none',
                    color: 'inherit',
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '12px',
                    padding: '12px',
                    transition: 'border-color 0.2s, transform 0.2s',
                    cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent)';
                    e.currentTarget.style.transform = 'translateY(-3px)';
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border)';
                    e.currentTarget.style.transform = 'translateY(0)';
                }}
            >
                {/* Изображение / плейсхолдер */}
                <div
                    style={{
                        height: '100px',
                        backgroundColor: hasImage ? 'transparent' : 'var(--code-bg)',
                        borderRadius: '8px',
                        marginBottom: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden',
                    }}
                >
                    {hasImage ? (
                        <img
                            src={result.imageUrl}
                            alt={result.title}
                            onError={() => setImageError(true)}
                            style={{
                                width: '100%',
                                height: '100%',
                                objectFit: 'cover',
                                borderRadius: '8px',
                                display: 'block',
                            }}
                        />
                    ) : (
                        <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>PHOTO</span>
                    )}
                </div>

                {/* Название */}
                <div style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    marginBottom: '4px',
                    color: 'var(--text-main)',
                    lineHeight: 1.3,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                }}>
                    {result.title}
                </div>

                {/* Цена */}
                {result.price !== undefined && (
                    <div style={{
                        color: priceColor,
                        fontWeight: 700,
                        fontSize: '14px',
                        marginTop: '5px',
                    }}>
                        {formatPrice(result.price, result.currency)}
                    </div>
                )}
            </a>
        </div>
    );
};
