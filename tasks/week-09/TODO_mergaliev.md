# TODO — Мергалиев Радмир

**Неделя 9:** 5–11 мая 2026  
**Ветка:** `feature/mergaliev/contract-freeze-w9`

> Финальная заморозка API-контракта frontend/backend.  
> Не дублировать week-08 API release reference: использовать его как baseline и исправлять расхождения с реальным кодом.  
> Не трогать ranking algorithm, LLM prompts, frontend visual components.

---

## Задача: закрыть contract drift и зафиксировать финальный API

Сейчас есть риск, что backend, frontend Zod-схемы, тесты и документация ожидают разные формы данных. Нужно привести всё к одному финальному контракту.

Обязательные поверхности:

- `POST /api/chat`;
- `POST /api/query/parse`;
- `GET /api/sessions`;
- `POST /api/sessions`;
- `GET /api/sessions/{id}/messages`;
- `DELETE /api/sessions/{id}`;
- `DELETE /api/history`;
- `GET /api/stats`;
- `GET /api/metrics/health`;
- `WS /chat`.

---

## Шаг 1 — contract audit по реальному backend

### Что делать

Сверить реальные ответы backend с документацией и frontend-схемами.

Для каждого endpoint зафиксировать:

- request body;
- response body;
- error response;
- camelCase/snake_case для frontend-facing полей;
- какие optional поля реально optional;
- статус `ready`, `degraded` или `pending`.

Если `docs/API_RELEASE_REFERENCE.md` расходится с кодом, исправить документ или код. Нельзя оставлять документацию, которая обещает несуществующий контракт.

### Файлы

- Изменить: `docs/API_RELEASE_REFERENCE.md`
- Возможно изменить: `docs/examples/api/*.json`
- Возможно изменить: `backend/models.py`
- Возможно изменить: `backend/search/models.py`
- Возможно изменить: `backend/history/models.py`

### Критерий приёмки

- все documented examples парсятся;
- API reference соответствует реальному состоянию;
- pending/degraded endpoint-ы явно помечены.

### Проверка

```bash
pytest tests/test_api_examples.py tests/test_api_contract.py -v
```

### Коммит

`docs: audit final API contract`

---

## Шаг 2 — стабилизировать frontend/backend boundary

### Что делать

Исправить расхождения между backend responses и frontend API/Zod layer.

Зона ответственности:

- frontend API boundary:
  - `frontend/src/features/chat/api.ts`;
  - `frontend/src/features/chat/types.ts`;
  - `frontend/src/features/chat/__tests__/api.test.ts`;
  - `frontend/src/features/chat/__tests__/types.test.ts`;
- backend response models/serializers:
  - `backend/models.py`;
  - `backend/search/models.py`;
  - `backend/utils/serializer.py`.

Не менять visual components. Если компонент ломается из-за нового типа, согласовать с Сальниковым.

Финальное правило:

- frontend-facing поля должны быть camelCase;
- backend internal поля могут быть snake_case;
- conversion должен быть явным и покрытым проверками;
- ошибки должны иметь стабильный формат.

### Файлы

- Изменить: `frontend/src/features/chat/api.ts`
- Изменить: `frontend/src/features/chat/types.ts`
- Изменить: `frontend/src/features/chat/__tests__/api.test.ts`
- Изменить: `frontend/src/features/chat/__tests__/types.test.ts`
- Возможно изменить: `backend/utils/serializer.py`
- Возможно изменить: `tests/test_serializer.py`

### Критерий приёмки

- frontend API/type tests проходят;
- backend contract tests проходят;
- один и тот же пример response валиден в docs и frontend schema;
- optional поля не приводят к падению UI.

### Проверка

```bash
pytest tests/test_api_contract.py tests/test_serializer.py -v
cd frontend && npm run test -- --run src/features/chat/__tests__/api.test.ts src/features/chat/__tests__/types.test.ts
```

### Коммит

`fix: freeze frontend backend contract`

---

## Шаг 3 — final contract regression gate

### Что делать

Добавить или обновить минимальный набор regression-проверок для финального контракта:

- search response с 3–5 results;
- consultation response без results;
- empty results;
- validation error на empty query;
- missing optional fields;
- WS `status`;
- WS `result`;
- WS `error`;
- session history response.

Не проверять хрупкие поля вроде точного текста LLM-ответа.

### Файлы

- Изменить: `tests/test_api_contract.py`
- Возможно изменить: `tests/test_ws_endpoint.py`
- Возможно изменить: `tests/test_history_e2e.py`
- Возможно изменить: `frontend/src/features/chat/__tests__/api.test.ts`

### Критерий приёмки

- contract regression suite проходит локально;
- failures показывают конкретный endpoint/shape;
- frontend и backend больше не расходятся по базовым формам данных.

### Проверка

```bash
pytest tests/test_api_contract.py tests/test_ws_endpoint.py tests/test_history_e2e.py -v
cd frontend && npm run test -- --run src/features/chat/__tests__/api.test.ts src/features/chat/__tests__/types.test.ts
```

### Коммит

`test: add final contract regression checks`
