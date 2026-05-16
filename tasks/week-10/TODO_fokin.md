# TODO — Фокин Евгений

**Неделя 10:** 12–18 мая 2026  
**Ветка:** `feature/fokin/history-feedback-refactor-w10`

> Строго refactor-only.  
> Не менять API-контракт, SQL-схему, frontend, agent, search/ranking и release docs.  
> Цель недели — привести history/feedback backend services в аккуратный вид через группировку DB, row mapping и service logic.

---

## Общие правила week-10

- Только `refactor:` коммиты.
- Ровно 3 шага = ровно 3 осмысленных коммита.
- Новые тесты не писать.
- Не менять SQLite schema и migration behavior.
- Не менять endpoint response shape.
- Не менять auth/ownership правила.
- Не менять тексты ошибок.
- Новые helper-файлы разрешены, но каждый файл должен иметь одну понятную группу ответственности.
- Запрещено создавать новую свалку вида `utils.py`, `helpers.py`, `common.py`.
- Если при рефакторинге нужен новый файл, назвать его по смыслу: `row_mappers.py`, `queries.py`, `feedback_store.py`.

---

## Задача: сгруппировать history и feedback services без изменения поведения

Сейчас history/feedback backend-код можно сделать чище:

- отделить row-to-dict mapping от SQL;
- отделить query helpers от service operations;
- сделать feedback service симметричным history service;
- не менять API и данные.

---

## Шаг 1 — вынести history row mappers

### Что делать

Сгруппировать преобразование SQLite rows в dict-ответы.

Разрешённый вариант:

- создать `backend/history/row_mappers.py`;
- перенести туда только row mapping и JSON decode helpers;
- оставить DB operations в `service.py`.

Кандидаты на перенос:

- mapping session rows в dict;
- mapping message rows в dict;
- parsing stored JSON fields для state/results/search_params.

Нельзя:

- менять имена ключей в dict;
- менять обработку пустых/битых JSON полей;
- менять сортировку sessions/messages;
- менять strip think blocks behavior.

### Файлы

- Изменить: `backend/history/service.py`
- Создать при необходимости: `backend/history/row_mappers.py`

### Критерий приёмки

- row mapping не размазан по SQL-функциям;
- service methods читаются как операции;
- history responses не изменились.

### Проверка

```bash
pytest tests/test_history_e2e.py tests/test_history_search_params.py tests/test_pagination.py -v
```

### Коммит

`refactor: extract history row mappers`

---

## Шаг 2 — сгруппировать history query helpers

### Что делать

Упростить SQL/control flow в history service.

Разрешённый вариант:

- создать `backend/history/queries.py`;
- перенести туда только SQL strings или маленькие query helpers;
- оставить ownership/business decisions в `service.py`.

Нельзя:

- менять SQL schema;
- менять where/order/limit semantics;
- менять owner checks;
- менять behavior clear/delete.

### Файлы

- Изменить: `backend/history/service.py`
- Создать при необходимости: `backend/history/queries.py`

### Критерий приёмки

- SQL не мешает читать service operations;
- ownership logic осталась явной;
- history tests проходят как раньше.

### Проверка

```bash
pytest tests/test_history_e2e.py tests/test_stats.py tests/test_ws_integration.py -v
```

### Коммит

`refactor: group history query helpers`

---

## Шаг 3 — привести feedback service к той же структуре

### Что делать

Сгруппировать feedback service по тем же принципам, что history:

- storage/query helpers отдельно;
- service-level операции отдельно;
- mapping отдельно, если он есть.

Разрешённый вариант:

- создать `backend/feedback/feedback_store.py`, если это реально уменьшает смешение SQL и service logic;
- оставить public service functions совместимыми.

Нельзя:

- менять endpoint contract;
- менять DB fields;
- менять validation;
- менять тексты ошибок;
- менять auth behavior.

### Файлы

- Изменить: `backend/feedback/service.py`
- Создать при необходимости: `backend/feedback/feedback_store.py`

### Критерий приёмки

- feedback service структурно похож на history service;
- SQL/storage не смешан с response mapping;
- feedback behavior не изменился.

### Проверка

```bash
pytest tests/test_feedback.py tests/test_api_contract.py -v
```

### Коммит

`refactor: align feedback service structure`
