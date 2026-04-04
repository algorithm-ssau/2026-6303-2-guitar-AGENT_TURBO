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
 * Определяет цвет ценовой метки на основе бюджета
 * - Зелёный: цена в бюджете (≤ priceMax)
 * - Жёлтый: превышает до 20%
 * - Красный: превышает более 20%
 */
const getPriceColor = (price: number, priceMax?: number): 'green' | 'yellow' | 'red' => {
    if (priceMax === undefined || priceMax === null) {
        return 'green'; // Нет бюджета — считаем в бюджете
    }

    if (price <= priceMax) {
        return 'green';
    }

    const threshold20Percent = priceMax * 1.2;

    if (price <= threshold20Percent) {
        return 'yellow';
    }

    return 'red';
};

export const GuitarCard: React.FC<GuitarCardProps> = ({ result, priceMin, priceMax, position }) => {
    const priceColor = getPriceColor(result.price ?? 0, priceMax);
    const [imageError, setImageError] = React.useState(false);
    const [isHovered, setIsHovered] = React.useState(false);

    const priceColorStyle = {
        green: '#28a745',
        yellow: '#ffc107',
        red: '#dc3545',
    }[priceColor];

    const hasImage = result.imageUrl && !imageError;

    // Форматируем цену: "$499" вместо "499 USD"
    const formatPrice = (price: number, currency: string | undefined): string => {
        if (currency === 'USD') {
            return `$${price}`;
        }
        return `${price} ${currency || 'USD'}`;
    };

    // Placeholder для изображения
    const imagePlaceholder = (
        <div
            style={{
                width: '80px',
                height: '80px',
                backgroundColor: '#ccc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '4px',
                fontSize: '12px',
                color: '#666',
                flexShrink: 0,
            }}
        >
            Нет фото
        </div>
    );

    return (
        <div
            className="guitar-card"
            style={{
                border: '1px solid #ccc',
                borderRadius: '8px',
                padding: '16px',
                margin: '8px 0',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                backgroundColor: '#fff',
                transition: 'box-shadow 0.2s ease',
                boxShadow: isHovered ? '0 4px 12px rgba(0, 0, 0, 0.15)' : 'none',
            }}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {hasImage ? (
                    <a
                        href={result.listingUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <img
                            src={result.imageUrl}
                            alt={result.title}
                            onError={() => setImageError(true)}
                            style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '4px', display: 'block' }}
                        />
                    </a>
                ) : (
                    imagePlaceholder
                )}
                <div style={{ flex: 1 }}>
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>{result.title}</h4>
                    {result.price !== undefined && (
                        <div style={{
                            fontWeight: 'bold',
                            color: priceColorStyle,
                            fontSize: '15px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}>
                            <span
                                title={
                                    priceColor === 'green'
                                        ? 'В бюджете'
                                        : priceColor === 'yellow'
                                        ? 'Превышает до 20%'
                                        : 'Превышает более 20%'
                                }
                                style={{
                                    display: 'inline-block',
                                    width: '10px',
                                    height: '10px',
                                    borderRadius: '50%',
                                    backgroundColor: priceColorStyle
                                }}
                            />
                            {formatPrice(result.price, result.currency)}
                        </div>
                    )}
                </div>
                {position && <RelevanceBadge position={position} />}
            </div>
            <a
                href={result.listingUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                    padding: '8px 16px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '4px',
                    fontWeight: '500',
                    textAlign: 'center'
                }}
            >
                Смотреть
            </a>
        </div>
    );
};
