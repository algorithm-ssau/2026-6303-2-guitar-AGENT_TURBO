import React from 'react';

interface BudgetHintProps {
  priceMin?: number;
  priceMax?: number;
  resultsCount: number;
}

export const BudgetHint: React.FC<BudgetHintProps> = ({
  priceMin,
  priceMax,
  resultsCount,
}) => {
  const getBudgetText = () => {
    if (!priceMin && !priceMax) {
      return 'не ограничен';
    }
    if (priceMin !== undefined && priceMax !== undefined) {
      return `$${priceMin} – $${priceMax}`;
    }
    if (priceMax !== undefined) {
      return `до $${priceMax}`;
    }
    if (priceMin !== undefined) {
      return `от $${priceMin}`;
    }
    return 'не ограничен';
  };

  return (
    <div className="budget-hint text-sm text-gray-600 mb-2">
      <span>Бюджет: {getBudgetText()}</span>
      <span className="ml-2">({resultsCount} результатов)</span>
    </div>
  );
};
