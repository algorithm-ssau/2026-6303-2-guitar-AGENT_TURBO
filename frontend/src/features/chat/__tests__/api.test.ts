import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { sendMessage } from '../api';

// Мок для fetch
global.fetch = vi.fn();

describe('sendMessage API function', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('должен вызывать правильный URL и метод', async () => {
    const mockResponse = { reply: 'Тестовый ответ' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    await sendMessage('Привет');

    expect(global.fetch).toHaveBeenCalledWith('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: 'Привет' }),
    });
  });

  it('должен возвращать валидный ответ', async () => {
    const mockResponse = {
      reply: 'Рекомендую Fender Stratocaster',
      results: [{ title: 'Fender', url: 'https://reverb.com/1', price: 500 }]
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await sendMessage('Хочу гитару');

    expect(result).toEqual(mockResponse);
  });

  it('должен бросать ошибку при ошибке сети', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    await expect(sendMessage('Привет')).rejects.toThrow('Network error');
  });

  it('должен бросать ошибку при не-200 ответе сервера', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Внутренняя ошибка сервера' }),
    });

    await expect(sendMessage('Привет')).rejects.toThrow('Внутренняя ошибка сервера');
  });

  it('должен бросать ошибку при невалидном ответе от сервера', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ invalid: 'data' }), // нет поля reply
    });

    await expect(sendMessage('Привет')).rejects.toThrow('Сервер вернул невалидные данные');
  });

  it('должен бросать ошибку при пустом сообщении', async () => {
    await expect(sendMessage('')).rejects.toThrow('Невалидный запрос');
  });
});
