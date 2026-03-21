/**
 * Типы для модуля чата
 */
import { z } from 'zod';

/** Роль отправителя сообщения */
export type MessageRole = 'user' | 'agent';

/** Сообщение в чате */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
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
  title: z.string(),
  url: z.string().url(),
  price: z.number().optional(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

/** Схема ответа от API */
export const ChatResponseSchema = z.object({
  reply: z.string(),
  results: z.array(SearchResultSchema).optional(),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;
