# TODO — Сальников Илья

**Неделя 10:** 12–18 мая 2026  
**Ветка:** `feature/salnikov/chat-refactor-w10`

> Строго refactor-only.  
> Не менять UI/UX, тексты, стили, API-контракт, backend и demo-сценарии.  
> Цель недели — сгруппировать frontend chat-код, особенно `useChat.ts`, без изменения поведения.

---

## Общие правила week-10

- Только `refactor:` коммиты.
- Ровно 3 шага = ровно 3 осмысленных коммита.
- Новые тесты не писать.
- Не менять CSS-визуал, layout, тексты кнопок и состояния UI.
- Не менять frontend API/Zod contract types и не добавлять зависимость от новых contract-файлов. Если нужен input type для mapper — объявить его локально в `messageMappers.ts`.
- Не менять public props компонентов, если это ломает существующие imports.
- Новые helper-файлы разрешены, но каждый файл должен иметь одну понятную группу ответственности.
- Запрещено создавать новую свалку вида `utils.ts`, `helpers.ts`, `common.ts`.
- Если при рефакторинге нужен новый файл, назвать его по смыслу: `messageMappers.ts`, `sessionUrl.ts`, `chatViewModel.ts`.

---

## Задача: сгруппировать chat frontend без изменения UX

Сейчас frontend chat-код содержит несколько разных ответственностей:

- normalizing backend/history results;
- URL session sync;
- WebSocket lifecycle;
- message state;
- component rendering;
- fallback data mapping.

Нужно сделать код читабельнее и типобезопаснее, но оставить экран визуально и функционально прежним.

---

## Шаг 1 — типизировать и вынести message/history mapping

### Что делать

Убрать локальную свалку mapping-логики из `useChat.ts`.

Разрешённый вариант:

- создать `frontend/src/features/chat/messageMappers.ts`;
- перенести туда `normalizeResult` и `historyToMessages`;
- заменить `any` на узкие локальные input-типы внутри `messageMappers.ts`, не меняя и не расширяя `types.ts`;
- оставить возвращаемые `GuitarResult` и `Message` без изменений.

Нельзя:

- менять форму `Message`;
- менять порядок сообщений;
- менять fallback для image/title/price/url;
- менять отображаемые значения.
- менять imports из `types.ts` или зависеть от будущего `schemaTypes.ts`.

### Файлы

- Изменить: `frontend/src/features/chat/hooks/useChat.ts`
- Создать при необходимости: `frontend/src/features/chat/messageMappers.ts`

### Критерий приёмки

- mapping больше не живёт внутри `useChat.ts`;
- `useChat.ts` стал короче;
- frontend history/search отображаются как раньше;
- новых `any` в production chat-коде не появилось.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run src/features/chat/__tests__/useChat.test.ts
```

### Коммит

`refactor: group chat message mappers`

---

## Шаг 2 — вынести session URL helpers

### Что делать

Сгруппировать код, который читает и обновляет `?session=`.

Разрешённый вариант:

- создать `frontend/src/features/chat/sessionUrl.ts`;
- перенести туда `SESSION_QUERY_PARAM`, `readSessionIdFromUrl`, `updateSessionUrl`;
- оставить поведение URL sync прежним.

Нельзя:

- менять имя query param;
- менять replace/push behavior;
- менять обработку невалидного session id;
- менять поведение восстановления истории.

### Файлы

- Изменить: `frontend/src/features/chat/hooks/useChat.ts`
- Создать при необходимости: `frontend/src/features/chat/sessionUrl.ts`

### Критерий приёмки

- URL-specific код лежит отдельно;
- `useChat.ts` не содержит прямой работы с `URLSearchParams`, кроме вызова helper;
- session recovery работает как раньше.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run src/features/chat/__tests__/useChat.test.ts
```

### Коммит

`refactor: extract chat session url helpers`

---

## Шаг 3 — сгруппировать Chat component rendering

### Что делать

Упростить `Chat.tsx`, не меняя UI.

Разрешённый вариант:

- вынести маленькие render-only части в уже существующие компоненты, если они реально являются отдельной группой;
- либо создать один смысловой компонент рядом с остальными, например `ChatMain.tsx`, если он убирает смешение sidebar/main/input;
- оставить props и visual behavior прежними.

Нельзя:

- менять CSS;
- менять DOM-классы без необходимости;
- менять порядок блоков;
- менять тексты empty/loading/error;
- менять поведение отправки сообщения.

### Файлы

- Изменить: `frontend/src/features/chat/components/Chat.tsx`
- Возможно изменить: `frontend/src/features/chat/components/MessageList.tsx`
- Возможно создать: `frontend/src/features/chat/components/ChatMain.tsx`

### Критерий приёмки

- `Chat.tsx` стал проще и читабельнее;
- компоненты сгруппированы по смыслу;
- визуально экран не изменился;
- build и существующие component tests проходят.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run src/features/chat/__tests__/Chat.test.tsx src/features/chat/__tests__/Message.test.tsx
```

### Коммит

`refactor: simplify chat component composition`
