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

- Обновить `docs/AGENT_PROMPT.md`:
  - Добавить инструкцию: при search-режиме генерировать 1–2 предложения пояснения ("Вот варианты с тёплым звуком в вашем бюджете:")
  - Добавить 2–3 few-shot примера пояснений
- Обновить `backend/agent/service.py` — в `_handle_search()`:
  - После получения результатов — вызвать LLM с коротким промптом:
    "Напиши 1–2 предложения почему эти гитары подходят под запрос: {query}. Без списков, только текст."
  - Добавить поле `explanation` в ответ: `result["explanation"] = ...`
  - При ошибке LLM или degraded mode → `explanation = ""`
- Обновить `backend/models.py` — добавить `explanation: Optional[str] = None` в WSMessage
- Обновить маппинг в `frontend/src/features/chat/hooks/useChat.ts`:
  - Читать `data.explanation`, если есть — использовать как `content` вместо "Найдено гитар: N"

### Файлы

- Изменить: `docs/AGENT_PROMPT.md`
- Изменить: `backend/agent/service.py`
- Изменить: `backend/models.py`
- Изменить: `frontend/src/features/chat/hooks/useChat.ts` (маппинг поля)

### Критерий приёмки

- "Найди стратокастер до 500$" → перед карточками 1–2 строки пояснения
- Пояснение релевантно запросу, не шаблонное
- Без GROQ_API_KEY → explanation пустой, карточки показываются без него

### Тест: `tests/test_explanation.py`

- interpret_query search → результат содержит поле "explanation"
- explanation не пустой при доступном LLM (замокать ответ)
- explanation пустой в degraded mode — не ломает ответ

### Коммит: `feat: add search result explanation from LLM`

---

## Задача 3 (Backend): ужесточить off-topic в промптах LLM

### Что делать

- Обновить `docs/CONSULTATION_PROMPT.md`:
  - Расширить список запрещённых тем: программирование, математика, рецепты, погода, новости, любые не-музыкальные темы
  - Добавить строгую инструкцию: "Если запрос не связан с гитарами, музыкой, звуком или оборудованием — ответь ТОЛЬКО фразой отказа"
  - Добавить 3 negative few-shot примера (запрос → отказ)
- Обновить `docs/AGENT_PROMPT.md` аналогично
- Ограничение ответа consultation до 300 слов

### Файлы

- Изменить: `docs/CONSULTATION_PROMPT.md`
- Изменить: `docs/AGENT_PROMPT.md`

### Критерий приёмки

- LLM не отвечает на "напиши сортировку пузырьком" (второй рубеж после mode_detector)
- LLM не отвечает на "какая погода" / "реши уравнение"
- LLM продолжает нормально отвечать на гитарные вопросы
- Consultation-ответы ≤ 300 слов

### Тест: `tests/test_prompt_offtopic.py`

- Промпт содержит инструкцию об отказе на нерелевантные запросы
- Промпт содержит negative few-shot примеры
- Промпт содержит ограничение на 300 слов

### Коммит: `feat: harden prompts against off-topic queries`
