# 2026-6303-2-guitar-AGENT_TURBO

ИИ-агент по подбору гитар с интеграцией поиска на Reverb.

> Подробное описание продукта: [prd/prd.md](prd/prd.md)
> План разработки: [PROJECT_PLAN.md](PROJECT_PLAN.md)
> Стек технологий: [STACK.md](STACK.md)
> Архитектура и принципы разработки: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Команда

| # | Участник | Основной модуль |
|---|----------|----------------|
| 1 | Сальников Илья | Chat UI |
| 2 | Павлов Виктор | LLM-интерпретация |
| 3 | Мергалиев Радмир | Генерация search params |
| 4 | Сидоров Артемий | Интеграция с Reverb |
| 5 | Хасанов Дамир | Ранжирование результатов |
| 6 | Фокин Евгений | Консультационный режим |

---

## Changelog

> История изменений по неделям: [CHANGELOG.md](CHANGELOG.md)

---

## Структура проекта

```
backend/          # Python + FastAPI
├── main.py
├── agent/
├── search/
└── ranking/
frontend/         # Vite + React
├── src/
└── ...
docs/             # документация команды
tests/            # тесты
requirements.txt
.env.example
```

---

## Быстрый старт

### 1. Клонирование и настройка окружения

```bash
git clone <url-репозитория>
cd 2026-6303-2-guitar-AGENT_TURBO

# Создаём .env из шаблона
cp .env.example .env
# Заполни GROQ_API_KEY в .env (получить: https://console.groq.com/)
```

### 2. Вариант А: Docker

```bash
cp .env.example .env
docker compose up --build
```

Backend будет доступен по адресу `http://localhost:8000`.

> Если `GROQ_API_KEY` не задан, backend стартует в degraded-режиме.
> Если `USE_MOCK_REVERB=true`, поиск использует локальный набор `tests/mock_reverb.json`.

### 3. Вариант Б: локальный backend

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Сервер: `http://localhost:8000`

> Без `GROQ_API_KEY` проект запустится, но LLM-ответы будут в degraded-режиме.
> С `USE_MOCK_REVERB=true` поиск использует локальный набор мок-данных вместо обращения к Reverb.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Интерфейс: `http://localhost:5173`

### 5. Проверка

```bash
# REST API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Что такое хамбакер?"}'

# Тесты
pytest tests/ -v
```

---

## Используемые технологии

> См. [STACK.md](STACK.md)

---

## Архитектура

```
User → LLM → JSON params → Reverb script → Results → Ranking → Links → User
```

Подробнее в [prd/prd.md](prd/prd.md) и [PROJECT_PLAN.md](PROJECT_PLAN.md).

---

## Пример запроса и результата

### Поиск

Пользователь:

```text
Найди стратокастер до 500$
```

Пайплайн:

```text
User
  -> LLM / parse stage
  -> search params: {"type":"stratocaster","price_max":500}
  -> Reverb search (mock или live)
  -> ranking
  -> 3 карточки результатов
```

Пример ответа:

```text
Нашёл несколько подходящих вариантов до 500$:

1. Squier Classic Vibe Stratocaster - $429
2. Yamaha Pacifica 112V - $349
3. Fender Standard Stratocaster MIM (used) - $499
```

### Консультация

Пользователь:

```text
Что такое P90?
```

Пример ответа:

```text
P90 - это тип синглового звукоснимателя. По звучанию он обычно плотнее и жирнее,
чем классический single coil, но при этом сохраняет больше открытости и атаки,
чем хамбакер. Его часто выбирают для блюза, гаражного рока и винтажного звучания.
```

### UX-возможности

- Чат поддерживает поиск и консультационный режим.
- История диалогов хранится по сессиям и доступна через sidebar.
- В пользовательском сценарии week-07 также предусмотрены feedback-кнопки `👍/👎` и экспорт истории чата как часть общей UX-полировки продукта.

---

## Вклад участников

| Участник | Основной вклад |
|---|---|
| Павлов Виктор | LLM-клиент, промпты, маппинг абстракций, суммаризация контекста |
| Мергалиев Радмир | API-контракт, Pydantic-модели, карточки гитар, feedback |
| Сальников Илья | Chat UI, дизайн-система, `useChat` хук, UX-полировка |
| Сидоров Артемий | Интеграция Reverb API/парсинга, история чата, Docker, observability |
| Хасанов Дамир | Алгоритм ранжирования, `BudgetHint`, `RelevanceBadge` |
| Фокин Евгений | Консультационный режим, `mode_detector`, пайплайн, метрики |
