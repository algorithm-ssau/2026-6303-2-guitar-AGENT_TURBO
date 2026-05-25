# 2026-6303-2-guitar-AGENT_TURBO

ИИ-агент по подбору гитар на Reverb.

---

## Что делает продукт

Чат-агент, который помогает выбрать гитару:

- Принимает запрос на естественном языке — конкретный («Telecaster до 800$») или абстрактный («хочу тёплый джазовый звук, бюджет 1000»).
- Интерпретирует абстрактные характеристики звука (тёплый, яркий, плотный, мягкая атака и др.) в технические параметры инструмента (датчики, мензура, тип корпуса).
- Ищет подходящие объявления на Reverb.
- Ранжирует результаты по бюджету и релевантности, возвращает 3–5 ссылок с кратким пояснением.
- Отвечает на консультационные вопросы по теме (звукосниматели, древесина, мензура и т.п.) без вызова поиска.

---

## Как запустить

### Шаг 1. Получить Groq API key (бесплатно, ~1 минута)

LLM-провайдер — [Groq](https://groq.com/). На бесплатном тарифе всё уже работает.

1. Открой [console.groq.com](https://console.groq.com/).
2. Зарегистрируйся через Google или GitHub (бесплатно, без карты).
3. В левом меню выбери **API Keys** → **Create API Key**, скопируй значение (вида `gsk_...`).

> Ключ нужен для работы LLM — без него агент не сможет отвечать на запросы.

### Шаг 2. Склонировать репозиторий и подготовить `.env`

```bash
git clone https://github.com/algorithm-ssau/2026-6303-2-guitar-AGENT_TURBO.git
cd 2026-6303-2-guitar-AGENT_TURBO
cp .env.example .env
```

Открой `.env` и вставь свой ключ в строку `GROQ_API_KEY=...`. Остальные переменные уже настроены — менять ничего не нужно.

### Шаг 3. Запустить — Docker (рекомендуется, одна команда)

```bash
docker compose up --build
```

- Интерфейс: `http://localhost` (открой в браузере, зарегистрируйся, начинай диалог)
- Backend API: `http://localhost:8000`

### Альтернатива — локально без Docker (Python 3.10+, Node.js 18+)

```bash
# Backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload  # → http://localhost:8000

# Frontend (во втором терминале)
cd frontend && npm install && npm run dev  # → http://localhost:5173
```

### Проверка

```bash
curl http://localhost:8000/api/health/
pytest tests/ -v
```

---

## Архитектура решения

```
User → Frontend (React) → Backend (FastAPI)
                              │
                              ├─ LLM-router (Groq) — определяет режим: search / consultation / clarification
                              │
                              ├─ search  → search params → Reverb → Ranking → Answer-LLM
                              ├─ consultation → Answer-LLM с системным промптом по гитарам
                              └─ clarification → уточняющий вопрос
                              │
                              └─ БД — история сессий, авторизация, feedback
```

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md), [prd/prd.md](prd/prd.md), [STACK.md](STACK.md).

---

## Вклад участников

Команда работала по принципу **full-stack** — каждый участник занимался и backend-, и frontend-частью. Ниже — основная зона ответственности и характерные доработки на обеих сторонах.

| Участник | Backend | Frontend |
|---|---|---|
| Сальников Илья | Доработки `main.py`, agent flows, WS-эндпоинт | Chat UI, дизайн-система, `useChat`, sessions, UX-полировка |
| Павлов Виктор | LLM-клиент, промпты, маппинг абстракций, суммаризация контекста | Компоненты `GuitarCard`, `ResultsList`, интеграция с агентом |
| Мергалиев Радмир | API-контракт, Pydantic-модели, search params, feedback, history | Карточки гитар, фронтенд-валидация, API-клиент |
| Сидоров Артемий | Reverb API/парсер, history-сервис, Docker, observability | Sidebar истории, `SearchStatus`, фронтенд интеграции |
| Фокин Евгений | LLM-router pipeline, consultation, history, метрики, `main.py` | Центральная часть чата, sessions, toast/confirm, mode badges |
| Хасанов Дамир (перевёлся на другое направление в середине семестра) | Алгоритм ранжирования, agent integration | `BudgetHint`, `RelevanceBadge`, frontend-доработки |
