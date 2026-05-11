import React from 'react';
import { SearchParams } from '../types';
import './SearchParamsPanel.css';

interface Props {
  params?: SearchParams | null;
}

export const SearchParamsPanel: React.FC<Props> = ({ params }) => {
  if (!params) return null;

  const budget = formatBudget(params.priceMin, params.priceMax);
  const queries = (params.searchQueries || []).slice(0, 3).join(', ');
  const fields = [
    { label: 'Тип', value: params.type },
    { label: 'Бюджет', value: budget },
    { label: 'Бренд', value: params.brand },
    { label: 'Датчики', value: params.pickups },
    { label: 'Звук', value: params.sound },
    { label: 'Стиль', value: params.style },
    { label: 'Запросы', value: queries },
  ].filter(f => f.value);

  // Если все пусто - не рендерим
  if (fields.length === 0) return null;

  return (
    <div className="search-params-panel">
      <span className="search-params-panel__label">Я понял так:</span>
      
      {fields.map((f, i) => (
        <React.Fragment key={f.label}>
          <span className="search-params-panel__item">
            {f.label}: <strong>{f.value}</strong>
          </span>
          {i < fields.length - 1 && <span className="search-params-panel__separator">|</span>}
        </React.Fragment>
      ))}
    </div>
  );
};

function formatBudget(priceMin?: number | null, priceMax?: number | null): string | null {
  if (priceMin != null && priceMax != null) return `$${priceMin}-${priceMax}`;
  if (priceMax != null) return `до $${priceMax}`;
  if (priceMin != null) return `от $${priceMin}`;
  return null;
}
