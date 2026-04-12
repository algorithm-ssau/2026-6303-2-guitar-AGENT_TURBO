# TODO — Сальников Илья

**Неделя 6:** 14–20 апреля 2026
**Ветка:** `feature/salnikov/welcome-polish`

> Независимая задача. Все файлы — его собственные, никто другой в week-6 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Frontend): Welcome-экран с примерами промптов

### Что делать

- Создать `frontend/src/features/chat/components/WelcomeScreen.tsx`:
  - Компонент принимает проп `onPromptSelect: (text: string) => void`
  - Заголовок: `🎸 Что подобрать?` + подзаголовок "Нажмите на пример или напишите свой запрос"
  - **4 карточки-примера** (сетка 2×2 на десктопе, 1×4 на мобилке):
    1. `"Найди стратокастер до 500$"` — подпись "Поиск по бюджету"
    2. `"Тёплый звук для джаза, бюджет до $1500"` — подпись "Абстрактный запрос"
    3. `"Что такое P90?"` — подпись "Консультация"
    4. `"Акустика для костра до 200$"` — подпись "Для начинающих"
  - Клик по карточке → `onPromptSelect(text)` → компонент вставляет текст в инпут и отправляет сообщение
  - Стилизация через CSS-переменные из `shared/styles/variables.css` (введены в week-5):
    `--bg-secondary` для фона карточек, `--accent` для hover, `--text-primary` для текста
- Обновить `frontend/src/features/chat/components/Chat.tsx`:
  - Импортировать `WelcomeScreen`
  - Условный рендер: `{messages.length === 0 && !currentSessionId && <WelcomeScreen onPromptSelect={handleSend} />}`
  - Вставить ПЕРЕД `<MessageList />` внутри `<main>`
  - Это **единственное изменение Chat.tsx** на week-6 — 3 строки

### Файлы

- Создать: `frontend/src/features/chat/components/WelcomeScreen.tsx`
- Изменить: `frontend/src/features/chat/components/Chat.tsx` (3 строки: import + условный рендер)

### Критерий приёмки

- На пустом чате (без сессии) виден Welcome-экран с 4 карточками
- Клик по карточке → текст отправляется, экран исчезает, появляются сообщения
- После выбора сессии из сайдбара Welcome не показывается
- Карточки выглядят согласно дизайн-системе week-5 (тёмная тема)
- На мобилке (≤480px) карточки идут в 1 колонку
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/WelcomeScreen.test.tsx`

- Компонент рендерит 4 карточки с текстами примеров
- Клик по карточке вызывает `onPromptSelect` с правильным текстом
- Компонент скрыт когда `messages.length > 0` (в тесте Chat.tsx)

### Коммит: `feat: add welcome screen with example prompts`

---

## Задача 2 (Frontend): перевод мелких компонентов на дизайн-систему

### Что делать

- Обновить `frontend/src/features/chat/components/EmptyResults.tsx`:
  - Убрать ВСЕ инлайн-стили (`style={{...}}`)
  - Добавить CSS-классы, использующие переменные из `variables.css`:
    `.empty-results` (контейнер), `.empty-results__icon` (🔍), `.empty-results__title`, `.empty-results__hint`
  - CSS написать в самом компоненте через `<style>` блок ИЛИ вынести в `EmptyResults.module.css`
- Обновить `frontend/src/features/chat/components/ErrorMessage.tsx`:
  - То же самое: убрать инлайн, добавить классы
  - `.error-message`, `.error-message__text`, `.error-message__retry-btn`
  - Цвет ошибки: `var(--error, #ef4444)` (если `--error` не определён в week-5 — добавить в `variables.css`, это **единственное исключение** где трогается week-5 файл Сальникова-же)
- **НЕ трогать**: `Message.tsx` (Мергалиев), `MessageList.tsx`, `StatusIndicator.tsx`, `InputForm.tsx`, `Sidebar.tsx`

### Файлы

- Изменить: `frontend/src/features/chat/components/EmptyResults.tsx`
- Изменить: `frontend/src/features/chat/components/ErrorMessage.tsx`
- Возможно: `frontend/src/shared/styles/variables.css` (1 переменная `--error`)

### Критерий приёмки

- Ни одного `style={{...}}` в EmptyResults.tsx и ErrorMessage.tsx
- Все цвета — через CSS-переменные
- Визуально выглядит как в дизайн-системе (тёмная тема)
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/EmptyResults.test.tsx` + `ErrorMessage.test.tsx`

- Обновить/создать: проверка что у элементов есть соответствующие классы (вместо проверки инлайн-стилей)
- ErrorMessage клик по retry-кнопке вызывает `onRetry`

### Коммит: `refactor: move EmptyResults and ErrorMessage to design system`

---

## Задача 3 (Тестирование): визуальный регрешн-чеклист + smoke npm run build

### Что делать

- Создать `frontend/VISUAL_CHECKLIST.md` — ручной чеклист для защиты:
  - Скриншот-инструкции что проверить (8–10 пунктов):
    - Welcome экран с 4 карточками (1440px, 768px, 375px)
    - Консультация-ответ (тёмная тема, markdown)
    - Search-ответ с карточками гитар
    - Пустая выдача (EmptyResults)
    - Ошибка WS с кнопкой retry
    - Сайдбар открыт/закрыт
    - Переключение сессий
    - Loading-скелетоны (week-5 Мергалиев)
- Создать `frontend/src/features/chat/__tests__/Chat.smoke.test.tsx`:
  - Smoke-тест: импорт Chat → render с мок-useChat → нет ошибок
  - Проверить что WelcomeScreen отображается при пустых messages
  - Проверить что MessageList отображается при непустых
- Добавить в `frontend/package.json` скрипт `"test:smoke": "vitest run --reporter=verbose Chat.smoke"`

### Файлы

- Создать: `frontend/VISUAL_CHECKLIST.md`
- Создать: `frontend/src/features/chat/__tests__/Chat.smoke.test.tsx`
- Изменить: `frontend/package.json` (1 строка в scripts)

### Критерий приёмки

- Чеклист покрывает 8+ визуальных состояний
- Smoke-тест проходит локально `npm run test:smoke`
- Скрипт `test:smoke` работает

### Коммит: `test: add visual checklist and Chat smoke test`
