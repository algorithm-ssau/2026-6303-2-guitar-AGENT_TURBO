# TODO — Фокин Евгений

**Неделя 4:** 30 марта – 5 апреля 2026
**Ветка:** `feature/fokin/router-env`

> **Приоритет: КРИТИЧЕСКИЙ.** Задача 1 должна быть завершена в первые 2 дня — от неё зависит Мергалиев.

---

## Задача 1 (Backend): оживить POST /api/chat и добавить .env документацию

### Что делать

- Переписать `backend/search/router.py` — убрать заглушку, подключить реальный pipeline:
  - Импортировать `interpret_query` из `backend.agent.service`
  - Вызывать `interpret_query(text=request.query)` и возвращать реальный результат
  - Для mode="search" → `ChatResponse(mode="search", results=result.get("results", []))`
  - Для mode="consultation" → `ChatResponse(mode="consultation", answer=result.get("answer", ""))`
- Создать `.env.example` в корне проекта:
  ```
  # Обязательно: API ключ Groq (https://console.groq.com/)
  GROQ_API_KEY=gsk_...

  # Опционально: модель LLM (по умолчанию llama-3.3-70b-versatile)
  LLM_MODEL=llama-3.3-70b-versatile

  # Опционально: использовать мок-данные вместо реального Reverb API
  USE_MOCK_REVERB=true

  # Опционально: токен Reverb API (для реального поиска)
  REVERB_API_TOKEN=
  ```
- Обновить `backend/main.py` — добавить загрузку `.env` через `python-dotenv`:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  ```
- Обновить `README.md` — добавить секцию "Быстрый старт" с инструкцией по `.env`

### Файлы

- Изменить: `backend/search/router.py`
- Создать: `.env.example`
- Изменить: `backend/main.py`
- Изменить: `README.md`

### Критерий приёмки

- `POST /api/chat` с `{"query": "Найди Fender"}` → реальный результат с mode="search" и results
- `POST /api/chat` с `{"query": "Что такое хамбакер?"}` → mode="consultation" с answer
- `.env.example` содержит все необходимые переменные с комментариями
- `python-dotenv` загружает `.env` при старте

### Тест: `tests/test_router_live.py`

- POST /api/chat search query → mode="search", results не пустой (с USE_MOCK_REVERB=true)
- POST /api/chat consultation → mode="consultation", answer не пустой
- POST /api/chat пустой query → 422 (validation error)

### Коммит: `feat: wire router.py to real pipeline and add env documentation`

---

## Задача 2 (Backend): graceful degradation — работа без внешних сервисов

### Что делать

- Обновить `backend/agent/service.py` — добавить обработку ошибок на каждом этапе:
  - `detect_mode` выбросил исключение → fallback на "consultation"
  - `LLMClient` недоступен (нет ключа) → для search: использовать текст запроса как search_queries, для consultation: вернуть "Сервис LLM временно недоступен"
  - `search_reverb` выбросил исключение → вернуть пустой results с пояснением
  - `rank_results` выбросил исключение → вернуть неранжированные результаты (первые 5)
- Обновить `backend/main.py` — WebSocket endpoint:
  - Обернуть всю обработку в try/except с отправкой `type="error"`
  - Добавить логирование ошибок через `logging` модуль
- Создать `backend/utils/logger.py`:
  - Настроить формат: `[%(asctime)s] %(levelname)s: %(message)s`
  - Уровень по умолчанию: INFO
  - Логировать: каждый запрос, каждую ошибку, время обработки

### Файлы

- Изменить: `backend/agent/service.py`
- Изменить: `backend/main.py`
- Создать: `backend/utils/logger.py`

### Критерий приёмки

- Без GROQ_API_KEY → search всё равно работает (mock data), consultation → сообщение об ограничении
- Ошибка в search_reverb → пользователь видит сообщение, не crash
- Все ошибки логируются с timestamp
- WebSocket никогда не падает — всегда отправляет type="error"

### Тест: `tests/test_graceful_degradation.py`

- Mock search_reverb бросает Exception → fallback, не crash
- Mock rank_results бросает Exception → неранжированные первые 5
- Без GROQ_API_KEY → pipeline работает в degraded mode

### Коммит: `feat: add graceful degradation and error logging`

---

## Задача 3 (Тестирование): smoke-тест запуска проекта с нуля

### Что делать

- Написать `tests/test_startup_smoke.py`:
  - Проверить что `backend/main.py` импортируется без ошибок
  - Проверить что FastAPI app создаётся
  - Проверить `GET /` → `{"status": "ok"}`
  - Проверить что WebSocket `/chat` принимает соединение
  - Проверить что `POST /api/chat` работает (не 500)
  - Все тесты — без внешних зависимостей (без GROQ_API_KEY, без REVERB_API_TOKEN)
- Написать `docs/QUICKSTART.md`:
  - Пошаговая инструкция: клонирование → `.env` → `pip install` → `uvicorn` → `npm run dev` → открыть браузер
  - Описание ожидаемого результата

### Файлы

- Создать: `tests/test_startup_smoke.py`
- Создать: `docs/QUICKSTART.md`

### Критерий приёмки

- Новый человек может запустить проект за 5 минут по QUICKSTART.md
- Smoke-тесты проходят на чистой машине с Python 3.10+ и Node 18+

### Коммит: `test: add startup smoke tests and quickstart guide`
