# TODO — Мергалиев Радмир
**Модуль:** Генерация search params / API-контракт
**Неделя:** 15–22 марта 2026
**Ветка:** `feature/mergaliev/api-endpoint`

---

## Из week-01 должно быть готово
- `docs/SEARCH_PARAMS.md` — JSON-структура параметров поиска
- `docs/API_CONTRACT.md` — формат запроса/ответа между фронтом и бэком
- Примеры: запрос пользователя → JSON в скрипт → ответ обратно

---

## Задача: реализовать FastAPI-эндпоинт

### Шаг 1 — Pydantic-модели и тесты на них
Создать `backend/search/models.py`: модели `ChatRequest(query: str)` и `ChatResponse(mode, results/answer)` по контракту из `docs/API_CONTRACT.md`. Написать тесты в `tests/test_models.py`: валидация обязательных полей, типы, поведение при невалидных данных.
`feat: add api pydantic models with tests`

### Шаг 2 — Роутер и интеграционные тесты
Создать `backend/search/router.py` с эндпоинтом `POST /api/chat`: принимает `ChatRequest`, вызывает LLM-сервис Павлова, возвращает `ChatResponse`. Написать интеграционный тест в `tests/test_router.py` через FastAPI `TestClient`: корректный запрос → 200, пустой query → 422.
`feat: add chat api endpoint with integration tests`

### Шаг 3 — Подключить в main.py и smoke-тест
Подключить роутер в `backend/main.py`. Добавить `.env.example` с `GROQ_API_KEY=` и `LLM_MODEL=`. Написать smoke-тест: приложение стартует, `/api/chat` доступен, возвращает ожидаемую структуру.
`feat: wire up backend entrypoint with smoke test`

---

> Стек: Python + FastAPI + Pydantic. Подробнее — [STACK.md](../../STACK.md)
