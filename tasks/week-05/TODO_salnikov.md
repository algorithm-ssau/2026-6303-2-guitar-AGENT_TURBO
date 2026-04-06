# TODO — Сальников Илья

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/salnikov/design-system`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Frontend): дизайн-система и тёмная тема из мокапа

### Что делать

- Создать `frontend/src/shared/styles/variables.css` — CSS-переменные из `design/mockup.html`:
  - Цвета: `--bg-primary: #0f0f23`, `--bg-secondary: #1a1a3e`, `--accent: #4d88ff`, `--text-primary: #e8e8f0` и т.д.
  - Радиусы, тени, отступы, шрифты
- Создать `frontend/src/shared/styles/reset.css` — минимальный CSS-reset
- Подключить оба файла в `frontend/src/main.tsx`
- Перевести `frontend/src/features/chat/components/Chat.tsx` на дизайн-систему:
  - Тёмный фон основной области (`--bg-primary`)
  - Хедер по мокапу (`--bg-secondary`)
  - Убрать все инлайн-стили, заменить на CSS-классы с переменными
- Убрать инлайн `<style>` из `frontend/index.html` (заменён на reset.css)

### Файлы

- Создать: `frontend/src/shared/styles/variables.css`
- Создать: `frontend/src/shared/styles/reset.css`
- Изменить: `frontend/src/main.tsx`
- Изменить: `frontend/src/features/chat/components/Chat.tsx`
- Изменить: `frontend/index.html`

### Критерий приёмки

- Приложение визуально соответствует тёмной теме мокапа
- Все цвета задаются через CSS-переменные (ни одного хардкод-цвета в Chat.tsx)
- `npm run build` без ошибок

### Тест: визуальная проверка + `npm run build` без ошибок

### Коммит: `feat: implement design system with dark theme from mockup`

---

## Задача 2 (Frontend): адаптивная вёрстка (мобилка)

### Что делать

- Обновить `frontend/src/features/chat/components/Chat.tsx`:
  - Media query `@media (max-width: 768px)`:
    - Сайдбар — оверлей поверх чата (position: fixed, z-index)
    - По умолчанию скрыт, открывается по кнопке ☰
  - Media query `@media (max-width: 480px)`:
    - Инпут прилипает к низу (position: sticky)
    - Хедер — компактный (меньше высота, меньше шрифт)
- Обновить `frontend/src/features/chat/components/InputForm.tsx`:
  - На мобилке — полная ширина без боковых отступов

### Файлы

- Изменить: `frontend/src/features/chat/components/Chat.tsx`
- Изменить: `frontend/src/features/chat/components/InputForm.tsx`

### Критерий приёмки

- На десктопе (>768px): сайдбар слева, чат справа — как сейчас
- На планшете (≤768px): сайдбар — оверлей, чат занимает всю ширину
- На мобилке (≤480px): компактный хедер, инпут прилипает к низу
- Нет горизонтального скролла ни на одном разрешении

### Тест: ручная проверка в DevTools (320px, 768px, 1440px)

### Коммит: `feat: add responsive layout for mobile and tablet`

---

## Задача 3 (Backend): фильтрация off-topic запросов в mode_detector

### Что делать

- Добавить третий режим `"off_topic"` в `backend/agent/mode_detector.py`:
  - Паттерны НЕ про гитары: программирование ("напиши код", "сортировка", "функция", "python", "javascript"), математика ("реши", "посчитай", "уравнение", "интеграл"), бытовое ("погода", "рецепт", "борщ", "новости")
  - Если запрос попадает в off_topic — вернуть `"off_topic"` до вызова LLM
  - Фиксированный ответ-отказ — константа `OFF_TOPIC_ANSWER` прямо в `mode_detector.py`
- **НЕ трогать `service.py`** — `interpret_query()` уже вызывает `detect_mode()`, достаточно чтобы `detect_mode` возвращал `"off_topic"`, а в `service.py` добавить 3 строки:
  ```python
  if mode == "off_topic":
      return {"mode": "consultation", "answer": OFF_TOPIC_ANSWER}
  ```
  Это единственное изменение в service.py — добавить `import OFF_TOPIC_ANSWER` и 2 строки early return перед существующим `if mode == "consultation"`

### Файлы

- Изменить: `backend/agent/mode_detector.py` (основная работа)
- Изменить: `backend/agent/service.py` (только 3 строки: import + early return)

### Критерий приёмки

- "напиши сортировку пузырьком" → off_topic, отказ БЕЗ вызова LLM
- "какая погода завтра" → off_topic
- "реши уравнение" → off_topic
- "что такое хамбакер" → consultation (как раньше)
- "найди стратокастер" → search (как раньше)

### Тест: `tests/test_off_topic.py`

- 7+ off_topic запросов → все получают режим "off_topic"
- 5+ гитарных запросов → НЕ off_topic
- interpret_query с off_topic → ответ без вызова LLM (замокать LLMClient, проверить что не вызван)

### Коммит: `feat: add off-topic filter to reject non-guitar queries without LLM`
