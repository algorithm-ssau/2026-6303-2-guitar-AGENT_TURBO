import React from 'react';
import { GuitarCard } from './GuitarCard';
import { GuitarResult } from '../types';
import './ResultsList.css';

interface ResultsListProps {
    results: GuitarResult[];
    priceMin?: number;
    priceMax?: number;
}

export const ResultsList: React.FC<ResultsListProps> = ({ results, priceMin, priceMax }) => {
    if (!results || results.length === 0) {
        return null;
    }

    return (
        <div className="results-list">
            <h3 className="results-list__title">
                Лучшие совпадения
            </h3>
            <div className="results-list__grid">
                {results.map((result, index) => (
                    <GuitarCard
                        key={result.id || result.listingUrl || index}
                        result={result}
                        priceMin={priceMin}
                        priceMax={priceMax}
                    />
                ))}
            </div>
        </div>
    );
};
