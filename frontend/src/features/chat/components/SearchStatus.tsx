import React from 'react';

interface SearchStatusProps {
  isLoading: boolean;
  resultsCount?: number;
  mode?: string;
}

// Стили для анимации пульсации
const pulseAnimation = `
  @keyframes pulse {
    0% {
      opacity: 0.6;
    }
    50% {
      opacity: 1;
    }
    100% {
      opacity: 0.6;
    }
  }
`;

/**
 * Компонент отображения статуса поиска на Reverb
 */
export const SearchStatus: React.FC<SearchStatusProps> = ({
  isLoading,
  resultsCount,
  mode = 'search',
}) => {
  // Функция склонения слов: 1 вариант, 2 варианта, 5 вариантов
  const pluralize = (count: number, one: string, two: string, five: string): string => {
    const n = count % 100;
    if (n >= 11 && n <= 19) {
      return five;
    }
    const i = n % 10;
    if (i === 1) {
      return one;
    }
    if (i >= 2 && i <= 4) {
      return two;
    }
    return five;
  };

  // Состояние загрузки
  if (isLoading) {
    return (
      <>
        <style>{pulseAnimation}</style>
        <div
          style={{
            padding: '12px',
            textAlign: 'center',
            color: '#666',
            fontStyle: 'italic',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              animation: 'pulse 1.5s ease-in-out infinite',
            }}
          >
            🔍 Ищем на Reverb...
          </span>
        </div>
      </>
    );
  }

  // Состояние с результатами
  if (resultsCount !== undefined) {
    if (resultsCount === 0) {
      return (
        <div
          style={{
            padding: '12px',
            textAlign: 'center',
            color: '#999',
            fontStyle: 'italic',
          }}
        >
          ❌ Ничего не найдено
        </div>
      );
    }

    const word = pluralize(resultsCount, 'вариант', 'варианта', 'вариантов');
    return (
      <div
        style={{
          padding: '12px',
          textAlign: 'center',
          color: '#28a745',
          fontWeight: 'bold',
        }}
      >
        ✅ Найдено {resultsCount} {word}
      </div>
    );
  }

  return null;
};
