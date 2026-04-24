import { act, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Toast } from '../Toast';

describe('Toast компонент', () => {
  it('рендерит текст тоста', () => {
    render(<Toast text="Hello" type="success" onClose={vi.fn()} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('вызывает onClose после таймаута', () => {
    vi.useFakeTimers();
    const onClose = vi.fn();

    render(<Toast text="Hello" type="info" onClose={onClose} />);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(onClose).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});
