# TODO — Сидоров Артемий
**Модуль:** Интеграция с Reverb
**Неделя:** 15–22 марта 2026
**Ветка:** `feature/sidorov/reverb-search`

---

## Из week-01 должно быть готово
- `docs/REVERB_RESEARCH.md` — выводы по API vs парсинг
- `backend/search/search_reverb.py` — заглушка функции
- `tests/mock_reverb.json` — 3–5 реалистичных объявлений

---

## Задача: реализовать поиск на Reverb

### Шаг 1 — Функция с мок-fallback и тест на неё
Реализовать `backend/search/search_reverb.py`: функция `search_reverb(params: dict) -> list[dict]`. Если реальный Reverb недоступен (или переменная окружения `USE_MOCK_REVERB=true`) — возвращать данные из `tests/mock_reverb.json`. Написать тест: при мок-режиме функция возвращает список нужного формата (название, цена, ссылка).
`feat: implement search_reverb with mock fallback and tests`

### Шаг 2 — Реальный запрос к Reverb и тесты с мок-HTTP
Реализовать реальный запрос к Reverb (API или парсинг — по итогам `docs/REVERB_RESEARCH.md`). Написать тест с mocked HTTP (`responses` или `httpretty`): параметры правильно преобразуются в URL/тело запроса, ответ парсится корректно.
`feat: implement reverb search with http mock tests`

### Шаг 3 — Тесты на граничные случаи
Параметризованные тесты в `tests/test_search.py`: 3 разных набора params → проверить фильтрацию результатов, обработку пустого ответа от Reverb, обработку HTTP-ошибки (500, таймаут).
`test: add reverb search edge case tests`

---

> Способ интеграции зафиксировать в [STACK.md](../../STACK.md). Подробнее о стеке — там же.
