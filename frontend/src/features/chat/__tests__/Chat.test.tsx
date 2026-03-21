import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Chat } from '../components/Chat';
import { sendMessage } from '../api';

// Мок API функции
vi.mock('../api', () => ({
  sendMessage: vi.fn(),
}));

describe('Chat Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('должен рендериться с заголовком', () => {
    render(<Chat />);
    expect(screen.getByText('🎸 Guitar Agent')).toBeInTheDocument();
  });

  it('должен отображать введённый текст в поле ввода', () => {
    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    fireEvent.change(textarea, { target: { value: 'Тестовое сообщение' } });
    expect(textarea).toHaveValue('Тестовое сообщение');
  });

  it('должен отправлять сообщение и показывать ответ', async () => {
    (sendMessage as any).mockResolvedValue({ reply: 'Привет! Чем помочь?' });

    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    const button = screen.getByText('➤');

    fireEvent.change(textarea, { target: { value: 'Привет' } });
    fireEvent.click(button);

    // Проверка что сообщение пользователя отображается
    expect(screen.getByText('Привет')).toBeInTheDocument();

    // Проверка что показывается индикатор загрузки
    expect(screen.getByText('Агент подбирает гитары...')).toBeInTheDocument();

    // Проверка что ответ агента отображается
    await waitFor(() => {
      expect(screen.getByText('Привет! Чем помочь?')).toBeInTheDocument();
    });
  });

  it('должен показывать ошибку при неудачном запросе', async () => {
    (sendMessage as any).mockRejectedValue(new Error('Ошибка сети'));

    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    const button = screen.getByText('➤');

    fireEvent.change(textarea, { target: { value: 'Привет' } });
    fireEvent.click(button);

    // Проверка что ошибка отображается
    await waitFor(() => {
      expect(screen.getByText('⚠️ Ошибка сети')).toBeInTheDocument();
    });
  });

  it('должен очищать поле ввода после отправки', async () => {
    (sendMessage as any).mockResolvedValue({ reply: 'Ответ' });

    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    const button = screen.getByText('➤');

    fireEvent.change(textarea, { target: { value: 'Сообщение' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(textarea).toHaveValue('');
    });
  });

  it('должен блокировать кнопку во время загрузки', async () => {
    (sendMessage as any).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    const button = screen.getByText('➤');

    fireEvent.change(textarea, { target: { value: 'Привет' } });
    fireEvent.click(button);

    // Кнопка должна быть disabled во время загрузки
    expect(button).toBeDisabled();
  });

  it('должен отправлять по Enter без Shift', async () => {
    (sendMessage as any).mockResolvedValue({ reply: 'Ответ' });

    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');

    fireEvent.change(textarea, { target: { value: 'Привет' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false });

    // Проверяем что сообщение отправлено (появляется в списке)
    expect(screen.getByText('Привет')).toBeInTheDocument();
  });

  it('не должен отправлять пустое сообщение', () => {
    render(<Chat />);
    const button = screen.getByText('➤');

    // Кнопка должна быть disabled для пустого ввода
    expect(button).toBeDisabled();
  });
});
