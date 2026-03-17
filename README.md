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

## Запуск

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
cp ../.env.example ../.env    # заполни GROQ_API_KEY
uvicorn main:app --reload
```

Сервер: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Интерфейс: `http://localhost:5173`

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
