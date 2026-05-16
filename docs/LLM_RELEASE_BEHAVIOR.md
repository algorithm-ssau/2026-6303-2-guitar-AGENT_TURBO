# LLM Release Behavior — Поведение агента в production

Документ описывает режимы работы агента, ограничения и degraded-поведение для защиты проекта.

## Режимы работы

### 1. Search (Поиск)
- **Триггер:** Пользователь хочет подобрать/купить конкретный инструмент, указывает бюджет, модель или стиль.
- **Пайплайн:** `LLMClient.classify_and_plan_query` → validation/normalization → exact agent Reverb search → `rank_results` → ответ с карточками.
- **Результат:** JSON со списком гитар (ссылки, цены, фото) из реального каталога Reverb и `searchParams` из текущего LLM-router snapshot.
- **Ready contract:** `enough_for_search=true` требует финальный effective `search_params`: 1-3 `search_queries`, явный `price_max`/`price_min`, явный `type` или `"any"`, плюс нормализованные optional fields. Backend не достраивает ready search из старого session state.

### 2. Consultation (Консультация)
- **Триггер:** Теоретические вопросы ("что такое хамбакер?", "как дерево влияет на звук?") и follow-up вопросы по последней поисковой выдаче ("чем #1 лучше #2?", "что новичку взять из этих?").
- **Пайплайн:** `LLMClient.classify_and_plan_query` → numbered search context из истории → `_handle_consultation` → отдельный consultation prompt отвечает текстом.
- **Результат:** Markdown-текст с объяснением. **Поиск на Reverb НЕ вызывается.**
- **Follow-up over results:** backend передаёт сохранённые результаты как `Последняя поисковая выдача: #1 ... #2 ...`; смысл ссылок на "первый/второй/из этих" интерпретирует LLM, не backend regex.

### 3. Clarification (Уточнение)
- **Триггер:** Запрос на поиск, но не хватает данных (нет бюджета или типа гитары).
- **Пайплайн:** `LLMClient.classify_and_plan_query` → validation/normalization → structured clarification state → dedicated `CLARIFICATION_PROMPT.md`.
- **Результат:** LLM-generated уточняющий вопрос или подтверждение, сессионное состояние сохраняется.
- **Contract:** `search_params=null` допустим, если `intent="search"`, `enough_for_search=false` и `missing_fields` содержит `budget` и/или `type`.
- **No-preference:** если пользователь не может выбрать тип, router возвращает `no_preference_fields=["type"]` и explicit `type="any"`. Если бюджет неизвестен, backend не запускает unlimited search: используется `budget_default_offer=true` для одного подтверждения или explicit `search_params.price_max` с diagnostic `default_actions=["apply_beginner_budget"|"accept_beginner_budget"]`.

### 4. Off-topic (Не по теме)
- **Триггер:** Запрос не связан с гитарами/музыкой (программирование, погода, рецепты).
- **Пайплайн:** `LLMClient.classify_and_plan_query` → `off_topic` → dedicated `OFF_TOPIC_PROMPT.md` → strict refusal sanitizer.
- **Результат:** Короткий LLM-generated отказ. Router только выставляет intent; наружу остаётся `mode: "consultation"`.

## Что агент НЕ должен делать (антигаллюцинации)

1. **Не выдумывать цены** — все цены берутся только из API Reverb.
2. **Не выдумывать ссылки** — все URL берутся только из `search_reverb`. Consultation-ответы фильтруются через `_sanitize_consultation_answer` (блокирует URL, упоминания магазинов и invented catalog content; модели из последней search-выдачи разрешены для сравнения).
3. **Не проверять продавцов** — агент не оценивает репутацию продавцов.
4. **Не обсуждать доставку/оплату** — явный запрет в `AGENT_PROMPT.md`.
5. **Не генерировать JSON в consultation** — режим консультации возвращает только текст.

## Degraded Mode (работа без внешних сервисов)

### Без `GROQ_API_KEY`
- `create_llm_client()` возвращает `None`.
- REST `/api/chat` возвращает `503` с body `{"detail": "Сервис временно недоступен: не удалось обработать запрос через LLM."}`.
- WebSocket `/chat` отправляет `type="error"` с user-safe статусом.
- Regex/NLP fallback не используется.

### С `USE_MOCK_REVERB=true`
- `search_reverb` возвращает mock-данные вместо реальных запросов к Reverb API.
- Ранжирование (`rank_results`) работает нормально на mock-данных.
- Используется в тестах для изоляции от внешних API.

### Когда LLM-router вернул невалидный contract
- Backend сначала валидирует router JSON и собирает конкретные ошибки контракта.
- Для repairable ошибок, например `search_params.search_queries=[]` при `intent=search` и `enough_for_search=true`, backend делает один repair-вызов в тот же `LLM_ROUTER_MODEL`.
- Repair prompt получает исходный user query, компактный router context, structured state, невалидный JSON и validation errors.
- Backend не синтезирует `search_queries`, intent или missing fields сам; исправленный JSON должен вернуть LLM-router.
- Backend не применяет `default_actions` как runtime mutations: если используется beginner default, repair должен вернуть фактический `search_params.price_max`.
- Ready routes with non-empty `missing_fields`, unknown missing fields, empty or 4+ `search_queries`, invalid enum values, or incoherent price ranges are repaired/rejected instead of being silently coerced.
- Исправленный JSON проходит ту же валидацию. Если исходный intent был валидным, repair обязан сохранить его.
- Repair prompt тоже ограничен `ROUTER_MAX_PROMPT_CHARS`; oversized repair не отправляется provider.
- Если repair невозможен или снова невалиден, REST `/api/chat` возвращает `502` с body `{"detail": "Некорректный ответ LLM-router."}`, а WebSocket `/chat` отправляет `type="error"` с user-safe статусом.
- Regex/NLP fallback не используется.

### Когда consultation ответ похож на invented catalog
- Backend блокирует ссылки, магазины и конкретные модели, которых нет в последней search-выдаче.
- Если latest search context отсутствует, блок превращается в `mode="clarification"` с вопросом про бюджет и тип инструмента.
- Если latest search context есть, пользователь получает короткий consultation ответ о том, что агент может сравнивать только текущие numbered options.
- Внешний ответ не должен содержать внутренний guardrail текст `Сейчас это выглядит как запрос на подбор...`.

### Когда пользователь не знает критерий подбора
- Backend хранит `asked_fields`, `no_preference_fields` и `pending_defaults` в JSON `session_state`.
- Повторные ответы вроде "я не понимаю типы" интерпретирует LLM-router, не backend regex.
- Для неизвестного типа router может закрыть поле через `type="any"`.
- Для неизвестного бюджета применяется product policy: спросить "Ок, показать недорогие варианты для новичка до $500?" либо вернуть ready search с explicit `search_params.price_max=500`, если router видит начальный запрос без лишних вопросов. Backend сам не подставляет `$500`.

### Когда provider отклонил router-запрос из-за размера
- Router и генерация ответов могут использовать разные модели: `LLM_ROUTER_MODEL` для JSON-классификации, `LLM_ANSWER_MODEL`/`LLM_MODEL` для консультаций и off-topic ответов.
- Router model намеренно не наследует `LLM_MODEL` по умолчанию, чтобы тяжёлые answer-модели вроде `groq/compound` не использовались для каждого intent-запроса.
- `ROUTER_MAX_PROMPT_CHARS` — backend safety budget для стоимости/latency router-запроса, а не реальное context window модели.
- Если prompt tier превышает `ROUTER_MAX_PROMPT_CHARS`, backend пропускает этот tier локально только для текущего запроса.
- Если Groq возвращает `413/request_too_large`, backend не отдаёт ошибку пользователю сразу и помечает tier как known-bad для текущих `(session_id, router_model)` на короткий TTL.
- Router автоматически повторяется с более компактным context tier:
  1. `normal` — обычный компактный router context;
  2. `emergency` — последняя numbered search-выдача и последние user turns без длинных assistant-ответов;
  3. `stateless` — только текущий запрос и структурированное состояние сессии.
- Если один из retry успешен, пользователь получает обычный search/consultation/clarification ответ.
- Если все tiers не сработали, REST/WebSocket возвращают нейтральную ошибку обработки LLM без требования очистить историю.
- Rate limit (`429`) не retry-ится, потому что повторный запрос сразу потратит ещё лимит и не устранит причину.

### Когда Reverb вернул 0 результатов
- Agent path возвращает пустой список `results: []` с теми же LLM-router `searchParams`.
- Backend больше не запускает скрытый relaxed-query retry в agent path. Будущее расширение поиска должно быть LLM-owned refinement, чтобы executed queries и public `searchParams` не расходились.
- Direct low-level `search_reverb()` по-прежнему может расширять query synonyms для обратной совместимости; agent-owned search использует exact mode.

## Честные ограничения

1. **Качество маппинга зависит от LLM-router** — без `GROQ_API_KEY` сервис явно возвращает ошибку, потому что LLM является обязательной зависимостью.
2. **Reverb API может быть недоступен** — при проблемах с сетью поиск возвращает ошибку.
3. **Суммаризация длинных диалогов** — `context_manager` суммаризирует историю при превышении 75% лимита токенов, но качество суммаризации зависит от LLM.
4. **Router context tiers** — router использует compact/retry context tiers, чтобы не выносить provider payload limit в UX.
5. **Маршрутизация model-driven** — edge-cases зависят от качества router prompt и строгой валидации ответа.
