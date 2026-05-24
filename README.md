# 2026-6303-2-guitar-AGENT_TURBO

ИИ-агент по подбору гитар на Reverb.

---

## Что делает продукт

Чат-агент, который помогает выбрать гитару:

- Принимает запрос на естественном языке — конкретный («Telecaster до 800$») или абстрактный («хочу тёплый джазовый звук, бюджет 1000»).
- Интерпретирует абстрактные характеристики звука (тёплый, яркий, плотный, мягкая атака и др.) в технические параметры инструмента (датчики, мензура, тип корпуса).
- Ищет подходящие объявления на Reverb (или в локальном наборе мок-данных).
- Ранжирует результаты по бюджету и релевантности, возвращает 3–5 ссылок с кратким пояснением.
- Отвечает на консультационные вопросы по теме (звукосниматели, древесина, мензура и т.п.) без вызова поиска.

---

## Как запустить

### Вариант А — Docker (рекомендуется)

```bash
git clone https://github.com/algorithm-ssau/2026-6303-2-guitar-AGENT_TURBO.git
cd 2026-6303-2-guitar-AGENT_TURBO
cp .env.example .env
docker compose up --build
```

- Интерфейс: `http://localhost`
- Backend API: `http://localhost:8000`

`.env` опционально: `GROQ_API_KEY` для полноценных LLM-ответов (без него — degraded). `USE_MOCK_REVERB=true` по умолчанию — поиск работает без обращения к Reverb.

### Вариант Б — локально (Python 3.10+, Node.js 18+)

```bash
# Backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
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
                              ├─ search  → search params → Reverb (или mock) → Ranking → Answer-LLM
                              ├─ consultation → Answer-LLM с системным промптом по гитарам
                              └─ clarification → уточняющий вопрос
                              │
                              └─ БД — история сессий, авторизация, feedback
```

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md), [prd/prd.md](prd/prd.md), [STACK.md](STACK.md).

---

## Вклад участников

| Участник         | Основной вклад                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| Сальников Илья   | Chat UI, дизайн-система, `useChat` хук, UX-полировка                                                    |
| Павлов Виктор    | LLM-клиент, промпты, маппинг абстракций, суммаризация контекста                                         |
| Мергалиев Радмир | API-контракт, Pydantic-модели, карточки гитар, feedback                                                 |
| Сидоров Артемий  | Интеграция Reverb API/парсинга, история чата, Docker, observability                                     |
| Фокин Евгений    | Консультационный режим, LLM-router pipeline, метрики                                                    |
| Хасанов Дамир    | Алгоритм ранжирования, `BudgetHint`, `RelevanceBadge` (участвовал в марте–апреле 2026, затем перевёлся) |
