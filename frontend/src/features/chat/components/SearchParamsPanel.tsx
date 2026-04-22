import React from 'react';
import { ParsedParams } from '../types';

interface Props {
  params?: ParsedParams | null;
}

export const SearchParamsPanel: React.FC<Props> = ({ params }) => {
  if (!params) return null;

  // Формируем непустые поля
  const fields =[
    { label: 'Тип', value: params.type },
    { label: 'Бюджет', value: params.budget },
    { label: 'Бренд', value: params.brand },
    { label: 'Стиль', value: params.tags && params.tags.length > 0 ? params.tags.join(', ') : null }
  ].filter(f => f.value);

  // Если все пусто - не рендерим
  if (fields.length === 0) return null;

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary, #f8f9fa)',
      padding: '8px 12px',
      borderRadius: '8px',
      border: '1px solid #dee2e6',
      fontSize: '13px',
      marginBottom: '12px',
      display: 'flex',
      flexWrap: 'wrap',
      gap: '4px',
      alignItems: 'center',
      color: '#495057'
    }}>
      <span style={{ color: 'var(--accent, #007bff)', marginRight: '4px' }}>🎯</span>
      <span style={{ fontWeight: 500, marginRight: '4px' }}>Я понял так:</span>
      
      {fields.map((f, i) => (
        <React.Fragment key={f.label}>
          <span>{f.label}: <strong>{f.value}</strong></span>
          {i < fields.length - 1 && <span style={{ margin: '0 4px', color: '#adb5bd' }}>|</span>}
        </React.Fragment>
      ))}
    </div>
  );
};