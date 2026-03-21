# Стек технологий

---

## Backend — Python

| Компонент | Технология | Статус |
|-----------|-----------|--------|
| Язык | Python 3.11+ | ✅ |
| Фреймворк | FastAPI | ✅ |
| Менеджер пакетов | pip + `requirements.txt` | ✅ |
| Виртуальная среда | venv | ✅ |
| LLM API | Groq (бесплатные модели) | ✅ |
| LLM SDK | `groq` | ✅ |
| Интеграция с Reverb | Официальный Reverb API, парсинг только как fallback | ✅ |

---

## Frontend — React

| Компонент | Технология | Статус |
|-----------|-----------|--------|
| Язык | JavaScript (JS) | ✅ |
| Фреймворк | React | ✅ |
| Сборщик | Vite | ✅ |
| Менеджер пакетов | npm | ✅ |
| Связь с backend | fetch / axios → FastAPI | ✅ |

---

## LLM

| Компонент | Значение |
|-----------|----------|
| Провайдер | Groq |
| Модель | задаётся через `LLM_MODEL` в `.env` (дефолт: `llama-3.3-70b-versatile`) |
| Доступные модели | `llama-3.3-70b-versatile`, `qwen-qwq-32b`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768` |
| Способ вызова | Python SDK (`groq`, OpenAI-compatible) |
| API ключ | в `.env`, не коммитить |

---

## Интеграция с Reverb

| Вопрос | Статус |
|--------|--------|
| Способ (API vs парсинг) | ✅ основной вариант: официальный Reverb API; парсинг только как запасной путь |
| Библиотека | `requests` для вызова Reverb API |
| Реализация | ✅ `backend/search/search_reverb.py` — функция `search_reverb(search_queries, price_min, price_max)` |
| Тестирование | ✅ `tests/test_search.py` — тесты с мок-HTTP (`responses`), тесты на граничные случаи |
| Мок-данные | ✅ `tests/mock_reverb.json` — 5 реалистичных объявлений для тестирования |
| Переменная окружения | ✅ `USE_MOCK_REVERB` — переключатель режимов (true/false) |

---

## Структура проекта

```
project/
├── backend/          # Python + FastAPI
│   ├── main.py       # точка входа
│   ├── agent/        # LLM-логика (Павлов)
│   ├── search/       # Reverb-скрипт (Сидоров, Мергалиев)
│   └── ranking/      # ранжирование (Хасанов)
├── frontend/         # Vite + React
│   ├── src/
│   └── ...
├── docs/             # документация команды
├── tests/            # тесты
├── .env.example      # пример переменных окружения
├── requirements.txt  # Python-зависимости
└── README.md
```

---

## Переменные окружения (`.env`)

```
GROQ_API_KEY=...
LLM_MODEL=llama-3.3-70b-versatile
USE_MOCK_REVERB=false
```

> `.env` не коммитится. В репозитории хранится только `.env.example`.

---

## Открытые вопросы

- [x] Способ интеграции с Reverb — выбран официальный Reverb API, парсинг остаётся fallback-вариантом
- [ ] Нужен ли CORS-middleware в FastAPI (скорее всего да)
- [ ] Формат хранения маппинга абстракций: JSON-файл vs Python-словарь

---

_Обновлено: 21 марта 2026_
