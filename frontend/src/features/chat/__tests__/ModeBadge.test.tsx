import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ModeBadge } from '../components/ModeBadge';

describe('ModeBadge компонент', () => {
  it('mode="search" → текст "Поиск"', () => {
    render(<ModeBadge mode="search" />);
    expect(screen.getByText('Поиск')).toBeInTheDocument();
  });

  it('mode="consultation" → текст "Консультация"', () => {
    render(<ModeBadge mode="consultation" />);
    expect(screen.getByText('Консультация')).toBeInTheDocument();
  });

  it('mode="clarification" → текст "Уточнение"', () => {
    render(<ModeBadge mode="clarification" />);
    expect(screen.getByText('Уточнение')).toBeInTheDocument();
  });

  it('без mode → бейдж не показывается', () => {
    const { container } = render(<ModeBadge />);
    expect(container.firstChild).toBeNull();
  });
});
