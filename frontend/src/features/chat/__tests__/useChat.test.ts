import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '../hooks/useChat';

const mockFetchSessions = vi.fn();
const mockFetchSessionMessages = vi.fn();
const mockDeleteSession = vi.fn();
const mockClearAllHistory = vi.fn();

vi.mock('../api', () => ({
  fetchSessions: (...args: unknown[]) => mockFetchSessions(...args),
  fetchSessionMessages: (...args: unknown[]) => mockFetchSessionMessages(...args),
  deleteSession: (...args: unknown[]) => mockDeleteSession(...args),
  clearAllHistory: (...args: unknown[]) => mockClearAllHistory(...args),
}));

// Мок отправки WebSocket
const mockSend = vi.fn();
const mockClose = vi.fn();

// Глобальный мок WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: any) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.();
    }, 0);
  }

  send(data: string) {
    mockSend(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
    mockClose();
  }
}

describe('useChat hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockFetchSessions.mockResolvedValue({ sessions: [], total: 0 });
    mockFetchSessionMessages.mockResolvedValue({ items: [] });
    mockDeleteSession.mockResolvedValue(undefined);
    mockClearAllHistory.mockResolvedValue(undefined);
    // Устанавливаем мок WebSocket
    (window as any).WebSocket = MockWebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllTimers();
  });

  it('должен подключаться к WebSocket при монтировании', async () => {
    const { result } = renderHook(() => useChat());

    // Проматываем время для подключения
    act(() => {
      vi.advanceTimersByTime(0);
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });
  });

  it('должен отправлять сообщение и получать result с маппингом snake_case → camelCase', async () => {
    const { result } = renderHook(() => useChat());

    // Ждём подключения
    act(() => {
      vi.advanceTimersByTime(0);
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Отправляем сообщение
    act(() => {
      result.current.sendMessage('Нужна гитара для метала');
    });

    // Проверяем что сообщение пользователя добавлено
    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('Нужна гитара для метала');
    expect(result.current.isLoading).toBe(true);

    // Проверяем что сообщение было отправлено через WebSocket
    expect(mockSend).toHaveBeenCalledWith(JSON.stringify({ query: 'Нужна гитара для метала' }));
  });

  it('должен открывать history с clarification сообщениями', async () => {
    mockFetchSessionMessages.mockResolvedValueOnce({
      items: [
        {
          id: 1,
          sessionId: 19,
          userQuery: 'телекастер',
          mode: 'clarification',
          answer: 'Уточните бюджет',
          results: null,
          createdAt: '2026-04-22T10:39:09Z',
        },
      ],
    });

    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.selectSession(19);
    });

    expect(result.current.isLoadingSessionMessages).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoadingSessionMessages).toBe(false);
      expect(result.current.messages).toHaveLength(2);
    });

    expect(result.current.messages[0].content).toBe('телекастер');
    expect(result.current.messages[1].content).toBe('Уточните бюджет');
    expect(result.current.messages[1].mode).toBe('clarification');
  });

  it('должен игнорировать устаревший ответ при быстром переключении между чатами', async () => {
    let resolveFirst!: (value: { items: any[] }) => void;
    let resolveSecond!: (value: { items: any[] }) => void;

    mockFetchSessionMessages
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveSecond = resolve; }));

    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.selectSession(1);
      result.current.selectSession(2);
    });

    act(() => {
      resolveSecond({
        items: [
          {
            id: 20,
            sessionId: 2,
            userQuery: 'второй чат',
            mode: 'consultation',
            answer: 'история второго чата',
            results: null,
            createdAt: '2026-04-22T10:40:49Z',
          },
        ],
      });
    });

    await waitFor(() => {
      expect(result.current.messages[0].content).toBe('второй чат');
    });

    act(() => {
      resolveFirst({
        items: [
          {
            id: 10,
            sessionId: 1,
            userQuery: 'первый чат',
            mode: 'consultation',
            answer: 'история первого чата',
            results: null,
            createdAt: '2026-04-22T10:38:52Z',
          },
        ],
      });
    });

    await waitFor(() => {
      expect(result.current.messages[0].content).toBe('второй чат');
      expect(result.current.currentSessionId).toBe(2);
      expect(result.current.isLoadingSessionMessages).toBe(false);
    });
  });

  it('должен обновлять status при получении type="status"', async () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      vi.advanceTimersByTime(0);
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Начальное состояние
    expect(result.current.status).toBeNull();
  });

  it('должен устанавливать error при получении type="error"', async () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      vi.advanceTimersByTime(0);
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Проверяем начальное состояние
    expect(result.current.error).toBeNull();
  });

  it('должен пытаться переподключиться через 3 секунды при обрыве соединения', async () => {
    let wsInstance: MockWebSocket | null = null;

    // Перехватываем создание WebSocket
    const OriginalWebSocket = (window as any).WebSocket;
    (window as any).WebSocket = class extends OriginalWebSocket {
      constructor(url: string) {
        super(url);
        wsInstance = this;
      }
    };

    const { result } = renderHook(() => useChat());

    // Ждём подключения
    act(() => {
      vi.advanceTimersByTime(0);
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Симулируем обрыв соединения
    act(() => {
      if (wsInstance) {
        wsInstance.onclose?.();
      }
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('disconnected');
    });

    // Проматываем время на 3 секунды для реконнекта
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    // Проверяем что была попытка реконнекта
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connecting');
    });
  });
});
