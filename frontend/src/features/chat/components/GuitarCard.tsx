import React from 'react';
import { GuitarResult } from '../types';

interface GuitarCardProps {
    result: GuitarResult;
}

export const GuitarCard: React.FC<GuitarCardProps> = ({ result }) => {
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
                    <div style={{ fontWeight: 'bold', color: '#28a745', fontSize: '15px' }}>
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
