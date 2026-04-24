import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConfirmDialog } from '../ConfirmDialog';

describe('ConfirmDialog компонент', () => {
  it('не отображается при isOpen=false', () => {
    render(
      <ConfirmDialog
        isOpen={false}
        title="Удалить?"
        message="Подтвердите действие"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('отображает диалог при isOpen=true', () => {
    render(
      <ConfirmDialog
        isOpen
        title="Удалить?"
        message="Подтвердите действие"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Удалить?')).toBeInTheDocument();
    expect(screen.getByText('Подтвердите действие')).toBeInTheDocument();
  });

  it('вызывает callbacks кнопок', () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <ConfirmDialog
        isOpen
        title="Удалить?"
        message="Подтвердите действие"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );

    fireEvent.click(screen.getByText('Отмена'));
    fireEvent.click(screen.getByText('Да'));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
