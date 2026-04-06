# TODO — Хасанов Дамир

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/khasanov/multistep-chat`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Backend): мультишаговый диалог — уточняющие вопросы (PRD п.4.1)

### Что делать

- Создать `backend/agent/clarification.py` — вся логика уточнений в отдельном файле:
  - Функция `check_needs_clarification(params: dict) -> Optional[str]`:
    - Принимает извлечённые search_params
    - Если нет бюджета ИЛИ нет типа гитары ИЛИ пустые search_queries → вернуть текст уточняющего вопроса ("Какой у вас бюджет?", "Какой тип гитары ищете?")
    - Если всё есть → вернуть `None` (уточнение не нужно)
  - Константы с шаблонами вопросов
- Обновить `backend/agent/service.py` — в `_handle_search()`:
  - После `extract_search_params` вызвать `check_needs_clarification(params)`
  - Если вернулся вопрос → `return {"mode": "clarification", "question": question}`
  - Если `None` → продолжить поиск как раньше
  - Это 4 строки изменений: import + вызов + early return
- Обновить `backend/main.py` — в WS цикле обработка `mode="clarification"`:
  - Отправить `{"type": "result", "mode": "clarification", "question": "...", "sessionId": session_id}`
  - Сохранить в историю с mode="clarification", answer=question

### Файлы

- Создать: `backend/agent/clarification.py` (основная работа)
- Изменить: `backend/agent/service.py` (4 строки: import + вызов + return)
- Изменить: `backend/main.py` (добавить блок `elif result_data["mode"] == "clarification"`)

### Критерий приёмки

- "Хочу гитару" (без бюджета, без типа) → mode="clarification", question содержит уточнение
- "Найди стратокастер до 500$" → mode="search" (достаточно данных, работает как раньше)
- После уточнения пользователь отвечает "до 1000$" → агент делает поиск

### Тест: `tests/test_clarification.py`

- Запрос без бюджета → check_needs_clarification возвращает вопрос
- Запрос с полными данными → возвращает None
- extract_search_params вернул пустой dict → вопрос

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

- Изменить: `frontend/src/features/chat/hooks/useChat.ts` (5 строк в switch/case)
- Изменить: `frontend/src/features/chat/types.ts` (1 строка)
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
  - Самостоятельный компонент: принимает `budget` и `results` через props
  - Если budget передан — показать бейдж "Бюджет: до $600" над карточками
  - Карточки дороже бюджета — приглушённый стиль (opacity 0.6)
- Обновить `frontend/src/features/chat/components/ResultsList.tsx`:
  - Подключить BudgetHint перед списком карточек
  - **НЕ трогать Message.tsx** — BudgetHint рендерится внутри ResultsList

### Файлы

- Изменить: `frontend/src/features/chat/components/RelevanceBadge.tsx`
- Создать: `frontend/src/features/chat/components/BudgetHint.tsx`
- Изменить: `frontend/src/features/chat/components/ResultsList.tsx`

### Критерий приёмки

- Бейджи релевантности визуально соответствуют мокапу
- Бюджетная подсказка показывается когда есть данные о бюджете
- Карточки дороже бюджета — визуально приглушены

### Тест: `frontend/src/features/chat/__tests__/BudgetHint.test.tsx`

- BudgetHint рендерится с переданным бюджетом
- Без бюджета → компонент не рендерится

### Коммит: `feat: add budget hint and styled relevance badges`
