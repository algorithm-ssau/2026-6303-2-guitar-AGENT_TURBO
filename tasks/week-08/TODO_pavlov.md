# TODO — Павлов Виктор

**Неделя 8:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/pavlov/llm-release-w8`

> Независимая release-задача по качеству LLM.
> Не трогать frontend, ranking, search_reverb, Docker, README.
> Тесты должны работать без `GROQ_API_KEY`.

---

## Задача: LLM golden scenarios для финальной проверки поведения агента

Нужно зафиксировать набор эталонных пользовательских запросов и проверить, что mode detection / LLM-facing логика соответствует PRD.

---

## Шаг 1 — fixture с 30 golden-сценариями

### Что делать

Создать `tests/fixtures/llm_golden_scenarios.json`.

Файл должен содержать ровно 30 объектов формата:

```json
{
  "id": "search_jazz_001",
  "query": "Хочу тёплый джазовый звук до 1500$",
  "expected_mode": "search",
  "expected": {
    "price_max": 1500,
    "must_include_terms": ["jazz"]
  }
}
```

Распределение:

- 12 search-запросов;
- 8 consultation-запросов;
- 5 clarification-запросов;
- 5 off-topic-запросов.

Обязательно покрыть:

- strat / tele / les paul;
- jazz / blues / metal;
- бюджет в долларах;
- бюджет в рублях;
- vintage / 70-е;
- beginner-запрос;
- P90 vs humbucker;
- off-topic;
- противоречивый запрос.

### Файлы

- Создать: `tests/fixtures/llm_golden_scenarios.json`

### Критерий приёмки

- JSON валиден;
- ровно 30 сценариев;
- у каждого сценария есть `id`, `query`, `expected_mode`, `expected`.

### Коммит

`test: add LLM golden scenario fixtures`

---

## Шаг 2 — regression test без реального LLM

### Что делать

Создать `tests/test_llm_golden_scenarios.py`.

Тест должен:

- загружать `llm_golden_scenarios.json`;
- не обращаться к Groq;
- проверять `detect_mode(query)` там, где это возможно;
- для search-сценариев проверять наличие ожидаемых budget/style/type признаков через существующие parser/helper функции, если они доступны;
- для consultation/off-topic проверять, что режим не search;
- при падении показывать `id` сценария.

Если часть логики зависит от LLM, использовать mock/fake response и проверять нормализацию результата.

### Файлы

- Создать: `tests/test_llm_golden_scenarios.py`

### Критерий приёмки

- тест запускается без `GROQ_API_KEY`;
- падение указывает `id` сценария;
- минимум 25 из 30 сценариев должны проходить, иначе тест падает.

### Коммит

`test: add LLM golden scenario regression`

---

## Шаг 3 — документ финального поведения LLM

### Что делать

Создать `docs/LLM_RELEASE_BEHAVIOR.md`.

Документ должен содержать разделы:

1. `## Режимы агента`
   - search
   - consultation
   - clarification
   - off-topic

2. `## Что агент не должен делать`
   - не выдумывать цены;
   - не обсуждать доставку;
   - не проверять продавцов;
   - не придумывать характеристики;
   - не возвращать ссылки вне результатов поиска.

3. `## Примеры`
   - минимум 10 примеров `запрос → ожидаемый режим`.

4. `## Ограничения`
   - degraded mode без API-ключа;
   - зависимость качества от LLM;
   - mock mode для Reverb.

### Файлы

- Создать: `docs/LLM_RELEASE_BEHAVIOR.md`

### Критерий приёмки

- документ можно использовать на защите;
- явно описаны антигаллюцинационные правила;
- есть минимум 10 примеров.

### Коммит

`docs: document final LLM release behavior`
