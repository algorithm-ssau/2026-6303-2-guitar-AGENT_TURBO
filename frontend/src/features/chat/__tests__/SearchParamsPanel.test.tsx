import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom'; 
import { describe, it, expect } from 'vitest';
import { SearchParamsPanel } from '../components/SearchParamsPanel';

describe('SearchParamsPanel', () => {
  it('renders non-empty params', () => {
    render(<SearchParamsPanel params={{ type: 'Stratocaster', budget: '≤ $500' }} />);
    expect(screen.getByText(/Stratocaster/i)).toBeInTheDocument();
    expect(screen.getByText(/≤ \$500/i)).toBeInTheDocument();
  });

  it('does not render when params are empty', () => {
    const { container } = render(<SearchParamsPanel params={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it('does not render when params is null', () => {
    const { container } = render(<SearchParamsPanel params={null} />);
    expect(container.firstChild).toBeNull();
  });
});