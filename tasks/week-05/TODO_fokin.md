# TODO — Фокин Евгений

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/fokin/limits-tests`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Backend): ограничение до 5 результатов + замер времени (PRD п.5.4, п.6)

### Что делать

- Создать `backend/agent/pipeline_middleware.py` — обёртка над пайплайном:
  - Функция-декоратор `with_timing(fn)` — замеряет время выполнения, логирует, добавляет `elapsed` в результат
  - Функция `limit_results(result: dict, max_results: int = 5) -> dict` — обрезает results до max_results
  - Если elapsed > 10 сек → `logger.warning` (PRD: < 10 сек)
- Обновить `backend/main.py` — в WS цикле обернуть вызов `interpret_query`:
  - Замер времени вокруг вызова (в main.py, а не в service.py)
  - Вызов `limit_results()` перед отправкой search-результатов
  - Добавить `elapsed` в WS-ответ: `{"type": "result", ..., "elapsed": 3.14}`
- **НЕ трогать `service.py`** — вся логика лимитов и таймингов в middleware и main.py

### Файлы

- Создать: `backend/agent/pipeline_middleware.py` (основная работа)
- Изменить: `backend/main.py` (обёртка вызова + limit_results перед отправкой)

### Критерий приёмки

- Результатов не больше 5 (даже если Reverb вернул 20)
- В ответе есть поле `elapsed` с числом секунд
- Ответ > 10 сек → warning в логах
- Ответ ≤ 10 сек → info в логах

### Тест: `tests/test_result_limits.py`

- limit_results с 20 результатами → 5
- limit_results с 3 результатами → 3 (не добавляет лишние)
- with_timing возвращает elapsed > 0

### Коммит: `feat: limit results to 5 and add response time tracking`

---

## Задача 2 (Frontend): тосты-уведомления и confirm-диалоги

### Что делать

- Создать `frontend/src/shared/components/Toast.tsx`:
  - Компонент тоста: текст + автоскрытие через 3 секунды
  - Типы: success (зелёный), error (красный), info (синий)
  - Позиция: нижний правый угол, поверх контента
- Создать `frontend/src/shared/components/ConfirmDialog.tsx`:
  - Модальное окно: "Вы уверены?" + кнопки "Да" / "Отмена"
  - Затемнение фона (overlay)
- Создать хук `frontend/src/shared/hooks/useToast.ts`:
  - `useToast()` → `{ showToast(text, type), ToastContainer }`
  - Позволяет любому компоненту показать тост без прямого импорта
- Обновить `frontend/src/features/chat/components/Chat.tsx`:
  - Подключить `useToast` и `<ToastContainer />`
  - При потере WS-соединения → Toast "Потеряно соединение, переподключаю..."
  - При восстановлении → Toast "Соединение восстановлено"
- **НЕ трогать Sidebar.tsx** — интеграцию confirm-диалогов в сайдбар делает Сидоров (он владеет этим файлом)

### Файлы

- Создать: `frontend/src/shared/components/Toast.tsx`
- Создать: `frontend/src/shared/components/ConfirmDialog.tsx`
- Создать: `frontend/src/shared/hooks/useToast.ts`
- Изменить: `frontend/src/features/chat/components/Chat.tsx` (только подключение ToastContainer + WS-тосты)

### Критерий приёмки

- Удаление чата → "Вы уверены?" → "Да" → чат удалён, тост "Чат удалён"
- "Очистить всё" → confirm → очистка, тост "История очищена"
- WS disconnect → тост "Потеряно соединение..." (красный)
- WS reconnect → тост "Соединение восстановлено" (зелёный)

### Тест: `frontend/src/shared/components/__tests__/Toast.test.tsx`

- Toast рендерится с текстом
- Toast исчезает после таймаута
- ConfirmDialog показывает текст и кнопки

### Коммит: `feat: add toast notifications and confirm dialogs`

---

## Задача 3 (Тестирование): e2e тесты истории + smoke-тест

### Что делать

- Написать `tests/test_history_e2e.py`:
  - Создать сессию через `POST /api/sessions` → получить id
  - Отправить 2 запроса через WS с этим sessionId
  - `GET /api/sessions` → сессия в списке, title = первый запрос
  - `GET /api/sessions/{id}/messages` → 2 записи с корректными полями
  - `DELETE /api/sessions/{id}` → `GET /api/sessions` → сессия исчезла
  - `DELETE /api/history` → всё пусто
- Написать `tests/test_smoke.py`:
  - Импорт `backend.main` → без ошибок
  - `GET /` → `{"status": "ok"}`
  - `GET /api/sessions` → 200
  - `GET /api/stats` → 200 (если Мергалиев успел, иначе skip)

### Файлы

- Создать: `tests/test_history_e2e.py`
- Создать: `tests/test_smoke.py`

### Критерий приёмки

- Все тесты проходят с `USE_MOCK_REVERB=true` без GROQ_API_KEY
- Покрыто: создание сессии, сообщения, удаление, очистка
- Smoke-тест проходит на чистой машине

### Коммит: `test: add e2e history tests and smoke tests`
