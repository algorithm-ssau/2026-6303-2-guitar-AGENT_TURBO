import { render, screen } from '@testing-library/react';
import { BudgetHint } from '../components/BudgetHint';

describe('BudgetHint', () => {
  test('renders priceMax correctly', () => {
    render(<BudgetHint priceMax={500} resultsCount={10} />);
    expect(screen.getByText(/Бюджет: до \$500/)).toBeInTheDocument();
    expect(screen.getByText('(10 результатов)')).toBeInTheDocument();
  });

  test('renders price range correctly', () => {
    render(<BudgetHint priceMin={300} priceMax={800} resultsCount={5} />);
    expect(screen.getByText(/\$300 – \$800/)).toBeInTheDocument();
    expect(screen.getByText('(5 результатов)')).toBeInTheDocument();
  });

  test('renders no budget correctly', () => {
    render(<BudgetHint resultsCount={3} />);
    expect(screen.getByText(/Бюджет: не ограничен/)).toBeInTheDocument();
    expect(screen.getByText('(3 результатов)')).toBeInTheDocument();
  });
});
