# TODO — Павлов Виктор

**Неделя 6:** 14–20 апреля 2026
**Ветка:** `feature/pavlov/prompt-quality`

> Независимая задача. Все файлы — его собственные, никто другой в week-6 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Backend/Docs): расширить маппинг до 20 абстракций (PRD §5.2, §9)

### Что делать

- Переписать `docs/MAPPING.md` — расширить таблицу до **20 строк абстракций**. Формат таблицы тот же:
  `| Абстрактный эпитет | Категория / Деталь | Значение (ТТХ) | Примеры для search_queries | Примечания |`
- Добавить (в дополнение к существующим 6): **jazz**, **blues**, **funk**, **reggae**, **country**, **shoegaze**, **djent**, **grunge**, **lo-fi**, **sparkle**, **crunch**, **bell-like**, **honky**, **quack**, **chime**, **punchy**, **scooped**, **creamy**
- Для каждой строки — минимум 3 `search_queries` (бренд + модель)
- Сохранить исходный стиль: "Примечание" с 1–2 строками про физическую природу звука
- В конце файла добавить секцию `## Покрытие PRD` с пояснением, что это закрывает требование MVP §9 "маппинг 15–20 абстрактных характеристик"

### Файлы

- Изменить: `docs/MAPPING.md`

### Критерий приёмки

- В таблице ≥ 20 строк абстракций
- Каждая строка имеет минимум 3 search_queries
- Все примечания содержательны (не "todo")
- Markdown-линтер не ругается

### Тест: покрывается Задачей 3 (test_prompt_snapshot)

### Коммит: `docs: expand mapping to 20 abstractions (PRD §5.2)`

---

## Задача 2 (Backend): улучшить few-shot в build_search_prompt

### Что делать

- Обновить `backend/agent/param_extractor.py::build_search_prompt`:
  - Добавить **3 новых few-shot примера** в тело промпта:
    1. **Противоречивый запрос** (PRD сценарий 6): `"Хочу акустику с флойдом и EMG"` → возврат валидного JSON с пояснением в `search_queries`, но ставить `type: "acoustic"` и предупреждение не генерировать (агент отдаст в consultation через detect_mode — но в этом few-shot'е показываем что LLM сама не выдумывает противоречивые бренды)
    2. **Бюджет в рублях**: `"ищу теле до 80 тыс руб"` → `price_max: 800` (курс 100 руб/$)
    3. **Vintage/год**: `"винтажный стратокастер 70-х до 3000$"` → `search_queries: ["Fender Stratocaster 1970s", "Fender Vintage Stratocaster"]`, `price_max: 3000`, `condition: "vintage"`
- Few-shot примеры оформить как JSON-блоки с комментариями-пояснениями
- **НЕ трогать** `llm_client.py`, `service.py`, `AGENT_PROMPT.md` (последний — зона week-5 Павлова, уже трогается там)

### Файлы

- Изменить: `backend/agent/param_extractor.py`

### Критерий приёмки

- В теле промпта видны 3 новых few-shot блока
- Сохраняется предыдущий формат (JSON на выходе)
- Запуск `pytest tests/test_param_extractor.py -v` зелёный

### Тест: покрывается Задачей 3

### Коммит: `feat: add few-shot examples for contradictions, rubles, vintage`

---

## Задача 3 (Тестирование): snapshot-регрессия качества промпта

### Что делать

- Создать `tests/fixtures/llm_snapshots.json` — 15 канонических запросов с ожидаемыми ответами замоканного LLM:
  ```json
  [
    {
      "query": "Найди стратокастер до 500$",
      "llm_response": {"search_queries": ["Fender Stratocaster", "Squier Classic Vibe Stratocaster"], "price_max": 500, "type": "stratocaster"},
      "expect": {"has_type": "stratocaster", "has_price_max": 500, "min_queries": 2}
    },
    ...
  ]
  ```
  Примеры должны покрывать: **strat/tele/LP, jazz/blues/metal, бюджет в $/руб, acoustic, vintage, противоречие, слэнг "страт/теле/лп"**
- Создать `tests/test_prompt_snapshot.py`:
  - Загрузить fixture
  - Замокать `LLMClient.extract_search_params` чтобы возвращал `llm_response` из fixture
  - Для каждого примера вызвать `interpret_query` (или напрямую параметр-экстрактор) и проверить `expect`
  - Работает **без GROQ_API_KEY** (mock)
  - Если < 13 из 15 проходят — падать
- Этот тест — **регрессионный барьер**: любое будущее изменение `MAPPING.md` или промпта прогоняется через него. Минимум 13 из 15 зелёных.

### Файлы

- Создать: `tests/fixtures/llm_snapshots.json`
- Создать: `tests/test_prompt_snapshot.py`

### Критерий приёмки

- 15 запросов покрывают разнообразие сценариев (металл, джаз, акустика, бюджет, vintage, сленг)
- Все 15 проходят (или минимум 13 — с жёстким порогом в `assert`)
- Тест стабилен между запусками (никакой рандомизации)
- Запуск без GROQ_API_KEY — не падает

### Коммит: `test: add prompt quality snapshot regression tests`
