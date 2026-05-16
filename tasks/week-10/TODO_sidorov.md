# TODO — Сидоров Артемий

**Неделя 10:** 12–18 мая 2026  
**Ветка:** `feature/sidorov/search-refactor-w10`

> Строго refactor-only.  
> Не менять Reverb/search поведение, API-контракт, ranking, agent, frontend и документацию release-слоя.  
> Цель недели — сгруппировать `backend/search/search_reverb.py`, чтобы mock/API/normalization/fallback не лежали одной свалкой.

---

## Общие правила week-10

- Только `refactor:` коммиты.
- Ровно 3 шага = ровно 3 осмысленных коммита.
- Новые тесты не писать.
- Не менять существующие тесты, кроме механического обновления import path после выноса helper-функций.
- Не менять публичную сигнатуру `search_reverb` и `search_reverb_exact`.
- Не менять формат результата поиска.
- Не менять env flags и degraded/mock поведение.
- Новые helper-файлы разрешены, но каждый файл должен иметь одну понятную группу ответственности.
- Запрещено создавать новую свалку вида `utils.py`, `helpers.py`, `common.py`.
- Если при рефакторинге нужен новый файл, назвать его по смыслу: `mock_reverb.py`, `reverb_normalizer.py`, `reverb_client.py`.

---

## Задача: сгруппировать Reverb search без изменения поведения

Сейчас `backend/search/search_reverb.py` смешивает:

- загрузку mock data;
- фильтрацию mock results;
- нормализацию ответа Reverb;
- deduplication;
- HTTP-запросы;
- retry/fallback flow.

Нужно разнести эти группы по смыслу и оставить внешний контракт прежним.

---

## Шаг 1 — вынести mock search helpers

### Что делать

Сгруппировать всё, что относится только к локальным mock-данным.

Разрешённый вариант:

- создать `backend/search/mock_reverb.py`;
- перенести туда mock data path/load/filter helpers;
- в `search_reverb.py` оставить только вызов mock-flow.

Кандидаты на перенос:

- `_get_mock_data_path`;
- `_load_mock_data`;
- `_filter_by_queries`;
- `_filter_by_price`.

Нельзя:

- менять путь к mock data;
- менять правила фильтрации;
- менять порядок результатов;
- менять поведение `USE_MOCK_REVERB`.

### Файлы

- Изменить: `backend/search/search_reverb.py`
- Создать при необходимости: `backend/search/mock_reverb.py`

### Критерий приёмки

- mock-specific код лежит отдельно;
- `search_reverb.py` не содержит деталей загрузки mock-файла;
- mock mode работает как раньше.

### Проверка

```bash
USE_MOCK_REVERB=true pytest tests/test_search_reverb.py tests/test_search.py -v
```

### Коммит

`refactor: isolate reverb mock helpers`

---

## Шаг 2 — вынести normalization и deduplication

### Что делать

Сгруппировать преобразование внешнего listing в внутренний search result.

Разрешённый вариант:

- создать `backend/search/reverb_normalizer.py`;
- перенести туда normalization/dedup helpers;
- использовать явные имена вместо длинных inline-преобразований.

Кандидаты на перенос:

- `_normalize_reverb_response`;
- `_deduplicate_listings`.

Нельзя:

- менять ключи результата;
- менять fallback для price/title/url/image;
- менять dedup key;
- менять порядок после deduplication.

### Файлы

- Изменить: `backend/search/search_reverb.py`
- Создать при необходимости: `backend/search/reverb_normalizer.py`

### Критерий приёмки

- normalization читается отдельно от HTTP-flow;
- format результата не изменился;
- deduplication работает как раньше.

### Проверка

```bash
pytest tests/test_reverb_api_format.py tests/test_search_reverb.py -v
```

### Коммит

`refactor: extract reverb result normalization`

---

## Шаг 3 — сгруппировать API search flow

### Что делать

Упростить контрольный поток в API search части без изменения логики.

Разрешённый вариант:

- создать `backend/search/reverb_client.py`;
- перенести туда только низкоуровневый HTTP/API flow;
- оставить `search_reverb.py` как thin orchestration layer.

Кандидаты на перенос:

- `_search_reverb_api`;
- небольшие private helpers, если они относятся только к HTTP/API flow.

Нельзя:

- менять timeout/retry поведение;
- менять fallback при malformed/empty response;
- менять количество возвращаемых результатов;
- менять обработку `price_min`, `price_max`, `search_queries`.

### Файлы

- Изменить: `backend/search/search_reverb.py`
- Создать при необходимости: `backend/search/reverb_client.py`

### Критерий приёмки

- `search_reverb.py` показывает общий flow: mock/API/fallback;
- HTTP details изолированы;
- search tests проходят без изменения expected behavior.

### Проверка

```bash
pytest tests/test_reverb_retry.py tests/test_search_reverb.py tests/test_reverb_real.py -v
```

### Коммит

`refactor: simplify reverb api flow`
