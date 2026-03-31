/**
 * Типы для модуля чата
 */
import { z } from 'zod';

/** Роль отправителя сообщения */
export type MessageRole = 'user' | 'agent';

export interface GuitarResult {
  id?: string;
  title: string;
  price?: number;
  currency?: string;
  imageUrl?: string;
  listingUrl: string;
}

/** Сообщение в чате */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  results?: GuitarResult[];
  mode?: 'search' | 'consultation';
}

/** Состояние чата */
export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

/** Схема запроса к API */
export const ChatRequestSchema = z.object({
  message: z.string().min(1, 'Сообщение не может быть пустым'),
});

export type ChatRequest = z.infer<typeof ChatRequestSchema>;

/** Схема результата поиска (одна гитара) */
export const SearchResultSchema = z.object({
  id: z.string().optional(),
  title: z.string(),
  price: z.number().optional(),
  currency: z.string().optional(),
  imageUrl: z.string().url().optional(),
  listingUrl: z.string().url(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

/** Схема ответа от API */
export const ChatResponseSchema = z.object({
  mode: z.enum(['search', 'consultation']),
  answer: z.string().optional(),
  results: z.array(SearchResultSchema).optional(),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;
