# TODO — Фокин Евгений

**Неделя 7:** 21–27 апреля 2026
**Ветка:** `feature/fokin/metrics-toast-w7`

> Независимая задача. Все файлы — его собственные, никто другой в week-7 их не трогает.
> Можно мержить в любом порядке с другими участниками.
>
> Фокин — единственный владелец `backend/main.py` и `frontend/src/main.tsx`, `App.tsx` на week-7.

---

## Задача 1 (Backend): analytics модуль — pipeline_metrics

### Что делать

- Создать `backend/analytics/__init__.py` (пустой)
- Создать `backend/analytics/pipeline_metrics.py`:
  - Функция `init_metrics_table() -> None`:
    ```sql
    CREATE TABLE IF NOT EXISTS pipeline_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        mode TEXT NOT NULL,
        elapsed_ms INTEGER NOT NULL,
        results_count INTEGER,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
    ```
    Использует соединение из `backend/history/service.py::_get_connection`
  - `record_exchange(session_id, mode, elapsed_ms, results_count) -> None`
  - `compute_kpi() -> dict`:
    ```python
    {
        "total_sessions": int,
        "total_exchanges": int,
        "avg_elapsed_ms": float,
        "p95_elapsed_ms": float,
        "avg_messages_to_first_search": float,
        "clarification_rate": float,   # % сессий где был mode=clarification
        "repeat_session_rate": float,  # % сессий с ≥2 search-запросами
        "kpi_met": bool,               # avg_messages_to_first_search ≤ 3 (PRD §11)
    }
    ```
- Обновить `backend/history/service.py::init_db`:
  - Добавить 1 строку: `from backend.analytics.pipeline_metrics import init_metrics_table; init_metrics_table()`
- Обновить `backend/main.py`:
  - Импорт `from backend.analytics.pipeline_metrics import record_exchange; import time`
  - Замер времени: `t0 = time.perf_counter()` перед `interpret_query`, `elapsed_ms = int((time.perf_counter() - t0) * 1000)` после
  - После отправки WS-ответа: `try: record_exchange(session_id, result_data["mode"], elapsed_ms, len(result_data.get("results", [])) if result_data["mode"] == "search" else None); except Exception as e: logger.error(...)`

### Файлы

- Создать: `backend/analytics/__init__.py`
- Создать: `backend/analytics/pipeline_metrics.py`
- Изменить: `backend/history/service.py` (1 строка)
- Изменить: `backend/main.py` (замер + запись + импорты)

### Критерий приёмки

- После отправки сообщения в чат в таблице `pipeline_metrics` появляется запись
- `init_db` создаёт обе таблицы (chat_history + pipeline_metrics)
- Consultation-ответы также записываются (`results_count=None`)
- Если `record_exchange` упал — WS-ответ всё равно отправлен клиенту

### Тест: покрывается Задачей 5

### Коммит: `feat: add pipeline metrics module with KPI calculation`

---

## Задача 2 (Backend): KPI endpoint + autoloader роутеров

### Что делать

**Часть A — KPI endpoint:**

- Создать `backend/analytics/router.py`:
  - `router = APIRouter(prefix="/api/metrics", tags=["metrics"])`
  - `GET /health` → вызывает `compute_kpi()` и возвращает как JSON (camelCase через `snake_to_camel`)
  - Модель `KPIResponse(BaseModel)`:
    ```python
    totalSessions: int
    totalExchanges: int
    avgElapsedMs: float
    p95ElapsedMs: float
    avgMessagesToFirstSearch: float
    clarificationRate: float
    repeatSessionRate: float
    kpiMet: bool
    ```

**Часть B — autoloader роутеров в main.py:**

- Обновить `backend/main.py`:
  - Заменить жёсткие `app.include_router(chat_router)`, `app.include_router(history_router)` на цикл:
    ```python
    import importlib
    ROUTER_MODULES = ["search", "history", "analytics", "feedback", "health"]
    for name in ROUTER_MODULES:
        try:
            mod = importlib.import_module(f"backend.{name}.router")
            if hasattr(mod, "router"):
                app.include_router(mod.router)
                logger.info(f"Loaded router: {name}")
        except ImportError as e:
            logger.warning(f"Router {name} not available: {e}")
    ```
  - Это позволяет Мергалиеву (feedback), Сидорову (health) создавать новые роутеры без трогания main.py — autoloader их подхватит

### Файлы

- Создать: `backend/analytics/router.py`
- Изменить: `backend/main.py` (autoloader + удаление хардкода include_router)

### Критерий приёмки

- `GET /api/metrics/health` → 200 + JSON со всеми полями
- На пустой БД → нули + `kpiMet: true`
- Autoloader подхватывает search и history (они уже существуют)
- Если feedback/health ещё не созданы → autoloader их пропускает без ошибок

### Тест: покрывается Задачей 5

### Коммит: `feat: add KPI endpoint and router autoloader in main.py`

---

## Задача 3 (Frontend): Toast + ConfirmDialog + useToast (shared UI)

### Что делать

- Создать `frontend/src/shared/components/Toast.tsx`:
  - Компонент тоста: текст + автоскрытие через 3 сек
  - Типы: `success` (зелёный), `error` (красный), `info` (синий)
  - Позиция: нижний правый угол, z-index высокий
  - Стилизация через CSS-переменные из `variables.css`
- Создать `frontend/src/shared/components/ConfirmDialog.tsx`:
  - Модальное окно с overlay
  - Принимает `title`, `message`, `onConfirm`, `onCancel`, `isOpen` через пропсы
  - Кнопки "Да" (accent) / "Отмена"
- Создать `frontend/src/shared/hooks/useToast.ts`:
  - React Context `ToastContext` + провайдер `ToastProvider`
  - Хук `useToast()` → `{ showToast(text, type), hideToast() }`
  - Компонент `<ToastContainer />` — рендерит текущий тост (или ничего)
- Обновить `frontend/src/main.tsx`:
  - Обернуть `<App />` в `<ToastProvider>`
  - Внутри App — `<ToastContainer />` после `<Chat />`
- Обновить `frontend/src/App.tsx` (если существует) или `frontend/src/main.tsx`:
  - Добавить `<ToastContainer />` в корень

### Файлы

- Создать: `frontend/src/shared/components/Toast.tsx`
- Создать: `frontend/src/shared/components/ConfirmDialog.tsx`
- Создать: `frontend/src/shared/hooks/useToast.ts`
- Изменить: `frontend/src/main.tsx`
- Возможно изменить: `frontend/src/App.tsx`

### Критерий приёмки

- `useToast().showToast("Hello", "success")` → виден зелёный тост внизу
- Тост исчезает через 3 сек
- `<ConfirmDialog isOpen={true} ...>` → виден диалог с overlay
- Клик по "Отмена" → вызов `onCancel`, диалог закрывается
- `npm run build` без ошибок

### Тест: `frontend/src/shared/components/__tests__/Toast.test.tsx` + `ConfirmDialog.test.tsx`

- Toast рендерит текст
- Toast исчезает после таймаута (mock timer)
- ConfirmDialog показывает/скрывается по isOpen
- Клик по кнопкам вызывает правильные callbacks

### Коммит: `feat: add Toast, ConfirmDialog, and useToast shared components`

---

## Задача 4 (Docs): CHANGELOG week-5 + week-6

### Что делать

- Обновить `CHANGELOG.md` — добавить секции:

**Неделя 5 — 7–13 апреля 2026:**
```
> Полировка: дизайн-система, мультишаг, суммаризация контекста

- **Павлов** — markdown-рендеринг ответов, пояснение к результатам поиска, суммаризация контекста диалога
- **Мергалиев** — редизайн карточек гитар, скелетоны загрузки, эндпоинт статистики
- **Сальников** — дизайн-система с тёмной темой, адаптивная вёрстка, фильтр off-topic запросов
- **Фокин** — ограничение до 5 результатов, тосты и confirm-диалоги, e2e тесты истории
- **Хасанов** — мультишаговый диалог с уточнениями, отображение уточнений, бейджи релевантности
- **Сидоров** — редизайн сайдбара, пагинация сессий, fallback картинок
```

**Неделя 6 — 14–20 апреля 2026:**
```
> Обогащение пайплайна: синонимы, retry, расширенное ранжирование, 50+ мок-данных

- **Павлов** — расширение маппинга до 20 абстракций, few-shot для противоречий/рублей/vintage, snapshot-тесты промпта
- **Мергалиев** — эндпоинт /api/query/parse, панель отображения параметров, Pydantic валидация
- **Сальников** — Welcome-экран с примерами, EmptyResults/ErrorMessage в дизайн-систему, smoke-тесты
- **Фокин** — модуль метрик пайплайна, KPI endpoint /api/metrics/health
- **Хасанов** — ranking v2 (condition + year), debug-лог компонентов, обновление RANKING.md
- **Сидоров** — мок до 65 записей, модуль синонимов, retry с exponential backoff
```

Корректировать фактическое содержание после week-5/6 завершения (если задачи были не выполнены — не упоминать).

### Файлы

- Изменить: `CHANGELOG.md`

### Критерий приёмки

- CHANGELOG содержит week-5 и week-6 в формате недель 1–4
- Упоминания совпадают с реально смерженными PR

### Коммит: `docs: update CHANGELOG with weeks 5 and 6`

---

## Задача 5 (Test): тесты метрик + e2e истории

### Что делать

**Часть A — тесты метрик:**

- Создать `tests/test_pipeline_metrics.py`:
  - Настройка: temp SQLite через `CHAT_DB_PATH` env или `monkeypatch`
  - `init_metrics_table()` → таблица создана
  - `record_exchange(1, "search", 1500, 5)` → запись в БД
  - `compute_kpi()` на пустой БД → все нули, `kpi_met=True`
  - После 5 записей → корректные средние
  - `avg_messages_to_first_search`: сессия 1 (3 консультации → 1 search), сессия 2 (0 консультаций → 1 search) → среднее 2.0, KPI=true
  - `p95_elapsed_ms`: 100 записей от 100 до 10000 → p95 ≈ 9500
  - `clarification_rate`: 10 сессий, в 3 был mode=clarification → 30%
  - `repeat_session_rate`: 10 сессий, в 4 было ≥2 search → 40%

- Создать `tests/test_metrics_endpoint.py`:
  - FastAPI TestClient → GET /api/metrics/health → 200
  - Все поля KPIResponse присутствуют
  - После `record_exchange` метрики обновились

**Часть B — e2e тесты истории:**

- Создать `tests/test_history_e2e.py`:
  - Создать сессию через `POST /api/sessions` (если endpoint существует) или через WS → получить id
  - Отправить 2 WS-запроса в эту сессию
  - `GET /api/sessions` → сессия в списке, title = первый запрос
  - `GET /api/sessions/{id}/messages` → 2 записи
  - `DELETE /api/sessions/{id}` → сессия исчезла из GET /api/sessions
  - `DELETE /api/history` → список пуст
  - Работает с `USE_MOCK_REVERB=true`, без GROQ_API_KEY

### Файлы

- Создать: `tests/test_pipeline_metrics.py`
- Создать: `tests/test_metrics_endpoint.py`
- Создать: `tests/test_history_e2e.py`

### Критерий приёмки

- Все три теста зелёные
- `pytest tests/test_pipeline_metrics.py tests/test_metrics_endpoint.py tests/test_history_e2e.py -v` → 100% pass
- Работает без GROQ_API_KEY

### Коммит: `test: add pipeline metrics, endpoint, and history e2e tests`
