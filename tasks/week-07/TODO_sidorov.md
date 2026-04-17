# TODO — Сидоров Артемий

**Неделя 7:** 21–27 апреля 2026
**Ветка:** `feature/sidorov/docker-infra-w7`

> Независимая задача. Все файлы — его собственные, никто другой в week-7 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Infra): Dockerfile для backend

### Что делать

- Создать `Dockerfile` в корне проекта:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY backend/ ./backend/
  COPY docs/ ./docs/
  COPY tests/mock_reverb.json ./tests/mock_reverb.json

  EXPOSE 8000
  ENV PYTHONUNBUFFERED=1
  ENV USE_MOCK_REVERB=true

  CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- Проверить что образ билдится: `docker build -t guitar-agent-backend .`
- Проверить что контейнер стартует: `docker run -p 8000:8000 guitar-agent-backend` → `curl http://localhost:8000/` → `{"status":"ok"}`

### Файлы

- Создать: `Dockerfile`

### Критерий приёмки

- `docker build -t guitar-agent-backend .` проходит без ошибок
- Контейнер стартует, GET / возвращает 200
- Размер образа разумный (< 500 MB)
- Без GROQ_API_KEY в ENV — работает в degraded-режиме (мок-данные)

### Тест: ручная проверка + скрипт `scripts/docker_smoke.sh` (опционально)

### Коммит: `feat: add Dockerfile for backend`

---

## Задача 2 (Infra): docker-compose + .dockerignore

### Что делать

- Создать `docker-compose.yml`:
  ```yaml
  services:
    backend:
      build: .
      ports:
        - "8000:8000"
      environment:
        - USE_MOCK_REVERB=${USE_MOCK_REVERB:-true}
        - GROQ_API_KEY=${GROQ_API_KEY:-}
        - LLM_MODEL=${LLM_MODEL:-llama-3.3-70b-versatile}
      volumes:
        - ./backend/history/chat.db:/app/backend/history/chat.db
  ```
- Создать `.dockerignore`:
  ```
  venv/
  __pycache__/
  .pytest_cache/
  node_modules/
  frontend/
  *.db-shm
  *.db-wal
  .git/
  .env
  tasks/
  design/
  ```
- Проверить `docker-compose up` — поднимает backend на порту 8000

### Файлы

- Создать: `docker-compose.yml`
- Создать: `.dockerignore`

### Критерий приёмки

- `docker-compose up` поднимает backend
- `.env` на хосте пробрасывается через `GROQ_API_KEY=...` переменную
- Volume для БД работает (данные сохраняются между перезапусками)

### Коммит: `feat: add docker-compose and dockerignore`

---

## Задача 3 (Docs): README с Docker, примером и вкладом участников

### Что делать

- Обновить `README.md`:
  - **Раздел "Быстрый старт" — добавить подраздел Docker:**
    ```
    ### Вариант А: Docker
    cp .env.example .env
    docker-compose up
    ```
  - **Раздел "Пример запроса и результата"** — заполнить реальным примером:
    - Скриншот чата (или ASCII-схема, если нет скриншота) с запросом "Найди стратокастер до 500$" и 3 карточками-результатами
    - Пример consultation-ответа на "Что такое P90?"
    - Упоминание поддержки 👍/👎 и экспорта чата
  - **Раздел "Вклад участников"** — заполнить по CHANGELOG:
    ```
    | Участник | Основной вклад |
    |---|---|
    | Павлов Виктор | LLM-клиент, промпты, маппинг абстракций, суммаризация контекста |
    | Мергалиев Радмир | API-контракт, Pydantic-модели, карточки гитар, feedback |
    | Сальников Илья | Chat UI, дизайн-система, useChat хук, UX-полировка |
    | Сидоров Артемий | Интеграция Reverb API, история чата, Docker, observability |
    | Хасанов Дамир | Алгоритм ранжирования, BudgetHint, RelevanceBadge |
    | Фокин Евгений | Консультационный режим, mode_detector, пайплайн, метрики |
    ```

### Файлы

- Изменить: `README.md`

### Критерий приёмки

- README содержит секцию Docker с командами
- Раздел "Пример запроса и результата" заполнен (не placeholder)
- Таблица вклада участников заполнена
- Ссылки в README работают

### Коммит: `docs: fill README with Docker, example, and contributors`

---

## Задача 4 (Backend): health check endpoint

### Что делать

- Создать `backend/health/__init__.py` (пустой)
- Создать `backend/health/router.py`:
  - `router = APIRouter(prefix="/api/health", tags=["health"])`
  - `GET /` → `HealthResponse`:
    ```python
    class HealthResponse(BaseModel):
        status: Literal["ok", "degraded"]
        checks: dict
        version: str  # hardcoded "0.7.0"
    ```
    - `checks`:
      - `database`: True/False (проверка SQLite — `SELECT 1`)
      - `llm_configured`: bool — проверка наличия `GROQ_API_KEY` env
      - `mock_mode`: bool — значение `USE_MOCK_REVERB`
      - `reverb_api_configured`: bool — наличие `REVERB_API_TOKEN`
    - `status="degraded"` если БД недоступна или `llm_configured=False`, иначе "ok"
  - `GET /ping` → `{"pong": true}` (для простого liveness check)
- **НЕ трогать `main.py`** — autoloader Фокина подцепит новый роутер автоматически

### Файлы

- Создать: `backend/health/__init__.py`
- Создать: `backend/health/router.py`

### Критерий приёмки

- `GET /api/health/` → 200 + JSON с checks
- `GET /api/health/ping` → `{"pong": true}`
- Без GROQ_API_KEY → `status: "degraded"`, `llm_configured: false`
- С GROQ_API_KEY → `status: "ok"`

### Тест: `tests/test_health.py`

- GET /api/health/ → 200, все ключи присутствуют
- GET /api/health/ping → `{"pong": true}`
- Мокнуть env без GROQ_API_KEY → status = degraded

### Коммит: `feat: add health check endpoint`

---

## Задача 5 (Docs): API Reference — полное описание endpoints

### Что делать

- Создать `docs/API_REFERENCE.md` — документация всех endpoints:
  - Секции:
    - `## REST Endpoints`
      - `POST /api/chat` — синхронный запрос, пример request/response JSON
      - `POST /api/query/parse` — parse-only (Мергалиев в этой же неделе)
      - `GET /api/sessions?offset=0&limit=20` — история
      - `GET /api/sessions/{id}/messages` — сообщения сессии
      - `DELETE /api/sessions/{id}` — удалить сессию
      - `DELETE /api/history` — очистить всё
      - `GET /api/stats` — статистика (Мергалиев week-5)
      - `POST /api/feedback` — отправить 👍/👎 (Мергалиев week-7)
      - `GET /api/feedback/stats` — агрегация feedback (Мергалиев week-7)
      - `GET /api/metrics/health` — KPI (Фокин week-7)
      - `GET /api/health/` — health check
    - `## WebSocket Endpoint`
      - `WS /chat` — основной endpoint; типы сообщений: `status`, `result`, `error`
      - Пример flow (user → status × N → result)
    - `## Мoдели данных`
      - ChatRequest, ChatResponse, GuitarResult, ParseQueryResponse, FeedbackRequest, HealthResponse
- Каждый endpoint:
  - URL + method
  - Headers
  - Request body (JSON пример)
  - Response body (JSON пример)
  - Коды ошибок (400, 422, 500)

### Файлы

- Создать: `docs/API_REFERENCE.md`

### Критерий приёмки

- Все endpoints описаны с примерами JSON
- WS-протокол описан со всеми типами сообщений
- Pydantic-модели описаны
- Markdown-валидный

### Коммит: `docs: add full API reference documentation`
