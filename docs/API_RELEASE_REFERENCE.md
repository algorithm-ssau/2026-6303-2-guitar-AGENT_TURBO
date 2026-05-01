# API Release Reference — Week 08

**Дата релиза:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/mergaliev/api-reference-w8`  
**Автор:** Мергалиев Радмир

Документ описывает API гитарного агента для защиты проекта. Все основные REST и WebSocket эндпоинты перечислены ниже с указанием их статуса.

---

## REST API

### POST /api/chat

**Статус:** `ready`

**Назначение:**  
Обработка запроса пользователя через LLM-пайплайн. Возвращает результат поиска на Reverb или текстовую консультацию.

**Request body:**
```json
{
  "query": "Найди стратокастер до 500$"
}
```

**Response body (search mode):**
```json
{
  "mode": "search",
  "results": [
    {
      "id": "12345",
      "title": "Fender Player Stratocaster",
      "price": 499.99,
      "currency": "USD",
      "imageUrl": "https://reverb.com/item/12345.jpg",
      "listingUrl": "https://reverb.com/item/12345"
    }
  ],
  "explanation": "Found guitars matching your criteria"
}
```

**Response body (consultation mode):**
```json
{
  "mode": "consultation",
  "answer": "Стратокастер — это модель гитары Fender..."
}
```

**Ошибки:**
- `400` — пустой запрос: `{"detail": "Запрос не может быть пустым"}`
- `500` — внутренняя ошибка сервера

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Найди гитару до 1000$"}'
```

---

### POST /api/query/parse

**Статус:** `ready`

**Назначение:**  
Быстрый парсинг параметров запроса без вызова LLM. Использует регулярные выражения для извлечения типа гитары, бюджета, бренда и тегов.

**Request body:**
```json
{
  "query": "Найди стратокастер до 500$"
}
```

**Response body:**
```json
{
  "type": "electric",
  "budget": "500",
  "brand": "Fender",
  "tags": ["stratocaster"]
}
```

**Ошибки:**
- `400` — некорректный запрос

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/query/parse \
  -H "Content-Type: application/json" \
  -d '{"query": "электрогитара Gibson до 2000$"}'
```

---

### GET /api/sessions

**Статус:** `ready`

**Назначение:**  
Получить список сессий чата с пагинацией. Сессии отсортированы от новых к старым.

**Query параметры:**
- `offset` (int, default=0) — смещение
- `limit` (int, default=20, max=100) — количество записей

**Response body:**
```json
{
  "sessions": [
    {
      "id": 1,
      "title": "Найди стратокастер до 500$",
      "createdAt": "2026-04-28T10:30:00",
      "updatedAt": "2026-04-28T10:32:00"
    }
  ],
  "total": 1
}
```

**Ошибки:**
- `422` — невалидные параметры запроса

**Пример запроса:**
```bash
curl "http://localhost:8000/api/sessions?limit=10&offset=0"
```

---

### POST /api/sessions

**Статус:** `ready`

**Назначение:**  
Создать новую сессию чата.

**Request body:**
```json
{
  "title": "Поиск гитары"
}
```

**Response body:**
```json
{
  "id": 1
}
```

**Ошибки:**
- `422` — невалидные данные

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Новая сессия"}'
```

---

### GET /api/sessions/{id}/messages

**Статус:** `ready`

**Назначение:**  
Получить все сообщения (историю) конкретной сессии.

**Response body:**
```json
{
  "items": [
    {
      "id": 1,
      "sessionId": 1,
      "userQuery": "Найди стратокастер до 500$",
      "mode": "search",
      "answer": null,
      "results": [...],
      "createdAt": "2026-04-28T10:30:00"
    }
  ]
}
```

**Ошибки:**
- `404` — сессия не найдена

**Пример запроса:**
```bash
curl http://localhost:8000/api/sessions/1/messages
```

---

### DELETE /api/sessions/{id}

**Статус:** `ready`

**Назначение:**  
Удалить сессию и все её сообщения.

**Response body:**
```json
{
  "ok": true
}
```

**Ошибки:**
- `404` — сессия не найдена

**Пример запроса:**
```bash
curl -X DELETE http://localhost:8000/api/sessions/1
```

---

### DELETE /api/history

**Статус:** `ready`

**Назначение:**  
Очистить всю историю чата (все сессии и сообщения).

**Response body:**
```json
{
  "deleted": 42
}
```

**Ошибки:**
- `500` — ошибка при удалении

**Пример запроса:**
```bash
curl -X DELETE http://localhost:8000/api/history
```

---

### GET /api/stats

**Статус:** `ready`

**Назначение:**  
Получить статистику использования чат-агента.

**Response body:**
```json
{
  "totalSessions": 10,
  "totalQueries": 25,
  "modeDistribution": {
    "search": 15,
    "consultation": 8,
    "clarification": 2
  },
  "avgMessagesPerSession": 2.5,
  "avgQueriesWithLinks": 1.8
}
```

**Ошибки:**
- `500` — ошибка при получении статистики

**Пример запроса:**
```bash
curl http://localhost:8000/api/stats
```

---

### GET /api/metrics/health

**Статус:** `ready`

**Назначение:**  
Вернуть KPI пайплайна для мониторинга здоровья системы.

**Response body:**
```json
{
  "totalSessions": 10,
  "totalExchanges": 25,
  "avgElapsedMs": 1250.5,
  "p95ElapsedMs": 2800.0,
  "avgMessagesToFirstSearch": 1.2,
  "clarificationRate": 0.15,
  "repeatSessionRate": 0.3,
  "kpiMet": true
}
```

**Ошибки:**
- `500` — ошибка вычисления метрик

**Пример запроса:**
```bash
curl http://localhost:8000/api/metrics/health
```

---

## WebSocket API

### WS /chat

**Статус:** `ready`

**Назначение:**  
WebSocket соединение для интерактивного чата с агентом. Поддерживает статусы выполнения, результаты поиска и консультации.

**URL:** `ws://localhost:8000/chat`

**Формат сообщений:**

Клиент отправляет:
```json
{
  "query": "Найди стратокастер до 500$",
  "sessionId": 1
}
```

Сервер отправляет статусы (progress updates):
```json
{
  "type": "status",
  "status": "Определяю режим..."
}
```

Сервер отправляет результат (search mode):
```json
{
  "type": "result",
  "mode": "search",
  "results": [...],
  "explanation": "Found 2 guitars matching your criteria",
  "sessionId": 1
}
```

Сервер отправляет результат (consultation mode):
```json
{
  "type": "result",
  "mode": "consultation",
  "answer": "Стратокастер — это...",
  "sessionId": 1
}
```

Сервер отправляет ошибку:
```json
{
  "type": "error",
  "status": "Запрос не может быть пустым"
}
```

**Режимы работы:**
- `search` — поиск гитар на Reverb
- `consultation` — ответ на вопрос о гитарах
- `clarification` — уточняющий вопрос (недостаточно данных)

**Ошибки:**
- `4001` — пустой запрос
- `4002` — превышено время ожидания (30 сек)
- `4003` — внутренняя ошибка

**Пример использования (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    query: 'Найди гитару до 1000$',
    sessionId: 1
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

## Сводная таблица статусов

| Endpoint | Method | Статус |
|----------|--------|--------|
| `/api/chat` | POST | ✅ ready |
| `/api/query/parse` | POST | ✅ ready |
| `/api/sessions` | GET | ✅ ready |
| `/api/sessions` | POST | ✅ ready |
| `/api/sessions/{id}/messages` | GET | ✅ ready |
| `/api/sessions/{id}` | DELETE | ✅ ready |
| `/api/history` | DELETE | ✅ ready |
| `/api/stats` | GET | ✅ ready |
| `/api/metrics/health` | GET | ✅ ready |
| `/chat` | WS | ✅ ready |

---

## Примечания

1. Все JSON-ответы используют **camelCase** для полей (настроено через Pydantic `alias_generator`).
2. Для работы LLM необходимо установить переменную окружения `GROQ_API_KEY`.
3. С Mock-режимом Reverb (`USE_MOCK_REVERB=true`) поиск работает без обращения к live-сайту.
4. WebSocket поддерживает автоматическое создание сессии, если `sessionId` не передан.
5. Таймаут обработки запроса — 30 секунд.
