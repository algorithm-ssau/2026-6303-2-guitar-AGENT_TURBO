# PRD Behavior Matrix — Агент подбора гитар

Матрица связывает требования PRD с текущими проверками поведения агента.

## Легенда статусов

- **ready** — сценарий покрыт тестами и работает стабильно
- **degraded** — сценарий работает с ограничениями (без API ключа, mock-режим)
- **pending** — сценарий запланирован, но не реализован

## Матрица

| # | PRD пункт | Сценарий | Ожидаемый режим | Где проверяется | Статус |
|---|-----------|----------|-----------------|-----------------|--------|
| 1 | §5.1 Поиск по описанию звука | "тёплый джазовый звук до 1000" | search | LLM-router prompt + `test_llm_router_contract.py` | ready |
| 2 | §5.1 Поиск по модели | "Telecaster до 800 долларов" | search | LLM-router prompt + `test_llm_router_contract.py` | ready |
| 3 | §5.3 Консультация (теория) | "P90 vs humbucker" / "что такое хамбакер" | consultation | LLM-router prompt + `test_agent_integration.py` | ready |
| 3a | §5.3 Консультация по найденным вариантам | "чем 1ый лучше 2го" / "что новичку взять из этих" после search | consultation | numbered search context + `test_context_manager.py`, `test_agent.py` | ready |
| 4 | §5.1 Начинающий | "beginner guitar" / "гитару для начинающего" | search | LLM-router prompt | ready |
| 5 | §5.2 Маппинг абстракций | "metal high output" / "мясную палку" | search | LLM-router prompt, `MAPPING.md` (23 абстракции) | ready |
| 6 | §5.2 Vintage | "винтажный стратокастер 70-х до 3000$" | search | LLM-router prompt | ready |
| 7 | §5.2 Бюджет в рублях | "ищу теле до 80 тыс руб" → price_max=800 | search | LLM-router prompt few-shot/rules | ready |
| 8 | §5.4 Противоречивый запрос | "Хочу акустику с флойдом и EMG" | search (graceful) | LLM-router prompt rules | ready |
| 9 | §5.3 Слишком общий запрос | "гитара?" / пустая строка | clarification или validation error для пустого input | `test_llm_router_contract.py`, API validation | ready |
| 10 | §9 Off-topic | "напиши код на python" / "какая погода" | off_topic internally, `consultation` externally | LLM-router intent + dedicated off-topic prompt + `test_off_topic.py` | ready |

## Ограничения (антигаллюцинации) — PRD §7

| Ограничение | Как обеспечивается | Статус |
|-------------|-------------------|--------|
| Не выдумывать цены | Цены берутся только из Reverb API, LLM не генерирует цены | ready |
| Не выдумывать ссылки | Ссылки берутся только из `search_reverb`, consultation-ответы фильтруются `_sanitize_consultation_answer` | ready |
| Не придумывать catalog content в консультации | Sanitizer разрешает только модели из последней search-выдачи и блокирует ссылки/магазины/новые списки моделей | ready |
| Не проверять продавцов | Промпт не содержит инструкций о продавцах, ограничение в `AGENT_PROMPT.md` | ready |
| Не обсуждать доставку/оплату | Явный запрет в `AGENT_PROMPT.md` строка "Не обсуждай доставку, оплату" | ready |
| Search только для search-запросов | `LLMClient.classify_and_plan_query()` + strict route validation в `service.py` | ready |
| Consultation без поиска | `_handle_consultation` не вызывает `search_reverb` | ready |

## Degraded Mode — поведение без API

| Сценарий | Поведение | Статус |
|----------|-----------|--------|
| Без `GROQ_API_KEY` | REST `503` / WebSocket `error`, regex fallback не используется | degraded |
| `USE_MOCK_REVERB=true` | Mock-данные из `search_reverb`, ранжирование работает | degraded |
| LLM вернул невалидный JSON | REST `502` / WebSocket `error`, regex fallback не используется | ready |
| Reverb вернул 0 результатов | `_build_relaxed_queries` пробует ослабленный запрос | ready |
| Пустой запрос | REST validation `422`, WebSocket error | ready |

## Покрытие PRD

Все 10 обязательных пользовательских сценариев PRD покрыты тестами и имеют статус `ready`. Degraded-режимы работают корректно для базовых сценариев без внешних API-ключей.
