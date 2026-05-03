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
    const mockResponse = { mode: 'consultation', answer: 'Тестовый ответ' };
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
      body: JSON.stringify({ query: 'Привет' }),
    });
  });

  it('должен возвращать валидный ответ (search mode)', async () => {
    const mockResponse = {
      mode: 'search',
      results: [{ title: 'Fender', listingUrl: 'https://reverb.com/1', price: 500 }]
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await sendMessage('Хочу гитару');

    expect(result).toEqual(mockResponse);
  });

  it('должен возвращать валидный ответ (consultation mode)', async () => {
    const mockResponse = {
      mode: 'consultation',
      answer: 'Рекомендую Fender Stratocaster'
    };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await sendMessage('Чем отличается Stratocaster?');

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
      json: async () => ({ invalid: 'data' }), // нет обязательных полей
    });

    await expect(sendMessage('Привет')).rejects.toThrow('Сервер вернул невалидные данные');
  });

  it('должен бросать ошибку при слишком коротком запросе', async () => {
    await expect(sendMessage('')).rejects.toThrow('Невалидный запрос');
    await expect(sendMessage('a')).rejects.toThrow('Невалидный запрос');
  });
});
