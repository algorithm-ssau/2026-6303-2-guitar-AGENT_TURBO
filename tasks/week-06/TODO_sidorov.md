# TODO — Сидоров Артемий

**Неделя 6:** 14–20 апреля 2026
**Ветка:** `feature/sidorov/mock-expansion`

> Независимая задача. Все файлы — его собственные, никто другой в week-6 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Backend/Test): обогатить mock_reverb.json до 50+ записей (PRD этап 4)

### Что делать

- Переписать `tests/mock_reverb.json` — расширить до **минимум 50 записей** с разнообразием:
  - **Бренды:** Fender, Gibson, Ibanez, PRS, Jackson, ESP, Epiphone, Squier, Yamaha, Taylor, Martin, G&L, Schecter, Gretsch, Rickenbacker, Music Man (минимум 15 брендов)
  - **Типы:** электро (strat/tele/LP/SG/RG/dinky/superstrat), акустика (dreadnought, parlor, OM, jumbo), классика, semi-hollow (335), hollow, бас (precision, jazz, stingray)
  - **Цены:** равномерное покрытие от $150 до $4500, минимум 10 позиций в диапазоне $300–$800 (начинающие), 10 в диапазоне $800–$2000 (средний), 5 в диапазоне $2000+
  - **Года:** добавить поле `year` (1965–2024), минимум 5 vintage (<1985)
  - **Состояние:** добавить поле `condition` ∈ {"mint","excellent","very good","good","fair"}, покрыть все категории
- Структура каждой записи:
  ```json
  {
    "id": "r_001",
    "title": "Fender Player Stratocaster MX 2023",
    "price": 749,
    "currency": "USD",
    "image_url": "https://rvb-img.reverb.com/image/upload/...",
    "listing_url": "https://reverb.com/item/...",
    "year": 2023,
    "condition": "mint"
  }
  ```
- **Важно:** URL-ы можно фиктивные, но валидные по формату (`https://reverb.com/item/<slug>`)
- Валидация: файл парсится `json.loads`, все поля типа str/int/float

### Файлы

- Изменить: `tests/mock_reverb.json`

### Критерий приёмки

- `jq length tests/mock_reverb.json` ≥ 50
- `jq '[.[] | .brand] | unique | length'` ≥ 15 (или по title — минимум 15 разных брендов)
- Есть минимум 3 bass-гитары и 8+ акустик
- Есть минимум 5 записей с `year < 1985` (vintage)
- pytest на существующих тестах `test_search_reverb.py` и `test_mock_reverb.py` — зелёный (ничего не сломалось)

### Тест: покрывается следующими задачами и существующими тестами

### Коммит: `test: expand mock_reverb.json to 50+ realistic entries`

---

## Задача 2 (Backend): модуль синонимов запросов

### Что делать

- Создать `backend/search/synonyms.py`:
  - Словарь `SYNONYMS: dict[str, str]` — сленг/сокращение → каноничное название:
    ```python
    SYNONYMS = {
        "strat": "stratocaster",
        "tele": "telecaster",
        "lp": "les paul",
        "сг": "sg",
        "стратокастер": "stratocaster",
        "телекастер": "telecaster",
        "лес пол": "les paul",
        "хамбакер": "humbucker",
        "сингл": "single coil",
        "акустика": "acoustic",
        "электричка": "electric",
        "бас": "bass",
        "полуакустика": "semi-hollow",
        ...  # минимум 20 записей, RU + EN
    }
    ```
  - Функция `expand_queries(queries: list[str]) -> list[str]`:
    - Для каждого запроса добавляет расширенную версию (каноничную форму через SYNONYMS)
    - Регистронезависимо
    - Исходный список сохраняется
    - Дубликаты удаляются
- Обновить `backend/search/search_reverb.py`:
  - В `search_reverb()` — ПЕРЕД `_filter_by_queries` и ПЕРЕД `_search_reverb_api` вызвать `expand_queries(search_queries)`
  - Мок-путь и real-путь оба используют расширенный список

### Файлы

- Создать: `backend/search/synonyms.py`
- Изменить: `backend/search/search_reverb.py` (1 строка вызова `expand_queries`)

### Критерий приёмки

- `expand_queries(["strat"])` → `["strat", "stratocaster"]`
- `expand_queries(["LP", "tele"])` → `["LP", "les paul", "tele", "telecaster"]` (случай сохраняется, расширение добавляется)
- Запрос "найди страт до 500$" через полный пайплайн с mock — находит Stratocaster
- Словарь содержит минимум 20 записей

### Тест: `tests/test_synonyms.py`

- expand_queries со сленгом → найдена канонич. форма
- expand_queries с пустым списком → пустой список
- expand_queries с неизвестным словом → без изменений
- SYNONYMS содержит русские и английские записи

### Коммит: `feat: add synonyms expansion for search queries`

---

## Задача 3 (Backend/Test): retry/backoff для реального Reverb API

### Что делать

- Обновить `backend/search/search_reverb.py::_search_reverb_api`:
  - Обернуть `requests.get(...)` в retry-цикл:
    - Максимум **3 попытки**
    - Backoff: 0.5s → 1s → 2s (экспоненциально)
    - Ретраится только при: `ConnectionError`, `Timeout`, HTTP 502, HTTP 503, HTTP 504
    - Другие HTTP ошибки (4xx) — сразу пропускаются без ретрая
  - Логировать каждую попытку через `get_logger("search.reverb")`
  - **Не использовать** `tenacity` (не добавляем новую зависимость) — простой цикл `for attempt in range(3): try: ... except: time.sleep(...)`

### Файлы

- Изменить: `backend/search/search_reverb.py`

### Критерий приёмки

- При мокнутом `requests.get` который 2 раза кидает `Timeout` и на 3-й раз возвращает ответ — функция возвращает успешный результат
- При мокнутом `requests.get` который 3 раза кидает ошибку — функция возвращает `[]` (не падает)
- При HTTP 404 — ретрая нет, функция сразу возвращает `[]`
- В логах виден `attempt 1/3`, `attempt 2/3` и т.д.

### Тест: `tests/test_reverb_retry.py`

- Mock `requests.get` → 2 неудачи + 1 успех → успех
- Mock → 3 неудачи → пустой результат
- Mock → 404 → пустой результат без ретрая
- Количество вызовов `requests.get` проверяется через `mock.call_count`

### Коммит: `feat: add retry with exponential backoff for Reverb API`
