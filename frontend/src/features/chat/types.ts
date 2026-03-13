/**
 * Типы для модуля чата
 */

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
