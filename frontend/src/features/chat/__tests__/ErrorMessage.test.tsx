import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorMessage } from '../components/ErrorMessage';

describe('ErrorMessage компонент', () => {
  it('должен рендерить текст ошибки', () => {
    render(<ErrorMessage message="Ошибка сети" />);
    
    expect(screen.getByText('⚠️ Ошибка сети')).toBeInTheDocument();
  });

  it('должен вызывать onRetry при клике на кнопку', () => {
    const onRetry = vi.fn();
    render(<ErrorMessage message="Ошибка сети" onRetry={onRetry} />);
    
    const button = screen.getByText('Попробовать снова');
    fireEvent.click(button);
    
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('не должен рендерить кнопку без onRetry', () => {
    render(<ErrorMessage message="Ошибка сети" />);
    
    expect(screen.queryByText('Попробовать снова')).not.toBeInTheDocument();
  });
});
