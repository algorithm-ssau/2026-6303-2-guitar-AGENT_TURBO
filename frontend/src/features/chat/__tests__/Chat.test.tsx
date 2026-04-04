import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Chat } from '../components/Chat';
import { useChat } from '../hooks/useChat';

// Мок хука useChat
vi.mock('../hooks/useChat', () => ({
  useChat: vi.fn(),
}));

describe('Chat Component', () => {
  const mockSendMessage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useChat as any).mockReturnValue({
      messages: [],
      isLoading: false,
      error: null,
      connectionStatus: 'connected',
      status: null,
      sendMessage: mockSendMessage,
    });
  });

  it('должен рендериться с заголовком', () => {
    render(<Chat />);
    expect(screen.getByText(/Guitar Agent/i)).toBeInTheDocument();
  });

  it('должен отображать введённый текст в поле ввода', () => {
    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    fireEvent.change(textarea, { target: { value: 'Тестовое сообщение' } });
    expect(textarea).toHaveValue('Тестовое сообщение');
  });

  it('должен отображать сообщения из хука useChat', () => {
    (useChat as any).mockReturnValue({
      messages: [
        { id: '1', role: 'user', content: 'Привет', timestamp: new Date() },
        { id: '2', role: 'agent', content: 'Привет! Чем помочь?', timestamp: new Date(), mode: 'consultation' }
      ],
      isLoading: false,
      error: null,
      connectionStatus: 'connected',
      status: null,
      sendMessage: mockSendMessage,
    });

    render(<Chat />);
    expect(screen.getByText('Привет')).toBeInTheDocument();
    expect(screen.getByText('Привет! Чем помочь?')).toBeInTheDocument();
  });

  it('Проверить отображение промежуточного статуса при isLoading', () => {
    (useChat as any).mockReturnValue({
      messages: [],
      isLoading: true,
      error: null,
      connectionStatus: 'connected',
      status: 'Ищу на Reverb...',
      sendMessage: mockSendMessage,
    });

    render(<Chat />);
    expect(screen.getByText('Ищу на Reverb...')).toBeInTheDocument();
  });

  it('Проверить отображение error через ErrorMessage', () => {
    (useChat as any).mockReturnValue({
      messages: [],
      isLoading: false,
      error: 'Ошибка сети',
      connectionStatus: 'connected',
      status: null,
      sendMessage: mockSendMessage,
    });

    render(<Chat />);
    expect(screen.getByText('⚠️ Ошибка сети')).toBeInTheDocument();
  });

  it('должен отправлять сообщение', () => {
    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Введите ваш запрос...');
    const button = screen.getByText('➤');

    fireEvent.change(textarea, { target: { value: 'Тест' } });
    fireEvent.click(button);

    expect(mockSendMessage).toHaveBeenCalledWith('Тест');
  });
});
