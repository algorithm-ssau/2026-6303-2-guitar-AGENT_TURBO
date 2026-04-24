# TODO — Мергалиев Радмир

**Неделя 8:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/mergaliev/api-reference-w8`

> Независимая release-задача по API-контракту.
> Не трогать backend runtime-код, frontend runtime-код, ranking, Docker.
> Не трогать `docs/API_REFERENCE.md`, потому что этот файл уже запланирован в week-07 у Сидорова.
> Можно выполнять даже если часть week-07 endpoint-ов ещё не смержена: такие endpoint-ы отметить как `planned/pending`.

---

## Задача: финальная API Release Reference + валидные JSON-примеры

Нужно подготовить документацию API для защиты и набор JSON-примеров, которые можно автоматически проверить.

---

## Шаг 1 — JSON examples

### Что делать

Создать папку `docs/examples/api/`.

Создать файлы:

- `chat_search.request.json`
- `chat_search.response.json`
- `chat_consultation.request.json`
- `chat_consultation.response.json`
- `sessions.response.json`
- `messages.response.json`
- `metrics_health.response.json`
- `error.response.json`

Каждый файл должен быть валидным JSON.

Пример `chat_search.request.json`:

```json
{
  "query": "Найди стратокастер до 500$"
}
```

Пример `error.response.json`:

```json
{
  "detail": "Запрос не может быть пустым"
}
```

### Файлы

- Создать: `docs/examples/api/*.json`

### Критерий приёмки

- все JSON-файлы парсятся;
- нет placeholder-значений вроде `TODO`, `...`, `example.com`;
- response-примеры используют camelCase для frontend-facing полей.

### Коммит

`docs: add final API JSON examples`

---

## Шаг 2 — финальный API Release Reference

### Что делать

Создать `docs/API_RELEASE_REFERENCE.md`.

Это отдельный release-документ week-08. Он не заменяет и не редактирует `docs/API_REFERENCE.md` из week-07.

Описать endpoints:

- `POST /api/chat`
- `POST /api/query/parse`
- `GET /api/sessions`
- `POST /api/sessions`
- `GET /api/sessions/{id}/messages`
- `DELETE /api/sessions/{id}`
- `DELETE /api/history`
- `GET /api/stats`
- `GET /api/metrics/health`
- `WS /chat`

Для каждого endpoint:

- method + URL;
- назначение;
- request body;
- response body;
- пример;
- ошибки;
- статус: `ready`, `degraded`, `pending`.

Если endpoint ещё не реализован в main, не писать что он готов. Отметить `pending`.

### Файлы

- Создать: `docs/API_RELEASE_REFERENCE.md`

### Критерий приёмки

- все основные REST/WS точки описаны;
- явно указаны pending/degraded endpoint-ы;
- документ не врёт о текущем состоянии проекта.

### Коммит

`docs: add final API release reference`

---

## Шаг 3 — тест валидности API examples

### Что делать

Создать `tests/test_api_examples.py`.

Тест должен:

- найти все `docs/examples/api/*.json`;
- проверить, что каждый файл парсится через `json.loads`;
- проверить, что request-файлы содержат ожидаемые поля;
- проверить, что response-файлы не пустые;
- проверить, что `error.response.json` содержит `detail`.

### Файлы

- Создать: `tests/test_api_examples.py`

### Критерий приёмки

- `pytest tests/test_api_examples.py -v` проходит;
- при невалидном JSON тест показывает имя файла.

### Коммит

`test: validate API example fixtures`
