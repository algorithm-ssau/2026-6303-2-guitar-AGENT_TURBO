# TODO — Мергалиев Радмир

**Неделя 7:** 21–27 апреля 2026
**Ветка:** `feature/mergaliev/feedback-params-w7`

> Независимая задача. Все файлы — его собственные, никто другой в week-7 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Backend): endpoint `/api/query/parse` + params_echo

### Что делать

- Создать `backend/agent/params_echo.py`:
  - Функция `parse_query_simple(query: str) -> dict` — **regex-парсер без LLM**:
    - Бюджет: `r"(?:до|up to|<=?)\s*\$?(\d+)"` → `price_max`
    - Диапазон: `r"(\d+)\s*[–-]\s*(\d+)"` → `price_min` и `price_max`
    - Рубли: `r"(\d+)\s*(?:тыс|000)?\s*руб"` → делит на 100
    - Тип: `"strat|стратокастер"` → `"stratocaster"`, аналогично telecaster, les paul, acoustic, bass
    - Бренд: `"fender|gibson|ibanez|prs|yamaha|taylor|martin|squier|epiphone"` → `brand`
    - Теги: `"джаз|jazz|блюз|blues|метал|metal|funk|country"` → `tags: list`
  - Функция `format_params_for_display(params: dict) -> dict` → человекочитаемая форма:
    - `budget`: "≤ $X" / "≥ $X" / "$X–$Y" / None
    - `type`: "Stratocaster" / None
    - `brand`, `tags`
  - Чистые функции без сайд-эффектов, без обращений к LLM
- Добавить endpoint в `backend/search/router.py`:
  - `POST /api/query/parse` принимает `ChatRequest`, возвращает `ParseQueryResponse` (модель в Задаче 3)
  - Тело: `return ParseQueryResponse(**format_params_for_display(parse_query_simple(request.query)))`
  - **НЕ вызывает `interpret_query`**, не пересекается с `/api/chat`

### Файлы

- Создать: `backend/agent/params_echo.py`
- Изменить: `backend/search/router.py`

### Критерий приёмки

- `POST /api/query/parse {"query": "Найди стратокастер до 500$"}` → `{"type": "Stratocaster", "budget": "≤ $500", "brand": null, "tags": []}`
- `POST /api/query/parse {"query": "Gibson LP 800-1500$"}` → `{"type": "Les Paul", "budget": "$800–$1500", "brand": "Gibson"}`
- `POST /api/query/parse {"query": "теле до 80 тыс руб"}` → `{"type": "Telecaster", "budget": "≤ $800"}`
- Работает **БЕЗ GROQ_API_KEY**

### Тест: `tests/test_params_echo.py`

- parse_query_simple на 10 запросах
- format_params_for_display с полным/частичным/пустым набором
- POST /api/query/parse через FastAPI TestClient → 200 + JSON

### Коммит: `feat: add /api/query/parse endpoint with regex parser`

---

## Задача 2 (Frontend): SearchParamsPanel — отображение понятых параметров

### Что делать

- Создать `frontend/src/features/chat/components/SearchParamsPanel.tsx`:
  - Принимает `params: {type?, budget?, brand?, tags?} | null`
  - Если все поля пустые — возвращает `null`
  - Формат: `🎯 Я понял так: Тип: Stratocaster | Бюджет: ≤ $500 | Бренд: Fender | Стиль: blues`
  - Скрывать пустые поля
  - Стилизация через CSS-переменные
- Обновить `frontend/src/features/chat/types.ts`:
  - Добавить `ParsedParams { type?: string; budget?: string; brand?: string; tags?: string[] }`
  - Расширить тип сообщения: `parsedParams?: ParsedParams`
- Обновить `frontend/src/features/chat/api.ts`:
  - Функция `parseQuery(query: string): Promise<ParsedParams>` — `fetch('/api/query/parse', {method: 'POST', body: ...})`
  - Zod-схема `ParsedParamsSchema`
- Обновить `frontend/src/features/chat/hooks/useChat.ts`:
  - В `sendMessage(text)` параллельно с WS вызвать `parseQuery(text).then(params => ...)` — не блокирующе
  - Сохранить `params` в сообщении user (или в state `lastSearchParams`)
  - Если запрос упал — просто без панели (не ломать flow)
- Обновить `frontend/src/features/chat/components/Message.tsx`:
  - Если `message.mode === "search"` и есть `parsedParams` предыдущего user-сообщения — рендерить `<SearchParamsPanel params={parsedParams} />` перед `<ResultsList />`

### Файлы

- Создать: `frontend/src/features/chat/components/SearchParamsPanel.tsx`
- Изменить: `frontend/src/features/chat/types.ts`
- Изменить: `frontend/src/features/chat/api.ts`
- Изменить: `frontend/src/features/chat/hooks/useChat.ts`
- Изменить: `frontend/src/features/chat/components/Message.tsx`

### Критерий приёмки

- После search видна плашка с понятыми параметрами
- Если все поля пусты — панель не показывается
- При падении `/api/query/parse` — чат работает как раньше
- `npm run build` без ошибок

### Тест: `frontend/src/features/chat/__tests__/SearchParamsPanel.test.tsx`

- Рендерит непустые поля
- Не рендерится при пустом params

### Коммит: `feat: add search params panel with parse endpoint`

---

## Задача 3 (Backend): строгая Pydantic валидация + ParseQueryResponse

### Что делать

- Обновить `backend/search/models.py`:
  - `ChatRequest.query`: длина от 2 до 500 символов (Field constraints)
  - `GuitarResult.price`: `Field(ge=0, le=100000)`
  - `GuitarResult.currency`: `Literal["USD", "EUR", "GBP", "RUB", "JPY"]`
  - `GuitarResult.listing_url`: `HttpUrl` вместо `str`
  - `GuitarResult.image_url`: `HttpUrl | None`
  - **Новая модель `ParseQueryResponse`**:
    ```python
    class ParseQueryResponse(BaseModel):
        type: str | None = None
        budget: str | None = None
        brand: str | None = None
        tags: list[str] = []
    ```

### Файлы

- Изменить: `backend/search/models.py`

### Критерий приёмки

- `POST /api/chat {"query": "a"}` → 422
- `POST /api/chat {"query": "x" * 501}` → 422
- `GuitarResult(price=-5)` → ValidationError
- `GuitarResult(currency="XYZ")` → ValidationError
- `GuitarResult(listing_url="not-a-url")` → ValidationError
- `ParseQueryResponse(type="Strat")` → валидный объект

### Тест: `tests/test_models_validation.py`

- 8 позитивных/негативных кейсов по всем полям

### Коммит: `feat: tighten Pydantic validation and add ParseQueryResponse`

---

## Задача 4 (Backend): feedback-модуль — таблица, endpoints, миграция

### Что делать

- Создать `backend/feedback/__init__.py` (пустой)
- Создать `backend/feedback/models.py`:
  - `FeedbackRequest(BaseModel)`: `session_id: int`, `guitar_id: str`, `rating: Literal["up", "down"]`, `query: str | None = None`
  - `FeedbackStats(BaseModel)`: `total: int`, `up: int`, `down: int`, `ratio: float`, `by_guitar: dict[str, dict]`
- Создать `backend/feedback/service.py`:
  - `init_feedback_table()` — SQL в общей `chat.db`:
    ```sql
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        guitar_id TEXT NOT NULL,
        rating TEXT NOT NULL CHECK(rating IN ('up','down')),
        query TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
    ```
    Использует то же соединение что `history/service.py::_get_connection`
  - `save_feedback(req: FeedbackRequest) -> int`
  - `get_feedback_stats() -> FeedbackStats` (агрегация по БД)
- Создать `backend/feedback/router.py`:
  - `router = APIRouter(prefix="/api/feedback", tags=["feedback"])`
  - `POST /` — принимает FeedbackRequest → save_feedback → `{"id": N}`
  - `GET /stats` — `get_feedback_stats()`
  - `init_feedback_table()` вызывается на import модуля (lazy) ИЛИ через autoloader Фокина
- **НЕ трогать `main.py`** — autoloader Фокина из task 2 автоматически подхватит новый роутер

### Файлы

- Создать: `backend/feedback/__init__.py`
- Создать: `backend/feedback/models.py`
- Создать: `backend/feedback/service.py`
- Создать: `backend/feedback/router.py`

### Критерий приёмки

- `POST /api/feedback` с валидным JSON → 200, запись в БД
- `GET /api/feedback/stats` → JSON с агрегацией
- На пустой БД → `{total: 0, up: 0, down: 0, ratio: 0}`
- Невалидный rating ("mid") → 422
- Таблица `feedback` создаётся при старте

### Тест: `tests/test_feedback.py`

- POST /api/feedback с up/down → сохранено
- GET /api/feedback/stats → корректная агрегация
- Невалидный rating → 422
- На пустой БД → нули

### Коммит: `feat: add feedback module with POST and stats endpoints`

---

## Задача 5 (Frontend): кнопки 👍/👎 на карточках гитар

### Что делать

- Обновить `frontend/src/features/chat/components/GuitarCard.tsx`:
  - Добавить две кнопки в карточку: 👍 и 👎
  - Клик → вызов `sendFeedback(guitarId, rating)` из useChat
  - После клика — показать визуальный feedback (рамка зелёная/красная), заблокировать кнопки для этой карточки на 3 сек
  - Хранить `feedbackGiven: Set<string>` в хуке useChat, чтобы не давать повторно нажать
- Обновить `frontend/src/features/chat/api.ts`:
  - Функция `submitFeedback(sessionId, guitarId, rating, query?)` — POST /api/feedback
  - Zod-схема для ответа
- Обновить `frontend/src/features/chat/hooks/useChat.ts`:
  - Экспонировать `sendFeedback(guitarId, rating)` — вызывает `submitFeedback` с текущими sessionId и последним query
  - Обработка ошибок: fallback silent (не ломать UI)

### Файлы

- Изменить: `frontend/src/features/chat/components/GuitarCard.tsx`
- Изменить: `frontend/src/features/chat/api.ts`
- Изменить: `frontend/src/features/chat/hooks/useChat.ts`

### Критерий приёмки

- На каждой карточке гитары видны кнопки 👍/👎
- Клик отправляет POST /api/feedback и показывает визуальный feedback
- Повторный клик на ту же карточку — заблокирован
- Если backend упал — UI не ломается (silent fail)

### Тест: `frontend/src/features/chat/__tests__/GuitarCard.feedback.test.tsx`

- Клик по 👍 вызывает sendFeedback с rating="up"
- Клик по 👎 вызывает sendFeedback с rating="down"
- После клика кнопки disabled

### Коммит: `feat: add thumbs up/down feedback buttons on guitar cards`
