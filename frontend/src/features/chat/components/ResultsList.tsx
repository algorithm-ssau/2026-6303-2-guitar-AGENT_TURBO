import React from 'react';
import { GuitarCard } from './GuitarCard';
import { GuitarResult } from '../types';

interface ResultsListProps {
    results: GuitarResult[];
}

export const ResultsList: React.FC<ResultsListProps> = ({ results }) => {
    if (!results || results.length === 0) {
        return null;
    }

    return (
        <div className="results-list" style={{ marginTop: '16px', width: '100%' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>
                Найдено {results.length} вариантов
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {results.map((result, index) => (
                    <GuitarCard key={result.id || result.listingUrl || index} result={result} />
                ))}
            </div>
        </div>
    );
};
