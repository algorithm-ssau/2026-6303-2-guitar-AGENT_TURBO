import {
  ChatRequestSchema, ChatResponseSchema, ChatResponse,
  SessionsResponseSchema, HistoryResponseSchema, HistoryResponse,
  Session,
} from './types';
import { API_BASE_URL, createApiError, authHeaders, apiRequest } from './apiClient';

export async function sendMessage(text: string): Promise<ChatResponse> {
  const parseResult = ChatRequestSchema.safeParse({ query: text });
  if (!parseResult.success) {
    const errorMessage = parseResult.error.errors?.[0]?.message || 'Невалидный запрос';
    throw new Error(errorMessage);
  }

  try {
    const data = await apiRequest(
      `${API_BASE_URL}/chat`,
      {
        method: 'POST',
        body: JSON.stringify({ query: text }),
      },
      (raw) => {
        const result = ChatResponseSchema.safeParse(raw);
        if (!result.success) {
          console.error('Невалидный ответ от сервера:', raw);
          throw new Error('Сервер вернул невалидные данные');
        }
        return result.data;
      },
    );
    return data;
  } catch (error) {
    if (error instanceof Error) throw error;
    throw new Error('Неизвестная ошибка при подключении к серверу');
  }
}

export async function fetchSessions(
  token: string,
  offset = 0,
  limit = 20,
): Promise<{ sessions: Session[]; total: number }> {
  const response = await fetch(
    `${API_BASE_URL}/sessions?offset=${offset}&limit=${limit}`,
    { headers: authHeaders(token) },
  );
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw createApiError(response.status, `Ошибка сервера: ${response.status}`, errorData.detail);
  }

  const data = await response.json();
  const parseResult = SessionsResponseSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('Невалидный ответ сессий:', data);
    throw new Error('Сервер вернул невалидные данные');
  }

  return { sessions: parseResult.data.sessions, total: parseResult.data.total };
}

export async function fetchSessionMessages(sessionId: number, token: string): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`, {
    headers: authHeaders(token),
  });
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

export async function deleteSession(sessionId: number, token: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw createApiError(response.status, `Ошибка сервера: ${response.status}`, errorData.detail);
  }
}

export async function clearAllHistory(token: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/history`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw createApiError(response.status, `Ошибка сервера: ${response.status}`, errorData.detail);
  }
}
