# TODO — Сальников Илья

**Неделя 8:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/salnikov/frontend-release-w8`

> Независимая release-задача. Сальников работает только с frontend demo/QA-файлами.
> Не трогать backend, `backend/`, `docs/API_REFERENCE.md`, `README.md`.
> Задача не зависит от готовности week-06/week-07 backend-фич.

---

## Задача: Frontend release demo states + visual QA

Нужно подготовить набор изолированных frontend-сценариев, чтобы перед защитой можно было проверить основные состояния интерфейса без живого backend.

---

## Шаг 1 — demo fixtures для состояний чата

### Что делать

Создать `frontend/src/features/chat/demo/demoMessages.ts`.

Экспортировать 6 сценариев:

- `emptyChatDemo`
- `consultationDemo`
- `searchResultsDemo`
- `emptyResultsDemo`
- `errorDemo`
- `longTextDemo`

Каждый сценарий должен содержать данные, совместимые с текущими frontend-типами сообщений.

`searchResultsDemo` должен содержать минимум 3 результата:

- title
- price
- currency
- imageUrl или image_url — в зависимости от текущих типов
- listingUrl или listing_url — в зависимости от текущих типов

### Файлы

- Создать: `frontend/src/features/chat/demo/demoMessages.ts`

### Критерий приёмки

- fixtures импортируются без ошибок;
- данные не содержат `any`;
- сценарии покрывают search, consultation, empty, error и длинный текст.

### Коммит

`feat: add frontend release demo fixtures`

---

## Шаг 2 — изолированный компонент просмотра сценариев

### Что делать

Создать `frontend/src/features/chat/demo/ChatDemoScenarios.tsx`.

Компонент должен:

- показывать список кнопок сценариев;
- по клику переключать активный сценарий;
- рендерить выбранный сценарий через существующие chat-компоненты, где это возможно;
- не подключаться в `App.tsx`;
- не менять production flow.

Если текущие компоненты сложно переиспользовать напрямую, допустимо сделать простой read-only preview внутри demo-компонента.

### Файлы

- Создать: `frontend/src/features/chat/demo/ChatDemoScenarios.tsx`

### Критерий приёмки

- компонент можно импортировать в тесте;
- все 6 сценариев доступны через UI;
- production `Chat.tsx` не меняется.

### Коммит

`feat: add isolated chat demo scenarios`

---

## Шаг 3 — visual QA checklist + тест

### Что делать

Создать `docs/FRONTEND_RELEASE_QA.md`.

Документ должен содержать таблицу:

| Состояние | Что проверить | Desktop 1440 | Tablet 768 | Mobile 375 |
|-----------|---------------|--------------|------------|------------|

Минимум 10 пунктов:

1. пустой чат;
2. welcome/начальное состояние, если есть;
3. search-ответ с карточками;
4. consultation-ответ;
5. empty results;
6. error state;
7. loading state;
8. длинный ответ;
9. длинный title карточки;
10. светлая/тёмная тема или текущая тема;
11. сайдбар;
12. мобильный input.

Создать `frontend/src/features/chat/__tests__/ChatDemoScenarios.test.tsx`.

Тест должен проверить:

- рендерится список сценариев;
- минимум 6 кнопок/сценариев;
- клик переключает активный сценарий;
- search-сценарий показывает минимум одну гитару.

### Файлы

- Создать: `docs/FRONTEND_RELEASE_QA.md`
- Создать: `frontend/src/features/chat/__tests__/ChatDemoScenarios.test.tsx`

### Критерий приёмки

- `npm run build` проходит;
- `npm run test -- ChatDemoScenarios` проходит;
- QA checklist пригоден для ручной проверки перед защитой.

### Коммит

`test: add frontend release demo checks`
