# TODO — Павлов Виктор

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/pavlov/markdown-render`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Frontend): Markdown-рендеринг ответов агента

### Что делать

- Установить `react-markdown` в `frontend/`
- Изменить `frontend/src/features/chat/components/Message.tsx`:
  - Для `mode="consultation"` — рендерить `content` через `<ReactMarkdown>`
  - Поддержка: **жирный**, *курсив*, списки, заголовки, `код`, блоки кода
  - Стилизация: белый текст, ссылки — accent цвет, код — тёмный фон
- Добавить кнопку "Копировать" на consultation-ответах:
  - По клику — `navigator.clipboard.writeText(content)`
  - Показать "Скопировано!" на 2 секунды, затем вернуть иконку

### Файлы

- Изменить: `frontend/src/features/chat/components/Message.tsx`
- Изменить: `frontend/package.json` (добавить react-markdown)

### Критерий приёмки

- `**жирный**` рендерится жирным, списки — как списки, код — моноширинным блоком
- Кнопка "Копировать" работает, показывает подтверждение
- Для user-сообщений кнопка копирования отсутствует
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/Message.test.tsx`

- Markdown-контент рендерится (проверить наличие `<strong>`, `<li>`, `<code>`)
- Кнопка копирования присутствует для consultation-сообщений
- Кнопка отсутствует для user-сообщений

### Коммит: `feat: add markdown rendering and copy button for agent responses`

---

## Задача 2 (Backend): пояснение к результатам поиска (PRD п.5.5)

### Что делать

- Создать `backend/agent/explanation.py` — генерация пояснений в отдельном файле:
  - Функция `generate_explanation(query: str, results: list, llm_client) -> str`:
    - Вызывает LLM с коротким промптом: "Напиши 1–2 предложения почему эти гитары подходят под запрос: {query}. Без списков, только текст."
    - При ошибке LLM или degraded mode → возвращает `""`
  - Промпт-шаблон — константа в этом же файле
- Обновить `docs/AGENT_PROMPT.md`:
  - Добавить инструкцию: при search-режиме генерировать пояснение
  - Добавить 2–3 few-shot примера пояснений
- Обновить `backend/main.py` — в WS цикле, после получения search-результатов:
  - Вызвать `generate_explanation(query, results, llm_client)`
  - Добавить `explanation` в WS-ответ
  - **НЕ трогать service.py** — explanation генерируется в main.py перед отправкой
- Обновить маппинг в `frontend/src/features/chat/hooks/useChat.ts`:
  - Читать `data.explanation`, если есть — использовать как `content` вместо "Найдено гитар: N"

### Файлы

- Создать: `backend/agent/explanation.py` (основная работа)
- Изменить: `docs/AGENT_PROMPT.md`
- Изменить: `backend/main.py` (вызов generate_explanation + добавление в ответ)
- Изменить: `frontend/src/features/chat/hooks/useChat.ts` (маппинг поля)

### Критерий приёмки

- "Найди стратокастер до 500$" → перед карточками 1–2 строки пояснения
- Пояснение релевантно запросу, не шаблонное
- Без GROQ_API_KEY → explanation пустой, карточки показываются без него

### Тест: `tests/test_explanation.py`

- generate_explanation с замоканным LLM → непустая строка
- generate_explanation без LLM → пустая строка
- generate_explanation с пустыми результатами → пустая строка

### Коммит: `feat: add search result explanation from LLM`

---

## Задача 3 (Backend): суммаризация контекста диалога при превышении лимита токенов

### Что делать

- Создать `backend/agent/context_manager.py`:
  - Функция `build_context(session_id, system_prompt, current_query) -> list[dict]`:
    - Загружает историю диалога из БД (через `get_session_messages`)
    - Считает примерное количество токенов (1 токен ≈ 3 символа для русского текста)
    - Лимит берётся из конфига модели: `MODEL_CONTEXT_LIMIT` из `.env` (по умолчанию 128000 для llama-3.3-70b). Порог суммаризации — 75% от лимита, чтобы оставить место на system prompt + ответ
    - Если история укладывается в порог — возвращает полную историю как есть
    - Если НЕ укладывается — вызывает LLM с промптом суммаризации:
      ```
      "Сделай краткое summary предыдущего диалога (ключевые предпочтения пользователя, 
      его имя если представился, что он искал, что ему понравилось). До 200 слов."
      ```
    - Формирует новый контекст: system prompt → {"role": "system", "content": summary} → последние 3 пары → текущий вопрос
  - Функция `estimate_tokens(text: str) -> int`: грубая оценка токенов (`len(text) // 3`)
  - Лимит читается из `os.getenv("MODEL_CONTEXT_LIMIT", "128000")` — привязан к реальной модели
- Обновить `backend/agent/service.py`:
  - Убрать `MAX_HISTORY_PAIRS` и `_load_chat_history()`
  - В `_handle_consultation()` и `interpret_query()` использовать `build_context()` вместо тупого обрезания
  - **Важно:** при рефакторинге сохранить логику форматирования search-результатов в историю (сейчас в `_load_chat_history` для mode="search" результаты форматируются как "Я нашёл следующие гитары:\n- Title, $price" — без этого LLM теряет контекст предыдущих поисков)
  - **Важно:** не дублировать логику пере-поиска — в `interpret_query()` уже есть `_get_last_search_query()` + `detect_mode(text, has_previous_search=...)`, при рефакторинге сохранить эту связку
- Обновить `backend/agent/llm_client.py`:
  - Метод `summarize(messages: list, prompt: str) -> str` — вызов LLM для суммаризации

### Файлы

- Создать: `backend/agent/context_manager.py`
- Изменить: `backend/agent/service.py`
- Изменить: `backend/agent/llm_client.py`

### Критерий приёмки

- Короткий диалог (< 75% контекста модели) → полная история без суммаризации
- Длинный диалог (> 75% контекста) → summary старых сообщений + последние 3 пары полностью
- "Меня зовут Антон" → через 20 сообщений "как меня зовут?" → "Антон" (имя сохранено в summary)
- Без GROQ_API_KEY → graceful fallback (последние 5 пар без суммаризации)

### Тест: `tests/test_context_manager.py`

- estimate_tokens возвращает адекватные числа
- build_context с короткой историей → полная история без суммаризации
- build_context с длинной историей (замокать > 75% лимита) → вызывает summarize, возвращает summary + последние пары
- build_context без session_id → пустая история

### Коммит: `feat: add context summarization for long conversations`
