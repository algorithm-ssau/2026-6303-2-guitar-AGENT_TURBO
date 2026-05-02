# TODO — Сальников Илья

**Неделя 9:** 5–11 мая 2026  
**Ветка:** `feature/salnikov/frontend-production-w9`

> Production hardening frontend-части.  
> Не дублировать week-08 demo/QA-задачи: если они уже сделаны, использовать их как baseline.  
> Не трогать backend runtime-код, ranking, LLM prompts, API docs.

---

## Задача: довести frontend до production-ready уровня

Нужно закрыть все frontend blockers после week-08: тесты, реальные UI-состояния, адаптив, history/session UX и стабильность WebSocket flow.

PRD-сценарии, которые frontend должен уметь показать без ручных оправданий:

- абстрактный search-запрос с карточками;
- конкретный search-запрос с карточками;
- consultation answer без карточек;
- clarification/error/empty states;
- история сессий и восстановление по URL;
- degraded/mock mode с понятным состоянием интерфейса.

---

## Шаг 1 — стабилизировать frontend test suite

### Что делать

Починить текущие blockers в frontend-тестах:

- syntax error в `frontend/src/features/chat/__tests__/StatusIndicator.test.tsx`;
- timeout-ы в `frontend/src/features/chat/__tests__/useChat.test.ts`;
- UI/component tests, которые не зависят от финального API-контракта.

Важно: `api.test.ts` и `types.test.ts` принадлежат contract freeze Мергалиева. Если они падают, зафиксировать симптом и передать ему, но не менять API/Zod contract самостоятельно.

### Файлы

- Изменить: `frontend/src/features/chat/__tests__/StatusIndicator.test.tsx`
- Изменить: `frontend/src/features/chat/__tests__/useChat.test.ts`
- Возможно изменить: `frontend/src/features/chat/hooks/useChat.ts`

### Критерий приёмки

- `cd frontend && npm run test -- --run` не падает из-за syntax error;
- `useChat` tests не висят до timeout;
- UI/component frontend failures имеют исправление;
- API/type failures, если остаются, явно переданы в contract freeze Мергалиева.

### Проверка

```bash
cd frontend
npm run test -- --run
```

### Коммит

`test: stabilize frontend production tests`

---

## Шаг 2 — production UX для всех PRD-состояний

### Что делать

Проверить и при необходимости исправить реальные состояния интерфейса:

1. initial/welcome;
2. loading/status;
3. search results с 3–5 карточками;
4. consultation answer без карточек;
5. clarification;
6. empty results;
7. error state;
8. long text;
9. long guitar title;
10. missing/fallback image;
11. history sidebar;
12. mobile input.

Особое внимание:

- текст не должен вылезать из карточек;
- карточки не должны ломать layout;
- input должен быть доступен на mobile 375px;
- reconnect/status не должны создавать неконсистентные сообщения;
- session URL sync не должен открывать несуществующую историю как валидный чат.

### Файлы

- Изменить: `frontend/src/features/chat/components/*.tsx`
- Изменить: `frontend/src/features/chat/components/*.css`
- Изменить: `frontend/src/features/chat/hooks/useChat.ts`
- Возможно изменить: `frontend/src/features/chat/demo/*`

### Критерий приёмки

- frontend показывает все PRD-сценарии без визуальных поломок;
- desktop 1440, tablet 768 и mobile 375 выглядят пригодно для защиты;
- production `Chat.tsx` не зависит от demo-only данных.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run
```

Плюс ручная проверка размеров:

- 1440px;
- 768px;
- 375px.

### Коммит

`fix: harden frontend release states`

---

## Шаг 3 — финальный frontend QA отчёт

### Что делать

Обновить `docs/FRONTEND_RELEASE_QA.md` по фактическому состоянию после правок.

Документ должен содержать:

- таблицу состояний;
- отметки для desktop/tablet/mobile;
- список найденных и закрытых frontend blockers;
- список оставшихся ограничений, если они есть;
- команды проверки.

Не писать, что состояние `ready`, если оно реально `degraded`.

### Файлы

- Изменить: `docs/FRONTEND_RELEASE_QA.md`

### Критерий приёмки

- QA checklist соответствует реальному UI;
- документ можно использовать перед защитой;
- frontend status можно синхронизировать с `docs/PROJECT_STATUS.md`.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run
```

### Коммит

`docs: finalize frontend release qa`
