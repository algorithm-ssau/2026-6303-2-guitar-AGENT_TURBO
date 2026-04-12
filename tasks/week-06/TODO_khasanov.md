# TODO — Хасанов Дамир

**Неделя 6:** 14–20 апреля 2026
**Ветка:** `feature/khasanov/ranking-v2`

> Независимая задача. Все файлы — его собственные, никто другой в week-6 их не трогает.
> Можно мержить в любом порядке с другими участниками.
> Фронтенд в week-6 не трогаем — debug-панель делается через backend-логи и env-флаг.

---

## Задача 1 (Backend): ранжирование v2 — condition и year

### Что делать

- Обновить `backend/ranking/ranking.py` — добавить 2 новых скор-функции:
  - `score_condition(result: dict, params: dict) -> float`:
    - Читает `result.get("condition")` и `params.get("condition")`
    - Если оба указаны и совпадают → 100
    - Если `params["condition"] == "vintage"` и год результата `< 1985` → 100 даже если condition отличается
    - Если `params["condition"] == "mint"` и result == "mint"/"excellent" → 80
    - Без указаний → 50 (нейтральный)
    - Полное несовпадение → 20
  - `score_year_match(result: dict, params: dict) -> float`:
    - Читает `result.get("year")`, `params.get("year_min")`, `params.get("year_max")`
    - В диапазон → 100, ±2 года от диапазона → 60, иначе → 0
    - Без указаний → 50
- Обновить `calculate_total_score` — новая полная формула:
  ```
  budget 30% + type 20% + pickups 15% + brand 10% + title 10% + condition 10% + year 5%
  ```
  (Сумма = 100%. Было: budget 30 + type 25 + pickups 20 + brand 10 + title 15 = 100)
- `has_full_params` — расширить проверкой на наличие `condition` или `year_min/year_max` (если хотя бы одно — включается полная формула)
- **Упрощённую формулу (55/45) НЕ ТРОГАТЬ** — сохраняем обратную совместимость
- Обновить все существующие тесты `tests/test_ranking.py`, `test_ranking_cleanup.py`, `test_ranking_edge_cases.py`, `test_ranking_pipeline.py` — если что-то сломалось после изменения весов

### Файлы

- Изменить: `backend/ranking/ranking.py`
- Возможно изменить (если сломались после изменения весов — все эти тесты принадлежат Хасанову):
  - `tests/test_ranking.py`
  - `tests/test_ranking_cleanup.py`
  - `tests/test_ranking_edge_cases.py`
  - `tests/test_ranking_pipeline.py`

### Критерий приёмки

- Существующие тесты ранжирования — зелёные (после корректировки весов в ассертах)
- `score_condition` на 4 кейсах (match/mismatch/vintage-rescue/unspecified) даёт правильные баллы
- `score_year_match` на 4 кейсах даёт правильные баллы
- Сумма всех весов в полной формуле = 100%
- Упрощённая формула работает как раньше (тесты `test_ranking_cleanup.py` зелёные)

### Тест: покрывается Задачей 3

### Коммит: `feat: add condition and year scoring to ranking v2`

---

## Задача 2 (Backend): debug-логирование компонентов score под env-флагом

### Что делать

- Создать `backend/ranking/explain.py`:
  - Функция `explain_ranking(results: list, params: dict) -> list[dict]`:
    - Для каждого результата возвращает словарь с разбивкой по компонентам:
      ```python
      {
          "title": "Fender Stratocaster",
          "total": 87.5,
          "components": {
              "budget": 100, "type": 100, "pickups": 70,
              "brand": 80, "title": 70, "condition": 50, "year": 50
          }
      }
      ```
  - Функция `dump_ranking_debug(explain_data: list[dict], log_path: str) -> None`:
    - Добавляет запись в JSONL-файл `log_path`:
      ```
      {"timestamp": "...", "items": [...]}
      ```
    - Директорию создаёт если не существует
- Обновить `backend/ranking/ranking.py::rank_results`:
  - Читать `os.getenv("DEBUG_RANKING", "false").lower() == "true"`
  - Если true → вызвать `dump_ranking_debug(explain_ranking(results, params), "logs/ranking_debug.jsonl")`
  - Никаких изменений в возвращаемом результате (поле `score` по-прежнему удаляется из output)
- Создать директорию `logs/` и добавить в `.gitignore` паттерн `logs/*.jsonl`

### Файлы

- Создать: `backend/ranking/explain.py`
- Изменить: `backend/ranking/ranking.py` (3 строки условного вызова)
- Изменить: `.gitignore` (1 строка)

### Критерий приёмки

- `DEBUG_RANKING=true` + запуск search → в `logs/ranking_debug.jsonl` появляется запись с timestamp и компонентами
- `DEBUG_RANKING=false` (или не задан) → лог не создаётся
- JSONL корректно парсится построчно (одна запись — одна строка)
- Лог-файл в `.gitignore`

### Тест: `tests/test_ranking_explain.py`

- `explain_ranking` на результатах → словари с `components` содержат все 7 ключей
- `dump_ranking_debug` создаёт файл с одной JSON-строкой
- Мок `os.getenv` → DEBUG_RANKING=true → `rank_results` вызывает `dump_ranking_debug`
- DEBUG_RANKING не задан → `dump_ranking_debug` не вызывается

### Коммит: `feat: add ranking explain debug logs under DEBUG_RANKING flag`

---

## Задача 3 (Тестирование): тесты ranking v2 + расширенные edge-cases

### Что делать

- Создать `tests/test_ranking_v2.py`:
  - **Тест condition:**
    - mint request + mint result → score_condition = 100
    - vintage request + year=1975 result → score_condition = 100 (даже если condition="good")
    - mint request + fair result → score_condition = 20
    - Без указаний → 50
  - **Тест year:**
    - year_min=1970, year_max=1980, result year=1975 → 100
    - year_min=1970, year_max=1980, result year=1981 → 60 (±2)
    - result year=2020 → 0
    - Без year_min/year_max → 50
  - **Интеграционный:** `rank_results` на списке из 5 гитар с разным годом/состоянием + params с "vintage" → топ-результаты имеют высокий condition/year score
  - **Регрессия:** `rank_results` без condition/year в params → использует упрощённую формулу, порядок как в `test_ranking_cleanup.py`

### Файлы

- Создать: `tests/test_ranking_v2.py`

### Критерий приёмки

- 10+ тестов в test_ranking_v2.py
- Все существующие ranking-тесты зелёные (ничего не сломано)
- `pytest tests/test_ranking*.py -v` → 100% pass

### Коммит: `test: add ranking v2 tests for condition and year scoring`
