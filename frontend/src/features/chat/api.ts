import {
  ChatRequestSchema, ChatResponseSchema, ChatResponse,
  SessionsResponseSchema, HistoryResponseSchema, HistoryResponse,
  Session,
} from './types';

const API_BASE_URL = '/api';

/**
 * Отправляет сообщение пользователя на сервер
 */
export async function sendMessage(text: string): Promise<ChatResponse> {
  const parseResult = ChatRequestSchema.safeParse({ message: text });
  if (!parseResult.success) {
    const errorMessage = parseResult.error.errors?.[0]?.message || 'Невалидный запрос';
    throw new Error(errorMessage);
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
    }

    const data = await response.json();
    const parseResult = ChatResponseSchema.safeParse(data);
    if (!parseResult.success) {
      console.error('Невалидный ответ от сервера:', data);
      throw new Error('Сервер вернул невалидные данные');
    }

    return parseResult.data;
  } catch (error) {
    if (error instanceof Error) throw error;
    throw new Error('Неизвестная ошибка при подключении к серверу');
  }
}

/**
 * Получить список сессий
 */
export async function fetchSessions(): Promise<Session[]> {
  const response = await fetch(`${API_BASE_URL}/sessions`);
  if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

  const data = await response.json();
  const parseResult = SessionsResponseSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('Невалидный ответ сессий:', data);
    throw new Error('Сервер вернул невалидные данные');
  }

  return parseResult.data.sessions;
}

/**
 * Получить сообщения сессии
 */
export async function fetchSessionMessages(sessionId: number): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
  if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

  const data = await response.json();
  const parseResult = HistoryResponseSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('Невалидный ответ истории:', data);
    throw new Error('Сервер вернул невалидные данные');
  }

  return parseResult.data;
}

/**
 * Удалить сессию
 */
export async function deleteSession(sessionId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);
}

/**
 * Очистить всю историю
 */
export async function clearAllHistory(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/history`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);
}
