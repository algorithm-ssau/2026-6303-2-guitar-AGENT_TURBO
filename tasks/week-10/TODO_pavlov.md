# TODO — Павлов Виктор

**Неделя 10:** 12–18 мая 2026  
**Ветка:** `feature/pavlov/agent-refactor-w10`

> Строго refactor-only.  
> Не менять поведение агента, промпты, тексты ответов, API-контракт, search/ranking/frontend.  
> Цель недели — разгрести `backend/agent/service.py` через нормальную группировку кода, без функциональных изменений.

---

## Общие правила week-10

- Только `refactor:` коммиты.
- Ровно 3 шага = ровно 3 осмысленных коммита.
- Новые тесты не писать.
- Не менять существующие тесты, кроме механического обновления import path после выноса helper-функций.
- Не менять публичные сигнатуры функций, которые вызываются из других модулей.
- Не менять тексты prompt-файлов и fallback-ответов.
- Новые helper-файлы разрешены, но каждый файл должен иметь одну понятную группу ответственности.
- Запрещено создавать новую свалку вида `utils.py`, `helpers.py`, `common.py`.
- Если при рефакторинге нужен новый файл, назвать его по смыслу: `route_plan.py`, `state.py`, `guardrails.py`.

---

## Задача: сгруппировать agent service без изменения поведения

Сейчас `backend/agent/service.py` слишком большой и смешивает несколько разных зон:

- загрузка prompt-ов;
- router/classification flow;
- валидация route plan;
- search state mapping;
- guardrails/sanitizers;
- LLM recovery/fallback.

Нужно сделать код проще для чтения, но оставить поведение прежним.

---

## Шаг 1 — вынести route plan validation

### Что делать

Вынести в отдельную смысловую группу функции, которые отвечают за нормализацию и проверку router/route plan.

Разрешённый вариант:

- создать `backend/agent/route_plan.py`;
- перенести туда только route-plan функции;
- в `backend/agent/service.py` оставить orchestration и импорты.

Кандидаты на перенос:

- `_candidate_intent`;
- `_normalize_route_plan`;
- `_validate_route_plan`;
- `_validate_route_plan_for_state`;
- `_validate_ready_search_params`;
- `_normalize_search_params`;
- `_normalize_type_value`;
- `_normalize_pickups_value`;
- `_number_or_none`;
- `_string_or_none`.

Нельзя:

- менять список допустимых intent;
- менять правила ready/incomplete search;
- менять тексты ошибок validation;
- менять структуру route plan.

### Файлы

- Изменить: `backend/agent/service.py`
- Создать при необходимости: `backend/agent/route_plan.py`

### Критерий приёмки

- route-plan код собран в одном месте;
- `service.py` стал короче;
- imports не создают циклических зависимостей;
- поведение router validation не изменилось.

### Проверка

```bash
pytest tests/test_agent.py tests/test_llm_router_contract.py tests/test_llm_scenarios.py -v
```

### Коммит

`refactor: extract agent route plan helpers`

---

## Шаг 2 — вынести search state mapping

### Что делать

Сгруппировать функции, которые отвечают за состояние поиска, clarification state и преобразование state в search params.

Разрешённый вариант:

- создать `backend/agent/state.py`;
- перенести туда только state/search-param mapping;
- оставить в `service.py` высокоуровневый flow.

Кандидаты на перенос:

- `_apply_ready_search_snapshot`;
- `_apply_incomplete_search_patch`;
- `_unique_preserving_order`;
- `_beginner_default_price_max`;
- `_finalize_search_state`;
- `_prepare_clarification_state`;
- `_state_to_search_params`;
- `_state_to_user_search_params`;
- `_search_params_to_user_search_params`;
- `_empty_search_params`;
- `_safe_router_params_for_log`;
- `_clarification_target_from_missing_fields`;
- `_question_from_missing_fields`.

Нельзя:

- менять поля state;
- менять camelCase/snake_case mapping;
- менять default budget;
- менять условия clarification.

### Файлы

- Изменить: `backend/agent/service.py`
- Создать при необходимости: `backend/agent/state.py`

### Критерий приёмки

- все state/search mapping функции сгруппированы;
- нет дублирования conversion logic;
- поведение поиска и уточнений не изменилось.

### Проверка

```bash
pytest tests/test_context_manager.py tests/test_clarification.py tests/test_pipeline.py -v
```

### Коммит

`refactor: group agent search state helpers`

---

## Шаг 3 — вынести guardrails и sanitizers

### Что делать

Сгруппировать функции, которые чистят ответы агента и защищают от лишних ссылок/каталожного контента.

Разрешённый вариант:

- создать `backend/agent/guardrails.py`;
- перенести туда только guardrail/sanitizer helpers;
- оставить в `service.py` вызовы `_handle_*`.

Кандидаты на перенос:

- `_sanitize_consultation_answer`;
- `_sanitize_consultation_answer_result`;
- `_consultation_guardrail_recovery`;
- `_extract_think_block`;
- `_compact_llm_visible_text`;
- `_sanitize_off_topic_answer`;
- `_sanitize_clarification_question`;
- `_sanitize_conversation_answer`;
- `_recover_conversation_answer`;
- `_contains_external_link_or_shop`;
- `_looks_like_catalog_content`;
- `_extract_branded_model_mentions`;
- `_normalize_model_text`;
- `_is_allowed_model_mention`;
- `_maybe_append_search_offer`.

Нельзя:

- менять тексты sanitization fallback;
- менять правила удаления ссылок;
- менять allowed model mention logic;
- менять consultation/off-topic/conversation ответы.

### Файлы

- Изменить: `backend/agent/service.py`
- Создать при необходимости: `backend/agent/guardrails.py`

### Критерий приёмки

- guardrails лежат отдельно от orchestration;
- `service.py` читабельно показывает flow;
- пользовательские ответы не меняются.

### Проверка

```bash
pytest tests/test_explanation.py tests/test_off_topic.py tests/test_graceful_degradation.py -v
```

### Коммит

`refactor: isolate agent guardrail helpers`
