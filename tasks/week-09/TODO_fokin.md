# TODO — Фокин Евгений

**Неделя 9:** 5–11 мая 2026  
**Ветка:** `feature/fokin/final-release-w9`

> Финальная упаковка проекта к сдаче.  
> Не дублировать week-08 release docs: если они уже сделаны, синхронизировать их с фактическим состоянием после production hardening.  
> Не трогать frontend source, backend runtime-код, ranking-код, API examples Мергалиева.

---

## Задача: финальный release readiness по фактическому состоянию проекта

Нужно собрать честный финальный слой документации: как запустить, что показать, что готово, что degraded/pending, какие проверки прошли.

Главный принцип: документация не должна обещать больше, чем реально работает в коде.

---

## Шаг 1 — финальный README и runbook sync

### Что делать

После мержа week-08 и основных production fixes обновить `README.md` и `docs/RUNBOOK.md`.

README должен содержать:

- что делает проект;
- быстрый запуск backend;
- быстрый запуск frontend;
- переменные окружения;
- mock/degraded mode;
- основные команды проверки;
- ссылку на runbook;
- краткое описание команды и вкладов.

RUNBOOK должен содержать:

- запуск с нуля;
- установка backend dependencies;
- установка frontend dependencies;
- запуск без `GROQ_API_KEY`;
- `USE_MOCK_REVERB=true`;
- частые ошибки;
- команды smoke-проверки.

### Файлы

- Изменить: `README.md`
- Изменить: `docs/RUNBOOK.md`

### Критерий приёмки

- по README можно поднять проект без дополнительного объяснения;
- `.env` не предлагается коммитить;
- mock/degraded mode описан честно;
- команды соответствуют реальным scripts/package.json.

### Проверка

```bash
python scripts/check_env.py
bash scripts/smoke_backend.sh
cd frontend && npm run build
```

### Коммит

`docs: finalize readme and runbook`

---

## Шаг 2 — project status и release checklist

### Что делать

Обновить после production hardening:

- `docs/PROJECT_STATUS.md`;
- `docs/RELEASE_CHECKLIST.md`.

`PROJECT_STATUS.md` должен содержать таблицу:

| Модуль | Статус | Как проверить | Владелец | Комментарий |
|--------|--------|---------------|----------|-------------|

Модули:

- Chat UI;
- WebSocket chat;
- LLM interpretation;
- Consultation mode;
- Search params;
- Reverb/mock search;
- Ranking;
- History;
- Metrics;
- Feedback, если есть;
- Docker/Runbook;
- Tests;
- Docs.

Статусы использовать только:

- `ready`;
- `degraded`;
- `pending`.

`RELEASE_CHECKLIST.md` должен быть checklist перед защитой:

- backend стартует;
- frontend стартует;
- `.env.example` актуален;
- `.env` не закоммичен;
- mock search работает;
- consultation работает;
- search работает;
- history работает;
- API docs есть;
- demo script есть;
- smoke-тесты проходят;
- frontend build проходит;
- README не содержит placeholder.

### Файлы

- Изменить: `docs/PROJECT_STATUS.md`
- Изменить: `docs/RELEASE_CHECKLIST.md`

### Критерий приёмки

- статусы соответствуют фактическому состоянию после проверок;
- pending/degraded не скрыты;
- checklist можно реально пройти перед сдачей.

### Проверка

```bash
pytest tests/test_api_examples.py -v
cd frontend && npm run build
```

### Коммит

`docs: finalize project status and release checklist`

---

## Шаг 3 — demo script и PRD closure summary

### Что делать

Обновить demo script из week-08 и добавить финальное PRD closure summary:

- `docs/DEMO_SCRIPT.md`;
- `docs/PRD_CLOSURE.md`.

`DEMO_SCRIPT.md` должен содержать сценарии:

1. search flow:
   - ввод: `Найди стратокастер до 500$`;
   - ожидаемый результат: 3–5 карточек/ссылок.
2. abstract sound flow:
   - ввод: `Хочу тёплый джазовый звук до 1500$`;
   - что показать: интерпретация, результаты, пояснение.
3. consultation flow:
   - ввод: `Чем отличаются P90 от хамбакеров?`;
   - ожидаемый результат: ответ без поиска.
4. history flow:
   - создать/открыть сессию;
   - показать сообщения;
   - удалить сессию или очистить историю.
5. degraded/mock mode:
   - что работает без Groq;
   - что работает с `USE_MOCK_REVERB=true`.

`PRD_CLOSURE.md` должен связать PRD с фактической реализацией:

| PRD требование | Где реализовано | Как проверить | Статус |
|----------------|-----------------|---------------|--------|

### Файлы

- Изменить: `docs/DEMO_SCRIPT.md`
- Создать: `docs/PRD_CLOSURE.md`

### Критерий приёмки

- по demo script можно провести защиту;
- каждый PRD user flow имеет способ проверки;
- все ограничения PRD перечислены честно;
- финальный статус не противоречит `PROJECT_STATUS.md`.

### Проверка

```bash
python scripts/check_env.py
bash scripts/smoke_backend.sh
pytest
cd frontend && npm run build
cd frontend && npm run test -- --run
```

### Коммит

`docs: add final demo and PRD closure`
