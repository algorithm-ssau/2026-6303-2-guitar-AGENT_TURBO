# TODO — Сидоров Артемий

**Неделя 9:** 5–11 мая 2026  
**Ветка:** `feature/sidorov/pipeline-production-w9`

> Production hardening запуска, поиска, ranking и backend stability.  
> Хвост week-08: забрать и закрыть `tasks/week-08/TODO_khasanov.md` по ranking acceptance, потому что Хасанов больше не участвует.  
> Не трогать frontend source, LLM prompts, API docs Мергалиева, release docs Фокина.

---

## Задача: довести полный search/ranking pipeline до production-ready уровня

Нужно добиться, чтобы проект стабильно запускался и проходил backend smoke/acceptance в mock/degraded mode без внешних ключей.

Реальные blockers, которые нужно закрыть:

- backend `pytest` сейчас не проходит collection;
- нет папки `scripts/`, если week-08 runbook-задача ещё не влита;
- ranking acceptance из week-08 остался без владельца;
- search/Reverb fallback должен быть проверен для защиты.

---

## Шаг 1 — закрыть backend collection blockers

### Что делать

Добиться, чтобы `pytest` хотя бы полностью собирал тесты.

Известные текущие проблемы:

1. `tests/test_models.py` импортирует `SearchResult` из `backend.search.models`, но импорт сейчас падает.
2. `tests/test_reverb_retry.py` использует `dict | None`, что падает на Python 3.9.
3. `tests/test_search.py` требует зависимость `responses`, которой нет в текущем окружении/requirements.

Исправлять нужно на уровне причины:

- либо вернуть/экспортировать совместимый `SearchResult`;
- либо обновить тест/код под Python 3.9-compatible typing;
- либо добавить `responses` в `requirements.txt`, если эти тесты реально нужны.

### Файлы

- Изменить: `backend/search/models.py`
- Изменить: `tests/test_models.py`
- Изменить: `tests/test_reverb_retry.py`
- Изменить: `requirements.txt`
- Возможно изменить: `tests/test_search.py`

### Критерий приёмки

- `pytest` не падает на collection;
- проект остаётся совместимым с Python >= 3.9;
- изменения не маскируют реальные failures через skip без причины.

### Проверка

```bash
pytest --collect-only -q
pytest tests/test_models.py tests/test_reverb_retry.py tests/test_search.py -v
```

### Коммит

`fix: restore backend test collection`

---

## Шаг 2 — ranking acceptance после ухода Хасанова

### Что делать

Закрыть week-08 задачу Хасанова:

- создать/доделать `tests/fixtures/ranking_acceptance.json`;
- создать/доделать `tests/test_ranking_acceptance.py`;
- создать/доделать `docs/RANKING_ACCEPTANCE.md`.

Сценарии должны покрывать:

1. `jazz_warm`;
2. `metal_high_output`;
3. `beginner_budget`;
4. `vintage_strat`;
5. `acoustic_campfire`;
6. `bass_funk`;
7. `blues_les_paul`;
8. `tele_country`;
9. `empty_results`;
10. `irrelevant_results`.

Не проверять точные score. Проверять инварианты:

- результат не больше 5;
- empty input возвращает пустой список;
- top-1 содержит ожидаемые слова;
- нерелевантные результаты не поднимаются выше релевантных;
- отсутствующие optional поля не ломают `rank_results`.

### Файлы

- Создать или изменить: `tests/fixtures/ranking_acceptance.json`
- Создать или изменить: `tests/test_ranking_acceptance.py`
- Создать или изменить: `docs/RANKING_ACCEPTANCE.md`

### Критерий приёмки

- ровно 10 acceptance-сценариев;
- каждый non-empty сценарий содержит минимум 4 результата;
- `pytest tests/test_ranking_acceptance.py -v` проходит;
- документ пригоден для защиты.

### Проверка

```bash
pytest tests/test_ranking_acceptance.py -v
```

### Коммит

`test: finalize ranking acceptance coverage`

---

## Шаг 3 — full pipeline launch и search fallback

### Что делать

Проверить и стабилизировать запуск проекта без внешних ключей, используя scripts/runbook из week-08 как baseline:

- `USE_MOCK_REVERB=true`;
- без `GROQ_API_KEY`;
- Reverb timeout;
- Reverb malformed response;
- Reverb empty results;
- search возвращает максимум 5 результатов после ranking;
- backend smoke не требует реального API-ключа.

Не редактировать `docs/RUNBOOK.md` в этом шаге: финальную документацию синхронизирует Фокин. Если при проверке найдены расхождения в runbook, передать Фокину точный список команд/ошибок.

### Файлы

- Изменить: `scripts/check_env.py`
- Изменить: `scripts/smoke_backend.sh`
- Изменить: `backend/search/search_reverb.py`
- Изменить: `backend/search/synonyms.py`
- Возможно изменить: `tests/test_search_reverb.py`
- Возможно изменить: `tests/test_reverb_retry.py`
- Возможно изменить: `tests/test_startup_smoke.py`

### Критерий приёмки

- проект можно проверить без внешних ключей;
- mock/degraded mode не падает;
- search fallback возвращает честный результат или понятное пустое состояние;
- smoke-команды готовы для защиты.

### Проверка

```bash
python scripts/check_env.py
bash scripts/smoke_backend.sh
pytest tests/test_search_reverb.py tests/test_reverb_retry.py tests/test_startup_smoke.py -v
```

### Коммит

`chore: harden launch and search pipeline`
