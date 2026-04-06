# TODO — Фокин Евгений

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/fokin/limits-tests`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Backend): ограничение до 5 результатов + замер времени (PRD п.5.4, п.6)

### Что делать

- Обновить `backend/agent/service.py` — в `_handle_search()`:
  - После ранжирования — обрезать до `MAX_RESULTS = 5`
  - Замерить время выполнения `interpret_query`:
    ```python
    import time
    start = time.time()
    # ... pipeline ...
    elapsed = time.time() - start
    logger.info("Время ответа: %.2f сек", elapsed)
    ```
  - Добавить `elapsed_seconds` в ответ: `result["elapsed"] = round(elapsed, 2)`
  - Если elapsed > 10 сек → `logger.warning` (PRD: < 10 сек)
- Обновить `backend/main.py` — передать `elapsed` в WebSocket result:
  - `{"type": "result", "mode": "search", "results": [...], "elapsed": 3.14}`
- Обновить `backend/models.py` — добавить `elapsed: Optional[float] = None`

### Файлы

- Изменить: `backend/agent/service.py`
- Изменить: `backend/main.py`
- Изменить: `backend/models.py`

### Критерий приёмки

- Результатов не больше 5 (даже если Reverb вернул 20)
- В ответе есть поле `elapsed` с числом секунд
- Ответ > 10 сек → warning в логах
- Ответ ≤ 10 сек → info в логах

### Тест: `tests/test_result_limits.py`

- 20 результатов → после pipeline остаётся ≤ 5
- elapsed присутствует и > 0
- Пустой результат → elapsed всё равно есть

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
- Обновить `frontend/src/features/chat/components/Sidebar.tsx`:
  - Удаление сессии → ConfirmDialog перед удалением
  - "Очистить всё" → ConfirmDialog
  - После удаления → Toast "Чат удалён"
- Обновить `frontend/src/features/chat/components/Chat.tsx`:
  - При потере WS-соединения → Toast "Потеряно соединение, переподключаю..."
  - При восстановлении → Toast "Соединение восстановлено"

### Файлы

- Создать: `frontend/src/shared/components/Toast.tsx`
- Создать: `frontend/src/shared/components/ConfirmDialog.tsx`
- Изменить: `frontend/src/features/chat/components/Sidebar.tsx` (вызов confirm/toast)
- Изменить: `frontend/src/features/chat/components/Chat.tsx` (toast при переподключении)

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
