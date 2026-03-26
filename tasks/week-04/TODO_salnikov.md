# TODO — Сальников Илья

**Неделя 4:** 30 марта – 5 апреля 2026
**Ветка:** `feature/salnikov/ws-hook`

> **Приоритет: КРИТИЧЕСКИЙ.** Задача 1 должна быть завершена в первые 2 дня — от useChat хука зависит Павлов.

---

## Задача 1 (Frontend): реализация useChat хука через WebSocket

### Что делать

- Реализовать `frontend/src/features/chat/hooks/useChat.ts` — полноценный React-хук:
  - Состояние: `messages: Message[]`, `isLoading: boolean`, `error: string | null`, `status: string | null`
  - При монтировании: открыть WebSocket на `ws://localhost:8000/chat`
  - Метод `sendMessage(text: string)`:
    - Добавляет user message в messages
    - Отправляет `{"query": text}` через WS
    - Слушает ответы:
      - `type="status"` → обновляет `status` (текст промежуточного статуса)
      - `type="result"`, `mode="search"` → создаёт agent message с results (с маппингом snake_case → camelCase: `image_url` → `imageUrl`, `listing_url` → `listingUrl`)
      - `type="result"`, `mode="consultation"` → создаёт agent message с content = answer
      - `type="error"` → устанавливает error
    - Сбрасывает isLoading после получения result или error
  - Автоматический реконнект при обрыве соединения (через 3 секунды)
  - Хук возвращает: `{ messages, isLoading, error, status, sendMessage }`

### Файлы

- Изменить: `frontend/src/features/chat/hooks/useChat.ts`

### Критерий приёмки

- Хук подключается к WS при монтировании
- `sendMessage("текст")` → user message добавляется → isLoading=true → status обновляется → result приходит → agent message добавляется → isLoading=false
- Обрыв соединения → попытка реконнекта через 3 секунды
- Ошибка от сервера → error устанавливается, isLoading=false

### Тест: `frontend/src/features/chat/__tests__/useChat.test.ts`

- Mock WebSocket: sendMessage → получение result → agent message в messages
- Mock WebSocket: type="status" → status обновляется
- Mock WebSocket: type="error" → error не null
- Реконнект при обрыве

### Коммит: `feat: implement useChat WebSocket hook with reconnect`

---

## Задача 2 (Backend): отправка статусов через WebSocket в реальном времени

### Что делать

- Изменить `backend/main.py` — отправлять статусы по мере их появления, а не батчем после завершения:
  - Сейчас: `statuses = []` → `on_status` собирает в список → все отправляются после `interpret_query`
  - Нужно: использовать `asyncio.Queue` для передачи статусов из синхронного callback в async WS:
    ```python
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    # В websocket_chat:
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_status(text):
        loop.call_soon_threadsafe(queue.put_nowait, {"type": "status", "text": text})

    # Запустить interpret_query в executor, параллельно слушать queue
    ```
  - Добавить try/except вокруг `interpret_query` с отправкой `type="error"` при любом исключении
  - Добавить таймаут: если interpret_query работает > 30 секунд → отправить error

### Файлы

- Изменить: `backend/main.py`

### Критерий приёмки

- Клиент получает статусы ("Определяю режим...", "Ищу на Reverb...") по одному, до финального result
- Исключение в pipeline → `{"type": "error", "text": "..."}` без падения WS
- WebSocket соединение остаётся открытым после ошибки

### Тест: `tests/test_ws_realtime.py`

- Статусы приходят до result (проверить порядок)
- Ошибка в pipeline → type="error", соединение не рвётся
- Повторный запрос после ошибки работает

### Коммит: `feat: send WebSocket status updates in real-time`

---

## Задача 3 (Тестирование): интеграционные тесты useChat + WebSocket

### Что делать

- Написать `tests/test_ws_integration.py` — проверка полного flow через FastAPI TestClient:
  - Search query → серия status → result с mode="search" и непустыми results
  - Consultation query → status → result с mode="consultation" и непустым answer
  - Два последовательных запроса в одном WS-соединении → оба работают
  - Проверка формата результатов: каждый result содержит id, title, price, listing_url

### Файлы

- Создать: `tests/test_ws_integration.py`

### Критерий приёмки

- Все тесты проходят с `USE_MOCK_REVERB=true` без GROQ_API_KEY
- Покрыты оба режима + повторные запросы

### Коммит: `test: add WebSocket integration tests for full flow`
