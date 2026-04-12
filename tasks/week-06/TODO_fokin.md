# TODO — Фокин Евгений

**Неделя 6:** 14–20 апреля 2026
**Ветка:** `feature/fokin/pipeline-metrics`

> Независимая задача. Все файлы — его собственные, никто другой в week-6 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Backend): модуль метрик пайплайна + запись из main.py

### Что делать

**Часть A — модуль метрик:**

- Создать `backend/analytics/__init__.py` (пустой)
- Создать `backend/analytics/pipeline_metrics.py`:
  - Функция `init_metrics_table() -> None`:
    - Создаёт таблицу в общей `chat.db`:
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
    - Использует то же соединение что `backend/history/service.py::_get_connection` — импортирует его
  - Функция `record_exchange(session_id: int | None, mode: str, elapsed_ms: int, results_count: int | None) -> None`:
    - Вставка в `pipeline_metrics`
    - Логирует через `get_logger("analytics")`
  - Функция `compute_kpi() -> dict`:
    - Возвращает:
      ```python
      {
          "total_sessions": ...,         # SELECT COUNT(DISTINCT session_id)
          "total_exchanges": ...,        # SELECT COUNT(*)
          "avg_elapsed_ms": ...,         # SELECT AVG(elapsed_ms)
          "p95_elapsed_ms": ...,         # приближение через ORDER BY + LIMIT
          "avg_messages_to_first_search": ...,  # среднее число сообщений до первого "mode=search" в сессии
          "kpi_met": bool,               # avg_messages_to_first_search <= 3 (PRD §11)
      }
      ```
- Обновить `backend/history/service.py::init_db`:
  - Добавить 1 строку: `from backend.analytics.pipeline_metrics import init_metrics_table; init_metrics_table()`

**Часть B — запись метрик в main.py:**

- Обновить `backend/main.py`:
  - Импортировать `from backend.analytics.pipeline_metrics import record_exchange`
  - Импортировать `import time`
  - Перед вызовом `interpret_query` — `t0 = time.perf_counter()`
  - После получения `result_data` — `elapsed_ms = int((time.perf_counter() - t0) * 1000)`
  - После успешной отправки WS-ответа — `record_exchange(session_id, result_data["mode"], elapsed_ms, len(result_data.get("results", [])) if result_data["mode"] == "search" else None)`
  - Обернуть вызов `record_exchange` в try/except (метрики никогда не должны валить основной flow)

**НЕ трогать**: `backend/agent/service.py`, `backend/agent/llm_client.py`, никакие другие файлы кроме указанных

### Файлы

- Создать: `backend/analytics/__init__.py`
- Создать: `backend/analytics/pipeline_metrics.py`
- Изменить: `backend/history/service.py` (1 строка в `init_db`)
- Изменить: `backend/main.py` (замер времени + запись метрик + импорты)

### Критерий приёмки

- После отправки сообщения в чат в таблице `pipeline_metrics` появляется запись
- `init_db` на чистой БД создаёт обе таблицы (chat_history и pipeline_metrics)
- Consultation-ответы также записываются в метрики (с `results_count=None`)
- Если `record_exchange` упал — WS-ответ всё равно отправлен клиенту

### Тест: покрывается Задачей 3

### Коммит: `feat: add pipeline metrics module and record from main.py`

---

## Задача 2 (Backend): KPI health endpoint `/api/metrics/health`

### Что делать

- Создать `backend/analytics/router.py`:
  - `router = APIRouter(prefix="/api/metrics", tags=["metrics"])`
  - `GET /health` → вызывает `compute_kpi()` и возвращает результат как JSON
  - camelCase-конвертация перед возвратом (через `snake_to_camel`)
  - Модель ответа — Pydantic `KPIResponse`:
    ```python
    class KPIResponse(BaseModel):
        totalSessions: int
        totalExchanges: int
        avgElapsedMs: float
        p95ElapsedMs: float
        avgMessagesToFirstSearch: float
        kpiMet: bool
    ```
- Обновить `backend/main.py` — добавить `app.include_router(analytics_router)` (одна строка)

### Файлы

- Создать: `backend/analytics/router.py`
- Изменить: `backend/main.py` (1 строка include_router)

### Критерий приёмки

- `GET /api/metrics/health` → 200 + JSON со всеми полями
- На пустой БД → все метрики = 0, `kpiMet = true` (нет сессий, KPI не нарушен)
- После нескольких search-запросов → метрики ненулевые
- Если avgMessagesToFirstSearch > 3 → kpiMet = false

### Тест: покрывается Задачей 3

### Коммит: `feat: add KPI health endpoint for pipeline metrics`

---

## Задача 3 (Docs/Test): CHANGELOG week-5 + тесты метрик

### Что делать

**Часть A — CHANGELOG:**

- Обновить `CHANGELOG.md` — добавить секцию **Неделя 5 — 7–13 апреля 2026**
- Формат — как у недель 1–4:
  ```
  ---

  ## Неделя 5 — 7–13 апреля 2026

  > Полировка: дизайн-система, мультишаг, суммаризация контекста, метрики

  - **Павлов** — markdown-рендеринг ответов, пояснение к результатам поиска, суммаризация контекста диалога
  - **Мергалиев** — редизайн карточек гитар, скелетоны загрузки, эндпоинт статистики
  - **Сальников** — дизайн-система с тёмной темой, адаптивная вёрстка, фильтр off-topic запросов
  - **Фокин** — ограничение до 5 результатов, тосты и confirm-диалоги, e2e тесты истории
  - **Хасанов** — мультишаговый диалог с уточнениями, отображение уточнений, бейджи релевантности
  - **Сидоров** — редизайн сайдбара, пагинация сессий, fallback картинок
  ```

**Часть B — тесты метрик:**

- Создать `tests/test_pipeline_metrics.py`:
  - Настройка: temp SQLite БД через `monkeypatch` или env `CHAT_DB_PATH`
  - `init_metrics_table()` — таблица создана
  - `record_exchange(1, "search", 1500, 5)` + чтение из SQL → запись есть
  - `compute_kpi()` на пустой БД → все нули + `kpi_met=True`
  - `compute_kpi()` после 5 записей → корректные средние
  - Тест `avg_messages_to_first_search`: в сессии 1 было 3 консультации → 1 search, в сессии 2 было 0 консультаций → 1 search; среднее = 2.0; KPI = true (≤3)
  - Тест `p95_elapsed_ms`: 100 записей с elapsed от 100 до 10000 → p95 близок к 9500

- Создать `tests/test_metrics_endpoint.py`:
  - FastAPI TestClient → GET /api/metrics/health → 200
  - Проверка всех полей ответа
  - После вставки через `record_exchange` → метрики обновились

### Файлы

- Изменить: `CHANGELOG.md`
- Создать: `tests/test_pipeline_metrics.py`
- Создать: `tests/test_metrics_endpoint.py`

### Критерий приёмки

- CHANGELOG содержит week-5 в том же формате, что недели 1–4
- Все тесты метрик зелёные
- `pytest tests/test_pipeline_metrics.py tests/test_metrics_endpoint.py -v` → 100% pass
- Работает без GROQ_API_KEY (не зависит от LLM)

### Коммит: `docs: update CHANGELOG with week-5 summary + test: pipeline metrics`
