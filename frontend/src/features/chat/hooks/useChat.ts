import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, ChatState, GuitarResult, Session } from '../types';
import { fetchSessions, fetchSessionMessages, deleteSession as apiDeleteSession, clearAllHistory } from '../api';
import { normalizeResult, historyToMessages } from '../messageMappers';
import { readSessionIdFromUrl, updateSessionUrl } from '../sessionUrl';

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://127.0.0.1:8000/chat';
const PAGE_SIZE = 20;

interface SessionSelectionOptions {
  syncUrl?: boolean;
  replaceUrl?: boolean;
}

function isUnauthorizedError(error: unknown): boolean {
  return error instanceof Error && 'status' in error && error.status === 401;
}

interface UseChatReturn extends ChatState {
  sendMessage: (text: string) => void;
  sendAction: (action: import('../types').AgentAction) => void;
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
 * Хук для управления чатом с поддержкой сессий и пагинацией
 */
export function useChat(authToken: string, onAuthExpired: () => void): UseChatReturn {
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
  const isUnmountingRef = useRef(false);
  const onAuthExpiredRef = useRef(onAuthExpired);

  // Синхронизируем ref с state для доступа из колбэков
  useEffect(() => {
    currentSessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

  useEffect(() => {
    onAuthExpiredRef.current = onAuthExpired;
  }, [onAuthExpired]);

  // Загрузка первой страницы сессий
  const loadSessions = useCallback(() => {
    const requestId = sessionsRequestIdRef.current + 1;
    sessionsRequestIdRef.current = requestId;
    loadedCountRef.current = 0;
    setIsLoadingSessions(true);
    fetchSessions(authToken, 0, PAGE_SIZE)
      .then(({ sessions: newSessions, total }) => {
        if (sessionsRequestIdRef.current !== requestId) {
          return;
        }
        setSessions(newSessions);
        loadedCountRef.current = newSessions.length;
        setHasMoreSessions(loadedCountRef.current < total);
      })
      .catch((err) => {
        if (isUnauthorizedError(err)) {
          onAuthExpiredRef.current();
          return;
        }
        console.error('Ошибка загрузки сессий:', err);
      })
      .finally(() => {
        if (sessionsRequestIdRef.current === requestId) {
          setIsLoadingSessions(false);
        }
      });
  }, [authToken]);

  // Подгрузка следующей страницы при скролле
  const loadMoreSessions = useCallback(() => {
    if (isLoadingMoreSessions || !hasMoreSessions) return;
    setIsLoadingMoreSessions(true);

    fetchSessions(authToken, loadedCountRef.current, PAGE_SIZE)
      .then(({ sessions: newSessions, total }) => {
        setSessions(prev => [...prev, ...newSessions]);
        loadedCountRef.current += newSessions.length;
        setHasMoreSessions(loadedCountRef.current < total);
      })
      .catch((err) => {
        if (isUnauthorizedError(err)) {
          onAuthExpiredRef.current();
          return;
        }
        console.error('Ошибка подгрузки сессий:', err);
      })
      .finally(() => setIsLoadingMoreSessions(false));
  }, [authToken, hasMoreSessions, isLoadingMoreSessions]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Подключение к WebSocket
  const connect = useCallback(() => {
    setConnectionStatus('connecting');

    try {
      const ws = new window.WebSocket(`${WS_URL}?token=${encodeURIComponent(authToken)}`);

      ws.onopen = () => {
        setConnectionStatus('connected');
        setError(prev => prev === 'Ошибка соединения с сервером' ? null : prev);
      };

      ws.onclose = (event) => {
        if (isUnmountingRef.current) {
          return;
        }
        if (event?.code === 1008) {
          onAuthExpiredRef.current();
          return;
        }
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
                updateSessionUrl(returnedSessionId);
              }

              let content = '';
              let results: GuitarResult[] | undefined = undefined;

              if (data.mode === 'consultation' || data.mode === 'conversation') {
                content = data.answer || '';
              } else if (data.mode === 'clarification') {
                // Уточняющий вопрос — продолжаем диалог в той же сессии
                content = data.question || '';
              } else if (data.mode === 'search') {
                results = (data.results || []).map((item: any) => normalizeResult(item));
                if (data.explanation) {
                  content = data.explanation;
                } else if (results && results.length > 0) {
                  content = `Найдено гитар: ${results.length}`;
                } else {
                  content = '';
                }
              }

              const agentMessage: Message = {
                id: Date.now().toString(),
                role: 'agent',
                content,
                timestamp: new Date(),
                results,
                mode: data.mode,
                debugThink: data.debugThink || null,
                searchParams: data.searchParams || null,
                actions: Array.isArray(data.actions) ? data.actions : undefined,
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
  }, [authToken, loadSessions]);

  useEffect(() => {
    connect();
    return () => {
      isUnmountingRef.current = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const resetToNewChat = useCallback((options?: SessionSelectionOptions) => {
    requestedSessionIdRef.current = null;
    currentSessionIdRef.current = null;
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
    setStatus(null);
    setLatestLiveMessageId(null);
    setIsLoadingSessionMessages(false);

    if (options?.syncUrl ?? true) {
      updateSessionUrl(null, options?.replaceUrl ?? false);
    }
  }, []);

  // Отправка сообщения
  const sendMessage = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== window.WebSocket.OPEN) {
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

  // Отправка action (клик по кнопке) — bypass LLM
  const sendAction = useCallback((action: import('../types').AgentAction) => {
    if (!wsRef.current || wsRef.current.readyState !== window.WebSocket.OPEN) {
      setError('Нет соединения с сервером');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: action.label,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setStatus(null);
    setLatestLiveMessageId(null);

    wsRef.current.send(JSON.stringify({
      action,
      sessionId: currentSessionIdRef.current || undefined,
    }));
  }, []);

  // Выбрать сессию — загрузить её сообщения
  const selectSession = useCallback((id: number, options?: SessionSelectionOptions) => {
    requestedSessionIdRef.current = id;
    currentSessionIdRef.current = id;
    setCurrentSessionId(id);
    setError(null);
    setStatus(null);
    setMessages([]);
    setLatestLiveMessageId(null);
    setIsLoadingSessionMessages(true);

    if (options?.syncUrl ?? true) {
      updateSessionUrl(id, options?.replaceUrl ?? false);
    }

    fetchSessionMessages(id, authToken)
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
        setIsLoadingSessionMessages(false);

        requestedSessionIdRef.current = null;
        currentSessionIdRef.current = null;
        setCurrentSessionId(null);
        setMessages([]);

        if (isUnauthorizedError(err)) {
          onAuthExpiredRef.current();
        } else if (err instanceof Error && 'status' in err && err.status === 404) {
          setError('Чат по этой ссылке не найден');
        } else {
          setError('Не удалось загрузить сообщения');
        }

        updateSessionUrl(null, true);
      })
      .finally(() => {
        if (requestedSessionIdRef.current === id) {
          setIsLoadingSessionMessages(false);
          requestedSessionIdRef.current = null;
        }
      });
  }, [authToken]);

  // Новый чат
  const newChat = useCallback(() => {
    resetToNewChat();
  }, [resetToNewChat]);

  useEffect(() => {
    const syncSessionFromUrl = () => {
      const { sessionId, error: urlError } = readSessionIdFromUrl();

      if (urlError) {
        resetToNewChat({ syncUrl: true, replaceUrl: true });
        setError(urlError);
        return;
      }

      if (sessionId === null) {
        if (currentSessionIdRef.current !== null) {
          resetToNewChat({ syncUrl: false });
        }
        return;
      }

      if (currentSessionIdRef.current === sessionId) {
        return;
      }

      selectSession(sessionId, { syncUrl: false });
    };

    syncSessionFromUrl();
    window.addEventListener('popstate', syncSessionFromUrl);

    return () => {
      window.removeEventListener('popstate', syncSessionFromUrl);
    };
  }, [resetToNewChat, selectSession]);

  // Удалить сессию
  const deleteSessionHandler = useCallback((id: number) => {
    apiDeleteSession(id, authToken)
      .then(() => {
        setSessions(prev => prev.filter(s => s.id !== id));
        loadedCountRef.current = Math.max(0, loadedCountRef.current - 1);
        // Если удалили текущую — сбрасываем
        if (currentSessionIdRef.current === id) {
          resetToNewChat();
        }
      })
      .catch((err) => {
        if (isUnauthorizedError(err)) {
          onAuthExpiredRef.current();
          return;
        }
        console.error('Ошибка удаления сессии:', err);
      });
  }, [authToken, resetToNewChat]);

  // Очистить всю историю
  const clearHistory = useCallback(() => {
    clearAllHistory(authToken)
      .then(() => {
        setSessions([]);
        resetToNewChat();
        loadedCountRef.current = 0;
        setHasMoreSessions(true);
      })
      .catch((err) => {
        if (isUnauthorizedError(err)) {
          onAuthExpiredRef.current();
          return;
        }
        console.error('Ошибка очистки истории:', err);
      });
  }, [authToken, resetToNewChat]);

  return {
    messages,
    isLoading,
    error,
    connectionStatus,
    status,
    sendMessage,
    sendAction,
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
    isLoadingSessionMessages
  };
}
