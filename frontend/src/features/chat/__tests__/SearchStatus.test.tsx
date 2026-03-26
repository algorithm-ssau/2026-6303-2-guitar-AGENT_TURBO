import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SearchStatus } from '../components/SearchStatus';

describe('SearchStatus компонент', () => {
  it('должен показывать "Ищем на Reverb..." при isLoading=true', () => {
    render(<SearchStatus isLoading={true} />);

    expect(screen.getByText(/Ищем на Reverb/i)).toBeInTheDocument();
  });

  it('должен показывать "5 вариантов" при resultsCount=5', () => {
    render(<SearchStatus isLoading={false} resultsCount={5} />);

    expect(screen.getByText(/5 вариантов/i)).toBeInTheDocument();
  });

  it('должен показывать "Ничего не найдено" при resultsCount=0', () => {
    render(<SearchStatus isLoading={false} resultsCount={0} />);

    expect(screen.getByText(/Ничего не найдено/i)).toBeInTheDocument();
  });

  it('должен показывать "1 вариант" при resultsCount=1', () => {
    render(<SearchStatus isLoading={false} resultsCount={1} />);

    expect(screen.getByText(/1 вариант/i)).toBeInTheDocument();
  });

  it('должен показывать "2 варианта" при resultsCount=2', () => {
    render(<SearchStatus isLoading={false} resultsCount={2} />);

    expect(screen.getByText(/2 варианта/i)).toBeInTheDocument();
  });

  it('должен показывать "10 вариантов" при resultsCount=10', () => {
    render(<SearchStatus isLoading={false} resultsCount={10} />);

    expect(screen.getByText(/10 вариантов/i)).toBeInTheDocument();
  });

  it('должен показывать "11 вариантов" при resultsCount=11', () => {
    render(<SearchStatus isLoading={false} resultsCount={11} />);

    expect(screen.getByText(/11 вариантов/i)).toBeInTheDocument();
  });

  it('должен показывать "21 вариант" при resultsCount=21', () => {
    render(<SearchStatus isLoading={false} resultsCount={21} />);

    expect(screen.getByText(/21 вариант/i)).toBeInTheDocument();
  });

  it('должен показывать "22 варианта" при resultsCount=22', () => {
    render(<SearchStatus isLoading={false} resultsCount={22} />);

    expect(screen.getByText(/22 варианта/i)).toBeInTheDocument();
  });

  it('должен возвращать null при isLoading=false и resultsCount=undefined', () => {
    const { container } = render(
      <SearchStatus isLoading={false} resultsCount={undefined} />
    );

    expect(container.firstChild).toBeNull();
  });
});
