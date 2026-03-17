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

### Неделя 0 — 3–8 марта 2026

- Инициализация репозитория, настройка Git Flow и веток (`main`, `feature/*`)
- Составлен PRD: описание продукта, сценарии использования, функциональные и нефункциональные требования ([prd/prd.md](prd/prd.md))
- Составлен PROJECT_PLAN.md: архитектура, этапы разработки, требования по коммитам, распределение модулей по участникам
- Планирование работы на следующую неделю: подготовка TODO-файлов для каждого участника, создание STACK.md

### Неделя 1 — 9–15 марта 2026

- **Сальников** — описан дизайн Chat UI ([docs/UI_DESIGN.md](docs/UI_DESIGN.md)), добавлен скелет интерфейса (поле ввода, кнопка, область вывода), написан README фронтенда
- **Павлов** — написан черновик системного промпта агента ([docs/AGENT_PROMPT.md](docs/AGENT_PROMPT.md)), составлена таблица маппинга абстракций в параметры ([docs/MAPPING.md](docs/MAPPING.md)), добавлены тестовые сценарии ([docs/test_scenarios.md](docs/test_scenarios.md))
- **Мергалиев** — описан формат search params и контракт API ([docs/SEARCH_PARAMS.md](docs/SEARCH_PARAMS.md)), добавлены примеры запрос → JSON → ответ
- **Сидоров** — проведено исследование Reverb ([docs/REVERB_RESEARCH.md](docs/REVERB_RESEARCH.md)), добавлена заглушка `search_reverb()` ([backend/search/search_reverb.py](backend/search/search_reverb.py)), подготовлены мок-данные ([tests/mock_reverb.json](tests/mock_reverb.json))
- **Хасанов** — описан алгоритм ранжирования с критериями и весами ([docs/RANKING.md](docs/RANKING.md)), добавлена заглушка `rank_results()` ([backend/ranking/ranking.py](backend/ranking/ranking.py))
- **Фокин** — описаны правила переключения режимов поиск/консультация, написан черновик промпта консультационного режима с примерами вопросов

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
