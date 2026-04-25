import {
  ChatRequestSchema, ChatResponseSchema, ChatResponse,
  SessionsResponseSchema, HistoryResponseSchema, HistoryResponse,
  Session, ParsedParams
} from './types';
import { z } from 'zod';

const API_BASE_URL = '/api';

interface ApiError extends Error {
  status?: number;
}

function createApiError(status: number, fallbackMessage: string, detail?: string): ApiError {
  const error = new Error(detail || fallbackMessage) as ApiError;
  error.status = status;
  return error;
}

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
 * Получить список сессий с пагинацией
 */
export async function fetchSessions(
  offset = 0,
  limit = 20,
): Promise<{ sessions: Session[]; total: number }> {
  const response = await fetch(
    `${API_BASE_URL}/sessions?offset=${offset}&limit=${limit}`,
  );
  if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

  const data = await response.json();
  const parseResult = SessionsResponseSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('Невалидный ответ сессий:', data);
    throw new Error('Сервер вернул невалидные данные');
  }

  return { sessions: parseResult.data.sessions, total: parseResult.data.total };
}

/**
 * Получить сообщения сессии
 */
export async function fetchSessionMessages(sessionId: number): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw createApiError(response.status, `Ошибка сервера: ${response.status}`, errorData.detail);
  }

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


export const ParsedParamsSchema = z.object({
  type: z.string().optional().nullable(),
  budget: z.string().optional().nullable(),
  brand: z.string().optional().nullable(),
  tags: z.array(z.string()).default([]),
});

/**
 * Парсинг параметров через backend без LLM
 */
export async function parseQuery(query: string): Promise<any> {
  const response = await fetch('/api/query/parse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  
  if (!response.ok) {
    throw new Error('Ошибка парсинга');
  }
  
  const data = await response.json();
  return ParsedParamsSchema.parse(data);
}

/**
 * Отправляет фидбек по гитаре
 */
export async function submitFeedback(
  sessionId: number, 
  guitarId: string, 
  rating: 'up' | 'down', 
  query?: string
): Promise<{ id: number }> {
  const response = await fetch(`${API_BASE_URL}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, guitar_id: guitarId, rating, query }),
  });
  if (!response.ok) throw new Error('Ошибка отправки фидбека');
  return response.json();
}