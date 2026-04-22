import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, ChatState, GuitarResult, Session } from '../types';
import { fetchSessions, fetchSessionMessages, deleteSession as apiDeleteSession, clearAllHistory } from '../api';
import { parseQuery } from '../api';

const WS_URL = 'ws://localhost:8000/chat';
const PAGE_SIZE = 20;

function normalizeResult(item: any): GuitarResult {
  return {
    id: item.id,
    title: item.title,
    price: item.price,
    currency: item.currency,
    imageUrl: item.imageUrl || item.image_url,
    listingUrl: item.listingUrl || item.listing_url,
  };
}

interface UseChatReturn extends ChatState {
  sendMessage: (text: string) => void;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  status: string | null;
  sessions: Session[];
  isLoadingSessions: boolean;
  latestLiveMessageId: string | null;
  currentSessionId: number | null;
  selectSession: (id: number) => void;
  newChat: () => void;
  deleteSession: (id: number) => void;
  clearHistory: () => void;
  loadMoreSessions: () => void;
  hasMoreSessions: boolean;
  isLoadingMoreSessions: boolean;
  isLoadingSessionMessages: boolean;
}

/**
 * Преобразует элементы истории в массив сообщений
 */
function historyToMessages(items: any[]): Message[] {
  const messages: Message[] = [];
  for (const item of items) {
    const normalizedResults = item.mode === 'search'
      ? (item.results || []).map((result: any) => normalizeResult(result))
      : undefined;

    messages.push({
      id: `hist-user-${item.id}`,
      role: 'user',
      content: item.userQuery,
      timestamp: new Date(item.createdAt),
    });
    messages.push({
      id: `hist-agent-${item.id}`,
      role: 'agent',
      content: item.mode !== 'search'
        ? (item.answer || '')
        : (item.answer || `Найдено гитар: ${(normalizedResults || []).length}`),
      timestamp: new Date(item.createdAt),
      mode: item.mode as 'search' | 'consultation' | 'clarification',
      results: normalizedResults,
    });
  }
  return messages;
}

/**
 * Хук для управления чатом с поддержкой сессий и пагинацией
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [status, setStatus] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [latestLiveMessageId, setLatestLiveMessageId] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [isLoadingSessionMessages, setIsLoadingSessionMessages] = useState(false);

  // Пагинация сессий
  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const [isLoadingMoreSessions, setIsLoadingMoreSessions] = useState(false);
  const loadedCountRef = useRef(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentSessionIdRef = useRef<number | null>(null);
  const requestedSessionIdRef = useRef<number | null>(null);
  const sessionsRequestIdRef = useRef(0);

  // Синхронизируем ref с state для доступа из колбэков
  useEffect(() => {
    currentSessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

  // Загрузка первой страницы сессий
  const loadSessions = useCallback(() => {
    const requestId = sessionsRequestIdRef.current + 1;
    sessionsRequestIdRef.current = requestId;
    loadedCountRef.current = 0;
    setIsLoadingSessions(true);
    fetchSessions(0, PAGE_SIZE)
      .then(({ sessions: newSessions, total }) => {
        if (sessionsRequestIdRef.current !== requestId) {
          return;
        }
        setSessions(newSessions);
        loadedCountRef.current = newSessions.length;
        setHasMoreSessions(loadedCountRef.current < total);
      })
      .catch((err) => console.error('Ошибка загрузки сессий:', err))
      .finally(() => {
        if (sessionsRequestIdRef.current === requestId) {
          setIsLoadingSessions(false);
        }
      });
  }, []);

  // Подгрузка следующей страницы при скролле
  const loadMoreSessions = useCallback(() => {
    if (isLoadingMoreSessions || !hasMoreSessions) return;
    setIsLoadingMoreSessions(true);

    fetchSessions(loadedCountRef.current, PAGE_SIZE)
      .then(({ sessions: newSessions, total }) => {
        setSessions(prev => [...prev, ...newSessions]);
        loadedCountRef.current += newSessions.length;
        setHasMoreSessions(loadedCountRef.current < total);
      })
      .catch((err) => console.error('Ошибка подгрузки сессий:', err))
      .finally(() => setIsLoadingMoreSessions(false));
  }, [hasMoreSessions, isLoadingMoreSessions]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Подключение к WebSocket
  const connect = useCallback(() => {
    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnectionStatus('connected');
        setError(null);
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = () => {
        setError('Ошибка соединения с сервером');
        ws.close();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'status':
              setStatus(data.status || null);
              break;

            case 'result': {
              setStatus(null);
              setIsLoading(false);

              // Бэкенд вернул sessionId (новый или существующий)
              const returnedSessionId = data.sessionId as number | undefined;
              if (returnedSessionId && !currentSessionIdRef.current) {
                currentSessionIdRef.current = returnedSessionId;
                setCurrentSessionId(returnedSessionId);
              }

              let content = '';
              let results: GuitarResult[] | undefined = undefined;

              if (data.mode === 'consultation') {
                content = data.answer || '';
              } else if (data.mode === 'clarification') {
                // Уточняющий вопрос — продолжаем диалог в той же сессии
                content = data.question || '';
              } else if (data.mode === 'search') {
                results = (data.results || []).map((item: any) => normalizeResult(item));
                content = data.explanation ? data.explanation : `Найдено гитар: ${results?.length ?? 0}`;
              }

              const agentMessage: Message = {
                id: Date.now().toString(),
                role: 'agent',
                content,
                timestamp: new Date(),
                results,
                mode: data.mode,
              };

              setMessages(prev => [...prev, agentMessage]);
              setLatestLiveMessageId(agentMessage.id);

              // Обновляем список сессий (сбрасываем пагинацию)
              loadSessions();
              break;
            }

            case 'error':
              setStatus(null);
              setIsLoading(false);
              setError(data.status || 'Произошла ошибка');
              break;
          }
        } catch (e) {
          console.error('Ошибка парсинга сообщения:', e);
          setError('Некорректный формат сообщения от сервера');
        }
      };

      wsRef.current = ws;
    } catch (e) {
      setConnectionStatus('disconnected');
      setError('Не удалось подключиться к серверу');
    }
  }, [loadSessions]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  // Отправка сообщения
  const sendMessage = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Нет соединения с сервером');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    parseQuery(text).then(params => {
      setMessages(currentMsgs => currentMsgs.map(m => 
        m.id === userMessage.id ? { ...m, parsedParams: params } : m
      ));
    }).catch(err => console.error("Ошибка парсинга параметров", err));
    
    setIsLoading(true);
    setIsLoading(true);
    setError(null);
    setStatus(null);
    setLatestLiveMessageId(null);

    // Отправляем sessionId если есть текущая сессия
    wsRef.current.send(JSON.stringify({
      query: text,
      sessionId: currentSessionIdRef.current || undefined,
    }));
  }, []);

  // Выбрать сессию — загрузить её сообщения
  const selectSession = useCallback((id: number) => {
    requestedSessionIdRef.current = id;
    currentSessionIdRef.current = id;
    setCurrentSessionId(id);
    setError(null);
    setStatus(null);
    setMessages([]);
    setLatestLiveMessageId(null);
    setIsLoadingSessionMessages(true);

    fetchSessionMessages(id)
      .then((data) => {
        if (requestedSessionIdRef.current !== id) {
          return;
        }
        setMessages(historyToMessages(data.items));
      })
      .catch((err) => {
        if (requestedSessionIdRef.current !== id) {
          return;
        }
        console.error('Ошибка загрузки сообщений сессии:', err);
        setError('Не удалось загрузить сообщения');
      })
      .finally(() => {
        if (requestedSessionIdRef.current === id) {
          setIsLoadingSessionMessages(false);
        }
      });
  }, []);

  // Новый чат
  const newChat = useCallback(() => {
    requestedSessionIdRef.current = null;
    currentSessionIdRef.current = null;
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
    setStatus(null);
    setLatestLiveMessageId(null);
    setIsLoadingSessionMessages(false);
  }, []);

  // Удалить сессию
  const deleteSessionHandler = useCallback((id: number) => {
    apiDeleteSession(id)
      .then(() => {
        setSessions(prev => prev.filter(s => s.id !== id));
        loadedCountRef.current = Math.max(0, loadedCountRef.current - 1);
        // Если удалили текущую — сбрасываем
        if (currentSessionIdRef.current === id) {
          requestedSessionIdRef.current = null;
          setCurrentSessionId(null);
          setMessages([]);
          setLatestLiveMessageId(null);
          setIsLoadingSessionMessages(false);
        }
      })
      .catch((err) => console.error('Ошибка удаления сессии:', err));
  }, []);

  // Очистить всю историю
  const clearHistory = useCallback(() => {
    clearAllHistory()
      .then(() => {
        setSessions([]);
        setCurrentSessionId(null);
        setMessages([]);
        setLatestLiveMessageId(null);
        requestedSessionIdRef.current = null;
        loadedCountRef.current = 0;
        setHasMoreSessions(true);
        setIsLoadingSessionMessages(false);
      })
      .catch((err) => console.error('Ошибка очистки истории:', err));
  }, []);

  return {
    messages,
    isLoading,
    error,
    connectionStatus,
    status,
    sendMessage,
    sessions,
    isLoadingSessions,
    latestLiveMessageId,
    currentSessionId,
    selectSession,
    newChat,
    deleteSession: deleteSessionHandler,
    clearHistory,
    loadMoreSessions,
    hasMoreSessions,
    isLoadingMoreSessions,
    isLoadingSessionMessages,
  };
}
