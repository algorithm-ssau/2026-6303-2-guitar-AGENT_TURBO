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

export interface SearchParams {
  searchQueries?: string[];
  priceMin?: number | null;
  priceMax?: number | null;
  type?: string | null;
  brand?: string | null;
  pickups?: string | null;
  sound?: string | null;
  style?: string | null;
}

export type ChatMode = 'search' | 'consultation' | 'conversation' | 'clarification';

/** Сообщение в чате */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  results?: GuitarResult[];
  mode?: 'search' | 'consultation' | 'clarification';
  question?: string;
  transient?: {
    phase: 'thinking' | 'revealing';
    status?: string | null;
  };
  searchParams?: SearchParams | null;
}

/** Состояние чата */
export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

/** Сессия чата */
export interface Session {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
}

/** Схема запроса к API */
export const ChatRequestSchema = z.object({
  query: z.string().min(2, 'Запрос не может быть пустым').max(500, 'Запрос слишком длинный'),
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

export const SearchParamsSchema = z.object({
  searchQueries: z.array(z.string()).optional().default([]),
  priceMin: z.number().nullable().optional(),
  priceMax: z.number().nullable().optional(),
  type: z.string().nullable().optional(),
  brand: z.string().nullable().optional(),
  pickups: z.string().nullable().optional(),
  sound: z.string().nullable().optional(),
  style: z.string().nullable().optional(),
});

/** Схема ответа от API */
export const ChatResponseSchema = z.object({
  mode: z.enum(['search', 'consultation', 'clarification']),
  answer: z.string().optional(),
  debugThink: z.string().nullable().optional(),
  results: z.array(SearchResultSchema).optional(),
  explanation: z.string().optional(),
  question: z.string().optional(),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;

/** Схема сессии */
export const SessionSchema = z.object({
  id: z.number(),
  title: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

/** Схема ответа GET /api/sessions */
export const SessionsResponseSchema = z.object({
  sessions: z.array(SessionSchema),
  total: z.number(),
});

/** Схема элемента истории */
export const HistoryItemSchema = z.object({
  id: z.number(),
  sessionId: z.number(),
  userQuery: z.string(),
  mode: z.enum(['search', 'consultation', 'conversation', 'clarification']),
  answer: z.string().nullable().optional(),
  results: z.array(z.record(z.string(), z.unknown())).nullable().optional(),
  searchParams: SearchParamsSchema.nullable().optional(),
  createdAt: z.string(),
});

export type HistoryItem = z.infer<typeof HistoryItemSchema>;

/** Схема ответа GET /api/sessions/{id}/messages */
export const HistoryResponseSchema = z.object({
  items: z.array(HistoryItemSchema),
});

export type HistoryResponse = z.infer<typeof HistoryResponseSchema>;
