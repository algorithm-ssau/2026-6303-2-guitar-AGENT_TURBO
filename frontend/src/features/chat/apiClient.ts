export const API_BASE_URL = '/api';

export interface ApiError extends Error {
  status?: number;
}

export function createApiError(status: number, fallbackMessage: string, detail?: string): ApiError {
  const error = new Error(detail || fallbackMessage) as ApiError;
  error.status = status;
  return error;
}

export function authHeaders(token: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function apiRequest<T>(
  url: string,
  options: RequestInit = {},
  validate?: (data: unknown) => T,
): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
  }

  const data = await response.json();

  if (validate) {
    const parsed = validate(data);
    return parsed;
  }

  return data as T;
}
