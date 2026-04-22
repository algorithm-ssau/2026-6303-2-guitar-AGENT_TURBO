import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
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
    vi.useFakeTimers();
    (useChat as any).mockReturnValue({
      messages: [],
      isLoading: false,
      error: null,
      connectionStatus: 'connected',
      status: null,
      sendMessage: mockSendMessage,
      sessions: [],
      isLoadingSessions: false,
      latestLiveMessageId: null,
      currentSessionId: null,
      selectSession: vi.fn(),
      newChat: vi.fn(),
      deleteSession: vi.fn(),
      clearHistory: vi.fn(),
      loadMoreSessions: vi.fn(),
      hasMoreSessions: false,
      isLoadingMoreSessions: false,
      isLoadingSessionMessages: false,
    });
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('должен рендериться с заголовком', () => {
    render(<Chat />);
    expect(screen.getByText(/REVERB AGENT/i)).toBeInTheDocument();
  });

  it('должен отображать введённый текст в поле ввода', () => {
    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Опишите звук или модель гитары...');
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
      sessions: [],
      isLoadingSessions: false,
      latestLiveMessageId: null,
      currentSessionId: null,
      selectSession: vi.fn(),
      newChat: vi.fn(),
      deleteSession: vi.fn(),
      clearHistory: vi.fn(),
      loadMoreSessions: vi.fn(),
      hasMoreSessions: false,
      isLoadingMoreSessions: false,
      isLoadingSessionMessages: false,
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
      sessions: [],
      isLoadingSessions: false,
      latestLiveMessageId: null,
      currentSessionId: null,
      selectSession: vi.fn(),
      newChat: vi.fn(),
      deleteSession: vi.fn(),
      clearHistory: vi.fn(),
      loadMoreSessions: vi.fn(),
      hasMoreSessions: false,
      isLoadingMoreSessions: false,
      isLoadingSessionMessages: false,
    });

    render(<Chat />);
    expect(screen.getByText('Ищу на Reverb...')).toBeInTheDocument();
    expect(screen.getByText('Думаю над ответом')).toBeInTheDocument();
  });

  it('Проверить отображение error через ErrorMessage', () => {
    (useChat as any).mockReturnValue({
      messages: [],
      isLoading: false,
      error: 'Ошибка сети',
      connectionStatus: 'connected',
      status: null,
      sendMessage: mockSendMessage,
      sessions: [],
      isLoadingSessions: false,
      latestLiveMessageId: null,
      currentSessionId: null,
      selectSession: vi.fn(),
      newChat: vi.fn(),
      deleteSession: vi.fn(),
      clearHistory: vi.fn(),
      loadMoreSessions: vi.fn(),
      hasMoreSessions: false,
      isLoadingMoreSessions: false,
      isLoadingSessionMessages: false,
    });

    render(<Chat />);
    expect(screen.getByText('⚠️ Ошибка сети')).toBeInTheDocument();
  });

  it('должен отправлять сообщение', () => {
    render(<Chat />);
    const textarea = screen.getByPlaceholderText('Опишите звук или модель гитары...');
    const button = screen.getByText('Отправить');

    fireEvent.change(textarea, { target: { value: 'Тест' } });
    fireEvent.click(button);

    expect(mockSendMessage).toHaveBeenCalledWith('Тест');
  });

  it('скрывает transient состояние после завершения reveal', () => {
    (useChat as any).mockReturnValue({
      messages: [
        { id: '1', role: 'user', content: 'Привет', timestamp: new Date() },
        { id: '2', role: 'agent', content: 'Готовый ответ', timestamp: new Date(), mode: 'consultation' }
      ],
      isLoading: false,
      error: null,
      connectionStatus: 'connected',
      status: null,
      sendMessage: mockSendMessage,
      sessions: [],
      isLoadingSessions: false,
      latestLiveMessageId: '2',
      currentSessionId: null,
      selectSession: vi.fn(),
      newChat: vi.fn(),
      deleteSession: vi.fn(),
      clearHistory: vi.fn(),
      loadMoreSessions: vi.fn(),
      hasMoreSessions: false,
      isLoadingMoreSessions: false,
      isLoadingSessionMessages: false,
    });

    render(<Chat />);

    act(() => {
      vi.runAllTimers();
    });

    expect(screen.getByText('Готовый ответ')).toBeInTheDocument();
    expect(screen.getByText('📋 Копировать')).toBeInTheDocument();
  });
});
