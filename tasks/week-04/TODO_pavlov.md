# TODO — Павлов Виктор

**Неделя 4:** 30 марта – 5 апреля 2026
**Ветка:** `feature/pavlov/chat-ws-switch`

> **Зависимость:** задача 1 зависит от useChat хука Сальникова. Начать можно с задачи 2, задачу 1 делать после мержа `feature/salnikov/ws-hook`.

---

## Задача 1 (Frontend): переключить Chat.tsx на WebSocket через useChat

### Что делать

- Переписать `frontend/src/features/chat/components/Chat.tsx`:
  - Убрать импорт `sendMessage` из `api.ts`
  - Использовать хук `useChat()` из `hooks/useChat.ts`
  - Получить: `{ messages, isLoading, error, status, sendMessage }`
  - Передать `messages` в `MessageList`
  - Показывать `status` при isLoading через `SearchStatus` (вместо статичного "Агент подбирает гитары...")
  - Показывать `error` через `ErrorMessage` с кнопкой retry (повторная отправка последнего запроса)
  - При пустых results в search-режиме → показывать `EmptyResults`
- Обновить `frontend/src/features/chat/components/Message.tsx`:
  - Для consultation mode: показывать `content` как текстовый ответ
  - Для search mode: показывать `ResultsList` с карточками гитар
  - Убедиться что `ModeBadge` корректно отображается для обоих режимов

### Файлы

- Изменить: `frontend/src/features/chat/components/Chat.tsx`
- Изменить: `frontend/src/features/chat/components/Message.tsx`

### Критерий приёмки

- Chat UI подключается к WS при загрузке страницы
- Отправка сообщения → видны промежуточные статусы ("Определяю режим...", "Ищу на Reverb...") → финальный ответ
- Search mode: карточки гитар со ссылками на Reverb
- Consultation mode: текстовый ответ с синим бейджем "Консультация"
- Ошибка → ErrorMessage с кнопкой retry

### Тест: `frontend/src/features/chat/__tests__/Chat.test.tsx`

- Обновить существующий тест: mock useChat → рендер Chat → messages отображаются
- Проверить отображение промежуточного статуса при isLoading
- Проверить отображение error через ErrorMessage

### Коммит: `feat: switch Chat.tsx from HTTP to WebSocket via useChat hook`

---

## Задача 2 (Backend): улучшить промпт для точного извлечения параметров

### Что делать

- Обновить `docs/AGENT_PROMPT.md`:
  - Добавить примеры маппинга: "тёплый звук" → Gibson, P90, humbucker; "яркий звук" → Fender, single coil
  - Добавить инструкцию: если пользователь указал конкретную модель — использовать её напрямую
  - Добавить инструкцию: если бюджет указан в рублях — конвертировать по курсу ~100 руб/доллар
- Обновить `docs/CONSULTATION_PROMPT.md`:
  - Добавить примеры ответов: структурированный текст с подзаголовками
  - Добавить ограничение: ответ до 300 слов
  - Добавить инструкцию: если вопрос не о гитарах — вежливо отказать
- Обновить `backend/agent/param_extractor.py` — расширить `build_search_prompt()`:
  - Добавить few-shot примеры для edge-кейсов (русский язык, сленг)

### Файлы

- Изменить: `docs/AGENT_PROMPT.md`
- Изменить: `docs/CONSULTATION_PROMPT.md`
- Изменить: `backend/agent/param_extractor.py`

### Критерий приёмки

- "Хочу тёплый блюзовый звук до 1000$" → search_queries содержит "Gibson" или "humbucker"
- "Что такое хамбакер?" → consultation, ответ до 300 слов, структурированный
- "Какая погода завтра?" → вежливый отказ

### Тест: `tests/test_prompt_quality.py`

- build_search_prompt включает few-shot примеры
- Промпт содержит инструкцию про бюджет в рублях
- Consultation промпт содержит ограничение длины

### Коммит: `feat: improve LLM prompts with few-shot examples`

---

## Задача 3 (Тестирование): сквозной тест "запрос → карточки" через mock LLM

### Что делать

- Написать `tests/test_full_flow.py`:
  - Мокнуть `LLMClient` — возвращает предсказуемый JSON с параметрами
  - Установить `USE_MOCK_REVERB=true`
  - Вызвать `interpret_query("Найди Fender до 1000$")` → проверить что results не пустой, каждый result содержит обязательные поля
  - Вызвать `interpret_query("Чем отличается Stratocaster от Telecaster?")` → проверить mode="consultation", answer непустой
  - Проверить fallback без API-ключа: results возвращаются через mock

### Файлы

- Создать: `tests/test_full_flow.py`

### Критерий приёмки

- Все тесты проходят без реального Groq API
- Покрыты: search с результатами, consultation, fallback без ключа

### Коммит: `test: add full pipeline flow tests with mock LLM`
