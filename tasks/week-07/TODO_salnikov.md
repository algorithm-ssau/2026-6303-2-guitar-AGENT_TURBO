# TODO — Сальников Илья

**Неделя 7:** 21–27 апреля 2026
**Ветка:** `feature/salnikov/ux-polish-w7`

> Независимая задача. Все файлы — его собственные, никто другой в week-7 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Frontend): Welcome-экран с примерами промптов

### Что делать

- Создать `frontend/src/features/chat/components/WelcomeScreen.tsx`:
  - Компонент принимает проп `onPromptSelect: (text: string) => void`
  - Заголовок `🎸 Что подобрать?` + подзаголовок "Нажмите на пример или напишите свой запрос"
  - **4 карточки-примера** (сетка 2×2 на десктопе, 1×4 на мобилке):
    1. "Найди стратокастер до 500$" — подпись "Поиск по бюджету"
    2. "Тёплый звук для джаза, бюджет до $1500" — "Абстрактный запрос"
    3. "Что такое P90?" — "Консультация"
    4. "Акустика для костра до 200$" — "Для начинающих"
  - Клик по карточке → `onPromptSelect(text)`
  - Стилизация через CSS-переменные (`--bg-secondary`, `--accent`, `--text-primary`)
- Обновить `frontend/src/features/chat/components/Chat.tsx`:
  - Импортировать `WelcomeScreen`
  - Условный рендер: `{messages.length === 0 && !currentSessionId && <WelcomeScreen onPromptSelect={handleSend} />}`
  - Вставить ПЕРЕД `<MessageList />` внутри `<main>`

### Файлы

- Создать: `frontend/src/features/chat/components/WelcomeScreen.tsx`
- Изменить: `frontend/src/features/chat/components/Chat.tsx`

### Критерий приёмки

- На пустом чате виден Welcome-экран с 4 карточками
- Клик по карточке → текст отправляется, экран исчезает
- После выбора сессии из сайдбара Welcome не показывается
- На мобилке карточки в 1 колонку
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/WelcomeScreen.test.tsx`

- Рендерит 4 карточки с текстами примеров
- Клик по карточке вызывает `onPromptSelect` с правильным текстом

### Коммит: `feat: add welcome screen with example prompts`

---

## Задача 2 (Frontend): EmptyResults в дизайн-систему

### Что делать

- Обновить `frontend/src/features/chat/components/EmptyResults.tsx`:
  - Убрать ВСЕ инлайн-стили
  - Добавить CSS-классы через CSS-переменные из `variables.css`:
    `.empty-results` (контейнер), `.empty-results__icon` (🔍), `.empty-results__title`, `.empty-results__hint`
  - CSS написать в самом компоненте через `<style>` или отдельный файл `EmptyResults.css`

### Файлы

- Изменить: `frontend/src/features/chat/components/EmptyResults.tsx`
- Возможно создать: `frontend/src/features/chat/components/EmptyResults.css`

### Критерий приёмки

- Ни одного `style={{...}}` в EmptyResults.tsx
- Все цвета через CSS-переменные
- Визуально соответствует тёмной теме

### Тест: `frontend/src/features/chat/__tests__/EmptyResults.test.tsx`

- Обновить/создать: проверка наличия CSS-классов (вместо инлайн-стилей)

### Коммит: `refactor: move EmptyResults to design system`

---

## Задача 3 (Frontend): ErrorMessage в дизайн-систему

### Что делать

- Обновить `frontend/src/features/chat/components/ErrorMessage.tsx`:
  - Убрать ВСЕ инлайн-стили
  - Добавить классы `.error-message`, `.error-message__text`, `.error-message__retry-btn`
  - Цвет ошибки через `var(--error, #ef4444)` (если `--error` не определён в `variables.css` — добавить)

### Файлы

- Изменить: `frontend/src/features/chat/components/ErrorMessage.tsx`
- Возможно изменить: `frontend/src/shared/styles/variables.css` (1 переменная `--error`)
- Возможно создать: `frontend/src/features/chat/components/ErrorMessage.css`

### Критерий приёмки

- Ни одного инлайн-стиля в ErrorMessage.tsx
- `--error` добавлена в variables.css если нужна
- Клик по retry работает

### Тест: `frontend/src/features/chat/__tests__/ErrorMessage.test.tsx`

- Обновить: проверка классов + клик по retry-кнопке вызывает `onRetry`

### Коммит: `refactor: move ErrorMessage to design system`

---

## Задача 4 (Frontend): экспорт чата в JSON/MD

### Что делать

- Создать `frontend/src/features/chat/hooks/useExport.ts`:
  - Функция `exportChatAsJson(messages, sessionTitle): void` — формирует JSON blob, триггерит download
  - Функция `exportChatAsMarkdown(messages, sessionTitle): void` — формирует MD:
    ```
    # {Session Title}
    > Экспортировано: {date}

    ## Вы
    {user message 1}

    ## Guitar Agent
    {agent response 1}
    ...
    ```
    Для search-ответов — добавить список найденных гитар как markdown-таблицу
- Создать `frontend/src/features/chat/components/ExportButton.tsx`:
  - Кнопка 💾 в хедере чата (или рядом с названием сессии)
  - Dropdown с опциями "JSON" и "Markdown"
  - Принимает messages и sessionTitle через пропсы
  - Использует хук useExport
- Интегрировать в `Chat.tsx` (он уже во владении Сальникова): добавить ExportButton в хедер

### Файлы

- Создать: `frontend/src/features/chat/hooks/useExport.ts`
- Создать: `frontend/src/features/chat/components/ExportButton.tsx`
- Изменить: `frontend/src/features/chat/components/Chat.tsx` (добавить кнопку)

### Критерий приёмки

- Клик по 💾 → JSON → скачивается файл `chat-{sessionId}-{date}.json`
- Клик по 💾 → MD → скачивается файл `chat-{sessionId}-{date}.md`
- MD содержит все сообщения + найденные гитары в виде таблицы
- На пустом чате кнопка disabled или скрыта

### Тест: `frontend/src/features/chat/__tests__/ExportButton.test.tsx`

- Клик по JSON триггерит download с правильным контентом (mock URL.createObjectURL)
- Клик по MD — аналогично
- На пустых messages кнопка disabled

### Коммит: `feat: add chat export to JSON and Markdown`

---

## Задача 5 (Frontend): keyboard shortcuts (hotkeys)

### Что делать

- Создать `frontend/src/shared/hooks/useHotkeys.ts`:
  - Хук `useHotkeys(bindings: Record<string, () => void>): void`:
    - `bindings` — карта `"cmd+k" → callback`, `"cmd+enter" → callback`
    - Использует `addEventListener('keydown', ...)` на window
    - В cleanup — `removeEventListener`
    - Поддержка Ctrl (Windows) и Cmd (Mac) автоматически
- Интегрировать в `Chat.tsx`:
  - `cmd+k` / `ctrl+k` → `newChat()` (новый чат)
  - `cmd+enter` / `ctrl+enter` → отправить текущий текст из инпута
  - `cmd+/` / `ctrl+/` → focus на input
- Добавить подсказку в Chat.tsx (header): "⌘K новый чат · ⌘↵ отправить"

### Файлы

- Создать: `frontend/src/shared/hooks/useHotkeys.ts`
- Изменить: `frontend/src/features/chat/components/Chat.tsx` (подключение + hint)

### Критерий приёмки

- Cmd+K создаёт новый чат
- Cmd+Enter отправляет текущий текст
- Cmd+/ фокусирует инпут
- Подсказка видна в хедере

### Тест: `frontend/src/shared/hooks/__tests__/useHotkeys.test.ts`

- Хук регистрирует обработчик
- KeyboardEvent с cmd+k вызывает callback
- В cleanup снимает обработчик

### Коммит: `feat: add keyboard shortcuts (Cmd+K, Cmd+Enter, Cmd+/)`
