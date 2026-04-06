# TODO — Мергалиев Радмир

**Неделя 5:** 7–13 апреля 2026
**Ветка:** `feature/mergaliev/guitar-cards-redesign`

> Независимая задача. Файлы не пересекаются с другими участниками.

---

## Задача 1 (Frontend): карточки гитар по мокапу

### Что делать

- Переписать `frontend/src/features/chat/components/GuitarCard.tsx` по дизайну из `design/mockup.html`:
  - Грид 2 колонки (1 колонка на мобилке ≤480px)
  - Картинка гитары сверху (с плейсхолдером если нет imageUrl)
  - Название, цена, валюта
  - Кнопка "Смотреть на Reverb" — ссылка на listing_url
  - Тёмный стиль карточки (фон `--bg-secondary`, текст `--text-primary`)
- Обновить `frontend/src/features/chat/components/ResultsList.tsx`:
  - CSS Grid вместо вертикального списка
  - `grid-template-columns: repeat(2, 1fr)` с gap

### Файлы

- Изменить: `frontend/src/features/chat/components/GuitarCard.tsx`
- Изменить: `frontend/src/features/chat/components/ResultsList.tsx`

### Критерий приёмки

- Карточки выглядят как в мокапе: 2 колонки, картинка + инфо + кнопка
- Без картинки → плейсхолдер (иконка гитары или серый фон)
- На мобилке (≤480px) → 1 колонка
- Кнопка "Смотреть на Reverb" открывает ссылку в новой вкладке

### Тест: `frontend/src/features/chat/__tests__/GuitarCard.test.tsx`

- Обновить: карточка рендерится с названием, ценой, ссылкой
- Без imageUrl → плейсхолдер отображается
- Ссылка имеет `target="_blank"`

### Коммит: `feat: redesign guitar cards with grid layout from mockup`

---

## Задача 2 (Frontend): скелетоны загрузки карточек

### Что делать

- Создать `frontend/src/features/chat/components/SkeletonCard.tsx`:
  - Анимированный скелетон карточки гитары (как в мокапе): серый мерцающий блок
  - Повторяет форму GuitarCard: картинка-прямоугольник, 2 строки текста, кнопка
- Обновить `frontend/src/features/chat/components/StatusIndicator.tsx`:
  - При isLoading в search-режиме показывать 2–4 скелетон-карточки вместо текста "Загрузка..."

### Файлы

- Создать: `frontend/src/features/chat/components/SkeletonCard.tsx`
- Изменить: `frontend/src/features/chat/components/StatusIndicator.tsx`

### Критерий приёмки

- При ожидании search-результатов видны мерцающие скелетоны (2–4 штуки)
- Скелетоны исчезают когда приходят реальные карточки
- Анимация плавная, без рывков

### Тест: `frontend/src/features/chat/__tests__/SkeletonCard.test.tsx`

- Компонент рендерится без ошибок
- Содержит анимированные элементы (CSS animation)

### Коммит: `feat: add skeleton loading cards for search results`

---

## Задача 3 (Backend): эндпоинт статистики `GET /api/stats`

### Что делать

- Создать `backend/history/stats.py`:
  - `get_stats() -> dict` — SQL запросы:
    - Общее количество сессий
    - Общее количество запросов
    - Распределение по режимам (search / consultation / off_topic)
    - Среднее количество сообщений на сессию
    - Среднее количество сообщений до выдачи ссылок (PRD п.11: ≤ 3)
- Добавить эндпоинт в `backend/history/router.py`:
  - `GET /api/stats` → `StatsResponse`
- Добавить модель `StatsResponse` в `backend/history/models.py`

### Файлы

- Создать: `backend/history/stats.py`
- Изменить: `backend/history/router.py`
- Изменить: `backend/history/models.py`

### Критерий приёмки

- `GET /api/stats` → JSON с total_sessions, total_queries, mode_distribution, avg_messages_per_session
- На пустой БД → нули, не ошибка
- После 3 сессий → корректные числа

### Тест: `tests/test_stats.py`

- Пустая БД → все метрики = 0
- После нескольких save_exchange → метрики корректны
- mode_distribution считает search и consultation отдельно

### Коммит: `feat: add stats endpoint with usage metrics`
