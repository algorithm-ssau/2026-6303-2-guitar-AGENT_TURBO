import { describe, it, expect } from 'vitest';
import { ChatRequestSchema, ChatResponseSchema, SearchResultSchema } from '../types';

describe('Chat API Zod Schemas', () => {
  describe('ChatRequestSchema', () => {
    it('должен проходить валидацию с корректным запросом', () => {
      const validData = { query: 'Хочу гитару с тёплым звуком' };
      const result = ChatRequestSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен бросать ошибку с пустым запросом', () => {
      const invalidData = { query: '' };
      const result = ChatRequestSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });


    it('должен бросать ошибку с отсутствующим полем query', () => {
      const invalidData = {};
      const result = ChatRequestSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    it('должен бросать ошибку с запросом короче 2 символов', () => {
      const invalidData = { query: 'a' };
      const result = ChatRequestSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('ChatResponseSchema', () => {
    it('должен проходить валидацию с корректным search ответом', () => {
      const validData = {
        mode: 'search',
        results: [
          { title: 'Fender Strat', listingUrl: 'https://reverb.com/item/123', price: 500 }
        ]
      };
      const result = ChatResponseSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен проходить валидацию с consultation ответом', () => {
      const validData = { mode: 'consultation', answer: 'Привет! Чем помочь?' };
      const result = ChatResponseSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен проходить валидацию с clarification ответом', () => {
      const validData = { mode: 'clarification', question: 'Какой у вас бюджет?' };
      const result = ChatResponseSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен бросать ошибку с невалидным URL', () => {
      const invalidData = {
        mode: 'search',
        results: [{ title: 'Test', listingUrl: 'not-a-url', price: 100 }]
      };
      const result = ChatResponseSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    it('должен бросать ошибку с отсутствующим mode', () => {
      const invalidData = { results: [] };
      const result = ChatResponseSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    it('должен бросать ошибку с невалидным mode', () => {
      const invalidData = { mode: 'invalid_mode' };
      const result = ChatResponseSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('SearchResultSchema', () => {
    it('должен проходить валидацию с корректным результатом', () => {
      const validData = { title: 'Gibson Les Paul', listingUrl: 'https://reverb.com/item/456', price: 1200 };
      const result = SearchResultSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен проходить валидацию без price', () => {
      const validData = { title: 'Guitar', listingUrl: 'https://reverb.com/item/789' };
      const result = SearchResultSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('должен требовать обязательное поле title', () => {
      const invalidData = { listingUrl: 'https://reverb.com/item/789' };
      const result = SearchResultSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    it('должен требовать обязательное поле listingUrl', () => {
      const invalidData = { title: 'Guitar' };
      const result = SearchResultSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });
});
