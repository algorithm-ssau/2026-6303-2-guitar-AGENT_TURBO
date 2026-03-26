# TODO — Хасанов Дамир

**Неделя 4:** 30 марта – 5 апреля 2026
**Ветка:** `feature/khasanov/ranking-cleanup`

> **Независимая задача.** Можно работать параллельно с остальными.

---

## Задача 1 (Backend): очистка score из результатов + передача search_queries в ranking

### Что делать

- Обновить `backend/ranking/ranking.py` — функция `rank_results()`:
  - Убрать поле `score` из выходных данных (удалять перед возвратом):
    ```python
    for r in scored_results:
        r.pop('score', None)
        r.pop('_score', None)
    ```
  - Текущая проблема: `service.py` передаёт только `{"budget_max": price_max}`, но ranking использует `params.get('type')`, `params.get('pickups')` и т.д. — эти поля отсутствуют
  - Добавить fallback-скоринг по `search_queries`: если нет type/pickups/brand — использовать `search_queries` для title matching
  - Упрощённая формула: budget(55%) + title_match(45%) — когда нет type/pickups
  - Полная формула: когда есть все параметры — веса как раньше
- Обновить `backend/agent/service.py` — передавать в `rank_results()` полный набор параметров:
  ```python
  rank_params = {
      "budget_max": params.get("price_max"),
      "search_queries": params.get("search_queries", []),
  }
  ranked = rank_results(results, rank_params)
  ```

### Файлы

- Изменить: `backend/ranking/ranking.py`
- Изменить: `backend/agent/service.py` (передача параметров в rank_results)

### Критерий приёмки

- Результаты НЕ содержат поле `score` или `_score`
- Ранжирование работает даже с минимальными параметрами (только budget_max + search_queries)
- Упрощённая формула: budget(55%) + title(45%) — когда нет type/pickups
- Полная формула: когда есть все параметры — веса как раньше

### Тест: `tests/test_ranking_cleanup.py`

- Результаты не содержат score/_score
- Минимальные параметры (budget_max + search_queries) → ранжирование работает
- Гитара с совпадением в title и в бюджете → выше чем без совпадения

### Коммит: `fix: remove score from output and improve minimal ranking`

---

## Задача 2 (Frontend): отображение позиции в ранге и индикатор релевантности

### Что делать

- Обновить `frontend/src/features/chat/components/ResultsList.tsx`:
  - Добавить нумерацию: "#1", "#2", "#3" перед каждой карточкой
  - Показать подзаголовок "Лучшие совпадения" над списком
- Создать `frontend/src/features/chat/components/RelevanceBadge.tsx`:
  - Props: `position: number` (1-5)
  - Позиция 1: зелёный бейдж "Лучшее совпадение"
  - Позиции 2-3: голубой бейдж "Отличный вариант"
  - Позиции 4-5: серый бейдж "Подходит"
- Интегрировать `RelevanceBadge` в `GuitarCard`

### Файлы

- Изменить: `frontend/src/features/chat/components/ResultsList.tsx`
- Создать: `frontend/src/features/chat/components/RelevanceBadge.tsx`
- Изменить: `frontend/src/features/chat/components/GuitarCard.tsx`
- Изменить: `frontend/src/features/chat/index.ts` (экспорт)

### Критерий приёмки

- Карточки пронумерованы #1–#5
- Первый результат имеет бейдж "Лучшее совпадение"
- Подзаголовок "Лучшие совпадения" над списком

### Тест: `frontend/src/features/chat/__tests__/RelevanceBadge.test.tsx`

- position=1 → "Лучшее совпадение"
- position=3 → "Отличный вариант"
- position=5 → "Подходит"

### Коммит: `feat: add relevance badges and ranking positions to results`

---

## Задача 3 (Тестирование): проверка ранжирования в полном пайплайне

### Что делать

- Написать `tests/test_ranking_pipeline.py`:
  - Подготовить 10 mock-результатов с разными ценами и title
  - Вызвать `interpret_query()` с mock LLM и mock search → проверить что возвращается не более 5 результатов
  - Проверить порядок: гитара в бюджете с совпадением в title → первая
  - Проверить что `score` не в выходных данных
  - Проверить граничный случай: search_reverb вернул 0 результатов → пустой список
  - Проверить граничный случай: search_reverb вернул 3 результата → 3 на выходе (не 5)

### Файлы

- Создать: `tests/test_ranking_pipeline.py`

### Критерий приёмки

- Тесты проверяют ранжирование внутри полного pipeline
- Порядок результатов соответствует ожиданиям
- Граничные случаи обработаны

### Коммит: `test: add ranking pipeline integration tests`
