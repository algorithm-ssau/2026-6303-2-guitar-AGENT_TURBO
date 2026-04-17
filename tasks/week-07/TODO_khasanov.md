# TODO — Хасанов Дамир

**Неделя 7:** 21–27 апреля 2026
**Ветка:** `feature/khasanov/ranking-polish-w7`

> Независимая задача. Все файлы — его собственные, никто другой в week-7 их не трогает.
> Можно мержить в любом порядке с другими участниками.

---

## Задача 1 (Backend): ranking/explain.py — debug-лог компонентов score

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
    - Добавляет JSONL-запись в `log_path`: `{"timestamp": "...", "items": [...]}`
    - Директорию создаёт если не существует
- Обновить `backend/ranking/ranking.py::rank_results`:
  - Читать `os.getenv("DEBUG_RANKING", "false").lower() == "true"`
  - Если true → `dump_ranking_debug(explain_ranking(results, params), "logs/ranking_debug.jsonl")`
  - Никаких изменений в возвращаемом результате (поле `score` по-прежнему удаляется из output)
- Создать директорию `logs/` (gitignore)
- Обновить `.gitignore` паттерном `logs/*.jsonl`

### Файлы

- Создать: `backend/ranking/explain.py`
- Изменить: `backend/ranking/ranking.py` (3 строки условного вызова)
- Изменить: `.gitignore` (1 строка)

### Критерий приёмки

- `DEBUG_RANKING=true` + запуск search → в `logs/ranking_debug.jsonl` появляется запись
- `DEBUG_RANKING=false` → лог не создаётся
- JSONL корректно парсится построчно
- Лог-файл в `.gitignore`

### Тест: `tests/test_ranking_explain.py`

- `explain_ranking` возвращает словари с `components` (все компоненты)
- `dump_ranking_debug` создаёт файл с одной JSON-строкой
- Мок `os.getenv` → DEBUG_RANKING=true → `rank_results` вызывает `dump_ranking_debug`
- DEBUG_RANKING не задан → `dump_ranking_debug` не вызывается

### Коммит: `feat: add ranking explain debug log under DEBUG_RANKING flag`

---

## Задача 2 (Test): регрессия ranking v2 (condition + year)

### Что делать

- Создать `tests/test_ranking_v2.py`:
  - **Тест condition:**
    - mint request + mint result → score_condition ≥ 80
    - vintage request + year=1975 result → score_condition ≥ 90 (даже если condition="good")
    - mint request + fair result → score_condition ≤ 30
    - Без указаний → 50
  - **Тест year:**
    - year_min=1970, year_max=1980, result year=1975 → 100
    - result year=1981 → ≥ 50 (близко к диапазону)
    - result year=2020 (при vintage-запросе) → низкий
  - **Интеграционный:** `rank_results` на списке из 5 гитар с разным годом/condition + params с vintage → топ-результат имеет подходящий год
  - **Регрессия:** `rank_results` без condition/year в params → порядок как в `test_ranking_cleanup.py`
  - **Совместимость:** функции `score_condition` и `score_year_match` существуют (если не существуют после week-6 adaptive-ranking — пропустить тест с skip)

### Файлы

- Создать: `tests/test_ranking_v2.py`

### Критерий приёмки

- 10+ тестов
- Все существующие ranking-тесты зелёные (ничего не сломано)
- `pytest tests/test_ranking*.py -v` → 100% pass

### Коммит: `test: add ranking v2 regression tests for condition and year`

---

## Задача 3 (Backend): дедупликация похожих результатов в ранжировании

### Что делать

- Обновить `backend/ranking/ranking.py::rank_results`:
  - Добавить функцию `_deduplicate_similar(ranked: list, threshold: float = 0.85) -> list`:
    - Два результата считаются дубликатами если их `title` совпадает по SequenceMatcher ratio ≥ `threshold`
    - Из каждой группы дубликатов оставляем первый (с наивысшим score)
    - Реализация через `difflib.SequenceMatcher` (встроенная библиотека Python)
  - Вызвать `_deduplicate_similar(scored_results)` после сортировки, ДО обрезки до 5

### Файлы

- Изменить: `backend/ranking/ranking.py`

### Критерий приёмки

- На вход: 5 результатов "Fender Stratocaster MX 2021", "Fender Stratocaster MX 2022", "Fender Strat MX 2023", "Gibson Les Paul", "Ibanez RG" → в топе остаются 3 (один Fender Strat + LP + RG)
- Оригинальное поведение сохраняется для непохожих тайтлов
- Threshold настраиваем (параметр функции)

### Тест: `tests/test_ranking_dedup.py`

- 5 похожих Strat'ов → 1 в топе
- 3 разных бренда → все 3 в топе
- Пустой вход → пустой выход
- Порог threshold=0.5 (агрессивный) → больше дубликатов удалено

### Коммит: `feat: add title similarity deduplication in ranking`

---

## Задача 4 (Backend): настраиваемые веса через env

### Что делать

- Создать `backend/ranking/weights.py`:
  - Константы дефолтных весов:
    ```python
    DEFAULT_WEIGHTS = {
        "budget": 0.30,
        "type": 0.20,
        "pickups": 0.15,
        "brand": 0.10,
        "title": 0.10,
        "condition": 0.10,
        "year": 0.05,
    }
    DEFAULT_SIMPLE_WEIGHTS = {"budget": 0.55, "title": 0.45}
    ```
  - Функция `load_weights() -> dict`:
    - Читает env-переменные `RANKING_WEIGHT_BUDGET`, `RANKING_WEIGHT_TYPE` и т.д.
    - Если все заданы — возвращает словарь из env
    - Если хотя бы одна не задана — возвращает `DEFAULT_WEIGHTS`
    - Проверка: сумма весов должна быть ≈ 1.0 (±0.01), иначе ValueError
  - Функция `load_simple_weights() -> dict` — аналогично для упрощённой формулы
- Обновить `backend/ranking/ranking.py::calculate_total_score`:
  - Использовать `load_weights()` вместо хардкода
  - Кешировать результат (lru_cache) — чтобы не парсить env на каждый вызов
- Обновить `.env.example` — добавить закомментированные строки с дефолтными весами

### Файлы

- Создать: `backend/ranking/weights.py`
- Изменить: `backend/ranking/ranking.py`
- (Опционально) Изменить: `.env.example` — Сидоров трогать не должен в week-7, можно оставить старый

### Критерий приёмки

- `load_weights()` без env → DEFAULT_WEIGHTS
- `load_weights()` с env → значения из env
- Сумма весов ≠ 1 → ValueError
- Существующие ranking-тесты не сломаны

### Тест: `tests/test_ranking_weights.py`

- load_weights без env → defaults
- load_weights с env → корректные значения
- Неполный набор env → defaults
- Сумма ≠ 1 → ValueError

### Коммит: `feat: make ranking weights configurable via env`

---

## Задача 5 (Docs): обновить RANKING.md

### Что делать

- Полностью переписать `docs/RANKING.md`:
  - **Раздел 1: Обзор** — что делает ранжирование, вход/выход
  - **Раздел 2: Формулы**
    - Упрощённая (budget 55% + title 45%) — когда работает
    - Полная (budget 30% + type 20% + pickups 15% + brand 10% + title 10% + condition 10% + year 5%) — когда работает
  - **Раздел 3: Scoring функции** — что каждая возвращает (`score_budget`, `score_title`, `score_type`, `score_pickups`, `score_brand`, `score_condition`, `score_year_match`)
  - **Раздел 4: Дедупликация** — SequenceMatcher threshold 0.85
  - **Раздел 5: Настройка весов** — env-переменные RANKING_WEIGHT_*
  - **Раздел 6: Debug-лог** — DEBUG_RANKING=true → logs/ranking_debug.jsonl
  - Примеры: 3 сценария с конкретными значениями скоров

### Файлы

- Изменить: `docs/RANKING.md`

### Критерий приёмки

- Документация покрывает все 7 scoring-функций
- Описан debug-режим и настройка весов
- Минимум 3 примера с конкретными скорами

### Коммит: `docs: rewrite RANKING.md with v2, dedup, weights, debug`
