import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BudgetHint } from '../components/BudgetHint';

describe('BudgetHint компонент', () => {
  it('budgetMax=500 → "Бюджет: до $500"', () => {
    render(<BudgetHint budgetMax={500} resultsCount={3} />);
    expect(screen.getByText(/Бюджет: до \$500/)).toBeInTheDocument();
  });

  it('budgetMin=300, budgetMax=800 → "$300 – $800"', () => {
    render(<BudgetHint budgetMin={300} budgetMax={800} resultsCount={5} />);
    expect(screen.getByText(/\$300.*\$800/)).toBeInTheDocument();
  });

  it('без бюджета → "не ограничен"', () => {
    render(<BudgetHint resultsCount={2} />);
    expect(screen.getByText(/не ограничен/)).toBeInTheDocument();
  });

  it('показывает количество результатов', () => {
    render(<BudgetHint budgetMax={600} resultsCount={5} />);
    expect(screen.getByText(/5 результатов/)).toBeInTheDocument();
  });

  it('один результат → "1 результат"', () => {
    render(<BudgetHint budgetMax={600} resultsCount={1} />);
    expect(screen.getByText(/1 результат/)).toBeInTheDocument();
  });
});
