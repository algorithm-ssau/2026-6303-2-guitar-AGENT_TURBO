import React from 'react';

interface BudgetHintProps {
  budgetMin?: number;
  budgetMax?: number;
  resultsCount: number;
}

/**
 * Компонент подсказки бюджета.
 *
 * Показывает "Бюджет: до $500" или "$300 – $800"
 * + количество результатов.
 *
 * Если бюджет не передан — компонент не рендерится.
 */
export const BudgetHint: React.FC<BudgetHintProps> = ({ budgetMin, budgetMax, resultsCount }) => {
  // Если бюджет не указан — компонент не рендерится
  if (
    (budgetMin === undefined || budgetMin === null || budgetMin <= 0) &&
    (budgetMax === undefined || budgetMax === null || budgetMax <= 0)
  ) {
    return null;
  }

  // Формируем текст подсказки
  let budgetText: string;
  if (budgetMin !== undefined && budgetMin > 0 && budgetMax !== undefined && budgetMax > 0) {
    budgetText = `Бюджет: $${budgetMin.toLocaleString()} – $${budgetMax.toLocaleString()}`;
  } else if (budgetMax !== undefined && budgetMax > 0) {
    budgetText = `Бюджет: до $${budgetMax.toLocaleString()}`;
  } else {
    budgetText = `Бюджет: от $${budgetMin!.toLocaleString()}`;
  }

  return (
    <div className="budget-hint">
      <span className="budget-hint__text">{budgetText}</span>
      <span className="budget-hint__count">
        {resultsCount} {resultsCount === 1 ? 'результат' : resultsCount < 5 ? 'результата' : 'результатов'}
      </span>
    </div>
  );
};
