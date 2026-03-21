# TODO — Сальников Илья

**Неделя 3:** 23–29 марта 2026
**Ветка:** `feature/salnikov/api-connect`

---

## Задача 1 (Backend): Pydantic-модели и WebSocket endpoint

### Что делать

- Создать `backend/models.py` с Pydantic-моделями по контракту из `docs/SEARCH_PARAMS.md`:
  - `GuitarResult` — поля: id, title, price, currency, image_url, listing_url
  - `WSMessage` — формат сообщения по WebSocket:
    - `type`: `"status"` | `"result"` | `"error"` — тип сообщения
    - `mode`: `"search"` | `"consultation"` | None — определённый режим
    - `status`: строка — текст статуса (например "Определяю режим...", "Ищу на Reverb...", "Ранжирую результаты...")
    - `answer`: строка | None — текст ответа (consultation)
    - `results`: список GuitarResult — результаты (search)
- Заменить `POST /chat` в `backend/main.py` на WebSocket endpoint `ws /chat`:
  - Принимать JSON `{"query": "текст"}` через WS
  - Валидировать: пустой query → отправить сообщение с type="error"
  - Вызывать `interpret_query()` из `backend/agent/service.py`
  - По ходу работы отправлять промежуточные статусы (type="status")
  - В конце отправить финальный результат (type="result")
- Добавить в requirements.txt: `websockets`

### Файлы

- Создать: `backend/models.py`
- Изменить: `backend/main.py`
- Изменить: `requirements.txt`

### Критерий приёмки

- WS подключение на `ws://localhost:8000/chat` работает
- Клиент отправляет `{"query": "текст"}` → получает серию JSON-сообщений:
  1. `{"type": "status", "status": "Определяю режим..."}`
  2. `{"type": "status", "status": "Ищу на Reverb..."}` (для search)
  3. `{"type": "result", "mode": "search", "results": [...]}` или `{"type": "result", "mode": "consultation", "answer": "..."}`
- Пустой query → `{"type": "error", "status": "Запрос не может быть пустым"}`
- Соединение не падает при ошибках, отправляет type="error"

### Тест: `tests/test_ws_endpoint.py`

- WebSocket подключается
- Отправка query → получение type="result" с mode
- Пустой query → type="error"

### Коммит: `feat: add websocket chat endpoint with status updates`

---

## Задача 2 (Frontend): хук useChat через WebSocket

### Что делать

- Реализовать `frontend/src/features/chat/hooks/useChat.ts`:
  - Состояние: messages, isLoading, error, connectionStatus
  - При монтировании: открыть WebSocket на `ws://localhost:8000/chat`
  - Метод `sendMessage(text)`:
    - Добавляет user message в messages
    - Отправляет `{"query": text}` через WS
    - Слушает ответы:
      - type="status" → обновляет текст статуса (можно показывать в UI)
      - type="result" → создаёт agent message с mode и results/answer
      - type="error" → устанавливает error
  - Обработка обрыва соединения: автоматический реконнект
- Переписать `Chat.tsx` — убрать `setTimeout` mock, использовать `useChat()`

### Файлы

- Изменить: `frontend/src/features/chat/hooks/useChat.ts`
- Изменить: `frontend/src/features/chat/components/Chat.tsx`

### Критерий приёмки

- Chat UI подключается к WS при загрузке
- Отправка сообщения → промежуточные статусы видны → финальный ответ в чате
- Обрыв соединения → попытка реконнекта
- Ошибка → текст ошибки в UI

### Тест: `frontend/src/features/chat/__tests__/useChat.test.ts`

- Mock WebSocket: отправка сообщения → получение result → agent message в messages
- Mock WebSocket: type="error" → error не null

### Коммит: `feat: implement useChat hook with WebSocket connection`

---

## Задача 3 (Тестирование): smoke-тест WebSocket пайплайна

### Что делать

- Написать `tests/test_ws_smoke.py` используя `fastapi.testclient.TestClient` и `client.websocket_connect("/chat")`
- Минимум 3 сценария:
  - Consultation запрос → получаем type="status", затем type="result" с mode="consultation"
  - Search запрос → получаем серию status, затем type="result" с mode="search"
  - Пустой query → type="error"

### Файлы

- Создать: `tests/test_ws_smoke.py`

### Критерий приёмки

- Все тесты проходят, не зависят от внешних API

### Коммит: `test: add WebSocket smoke tests for chat pipeline`
