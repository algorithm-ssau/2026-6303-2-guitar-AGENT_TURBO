# TODO — Фокин Евгений

**Неделя 3:** 23–29 марта 2026
**Ветка:** `feature/fokin/pipeline-wiring`

---

## Задача 1 (Backend): связать полный пайплайн в service.py с поддержкой статусов

### Что делать

- Переписать `backend/agent/service.py` — заменить mock callbacks на реальные модули:
  - Импортировать: `LLMClient`, `extract_params_from_llm_response`, `search_reverb`, `rank_results`
  - Добавить `create_llm_client()` — создаёт LLMClient, возвращает None если нет ключа
  - Загружать промпты из `docs/CONSULTATION_PROMPT.md` и `docs/AGENT_PROMPT.md`
  - Добавить поддержку callback `on_status(text)` — опциональная функция, которую пайплайн вызывает на каждом этапе для отправки промежуточных статусов через WebSocket:
    - `on_status("Определяю режим...")` → после detect_mode
    - `on_status("Генерирую параметры поиска...")` → перед вызовом LLM
    - `on_status("Ищу на Reverb...")` → перед search_reverb
    - `on_status("Ранжирую результаты...")` → перед rank_results
    - `on_status("Формирую ответ...")` → для consultation перед вызовом LLM
  - Consultation: `detect_mode` → статус → LLM отвечает → return answer
  - Search: `detect_mode` → статус → LLM параметры → статус → search → статус → ranking → return results
  - **Обратная совместимость:** `llm_client`, `search_fn` и `on_status` — опциональные параметры, если не переданы — используются реальные модули, статусы не отправляются
  - Без GROQ_API_KEY → fallback (не падает, использует текст запроса как search_queries)

### Файлы

- Изменить: `backend/agent/service.py`

### Критерий приёмки

- С mock LLM и mock search: consultation возвращает answer
- С mock LLM и mock search: search возвращает results
- on_status вызывается на каждом этапе (проверить через mock)
- Без on_status — работает как раньше (обратная совместимость)
- Без GROQ_API_KEY → не падает, fallback
- Старые тесты из week-02 не ломаются

### Тест: `tests/test_pipeline.py`

- consultation с mock → answer + on_status вызван
- search с mock → results через ranking + on_status вызван на каждом шаге
- без API ключа → fallback
- без on_status → работает без ошибок

### Коммит: `feat: wire full search pipeline with status callbacks`

---

## Задача 2 (Frontend): индикатор режима в чате

### Что делать

- Создать `ModeBadge.tsx`:
  - Props: `mode: 'search' | 'consultation'`
  - search → зелёный бейдж с текстом "Поиск"
  - consultation → синий бейдж с текстом "Консультация"
- Расширить тип `Message` в `types.ts` — добавить `mode?: 'search' | 'consultation'`
- Обновить `Message.tsx` — рядом с меткой "Агент" показывать ModeBadge (если mode задан)

### Файлы

- Создать: `frontend/src/features/chat/components/ModeBadge.tsx`
- Изменить: `types.ts`, `Message.tsx`

### Критерий приёмки

- search → зелёный "Поиск"
- consultation → синий "Консультация"
- Без mode → бейдж не показывается

### Тест: `frontend/src/features/chat/__tests__/ModeBadge.test.tsx`

- mode="search" → текст "Поиск"
- mode="consultation" → текст "Консультация"

### Коммит: `feat: add mode badge component to chat messages`

---

## Задача 3 (Тестирование): end-to-end тесты через WebSocket

### Что делать

- Написать `tests/test_e2e.py` используя FastAPI TestClient с `client.websocket_connect("/chat")`
- Минимум 4 теста:
  - Полный search flow (mock LLM) → получаем серию status сообщений → финальный result с mode=search
  - Полный consultation flow (mock LLM) → status → result с mode=consultation, answer не пустой
  - Пустой query → type="error"
  - Проверить что статусы приходят в правильном порядке (определение режима → поиск → ранжирование)
- Мокать `create_llm_client` через `unittest.mock.patch`

### Файлы

- Создать: `tests/test_e2e.py`

### Критерий приёмки

- Все тесты проходят, не зависят от внешних API
- Покрыты оба режима + ошибки + порядок статусов

### Коммит: `test: add end-to-end WebSocket tests for full pipeline`
