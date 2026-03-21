import { ChatRequestSchema, ChatResponseSchema, ChatResponse } from './types';

const API_BASE_URL = '/api';

/**
 * Отправляет сообщение пользователя на сервер
 * @param text - текст сообщения
 * @returns валидированный ответ от сервера
 * @throws Error при ошибке сети или невалидном ответе
 */
export async function sendMessage(text: string): Promise<ChatResponse> {
  // Валидация запроса перед отправкой
  const parseResult = ChatRequestSchema.safeParse({ message: text });
  if (!parseResult.success) {
    const errorMessage = parseResult.error.errors?.[0]?.message || 'Невалидный запрос';
    throw new Error(errorMessage);
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: text }),
    });

    if (!response.ok) {
      // Обработка ошибок от сервера
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
    }

    const data = await response.json();

    // Валидация ответа от сервера
    const parseResult = ChatResponseSchema.safeParse(data);
    if (!parseResult.success) {
      console.error('Невалидный ответ от сервера:', data);
      throw new Error('Сервер вернул невалидные данные');
    }

    return parseResult.data;
  } catch (error) {
    if (error instanceof Error) {
      // Пробрасываем известные ошибки дальше
      throw error;
    }
    throw new Error('Неизвестная ошибка при подключении к серверу');
  }
}
