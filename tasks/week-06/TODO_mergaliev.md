# TODO — Мергалиев Радмир

**Неделя 6:** 14–20 апреля 2026
**Ветка:** `feature/mergaliev/params-echo`

> Независимая задача. Все файлы — его собственные, никто другой в week-6 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Backend): REST endpoint `/api/query/parse` для извлечения параметров без пайплайна

### Что делать

- Создать `backend/agent/params_echo.py`:
  - Функция `parse_query_simple(query: str) -> dict` — **regex-парсер без LLM**:
    - Извлекает бюджет: `r"(?:до|up to|<=?)\s*\$?(\d+)"` → `price_max`
    - Извлекает диапазон: `r"(\d+)\s*[–-]\s*(\d+)"` → `price_min` и `price_max`
    - Распознаёт рубли: `r"(\d+)\s*(?:тыс|000)?\s*руб"` → делит на 100, даёт `price_max`
    - Распознаёт тип: `"strat|стратокастер"` → `"stratocaster"`, `"tele|телекастер"` → `"telecaster"`, `"lp|лес пол"` → `"les paul"`, `"акустик"` → `"acoustic"`, `"бас"` → `"bass"`, и т.п.
    - Распознаёт бренд: `"fender|gibson|ibanez|prs|yamaha|taylor|martin|squier|epiphone"` → `brand`
    - Распознаёт теги стиля: `"джаз|jazz|блюз|blues|метал|metal|funk|country"` → `tags` список
  - Функция `format_params_for_display(params: dict) -> dict`:
    - Принимает результат `parse_query_simple` (или совместимый словарь)
    - Возвращает человекочитаемую форму:
      ```python
      {
          "type": "Stratocaster" or None,
          "budget": "≤ $1000" or "$500–$1000" or "≥ $500" or None,
          "brand": "Fender" or None,
          "tags": ["blues"] or [],
      }
      ```
  - **Никаких сайд-эффектов**, никаких обращений к LLM, никаких импортов из service.py/main.py
- Добавить endpoint в `backend/search/router.py`:
  - `POST /api/query/parse`
  - Принимает `ChatRequest` (уже существует) — поле `query`
  - Возвращает `ParseQueryResponse` (новая модель в models.py — см. Задачу 3)
  - Тело: `return ParseQueryResponse(**format_params_for_display(parse_query_simple(request.query)))`
  - **НЕ вызывает `interpret_query`**, не пересекается с существующим `POST /api/chat`
- **НЕ трогать**: `backend/main.py`, `backend/agent/service.py`, `backend/agent/llm_client.py`

### Файлы

- Создать: `backend/agent/params_echo.py`
- Изменить: `backend/search/router.py` (добавить новый endpoint — никто другой его не трогает в week-6)

### Критерий приёмки

- `POST /api/query/parse` с `{"query": "Найди стратокастер до 500$"}` → `{"type": "Stratocaster", "budget": "≤ $500", "brand": null, "tags": []}`
- `POST /api/query/parse` с `{"query": "Gibson Les Paul 800-1500$"}` → `{"type": "Les Paul", "budget": "$800–$1500", "brand": "Gibson", ...}`
- `POST /api/query/parse` с `{"query": "теле до 80 тыс руб"}` → `{"type": "Telecaster", "budget": "≤ $800", ...}` (рубли / 100)
- `POST /api/query/parse` с `{"query": "что такое P90"}` → `{"type": null, "budget": null, "brand": null, "tags": []}`
- **Работает БЕЗ GROQ_API_KEY** (это regex, не LLM)

### Тест: `tests/test_params_echo.py`

- parse_query_simple на 10 различных запросах (бюджет в $/руб/диапазоне, типы, бренды)
- format_params_for_display с разными наборами (полный/частичный/пустой)
- POST /api/query/parse через FastAPI TestClient → 200 + корректный JSON

### Коммит: `feat: add /api/query/parse endpoint with regex parser`

---

## Задача 2 (Frontend): панель отображения понятых параметров

### Что делать

- Создать `frontend/src/features/chat/components/SearchParamsPanel.tsx`:
  - Принимает проп `params: { type?: string; budget?: string; brand?: string; tags?: string[] } | null`
  - Если все поля пусты/null — возвращает `null` (не рендерится)
  - Формат: горизонтальная плашка:
    ```
    🎯 Я понял так: Тип: Stratocaster | Бюджет: ≤ $500 | Бренд: Fender | Стиль: blues
    ```
  - Скрывать пустые поля (если `type` пусто — не показывать его секцию)
  - Стилизация через CSS-переменные (`--bg-secondary`, `--accent` для иконки) — они вводятся Сальниковым в week-5
- Обновить `frontend/src/features/chat/api.ts` (если не существует — создать):
  - Функция `parseQuery(query: string): Promise<ParsedParams>` — `fetch('/api/query/parse', { method: 'POST', body: JSON.stringify({query}) })`
  - Zod-схема `ParsedParamsSchema`
- Обновить `frontend/src/features/chat/hooks/useChat.ts`:
  - В `sendMessage(text)`:
    - Параллельно с WS отправкой вызвать `parseQuery(text)` (не `await` блокирующе — через `.then()`)
    - Когда ответ придёт — сохранить в `lastSearchParams` state хука
  - Добавить в return хука: `lastSearchParams`
- Обновить `frontend/src/features/chat/types.ts`:
  - Добавить тип `ParsedParams { type?: string; budget?: string; brand?: string; tags?: string[] }`
- Обновить `frontend/src/features/chat/components/Message.tsx`:
  - Если сообщение — первое agent-сообщение после пользователя И `message.mode === "search"` — рендерить `<SearchParamsPanel params={lastSearchParams} />` через пропс
  - Или проще: `useChat` прокидывает `lastSearchParams` в `Chat.tsx`, Chat.tsx передаёт в `MessageList`, тот в `Message.tsx`. Простое решение: `lastSearchParams` хранится в хуке и читается любым компонентом, который получает его через пропс

**Более простой вариант**, без прокидывания по дереву:
- `SearchParamsPanel` можно рендерить прямо в `Message.tsx`: каждое user-сообщение имеет поле `parsedParams`, которое заполняется в `useChat.ts` перед добавлением в список. Тогда `Message.tsx` для user-сообщений не показывает панель, а следующее agent-сообщение в search-режиме показывает.
- Реализация: в `sendMessage(text)` — `parseQuery(text).then(params => setMessages(prev => prev.map(m => m.role === 'user' && m.content === text ? {...m, parsedParams: params} : m)))`. Затем в `Message.tsx` для agent-сообщения рендерим панель, беря `parsedParams` из предыдущего user-сообщения через пропс `previousUserParams`.

**Самый простой вариант:** в `useChat.ts` хранить `parsedParams` на уровне сообщения user, показывать панель над search-карточками взяв params из предыдущего user-сообщения в массиве.

### Файлы

- Создать: `frontend/src/features/chat/components/SearchParamsPanel.tsx`
- Изменить: `frontend/src/features/chat/types.ts` (добавить тип ParsedParams)
- Изменить: `frontend/src/features/chat/hooks/useChat.ts` (вызов parseQuery и хранение)
- Изменить: `frontend/src/features/chat/components/Message.tsx` (рендер панели)
- Возможно изменить: `frontend/src/features/chat/api.ts` (функция parseQuery + Zod-схема)

### Критерий приёмки

- После отправки search-запроса появляется плашка с понятыми параметрами
- Если все поля пустые (консультация) — панель не показывается
- Работает параллельно с WS (не блокирует основной flow)
- Если `/api/query/parse` упал — WS всё равно работает, просто без панели
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/SearchParamsPanel.test.tsx`

- Рендерит все непустые поля
- Не рендерится при пустом params
- Не рендерится при params={null}

### Коммит: `feat: add parsed params panel with /api/query/parse`

---

## Задача 3 (Backend): строгая валидация Pydantic-моделей + ParseQueryResponse

### Что делать

- Обновить `backend/search/models.py`:
  - `ChatRequest.query`: длина от 2 до 500 символов
  - `GuitarResult.price`: `Field(ge=0, le=100000)`
  - `GuitarResult.currency`: `Literal["USD", "EUR", "GBP", "RUB", "JPY"]`
  - `GuitarResult.listing_url`: `HttpUrl`
  - `GuitarResult.image_url`: `HttpUrl | None`
  - **Новая модель `ParseQueryResponse`** для endpoint из Задачи 1:
    ```python
    class ParseQueryResponse(BaseModel):
        type: str | None = None
        budget: str | None = None
        brand: str | None = None
        tags: list[str] = []
    ```
- При ошибке парсинга — 422 от FastAPI автоматически

### Файлы

- Изменить: `backend/search/models.py`

### Критерий приёмки

- `POST /api/chat` с `{"query": "a"}` → 422
- `POST /api/chat` с `{"query": "x" * 501}` → 422
- `GuitarResult(price=-5)` → ValidationError
- `GuitarResult(currency="XYZ")` → ValidationError
- `GuitarResult(listing_url="not-a-url")` → ValidationError
- `ParseQueryResponse(type="Strat", budget="≤ $500")` → валидный объект

### Тест: `tests/test_models_validation.py`

- 6 позитивных/негативных кейсов по всем полям
- 2 кейса на ParseQueryResponse

### Коммит: `feat: tighten Pydantic validation and add ParseQueryResponse`
