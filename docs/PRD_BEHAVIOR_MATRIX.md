# PRD Behavior Matrix — Агент подбора гитар

Матрица связывает требования PRD с текущими проверками поведения агента.

## Легенда статусов

- **ready** — сценарий покрыт тестами и работает стабильно
- **degraded** — сценарий работает с ограничениями (без API ключа, mock-режим)
- **pending** — сценарий запланирован, но не реализован

## Матрица

| # | PRD пункт | Сценарий | Ожидаемый режим | Где проверяется | Статус |
|---|-----------|----------|-----------------|-----------------|--------|
| 1 | §5.1 Поиск по описанию звука | "тёплый джазовый звук до 1000" | search | `test_mode_detector.py::search_jazz_budget`, `test_prompt_snapshot.py` | ready |
| 2 | §5.1 Поиск по модели | "Telecaster до 800 долларов" | search | `test_mode_detector.py::search_blues_budget`, `test_prompt_snapshot.py` | ready |
| 3 | §5.3 Консультация (теория) | "P90 vs humbucker" / "что такое хамбакер" | consultation | `test_mode_detector.py::consultation_pickup_diff`, `test_mode_detector_edge_cases.py::p90_compromise_consultation` | ready |
| 4 | §5.1 Начинающий | "beginner guitar" / "гитару для начинающего" | search | `test_prompt_snapshot.py` (акустика для начинающего) | ready |
| 5 | §5.2 Маппинг абстракций | "metal high output" / "мясную палку" | search | `test_prompt_snapshot.py`, `MAPPING.md` (23 абстракции) | ready |
| 6 | §5.2 Vintage | "винтажный стратокастер 70-х до 3000$" | search | `test_prompt_snapshot.py` | ready |
| 7 | §5.2 Бюджет в рублях | "ищу теле до 80 тыс руб" → price_max=800 | search | `test_prompt_snapshot.py`, few-shot в `param_extractor.py` | ready |
| 8 | §5.4 Противоречивый запрос | "Хочу акустику с флойдом и EMG" | search (graceful) | `test_prompt_snapshot.py`, few-shot в `param_extractor.py` | ready |
| 9 | §5.3 Слишком общий запрос | "гитара?" / пустая строка | consultation | `test_mode_detector_edge_cases.py::test_very_short_query`, `test_mode_detector_edge_cases.py::test_empty_string` | ready |
| 10 | §9 Off-topic | "напиши код на python" / "какая погода" | off_topic | `test_mode_detector.py` (off-topic паттерны в `mode_detector.py`) | ready |

## Ограничения (антигаллюцинации) — PRD §7

| Ограничение | Как обеспечивается | Статус |
|-------------|-------------------|--------|
| Не выдумывать цены | Цены берутся только из Reverb API, LLM не генерирует цены | ready |
| Не выдумывать ссылки | Ссылки берутся только из `search_reverb`, consultation-ответы фильтруются `_sanitize_consultation_answer` | ready |
| Не проверять продавцов | Промпт не содержит инструкций о продавцах, ограничение в `AGENT_PROMPT.md` | ready |
| Не обсуждать доставку/оплату | Явный запрет в `AGENT_PROMPT.md` строка "Не обсуждай доставку, оплату" | ready |
| Search только для search-запросов | `mode_detector.py` + `_classify_query()` в `service.py` | ready |
| Consultation без поиска | `_handle_consultation` не вызывает `search_reverb` | ready |

## Degraded Mode — поведение без API

| Сценарий | Поведение | Статус |
|----------|-----------|--------|
| Без `GROQ_API_KEY` | `create_llm_client()` → None, consultation fallback "сервис недоступен", search fallback `search_queries=[text]` | degraded |
| `USE_MOCK_REVERB=true` | Mock-данные из `search_reverb`, ранжирование работает | degraded |
| LLM вернул невалидный JSON | `extract_params_from_llm_response` → fallback `{search_queries: [], price_min: None, price_max: None}` | ready |
| Reverb вернул 0 результатов | `_build_relaxed_queries` пробует ослабленный запрос | ready |
| Пустой запрос | `mode_detector` → consultation | ready |

## Покрытие PRD

Все 10 обязательных пользовательских сценариев PRD покрыты тестами и имеют статус `ready`. Degraded-режимы работают корректно для базовых сценариев без внешних API-ключей.
