import { describe, it, expect } from 'vitest';
import { ChatRequestSchema, ChatResponseSchema, SearchResultSchema } from '../types';

describe('Chat API Zod Schemas', () => {
  describe('ChatRequestSchema', () => {
    it('должен проходить валидацию с корректным сообщением', () => {
      const validData = { message: 'Хочу гитару с тёплым звуком' };
      const result = ChatRequestSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен бросать ошибку с пустым сообщением', () => {
      const invalidData = { message: '' };
      const result = ChatRequestSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    it('должен бросать ошибку с отсутствующим полем message', () => {
      const invalidData = {};
      const result = ChatRequestSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('ChatResponseSchema', () => {
    it('должен проходить валидацию с корректным ответом', () => {
      const validData = {
        reply: 'Рекомендую Fender Stratocaster',
        results: [
          { title: 'Fender Strat', url: 'https://reverb.com/item/123', price: 500 }
        ]
      };
      const result = ChatResponseSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен проходить валидацию без results', () => {
      const validData = { reply: 'Привет! Чем помочь?' };
      const result = ChatResponseSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен бросать ошибку с невалидным URL', () => {
      const invalidData = {
        reply: 'Тест',
        results: [{ title: 'Test', url: 'not-a-url', price: 100 }]
      };
      const result = ChatResponseSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    it('должен бросать ошибку с отсутствующим reply', () => {
      const invalidData = { results: [] };
      const result = ChatResponseSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('SearchResultSchema', () => {
    it('должен проходить валидацию с корректным результатом', () => {
      const validData = { title: 'Gibson Les Paul', url: 'https://reverb.com/item/456', price: 1200 };
      const result = SearchResultSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен проходить валидацию без price', () => {
      const validData = { title: 'Guitar', url: 'https://reverb.com/item/789' };
      const result = SearchResultSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });
  });
});
