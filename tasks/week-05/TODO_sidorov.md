# TODO — Сидоров Артемий

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/sidorov/sidebar-redesign`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Frontend): сайдбар по мокапу

### Что делать

- Переписать `frontend/src/features/chat/components/Sidebar.tsx` по дизайну из `design/mockup.html`:
  - Стилизация: тёмный фон, hover-эффекты на сессиях, активная сессия — подсвеченный фон
  - Кнопка "Новый чат" — стиль accent из мокапа
  - Кнопка удаления — появляется только при hover на сессии
  - Иконки вместо текста "x" (можно Unicode: 🗑 или ✕)
  - Плавная анимация открытия/закрытия сайдбара (transition)
- Добавить поле поиска по истории в верхней части сайдбара:
  - Инпут с placeholder "Поиск чатов..."
  - Фильтрация сессий по title (на клиенте, без запроса на сервер)

### Файлы

- Изменить: `frontend/src/features/chat/components/Sidebar.tsx`

### Критерий приёмки

- Сайдбар визуально соответствует мокапу
- Hover на сессии → подсветка + появляется кнопка удаления
- Поле поиска фильтрует сессии по заголовку (регистронезависимо)
- Открытие/закрытие сайдбара — плавная анимация

### Тест: визуальная проверка + `npm run build` без ошибок

### Коммит: `feat: redesign sidebar with search and hover effects from mockup`

---

## Задача 2 (Backend): пагинация сессий `GET /api/sessions`

### Что делать

- Обновить `backend/history/service.py` — функция `get_sessions()`:
  - Принимать параметры `offset: int = 0`, `limit: int = 20`
  - Возвращать также `total: int` (общее количество сессий)
- Обновить `backend/history/router.py`:
  - `GET /api/sessions?offset=0&limit=20` → `{ sessions: [...], total: 42 }`
- Обновить `backend/history/models.py`:
  - Добавить `total: int` в `SessionsResponse`
- Обновить фронтенд `frontend/src/features/chat/api.ts`:
  - `fetchSessions(offset?, limit?)` — передавать query-параметры
- Обновить `frontend/src/features/chat/hooks/useChat.ts`:
  - Подгрузка следующей страницы при скролле сайдбара к низу (lazy load)

### Файлы

- Изменить: `backend/history/service.py`
- Изменить: `backend/history/router.py`
- Изменить: `backend/history/models.py`
- Изменить: `frontend/src/features/chat/api.ts`
- Изменить: `frontend/src/features/chat/hooks/useChat.ts`

### Критерий приёмки

- `GET /api/sessions?limit=5` → возвращает максимум 5 сессий + total
- `GET /api/sessions?offset=5&limit=5` → следующие 5
- На фронте при скролле сайдбара вниз → подгружаются ещё сессии
- Обратная совместимость: без параметров — первые 20

### Тест: `tests/test_pagination.py`

- 10 сессий, limit=3 → 3 сессии, total=10
- offset=3, limit=3 → следующие 3
- offset > total → пустой список, total корректный

### Коммит: `feat: add pagination for sessions endpoint`

---

## Задача 3 (Backend): улучшение fallback картинок в Reverb-ответах

### Что делать

- Обновить `backend/search/search_reverb.py`:
  - Если Reverb API не вернул `image_url` → подставить URL плейсхолдера
  - Проверить что `image_url` — валидный URL (starts with http), иначе → плейсхолдер
  - Плейсхолдер: `https://placehold.co/400x300?text=No+Image`
- Обновить `backend/search/models.py` — добавить валидацию image_url

### Файлы

- Изменить: `backend/search/search_reverb.py`

### Критерий приёмки

- Результат без image_url → приходит плейсхолдер-URL
- Результат с невалидным image_url → приходит плейсхолдер
- Результат с нормальным image_url → без изменений

### Тест: `tests/test_image_fallback.py`

- Результат без image_url → плейсхолдер
- Результат с пустой строкой → плейсхолдер
- Результат с "not-a-url" → плейсхолдер
- Результат с "https://..." → оригинал

### Коммит: `feat: add image URL fallback for Reverb results`
