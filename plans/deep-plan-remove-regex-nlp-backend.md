# Deep Plan: убрать regex-распознавание естественного языка из backend

## Постановка проблемы

Сейчас в backend есть два параллельных механизма понимания пользовательского текста:

- LLM-router, который должен быть единственным семантическим слоем.
- Regex-эвристики, которые классифицируют intent, парсят параметры пользователя, распознают follow-up реплики и фразы формата "без разницы / не важно".

Из-за этого есть риск, что один слой покажет или применит одну интерпретацию, а реальный LLM-пайплайн использует другую. Целевая архитектура: LLM отвечает за всё распознавание естественного языка, а backend занимается валидацией, состоянием, поиском, ранжированием, хранением и API-ответами.

## Текущее поведение

- `interpret_query()` сначала вызывает regex-based `detect_mode()`, и только потом идёт LLM-routing.
- `backend/agent/mode_detector.py` классифицирует `search`, `consultation` и `off_topic` через списки паттернов.
- `/api/query/parse` вызывает `backend/agent/params_echo.py`, отдельный regex-only парсер пользовательского текста.
- Frontend сейчас вызывает `/api/query/parse` только для UI-плашки с распознанными параметрами.
- `service.py` всё ещё использует regex-like helpers для follow-up команд и ответов "без разницы / не важно".
- Часть документации и тестов описывает regex detection как реализованное поведение.

## Целевое поведение

- LLM-router является единственным компонентом, который интерпретирует intent и search-параметры из natural language.
- Backend не использует regex для классификации пользовательского intent, извлечения user-facing search params или интерпретации естественно-языковых фраз.
- Если LLM недоступна или вернула невалидный router response, сервис должен явно возвращать ошибку, а не падать в regex fallback.
- `/api/query/parse` удаляется как отдельная regex-ручка.
- Параметры поиска, которые показывает frontend, приходят из основного LLM-пайплайна, а не из второго парсера.
- Router не генерирует полноценные консультационные ответы. Он только классифицирует intent и возвращает структурированные данные. Consultation answer продолжает генерироваться отдельным consultation prompt.
- Off-topic answer остаётся фиксированным backend-ответом. LLM-router только выставляет `intent: "off_topic"`.

## Открытые вопросы

Решено пользователем:

- Удаляем `/api/query/parse` как отдельную regex-ручку.
- Прокидываем реальные LLM-derived `searchParams` через основной ответ.
- Обновляем существующие тесты и документацию, которые завязаны на regex-поведение.
- Добавляем тесты на новый LLM-router/searchParams/history/frontend contract, чтобы не сломать pipeline и edge cases.

## Ограничения и non-goals

- Добавлять тесты, которые проверяют новый contract и предотвращают регрессии. Не добавлять нерелевантные тесты вне scope.
- Не менять Reverb search behavior.
- Не менять ranking logic.
- Не удалять технический parsing/validation, если он не относится к распознаванию natural language.
- Держать scope вокруг удаления backend regex-распознавания в этом контексте плюс необходимые API/docs/test updates.
- Frontend-изменения должны быть минимальными: убрать зависимость от `/api/query/parse` или начать использовать `searchParams` из основного ответа.
- Не удалять safety guardrails только потому, что они используют regex сейчас. Если guardrail не распознаёт natural language, а проверяет технические форматы, ссылки или домены, его нужно оставить или заменить не-regex реализацией.

## Затронутые области

- `backend/agent/service.py`
- `backend/agent/llm_client.py`
- `backend/agent/mode_detector.py`
- `backend/agent/params_echo.py`
- `backend/agent/clarification.py`
- `backend/search/router.py`
- `backend/search/models.py`
- `backend/main.py`
- `frontend/src/features/chat/api.ts`
- `frontend/src/features/chat/hooks/useChat.ts`
- `frontend/src/features/chat/types.ts`
- Документация, где упоминаются `/api/query/parse` или regex-based mode detection.
- Существующие тесты, которые импортируют `mode_detector`, patch-ят `detect_mode` или тестируют `params_echo`.

## UX-состояния

- Search: пользователь получает результаты и optional explanation как раньше. Ответ дополнительно содержит `searchParams`, полученные из LLM-router.
- Consultation: пользователь получает LLM-ответ как раньше.
- Clarification: пользователь получает уточняющий вопрос как раньше.
- Off-topic: LLM-router определяет запрос как off-topic, backend возвращает стандартный отказ наружу как `mode: "consultation"` + фиксированный `answer`. Внешний API-контракт не расширяется новым `mode: "off_topic"`.
- Parsed params panel: если оставляем панель на frontend, она показывает `searchParams` из реального search response, а не отдельный `/api/query/parse` response.
- История: для новых search-сообщений `searchParams` должны сохраняться вместе с результатом, чтобы панель параметров работала после перезагрузки/открытия старой сессии. Для старых записей без `searchParams` панель просто не отображается.

## Data Flow / API / State Mapping

Целевой flow:

```text
user text
-> LLM-router
-> normalized route_plan
-> session state merge/finalization
-> search | clarification | consultation | off_topic
-> API/WS response
```

Canonical router response:

```json
{
  "intent": "search",
  "enough_for_search": true,
  "missing_fields": [],
  "search_params": {
    "search_queries": ["Fender Stratocaster"],
    "price_min": null,
    "price_max": 1200,
    "type": "stratocaster",
    "brand": "Fender",
    "pickups": null,
    "sound": "bright",
    "style": "blues"
  },
  "should_offer_search": false
}
```

Допустимые значения:

- `intent`: `"search"`, `"consultation"`, `"off_topic"`.
- `missing_fields`: только `"budget"` и `"type"`.
- `search_params`: object для `intent: "search"`, включая partial object при `enough_for_search: false`; `null` для `consultation` и `off_topic`.
- `should_offer_search`: meaningful только для `intent: "consultation"`.
- Router не возвращает `consultation_answer` и `off_topic_answer`.

Canonical `search_params`:

```json
{
  "search_queries": ["Fender Stratocaster"],
  "price_min": null,
  "price_max": 1200,
  "type": "stratocaster",
  "brand": "Fender",
  "pickups": "HH",
  "sound": "warm",
  "style": "blues"
}
```

Нормализованные значения:

- `type`: `stratocaster`, `telecaster`, `les_paul`, `sg`, `superstrat`, `acoustic`, `classical`, `bass`, `seven_string`, `any`, `null`.
- `pickups`: `SSS`, `SS`, `HSS`, `HSH`, `HH`, `P90`, `single_coil`, `humbucker`, `active`, `passive`, `null`.
- `sound`: короткий normalized token, например `warm`, `bright`, `heavy`, `soft_attack`, `glassy`, `aggressive`, `clean`, `crunch`, `null`.
- `style`: короткий normalized token, например `jazz`, `blues`, `metal`, `funk`, `country`, `indie`, `punk`, `djent`, `null`.
- `brand`: canonical display name или `null`.
- `price_min`/`price_max`: number в USD или `null`.

Search response должен включать LLM-derived params:

```json
{
  "mode": "search",
  "results": [],
  "explanation": "...",
  "searchParams": {
    "searchQueries": ["Fender Stratocaster"],
    "priceMin": null,
    "priceMax": 1200,
    "type": "stratocaster",
    "brand": "Fender",
    "pickups": null,
    "sound": "bright",
    "style": "blues"
  }
}
```

History response для новых search-записей должен уметь вернуть `searchParams`, если они были сохранены:

```json
{
  "id": 101,
  "sessionId": 12,
  "userQuery": "Подбери Telecaster до 800$",
  "mode": "search",
  "answer": null,
  "results": [],
  "searchParams": {
    "searchQueries": ["Fender Telecaster", "Squier Classic Vibe Telecaster"],
    "priceMax": 800,
    "type": "telecaster"
  },
  "createdAt": "2026-05-02T10:00:00Z"
}
```

Схема хранения history:

- Добавить nullable колонку `search_params TEXT` в `chat_history`.
- Хранить в ней JSON-serialized canonical `search_params`.
- Расширить `save_exchange(..., search_params: Optional[dict] = None)`.
- При чтении `get_session_messages()` парсить `search_params`, если колонка есть и значение не пустое.
- Сделать миграцию backward-compatible: если колонка уже есть, не падать; если старые записи без `search_params`, возвращать `searchParams: null` или не включать поле.
- Не вкладывать `searchParams` в `results`, чтобы не смешивать параметры запроса с карточками найденных инструментов.

Конкретная миграция:

- В `backend/history/service.py::init_db()` после `CREATE TABLE IF NOT EXISTS chat_history (...)` выполнить `ALTER TABLE chat_history ADD COLUMN search_params TEXT`.
- Обработать `sqlite3.OperationalError` для случая duplicate column и не считать это ошибкой.
- Не полагаться на `CREATE TABLE IF NOT EXISTS` для обновления существующей таблицы: он не добавит колонку в уже созданную `chat_history`.

## Error Contract

Так как LLM является обязательной зависимостью сервиса, недоступная или невалидная LLM не должна маскироваться regex fallback.

- REST `/api/chat`: возвращать `503 Service Unavailable`, если LLM-клиент не создан или API недоступен; возвращать `502 Bad Gateway`, если LLM вернула невалидный router JSON/shape.
- WebSocket `/chat`: отправлять `{"type": "error", "status": "Сервис временно недоступен: не удалось обработать запрос через LLM."}` для недоступной LLM и отдельный понятный error status для невалидного router response.
- Логи должны содержать техническую причину, но пользовательский ответ не должен раскрывать ключи, stack trace или внутренний prompt.
- Никакого fallback на `detect_mode`, `params_echo` или другой regex/NLP parser.

## Что НЕ удаляем

В рамках задачи удаляем regex только из распознавания естественного языка пользователя. Не нужно удалять:

- `json.loads` и Pydantic/manual validation структурированных ответов.
- Проверки URL/domain в safety guardrails, если они не пытаются понять intent пользователя.
- Техническую нормализацию API/DB форматов.
- Поиск по заголовкам/брендам/типам в ranking/search utils, если это не используется как user intent classifier.

Если текущий guardrail реализован через regex, но проверяет технический формат, допустимые варианты:

- оставить его, если он не входит в natural language recognition path;
- или заменить на structured parsing без regex, если хотим уменьшить `import re` в backend дополнительно.

## Prompt Design: чем заменяем регулярки

Regex-правила заменяются не общим "пусть LLM сама поймёт", а строгим router prompt с JSON-контрактом, правилами принятия решений и few-shot примерами. Цель prompt: заставить модель вернуть не текстовое рассуждение, а проверяемое структурированное решение.

### Router Prompt: базовая версия

```text
Ты router для сервиса подбора гитар. Твоя задача — определить, что пользователь хочет сделать, и вернуть строго JSON.

Ты НЕ отвечаешь пользователю свободным текстом.
Ты НЕ ищешь товары сам.
Ты НЕ выдумываешь ссылки, магазины, цены или объявления.

Возможные intent:
- "search" — пользователь хочет подобрать инструмент, увидеть варианты, получить ссылки, продолжить ранее начатый подбор или подтвердил готовность смотреть варианты.
- "consultation" — пользователь хочет объяснение, сравнение, совет или теорию без запроса на конкретные объявления.
- "off_topic" — запрос не относится к гитарам, бас-гитарам, музыкальному оборудованию, звуку, выбору инструмента или смежной музыкальной теме.

Правила:
1. Если пользователь просит "найди", "подбери", "покажи варианты", "дай ссылки", "что купить", "хочу купить", intent = "search".
2. Если пользователь указывает бюджет, конкретный тип/модель/бренд/жанр/звук и ожидает подбор, intent = "search".
3. Если пользователь задаёт вопрос "что такое", "чем отличается", "как влияет", "что лучше" без просьбы показать варианты, intent = "consultation".
4. Если запрос смешанный: пользователь просит и объяснить, и подобрать, intent = "search"; короткое объяснение будет добавлено другим слоем.
5. Если пользователь отвечает "да", "давай", "покажи", "ссылки", "подбери", "как выше", используй context/state. Если state уже содержит достаточно данных для подбора, intent = "search".
6. Если пользователь говорит "любой", "не важно", "без разницы", "что угодно" про тип или бюджет, это не missing field. Для типа верни type = "any".
7. Если данных для поиска недостаточно, intent всё равно "search", но enough_for_search = false и missing_fields содержит только реально недостающие поля.
8. Допустимые missing_fields: "budget", "type".
9. Если intent = "consultation", search_params должен быть null.
10. Если intent = "off_topic", search_params должен быть null, should_offer_search = false.
11. Не генерируй консультационные ответы. Для consultation только классифицируй intent и выставляй should_offer_search.

Верни строго JSON:

Форма для готового search:
{
  "intent": "search",
  "enough_for_search": true,
  "missing_fields": [],
  "search_params": {
    "search_queries": ["Fender Stratocaster"],
    "price_min": null,
    "price_max": 1200,
    "type": "stratocaster",
    "brand": "Fender",
    "pickups": "SSS",
    "sound": "bright",
    "style": null
  },
  "should_offer_search": false
}

Форма для search, которому нужно уточнение:
{
  "intent": "search",
  "enough_for_search": false,
  "missing_fields": ["budget"],
  "search_params": {
    "search_queries": ["Fender Telecaster", "Squier Classic Vibe Telecaster"],
    "price_min": null,
    "price_max": null,
    "type": "telecaster",
    "brand": null,
    "pickups": null,
    "sound": null,
    "style": null
  },
  "should_offer_search": false
}

Форма для consultation:
{
  "intent": "consultation",
  "enough_for_search": false,
  "missing_fields": [],
  "search_params": null,
  "should_offer_search": true
}

Форма для off_topic:
{
  "intent": "off_topic",
  "enough_for_search": false,
  "missing_fields": [],
  "search_params": null,
  "should_offer_search": false
}
```

### Search Params Prompt: извлечение параметров

```text
Когда intent = "search", заполни search_params так, чтобы backend мог выполнить поиск на Reverb.

Правила search_params:
1. search_queries — конкретные поисковые запросы для Reverb. Предпочитай бренд + модель/серия, если это можно вывести из запроса.
2. price_min и price_max — числа в USD или null.
3. Если бюджет указан в рублях, переведи примерно по курсу 100 RUB = 1 USD.
4. type — нормализованный тип/форма инструмента из allowed values: stratocaster, telecaster, les_paul, sg, superstrat, acoustic, classical, bass, seven_string, any или null. Не используй broad value "electric": если пользователь сказал только "электрогитара", заполни конкретные `search_queries`, а `type` оставь null, если форму нельзя определить.
5. brand — бренд, если пользователь его указал или он явно следует из модели.
6. pickups — нормализованное значение из allowed values: SSS, SS, HSS, HSH, HH, P90, single_coil, humbucker, active, passive или null.
7. sound — краткая нормализованная характеристика: warm, bright, heavy, soft_attack, glassy, aggressive и т.п.
8. style — jazz, blues, metal, funk, country, indie, punk, djent и т.п.
9. Не добавляй параметры, если они не следуют из запроса или context/state.
10. Если пользователь указал противоречивую комбинацию, не выдумывай невозможную модель. Верни search_params по наиболее надёжной части запроса и при необходимости enough_for_search = false.
```

### Few-Shot примеры для router

```text
Пользователь: "Подбери электрогитару до 1200$ для блюза, чтобы звук был теплый."
Ответ:
{
  "intent": "search",
  "enough_for_search": true,
  "missing_fields": [],
  "search_params": {
    "search_queries": ["Epiphone Les Paul", "Gibson Les Paul Studio", "PRS SE Custom 24"],
    "price_min": null,
    "price_max": 1200,
    "type": null,
    "brand": null,
    "pickups": "HH",
    "sound": "warm",
    "style": "blues"
  },
  "should_offer_search": false
}
```

```text
Пользователь: "Чем отличаются P90 от хамбакеров?"
Ответ:
{
  "intent": "consultation",
  "enough_for_search": false,
  "missing_fields": [],
  "search_params": null,
  "should_offer_search": true
}
```

```text
Context/state: {"type": "telecaster", "price_max": 800, "search_queries": ["Fender Telecaster", "Squier Classic Vibe Telecaster"], "ready_for_search": true}
Пользователь: "давай покажи ссылки"
Ответ:
{
  "intent": "search",
  "enough_for_search": true,
  "missing_fields": [],
  "search_params": {
    "search_queries": ["Fender Telecaster", "Squier Classic Vibe Telecaster"],
    "price_min": null,
    "price_max": 800,
    "type": "telecaster",
    "brand": null,
    "pickups": null,
    "sound": null,
    "style": null
  },
  "should_offer_search": false
}
```

```text
Пользователь: "тип не важен, бюджет до 500, хочу что-то для фанка"
Ответ:
{
  "intent": "search",
  "enough_for_search": true,
  "missing_fields": [],
  "search_params": {
    "search_queries": ["funk electric guitar", "Squier Stratocaster", "Yamaha Pacifica"],
    "price_min": null,
    "price_max": 500,
    "type": "any",
    "brand": null,
    "pickups": "single_coil",
    "sound": "bright",
    "style": "funk"
  },
  "should_offer_search": false
}
```

```text
Пользователь: "напиши сортировку пузырьком на python"
Ответ:
{
  "intent": "off_topic",
  "enough_for_search": false,
  "missing_fields": [],
  "search_params": null,
  "should_offer_search": false
}
```

```text
Пользователь: "Сначала коротко объясни разницу Telecaster и Stratocaster, а потом подбери Telecaster до 900$"
Ответ:
{
  "intent": "search",
  "enough_for_search": true,
  "missing_fields": [],
  "search_params": {
    "search_queries": ["Fender Telecaster", "Squier Classic Vibe Telecaster", "G&L ASAT"],
    "price_min": null,
    "price_max": 900,
    "type": "telecaster",
    "brand": null,
    "pickups": "single_coil",
    "sound": "bright",
    "style": null
  },
  "should_offer_search": false
}
```

### Quality Bar для prompt

- Prompt должен быть детерминированным: `temperature=0.0`.
- Ответ router должен проходить строгую нормализацию и Pydantic/ручную валидацию.
- Любой невалидный JSON/shape считается ошибкой LLM-router, а не поводом запускать regex fallback.
- Few-shot примеры должны покрывать минимум: прямой поиск, консультацию, off-topic, follow-up по context/state, "любой/не важно", смешанный запрос "объясни и подбери".
- Router prompt должен запрещать модели генерировать реальные ссылки, товарные карточки и полноценные consultation-тексты.
- Router prompt не должен генерировать полноценные consultation/off-topic тексты; он только маршрутизирует.

## Судьба второго LLM-парсера и `param_extractor.py`

После перехода на LLM-router в основном pipeline должен остаться один LLM-вызов для маршрутизации и извлечения search params:

- `LLMClient.classify_and_plan_query()` становится единственным источником `intent`, `missing_fields`, `enough_for_search` и `search_params`.
- `LLMClient.extract_search_params()` больше не вызывается из search path.
- `_handle_search()` принимает только `initial_params` из router/session state. Если `initial_params` отсутствует, это ошибка orchestration, а не повод делать второй LLM-call.
- Старый `build_search_prompt()` и extraction helpers из `param_extractor.py` становятся не нужны основному pipeline.
- Если после удаления references файл `param_extractor.py` больше нигде не нужен, удалить его целиком вместе с устаревшими тестами.
- Если часть функций ещё нужна для compatibility tests/docs, оставить только функции без regex и без natural language fallback, но не использовать их в production pipeline.

## Frontend Mapping для `searchParams`

Текущий frontend `SearchParamsPanel` ожидает старую форму `ParsedParams`: `type`, `budget`, `brand`, `tags`. Новый backend contract отдаёт реальные search params: `searchQueries`, `priceMin`, `priceMax`, `type`, `brand`, `pickups`, `sound`, `style`.

Решение для реализации:

- Заменить `ParsedParams` на новый тип `SearchParams`.
- Обновить `SearchParamsPanel`, чтобы она показывала:
  - `type`;
  - formatted budget из `priceMin/priceMax`;
  - `brand`;
  - `pickups`;
  - `sound`;
  - `style`;
  - при необходимости первые 1-3 `searchQueries`.
- Не делать отдельный frontend-side парсинг пользовательского текста.
- Для history messages брать `searchParams` из history response, если поле есть.
- Не сохранять старую модель `ParsedParams`/`tags` как смысловой контракт. Если UI нужен компактный, форматировать display labels из `SearchParams`, но не возвращаться к отдельному parse endpoint и не делать frontend-side NLP.

## Шаги реализации

1. Создать feature branch перед изменениями в коде.
2. Обновить `LLMClient._build_router_prompt()`, чтобы LLM-router отвечал за:
   - intent decisions: `search`, `consultation`, `off_topic`;
   - интерпретацию "не важно / без разницы / любой";
   - follow-up команды вроде "давай", "покажи", "я писал выше";
   - `missing_fields` и `enough_for_search`;
   - routing constraints для consultation.
3. Обновить `service.py`:
   - убрать `detect_mode()` pre-check из `interpret_query()`;
   - убрать regex fallback route plan;
   - считать missing/invalid LLM route plan ошибкой сервиса;
   - обрабатывать `off_topic` из route plan;
   - убрать regex-based helpers для no-preference/follow-up;
   - catalog/url safety guardrails не удалять без замены: оставить как техническую защиту или переписать на не-regex validation;
   - возвращать `search_params` вместе с search results.
   - убрать production-вызов `LLMClient.extract_search_params()` из search path.
4. Обновить clarification/state logic:
   - оставить deterministic state merge и field validation;
   - не выводить natural language meaning через regex;
   - полагаться на LLM-provided `missing_fields`, `type: "any"` и params.
5. Удалить `/api/query/parse`:
   - убрать route из `backend/search/router.py`;
   - убрать `ParseQueryResponse`, если больше не нужен;
   - удалить `backend/agent/params_echo.py`.
6. Убрать regex mode detector:
   - удалить или полностью отвязать `backend/agent/mode_detector.py`;
   - обновить imports и references.
7. Прокинуть `searchParams`:
   - REST `/api/chat` должен включать `searchParams` для search responses;
   - WebSocket search result должен включать `searchParams`;
   - history persistence должен сохранять `searchParams` для новых search-записей; старые записи без params отображаются без панели.
8. Обновить response schemas и типы:
   - backend Pydantic models (`ChatResponse`, `HistoryItem`) должны поддерживать optional `search_params` / `searchParams`;
   - WebSocket payload должен отдавать `searchParams` в camelCase;
   - frontend Zod schemas/types должны принимать `searchParams` в chat result и history response;
   - off-topic наружу остаётся `mode: "consultation"`, поэтому внешние enum для mode не расширяются.
9. Минимально выровнять frontend:
   - удалить `parseQuery()` API call;
   - перестать вызывать `/api/query/parse` в `useChat`;
   - заменить `ParsedParams` на `SearchParams`;
   - использовать backend-provided `searchParams` для `SearchParamsPanel`;
   - панель может быть пустой только до прихода search response или для старых history entries без `searchParams`.
10. Обновить docs:
   - убрать `/api/query/parse` из API docs/status tables;
   - заменить wording про regex-mode на wording про LLM-router;
   - обновить thesis draft, если там написано, что классификация делается регулярками.
11. Обновить существующие тесты:
   - удалить или переписать тесты, которые таргетят `mode_detector` и `params_echo`;
   - обновить тесты, которые patch-ят `backend.agent.service.detect_mode`;
   - удалить или переписать тесты вокруг `extract_search_params()` / `param_extractor.py`, если эти функции выходят из production pipeline;
   - обновить API contract expectations под удаление `/api/query/parse` и добавление `searchParams`.
12. Добавить новые регрессионные тесты:
   - router normalization: валидный mocked LLM router response для `search`, `consultation`, `off_topic`, partial search с `missing_fields`;
   - service orchestration: search path использует `search_params` из router/state и не вызывает `LLMClient.extract_search_params()`;
   - error contract: missing LLM / invalid router shape возвращают ожидаемые REST/WS ошибки без regex fallback;
   - history: новые search entries сохраняют и возвращают `searchParams`, старые entries без `search_params` читаются без ошибок;
   - API contract: `/api/query/parse` удалён, `/api/chat` search response содержит optional `searchParams`;
   - frontend: `SearchParamsPanel` отображает новый `SearchParams`, `useChat` больше не вызывает `parseQuery()`.
   - ориентиры по размещению: backend router/service tests — рядом с `tests/test_router.py`, `tests/test_agent.py` или отдельным `tests/test_llm_router.py`; history checks — рядом с `tests/test_history_e2e.py`; API contract — рядом с `tests/test_api_contract.py`; frontend tests — рядом с существующими `frontend/src/features/chat/__tests__/SearchParamsPanel.test.tsx` и `useChat` tests.

## Шаги проверки

- Проверить, что backend больше не импортирует `re` для natural language recognition paths. Если `re` остаётся где-либо в backend, каждое оставшееся место должно быть явно классифицировано как technical guardrail/parsing, не NLP.
- Проверить, что backend-код больше не импортирует `mode_detector` или `params_echo`.
- Проверить, что references на `/api/query/parse` удалены из backend/docs/frontend или явно отсутствуют.
- Проверить, что router contract в prompt, нормализации, REST/WS response и history response использует один и тот же shape.
- Проверить, что router не генерирует consultation/off-topic answer, а только intent/metadata.
- Проверить, что search path не вызывает `LLMClient.extract_search_params()` и не делает второй LLM-call для параметров.
- Проверить, что `searchParams` сохраняются в новых history entries и старые entries без поля читаются без ошибок.
- Запустить новые и обновлённые regression tests для router/service/history/API/frontend mapping.
- Запустить backend import/startup smoke.
- Запустить минимальные релевантные backend checks, которые есть в репозитории.
- Вручную проверить по коду сценарии search/consultation/clarification/off-topic и убедиться, что ownership у LLM-router.

## Риски и edge cases

- Качество LLM-router prompt становится критичным, потому что regex fallback удаляется.
- Существующие тесты потребуют обновления, потому что многие patch-ят `detect_mode`; новые tests должны закрепить новый LLM-router contract.
- Удаление `/api/query/parse` меняет timing frontend: parsed params появятся только после реального ответа, а не сразу после отправки сообщения.
- Для старых history entries без сохранённого `searchParams` панель параметров не будет отображаться даже после schema migration: migration добавляет nullable колонку, но не делает backfill исторических параметров. Это ожидаемый fallback.
- `off_topic` становится model-driven, а не deterministic.

## Рекомендованное решение

Двигаться с удалением regex-based распознавания естественного языка из backend и удалением `/api/query/parse`. Добавить LLM-derived `searchParams` в основной search response, чтобы frontend показывал реальные параметры, которые использовал агент.
