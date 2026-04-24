# TODO — Хасанов Дамир

**Неделя 8:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/khasanov/ranking-acceptance-w8`

> Независимая release-задача по acceptance-проверке ранжирования.
> Не трогать frontend, LLM, search_reverb, Docker, README.
> Тесты не должны зависеть от week-07 debug/weights/dedup: если этих функций нет, проверять базовые инварианты `rank_results`.

---

## Задача: ranking acceptance suite для финальных сценариев

Нужно создать набор сценариев, который показывает, что ранжирование выдаёт релевантный топ для типовых запросов из PRD.

---

## Шаг 1 — acceptance fixture

### Что делать

Создать `tests/fixtures/ranking_acceptance.json`.

Файл должен содержать 10 сценариев.

Обязательные сценарии:

1. `jazz_warm`
2. `metal_high_output`
3. `beginner_budget`
4. `vintage_strat`
5. `acoustic_campfire`
6. `bass_funk`
7. `blues_les_paul`
8. `tele_country`
9. `empty_results`
10. `irrelevant_results`

Формат сценария:

```json
{
  "id": "metal_high_output",
  "params": {
    "style": "metal",
    "price_max": 1200
  },
  "results": [
    {
      "id": "r1",
      "title": "Ibanez RG Standard",
      "price": 899,
      "currency": "USD",
      "listing_url": "https://reverb.com/item/ibanez-rg"
    }
  ],
  "expect": {
    "max_results": 5,
    "top_title_contains_any": ["Ibanez", "Jackson", "ESP"]
  }
}
```

### Файлы

- Создать: `tests/fixtures/ranking_acceptance.json`

### Критерий приёмки

- JSON валиден;
- ровно 10 сценариев;
- есть empty и irrelevant кейсы;
- каждый не-empty сценарий содержит минимум 4 результата.

### Коммит

`test: add ranking acceptance fixtures`

---

## Шаг 2 — acceptance tests

### Что делать

Создать `tests/test_ranking_acceptance.py`.

Тест должен:

- загрузить `ranking_acceptance.json`;
- вызвать `rank_results(results, params)`;
- проверить:
  - результат не больше 5;
  - empty input возвращает пустой список;
  - для обычных сценариев top-1 содержит ожидаемые слова из `top_title_contains_any`;
  - нерелевантные результаты не поднимаются выше релевантных, если fixture это задаёт;
  - функция не падает на отсутствующих optional-полях.

Не проверять точные score, чтобы тесты не были хрупкими.

### Файлы

- Создать: `tests/test_ranking_acceptance.py`

### Критерий приёмки

- `pytest tests/test_ranking_acceptance.py -v` проходит;
- тесты устойчивы к небольшим изменениям весов;
- не требуют внешних API.

### Коммит

`test: add ranking acceptance checks`

---

## Шаг 3 — документация acceptance-критериев

### Что делать

Создать `docs/RANKING_ACCEPTANCE.md`.

Разделы:

1. `## Зачем нужен acceptance suite`
2. `## Покрытые сценарии`
3. `## Проверяемые инварианты`
   - top <= 5;
   - попадание в бюджет;
   - соответствие стилю;
   - устойчивость к пустым результатам;
   - отсутствие падений на неполных данных.
4. `## Что не проверяется`
   - точные score;
   - реальные данные Reverb;
   - LLM extraction.

### Файлы

- Создать: `docs/RANKING_ACCEPTANCE.md`

### Критерий приёмки

- документ объясняет 10 сценариев;
- можно использовать на защите для объяснения ranking quality.

### Коммит

`docs: add ranking acceptance documentation`
