# TODO — Сидоров Артемий

**Неделя 3:** 23–29 марта 2026
**Ветка:** `feature/sidorov/reverb-impl`

---

## Задача 1 (Backend): реализация search_reverb на моковых данных

> **Важно:** реальный Reverb API пока НЕ используем. Работаем только с мок-данными.

### Что делать

- Расширить `tests/mock_reverb.json` до 15–20 объявлений:
  - 3–4 электрогитары разных брендов (Fender, Gibson, Ibanez, PRS)
  - 2–3 акустические гитары
  - 2–3 бас-гитары
  - 2–3 гитары для метала (7-струнные, активные датчики)
  - 2–3 винтажные гитары
  - Разброс цен: $150 – $3000
  - У каждого: id, title, price, currency, image_url, listing_url
- Переписать `backend/search/search_reverb.py`:
  - Загружать данные из `mock_reverb.json`
  - Фильтрация по `search_queries` — регистронезависимое совпадение с title
  - Фильтрация по `price_min` / `price_max`
  - Возвращать список dict в формате проекта

### Файлы

- Изменить: `backend/search/search_reverb.py`
- Расширить: `tests/mock_reverb.json`

### Критерий приёмки

- `search_reverb(["Fender"])` → только гитары с "Fender" в title
- `search_reverb([], price_max=500)` → только до $500
- `search_reverb(["Gibson"], price_min=800, price_max=2000)` → фильтрация по названию И цене
- `search_reverb(["несуществующий"])` → пустой список

### Коммит: `feat: implement search_reverb with mock data`

---

## Задача 2 (Frontend): компонент статуса поиска

### Что делать

- Создать `SearchStatus.tsx`:
  - Props: `isLoading: boolean`, `resultsCount?: number`, `mode?: string`
  - При isLoading → "Ищем на Reverb..." с анимацией
  - При resultsCount > 0 → "Найдено N вариантов" (с правильным склонением: вариант/варианта/вариантов)
  - При resultsCount = 0 → "Ничего не найдено"
- Интегрировать в `Message.tsx` — показывать перед списком результатов

### Файлы

- Создать: `frontend/src/features/chat/components/SearchStatus.tsx`
- Изменить: `Message.tsx`

### Критерий приёмки

- Правильное склонение: 1 вариант, 2 варианта, 5 вариантов
- Анимация при загрузке

### Тест: `frontend/src/features/chat/__tests__/SearchStatus.test.tsx`

- isLoading=true → текст "Ищем на Reverb..."
- resultsCount=5 → "5 вариантов"
- resultsCount=0 → "Ничего не найдено"

### Коммит: `feat: add search status component with loading states`

---

## Задача 3 (Тестирование): тесты поиска по моковым данным

### Что делать

- Написать `tests/test_search_reverb.py`
- Минимум 7 тестов:
  - Поиск по бренду — находит
  - Поиск несуществующего — пустой результат
  - Фильтрация по price_max
  - Фильтрация по диапазону цен
  - Комбинация запрос + цена
  - Пустой запрос — все в рамках бюджета
  - Формат результата — обязательные поля (id, title, price, currency, listing_url)

### Файлы

- Создать: `tests/test_search_reverb.py`

### Критерий приёмки

- Все тесты проходят, покрывают основные сценарии фильтрации

### Коммит: `test: add search_reverb mock data tests`
