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

### 2. Backend

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Сервер: `http://localhost:8000`

> Без `GROQ_API_KEY` проект запустится, но LLM-ответы будут в degraded-режиме.
> С `USE_MOCK_REVERB=true` поиск использует локальный набор мок-данных вместо обращения к Reverb.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Интерфейс: `http://localhost:5173`

### 4. Проверка

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

> Будет добавлен после реализации MVP

---

## Вклад участников

> Будет дополнен по ходу разработки
