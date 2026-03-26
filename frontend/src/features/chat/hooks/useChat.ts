import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, ChatState } from '../types';

const WS_URL = 'ws://localhost:8000/chat';

interface UseChatReturn extends ChatState {
  sendMessage: (text: string) => void;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  currentStatus: string | null;
}

/**
 * Хук для управления WebSocket соединением чата
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [currentStatus, setCurrentStatus] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageCallbackRef = useRef<((data: any) => void) | null>(null);

  // Функция подключения к WebSocket
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
        // Автоматический реконнект через 2 секунды
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 2000);
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
              setCurrentStatus(data.status || null);
              break;
              
            case 'result':
              setCurrentStatus(null);
              setIsLoading(false);
              
              // Создаём сообщение от агента
              const agentMessage: Message = {
                id: Date.now().toString(),
                role: 'agent',
                content: data.mode === 'consultation' 
                  ? (data.answer || '') 
                  : `Найдено гитар: ${data.results?.length || 0}`,
                timestamp: new Date(),
              };
              
              setMessages(prev => [...prev, agentMessage]);
              
              // Сохраняем результаты в messageCallbackRef для возможного использования
              if (messageCallbackRef.current) {
                messageCallbackRef.current(data);
              }
              break;
              
            case 'error':
              setCurrentStatus(null);
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
  }, []);

  // Подключение при монтировании
  useEffect(() => {
    connect();

    // Очистка при размонтировании
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Отправка сообщения
  const sendMessage = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Нет соединения с сервером');
      return;
    }

    // Добавляем сообщение пользователя
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setCurrentStatus(null);

    // Отправляем через WebSocket
    wsRef.current.send(JSON.stringify({ query: text }));
  }, []);

  return {
    messages,
    isLoading,
    error,
    connectionStatus,
    currentStatus,
    sendMessage,
  };
}
