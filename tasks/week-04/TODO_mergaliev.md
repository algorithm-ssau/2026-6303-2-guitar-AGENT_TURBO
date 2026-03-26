# TODO — Мергалиев Радмир

**Неделя 4:** 30 марта – 5 апреля 2026
**Ветка:** `feature/mergaliev/api-contract-fix`

> **Зависимость:** задача 1 зависит от router.py Фокина. Можно начинать параллельно, но мержить после `feature/fokin/router-env`.

---

## Задача 1 (Backend + Frontend): исправить маппинг полей snake_case ↔ camelCase

### Что делать

- **Проблема:** backend возвращает `image_url`, `listing_url` (snake_case), а frontend ожидает `imageUrl`, `listingUrl` (camelCase). Данные приходят, но поля не маппятся → картинки и ссылки не отображаются.
- Создать `backend/utils/serializer.py` — функция `snake_to_camel(results)`:
  - `image_url` → `imageUrl`
  - `listing_url` → `listingUrl`
  - Остальные поля (id, title, price, currency) — без изменений
- Применить маппинг в `backend/main.py` WebSocket endpoint перед отправкой `type="result"` с `mode="search"`
- Обновить `backend/search/models.py` — добавить `model_config` с `alias_generator` для Pydantic:
  ```python
  from pydantic import ConfigDict
  from pydantic.alias_generators import to_camel

  model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
  ```
- Обновить `frontend/src/features/chat/types.ts`:
  - `ChatResponseSchema` — убрать поле `reply`, добавить `answer` и `results` для соответствия WS-контракту:
    ```typescript
    export const ChatResponseSchema = z.object({
      mode: z.enum(['search', 'consultation']),
      answer: z.string().optional(),
      results: z.array(SearchResultSchema).optional(),
    });
    ```

### Файлы

- Создать: `backend/utils/serializer.py`
- Изменить: `backend/main.py`
- Изменить: `backend/search/models.py`
- Изменить: `frontend/src/features/chat/types.ts`

### Критерий приёмки

- WebSocket result для search содержит `imageUrl` и `listingUrl` (camelCase)
- Frontend GuitarCard получает корректные данные: картинка отображается, ссылка "Смотреть" ведёт на Reverb
- Pydantic модели поддерживают оба варианта (snake_case и camelCase)

### Тест: `tests/test_serializer.py`

- `snake_to_camel` преобразует image_url → imageUrl
- Список из 3 результатов → все поля преобразованы
- Поля без подчёркивания остаются без изменений

### Коммит: `fix: add snake_case to camelCase mapping for API contract`

---

## Задача 2 (Frontend): живой индикатор статуса поиска

### Что делать

- Создать `frontend/src/features/chat/components/StatusIndicator.tsx`:
  - Props: `status: string | null`, `isLoading: boolean`
  - При isLoading=true и status не null → показывает текст статуса с анимированными точками ("Ищу на Reverb...")
  - При isLoading=true и status null → показывает "Подключение..."
  - При isLoading=false → не рендерится (return null)
  - Анимация: пульсирующая точка + текст статуса
- Интегрировать в `Chat.tsx` — заменить статичный текст загрузки на `StatusIndicator`

### Файлы

- Создать: `frontend/src/features/chat/components/StatusIndicator.tsx`
- Изменить: `frontend/src/features/chat/components/Chat.tsx`
- Изменить: `frontend/src/features/chat/index.ts` (экспорт)

### Критерий приёмки

- Пользователь видит текущий этап обработки: "Определяю режим..." → "Ищу на Reverb..." → "Ранжирую результаты..."
- Текст статуса обновляется в реальном времени
- После получения ответа индикатор исчезает

### Тест: `frontend/src/features/chat/__tests__/StatusIndicator.test.tsx`

- isLoading=true, status="Ищу на Reverb..." → текст отображается
- isLoading=false → компонент не рендерится
- isLoading=true, status=null → "Подключение..."

### Коммит: `feat: add real-time status indicator component`

---

## Задача 3 (Тестирование): проверка API-контракта между backend и frontend

### Что делать

- Написать `tests/test_api_contract.py`:
  - Запустить WebSocket через FastAPI TestClient
  - Отправить search-запрос → проверить что result содержит `imageUrl` и `listingUrl` (camelCase, не snake_case)
  - Отправить consultation-запрос → проверить что result содержит `answer` (не `reply`)
  - Проверить что все обязательные поля GuitarResult присутствуют: id, title, price, listingUrl
  - Проверить что `score` НЕ присутствует в результатах

### Файлы

- Создать: `tests/test_api_contract.py`

### Критерий приёмки

- Тесты гарантируют что backend и frontend говорят на одном языке
- Любое изменение формата данных ломает тест → обнаруживается сразу

### Коммит: `test: add API contract validation tests`
