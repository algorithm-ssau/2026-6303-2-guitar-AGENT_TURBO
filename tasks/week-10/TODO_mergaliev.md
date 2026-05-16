# TODO — Мергалиев Радмир

**Неделя 10:** 12–18 мая 2026  
**Ветка:** `feature/mergaliev/contract-refactor-w10`

> Строго refactor-only.  
> Не менять API-контракт, documented examples, backend behavior, frontend UI и runtime semantics.  
> Цель недели — привести contract boundary в аккуратный вид, без изменения формы данных.

---

## Общие правила week-10

- Только `refactor:` коммиты.
- Ровно 3 шага = ровно 3 осмысленных коммита.
- Новые тесты не писать.
- Не менять JSON field names, optional/required поля и status codes.
- Не менять endpoint URLs.
- Не менять Zod-схемы по смыслу.
- Не менять serializers так, чтобы менялся output.
- Не менять import paths для компонентов, хуков и backend-модулей вне своей зоны.
- Новые helper-файлы разрешены, но каждый файл должен иметь одну понятную группу ответственности.
- Запрещено создавать новую свалку вида `utils.ts`, `helpers.py`, `common.py`.
- Если при рефакторинге нужен новый файл, назвать его по смыслу: `apiClient.ts`, `schemaTypes.ts`, `response_serializer.py`.

---

## Задача: сгруппировать frontend/backend contract boundary

Сейчас contract layer разбросан между:

- frontend `api.ts`;
- frontend `types.ts` с Zod-схемами;
- backend serializers/models;
- tests/docs, которые должны остаться baseline.

Нужно сделать boundary читаемее, но не менять контракт.

---

## Шаг 1 — сгруппировать frontend API request helpers

### Что делать

Упростить `frontend/src/features/chat/api.ts`, отделив generic request mechanics от конкретных API-функций.

Разрешённый вариант:

- создать `frontend/src/features/chat/apiClient.ts`;
- перенести туда `API_BASE_URL`, auth headers, error creation и общий JSON request helper;
- оставить в `api.ts` конкретные функции chat/history/session.

Нельзя:

- менять URL endpoints;
- менять HTTP methods;
- менять request/response body;
- менять error message fallback;
- менять auth header behavior.

### Файлы

- Изменить: `frontend/src/features/chat/api.ts`
- Создать при необходимости: `frontend/src/features/chat/apiClient.ts`

### Критерий приёмки

- `api.ts` содержит business API calls, а не low-level fetch boilerplate;
- все существующие exports остаются доступны;
- frontend API tests проходят без изменения expected data.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run src/features/chat/__tests__/api.test.ts
```

### Коммит

`refactor: group frontend api request helpers`

---

## Шаг 2 — сгруппировать schema/type exports

### Что делать

Привести `frontend/src/features/chat/types.ts` к более понятной структуре без изменения схем по смыслу.

Разрешённый вариант:

- сгруппировать domain types, request/response schemas, history/session schemas внутри `types.ts`;
- если создаётся `frontend/src/features/chat/schemaTypes.ts`, оставить `types.ts` compatibility facade и не требовать изменений в хуках/компонентах;
- оставить все public exports и import paths совместимыми.

Нельзя:

- менять Zod validation semantics;
- менять union values;
- менять optional/default поля;
- менять имена exported types, которые уже используются.
- менять import paths в `useChat.ts`, компонентах или тестах Сальникова.

### Файлы

- Изменить: `frontend/src/features/chat/types.ts`
- Создать при необходимости: `frontend/src/features/chat/schemaTypes.ts`

### Критерий приёмки

- schemas читаются группами;
- imports в компонентах/хуках не ломаются;
- `types.test.ts` проходит без изменения expected contract.

### Проверка

```bash
cd frontend
npm run build
npm run test -- --run src/features/chat/__tests__/types.test.ts
```

### Коммит

`refactor: group chat schema exports`

---

## Шаг 3 — сгруппировать backend serializer mapping

### Что делать

Привести backend serializer mapping к явным группам без изменения output.

Разрешённый вариант:

- оставить в `backend/utils/serializer.py`, если файл небольшой;
- либо создать `backend/utils/response_serializer.py`, если это реально улучшает группировку, но оставить `backend/utils/serializer.py` как совместимый facade;
- сгруппировать функции по entity: chat/search/history/error.

Нельзя:

- менять camelCase/snake_case output;
- менять fallback values;
- менять response shape;
- менять behavior `None`/missing fields.
- менять imports в `backend/main.py`, `backend/analytics/router.py` и других backend-модулях.

### Файлы

- Изменить: `backend/utils/serializer.py`
- Создать при необходимости: `backend/utils/response_serializer.py`

### Критерий приёмки

- serializer читается как contract mapping layer;
- output contract не изменился;
- API examples и serializer tests проходят.

### Проверка

```bash
pytest tests/test_serializer.py tests/test_api_contract.py tests/test_api_examples.py -v
```

### Коммит

`refactor: clarify backend serializer mapping`
