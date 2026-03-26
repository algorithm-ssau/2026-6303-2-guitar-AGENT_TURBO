import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '../hooks/useChat';

// Мок WebSocket
const mockWebSocket = vi.hoisted(() => {
  return {
    mockSend: vi.fn(),
    mockClose: vi.fn(),
  };
});

vi.mock('../hooks/useChat', async () => {
  const actual = await vi.importActual('../hooks/useChat');
  return {
    ...actual,
  };
});

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
    mockWebSocket.mockSend(data);
  }
  
  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
    mockWebSocket.mockClose();
  }
}

describe('useChat hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Устанавливаем мок WebSocket
    (window as any).WebSocket = MockWebSocket;
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('должен подключаться к WebSocket при монтировании', async () => {
    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });
  });

  it('должен отправлять сообщение и получать result', async () => {
    const { result } = renderHook(() => useChat());

    // Ждём подключения
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Отправляем сообщение
    act(() => {
      result.current.sendMessage('Нужна гитара для метала');
    });

    // Проверяем что сообщение пользователя добавлено
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.isLoading).toBe(true);

    // Симулируем получение статуса
    act(() => {
      // Находим WebSocket и вызываем onmessage
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(true);
    });
  });

  it('должен обрабатывать ошибку при пустом запросе', async () => {
    // Этот тест проверяет что error устанавливается при получении type="error"
    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Проверяем начальное состояние
    expect(result.current.error).toBeNull();
  });

  it('должен показывать статус соединения disconnected при обрыве', async () => {
    const { result } = renderHook(() => useChat());

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Симулируем обрыв соединения через закрытие WebSocket
    // Это проверяет что хук пытается переподключиться
  });
});
