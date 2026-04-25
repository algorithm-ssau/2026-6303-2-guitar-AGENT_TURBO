# API Reference

Документ описывает REST и WebSocket API проекта по состоянию на week-07.

> Статусы:
> `implemented` - endpoint уже есть в текущем `main`
> `contract` - endpoint входит в согласованный API-контракт недели, но может зависеть от merge соседней ветки

## REST Endpoints

### `POST /api/chat` (`implemented`)

- Headers: `Content-Type: application/json`
- Назначение: синхронный запрос к пайплайну агента

Request:

```json
{
  "query": "Найди стратокастер до 500$"
}
```

Response (`search`):

```json
{
  "mode": "search",
  "results": [
    {
      "id": "r_001",
      "title": "Squier Classic Vibe Stratocaster",
      "price": 429,
      "currency": "USD",
      "listingUrl": "https://reverb.com/item/10000005-squier-classic-vibe-50s-telecaster-2024-butterscotch-blonde",
      "imageUrl": "https://images.reverb.com/image/upload/mock/squier-classic-vibe-telecaster.jpg"
    }
  ]
}
```

Response (`consultation`):

```json
{
  "mode": "consultation",
  "answer": "P90 - это тип синглового звукоснимателя..."
}
```

- Ошибки: `400`, `422`, `500`

### `POST /api/query/parse` (`implemented`)

- Headers: `Content-Type: application/json`
- Назначение: parse-only режим без LLM и без побочных эффектов

Request:

```json
{
  "query": "Найди Fender Strat до 500$"
}
```

Response:

```json
{
  "type": "Stratocaster",
  "budget": "≤ $500",
  "brand": "Fender",
  "tags": []
}
```

- Ошибки: `400`, `422`, `500`

### `GET /api/sessions?offset=0&limit=20` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: получить список сессий с пагинацией

Response:

```json
{
  "sessions": [
    {
      "id": 12,
      "title": "Найди стратокастер до 500$",
      "createdAt": "2026-04-25T08:10:00Z",
      "updatedAt": "2026-04-25T08:11:05Z"
    }
  ],
  "total": 42
}
```

- Ошибки: `400`, `422`, `500`

### `GET /api/sessions/{id}/messages` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: получить историю сообщений одной сессии

Response:

```json
{
  "items": [
    {
      "id": 101,
      "sessionId": 12,
      "userQuery": "Что такое P90?",
      "mode": "consultation",
      "answer": "P90 - это тип синглового звукоснимателя...",
      "results": null,
      "createdAt": "2026-04-25T08:11:05Z"
    }
  ]
}
```

- Ошибки: `400`, `404`, `500`

### `DELETE /api/sessions/{id}` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: удалить одну сессию

Response:

```json
{
  "ok": true
}
```

- Ошибки: `400`, `404`, `500`

### `DELETE /api/history` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: очистить всю историю

Response:

```json
{
  "deleted": 12
}
```

- Ошибки: `400`, `500`

### `GET /api/stats` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: статистика использования истории и режимов

Response:

```json
{
  "totalSessions": 12,
  "totalQueries": 31,
  "modeDistribution": {
    "search": 18,
    "consultation": 10,
    "clarification": 3
  },
  "avgMessagesPerSession": 2.58,
  "avgQueriesWithLinks": 1.75
}
```

- Ошибки: `400`, `500`

### `POST /api/feedback` (`contract`)

- Headers: `Content-Type: application/json`
- Назначение: отправить feedback по ответу агента

Request:

```json
{
  "sessionId": 12,
  "messageId": "1714048200",
  "value": "up"
}
```

Response:

```json
{
  "ok": true
}
```

- Ошибки: `400`, `422`, `500`

### `GET /api/feedback/stats` (`contract`)

- Headers: `Accept: application/json`
- Назначение: получить агрегированную статистику feedback

Response:

```json
{
  "likes": 18,
  "dislikes": 4,
  "total": 22
}
```

- Ошибки: `400`, `500`

### `GET /api/metrics/health` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: KPI пайплайна

Response:

```json
{
  "totalSessions": 0,
  "totalExchanges": 0,
  "avgElapsedMs": 0.0,
  "p95ElapsedMs": 0.0,
  "avgMessagesToFirstSearch": 0.0,
  "clarificationRate": 0.0,
  "repeatSessionRate": 0.0,
  "kpiMet": true
}
```

- Ошибки: `400`, `500`

### `GET /api/health/` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: сводный health-check backend

Response:

```json
{
  "status": "degraded",
  "checks": {
    "database": true,
    "llm_configured": false,
    "mock_mode": true,
    "reverb_api_configured": false
  },
  "version": "0.7.0"
}
```

- Ошибки: `500`

### `GET /api/health/ping` (`implemented`)

- Headers: `Accept: application/json`
- Назначение: liveness-check для контейнера и orchestration

Response:

```json
{
  "pong": true
}
```

- Ошибки: `500`

## WebSocket Endpoint

### `WS /chat` (`implemented`)

- Назначение: основной realtime-канал чата
- Протокол: JSON-сообщения

Client -> Server:

```json
{
  "query": "Найди стратокастер до 500$",
  "sessionId": 12
}
```

Типы исходящих сообщений:

### `status`

```json
{
  "type": "status",
  "status": "Определяю режим..."
}
```

### `result`

Consultation:

```json
{
  "type": "result",
  "mode": "consultation",
  "answer": "P90 - это тип синглового звукоснимателя...",
  "sessionId": 12
}
```

Clarification:

```json
{
  "type": "result",
  "mode": "clarification",
  "question": "Уточни, пожалуйста, нужен электро- или акустический инструмент?",
  "sessionId": 12
}
```

Search:

```json
{
  "type": "result",
  "mode": "search",
  "results": [
    {
      "id": "r_001",
      "title": "Yamaha Pacifica 112V",
      "price": 349,
      "currency": "USD",
      "imageUrl": "https://images.reverb.com/image/upload/mock/yamaha.jpg",
      "listingUrl": "https://reverb.com/item/10000006-yamaha-pacifica-112v"
    }
  ],
  "explanation": "Нашёл несколько недорогих вариантов...",
  "sessionId": 12
}
```

### `error`

```json
{
  "type": "error",
  "status": "Запрос не может быть пустым"
}
```

Типичный flow:

```text
user -> status("Определяю режим...")
     -> status("Формирую ответ..." | "Ищу на Reverb..." | "Ранжирую результаты...")
     -> result
```

## Модели данных

### `ChatRequest`

```json
{
  "query": "Найди Gibson Les Paul до 1200$"
}
```

### `ChatResponse`

```json
{
  "mode": "search",
  "results": []
}
```

или

```json
{
  "mode": "consultation",
  "answer": "..."
}
```

### `GuitarResult`

```json
{
  "id": "r_001",
  "title": "Gibson Les Paul Studio",
  "price": 999,
  "currency": "USD",
  "listingUrl": "https://reverb.com/item/10000004-gibson-les-paul-studio-2016-wine-red",
  "imageUrl": "https://images.reverb.com/image/upload/mock/gibson-les-paul-studio.jpg"
}
```

### `ParseQueryResponse`

```json
{
  "type": "Stratocaster",
  "budget": "≤ $500",
  "brand": "Fender",
  "tags": []
}
```

### `FeedbackRequest`

```json
{
  "sessionId": 12,
  "messageId": "1714048200",
  "value": "up"
}
```

### `HealthResponse`

```json
{
  "status": "ok",
  "checks": {
    "database": true,
    "llm_configured": true,
    "mock_mode": true,
    "reverb_api_configured": false
  },
  "version": "0.7.0"
}
```
