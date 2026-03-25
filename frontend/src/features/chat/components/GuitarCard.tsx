import React from 'react';
import { GuitarResult } from '../types';

interface GuitarCardProps {
    result: GuitarResult;
    priceMin?: number;
    priceMax?: number;
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

export const GuitarCard: React.FC<GuitarCardProps> = ({ result, priceMin, priceMax }) => {
    const priceColor = getPriceColor(result.price ?? 0, priceMax);

    const priceColorStyle = {
        green: '#28a745',
        yellow: '#ffc107',
        red: '#dc3545',
    }[priceColor];

    return (
        <div
            className="guitar-card"
            style={{
                border: '1px solid #ccc',
                borderRadius: '8px',
                padding: '16px',
                margin: '8px 0',
                display: 'flex',
                alignItems: 'center',
                backgroundColor: '#fff'
            }}
        >
            {result.imageUrl && (
                <img
                    src={result.imageUrl}
                    alt={result.title}
                    style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '4px', marginRight: '16px' }}
                />
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
                        {result.price} {result.currency || 'USD'}
                    </div>
                )}
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
                    fontWeight: '500'
                }}
            >
                Смотреть
            </a>
        </div>
    );
};
