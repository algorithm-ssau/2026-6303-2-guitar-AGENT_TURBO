# TODO — Хасанов Дамир

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/khasanov/multistep-chat`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Backend): мультишаговый диалог — уточняющие вопросы (PRD п.4.1)

### Что делать

- Обновить `backend/agent/service.py` — в `_handle_search()`:
  - Перед вызовом `search_reverb`, проверить что LLM вернул достаточно параметров
  - Если нет бюджета ИЛИ нет типа гитары ИЛИ пустые search_queries → вернуть уточняющий вопрос:
    ```python
    {"mode": "clarification", "question": "Какой у вас бюджет?" }
    ```
  - Логика: `extract_search_params` вернул `{}` или нет ключевых полей → уточнение
- Обновить `backend/main.py` — WebSocket обработка нового типа `mode="clarification"`:
  - Отправить `{"type": "result", "mode": "clarification", "question": "..."}`
  - НЕ закрывать сессию — ждать следующее сообщение от клиента
- Обновить `backend/models.py`:
  - Добавить `question: Optional[str] = None` в WSMessage
  - Добавить `"clarification"` в Literal mode

### Файлы

- Изменить: `backend/agent/service.py`
- Изменить: `backend/main.py`
- Изменить: `backend/models.py`

### Критерий приёмки

- "Хочу гитару" (без бюджета, без типа) → mode="clarification", question содержит уточнение
- "Найди стратокастер до 500$" → mode="search" (достаточно данных, работает как раньше)
- После уточнения пользователь отвечает "до 1000$" → агент делает поиск

### Тест: `tests/test_clarification.py`

- Запрос без бюджета → mode="clarification"
- Запрос с полными данными → mode="search" (не clarification)
- extract_search_params вернул пустой dict → clarification

### Коммит: `feat: add clarification mode for incomplete search queries`

---

## Задача 2 (Frontend): отображение уточняющих вопросов

### Что делать

- Обновить `frontend/src/features/chat/hooks/useChat.ts`:
  - Обработать `data.mode === "clarification"` в onmessage:
    - Создать agent message с content = `data.question`, mode = "clarification"
    - Не сбрасывать currentSessionId — продолжаем диалог
- Обновить `frontend/src/features/chat/types.ts`:
  - Добавить `"clarification"` в тип mode: `'search' | 'consultation' | 'clarification'`
- Обновить `frontend/src/features/chat/components/ModeBadge.tsx`:
  - Добавить бейдж для clarification: жёлтый/оранжевый, текст "Уточнение"

### Файлы

- Изменить: `frontend/src/features/chat/hooks/useChat.ts`
- Изменить: `frontend/src/features/chat/types.ts`
- Изменить: `frontend/src/features/chat/components/ModeBadge.tsx`

### Критерий приёмки

- Уточняющий вопрос отображается как сообщение агента с бейджем "Уточнение"
- Пользователь может ответить → следующий запрос идёт в ту же сессию
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/ModeBadge.test.tsx`

- Обновить: бейдж "Уточнение" рендерится для mode="clarification"

### Коммит: `feat: display clarification questions in chat UI`

---

## Задача 3 (Frontend): бейджи релевантности + бюджетная подсказка

### Что делать

- Обновить `frontend/src/features/chat/components/RelevanceBadge.tsx`:
  - Стилизация по мокапу: компактный бейдж, цвет по уровню
- Создать `frontend/src/features/chat/components/BudgetHint.tsx`:
  - Если в ответе агента есть информация о бюджете — показать бейдж "Бюджет: до $600" над карточками
  - Карточки в рамках бюджета — нормальные, выше бюджета — приглушённый стиль (opacity 0.6)
- Обновить `frontend/src/features/chat/components/Message.tsx`:
  - Подключить BudgetHint перед ResultsList (если есть данные о бюджете)

### Файлы

- Изменить: `frontend/src/features/chat/components/RelevanceBadge.tsx`
- Создать: `frontend/src/features/chat/components/BudgetHint.tsx`
- Изменить: `frontend/src/features/chat/components/Message.tsx`

### Критерий приёмки

- Бейджи релевантности визуально соответствуют мокапу
- Бюджетная подсказка показывается когда есть данные о бюджете
- Карточки дороже бюджета — визуально приглушены

### Тест: `frontend/src/features/chat/__tests__/BudgetHint.test.tsx`

- BudgetHint рендерится с переданным бюджетом
- Без бюджета → компонент не рендерится

### Коммит: `feat: add budget hint and styled relevance badges`
