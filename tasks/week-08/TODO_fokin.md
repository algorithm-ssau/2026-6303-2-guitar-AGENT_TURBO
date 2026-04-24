# TODO — Фокин Евгений

**Неделя 8:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/fokin/release-package-w8`

> Независимая release-задача по упаковке проекта к сдаче.
> Не трогать frontend source, backend runtime-код, ranking-код, API examples Мергалиева.
> Не трогать `README.md`, потому что он уже запланирован в week-07 у Сидорова.
> Можно обновлять только release-документацию.

---

## Задача: финальный release package для защиты проекта

Нужно подготовить документы, по которым команда сможет показать проект, объяснить статус и пройти финальную проверку.

---

## Шаг 1 — demo script для защиты

### Что делать

Создать `docs/DEMO_SCRIPT.md`.

Документ должен содержать 5 сценариев:

1. `Search flow`
   - ввод: `"Найди стратокастер до 500$"`
   - ожидаемые статусы;
   - ожидаемый результат: 3–5 карточек/ссылок.

2. `Abstract sound flow`
   - ввод: `"Хочу тёплый джазовый звук до 1500$"`
   - что показать: интерпретация, результаты, пояснение.

3. `Consultation flow`
   - ввод: `"Что такое P90?"`
   - ожидаемый результат: ответ без поиска.

4. `History flow`
   - создать/открыть сессию;
   - показать сообщения;
   - удалить сессию или очистить историю.

5. `Degraded/mock mode`
   - что работает без Groq;
   - что работает с `USE_MOCK_REVERB=true`.

Для каждого сценария:

- точный текст ввода;
- что должно появиться;
- что сказать на защите;
- какие риски/ограничения честно упомянуть.

### Файлы

- Создать: `docs/DEMO_SCRIPT.md`

### Критерий приёмки

- по документу можно провести демонстрацию;
- есть минимум 5 сценариев;
- каждый сценарий содержит ввод и ожидаемый результат.

### Коммит

`docs: add defense demo script`

---

## Шаг 2 — project status + release checklist

### Что делать

Создать `docs/PROJECT_STATUS.md`.

Таблица:

| Модуль | Статус | Как проверить | Владелец | Комментарий |
|--------|--------|---------------|----------|-------------|

Модули:

- Chat UI
- WebSocket chat
- LLM interpretation
- Consultation mode
- Search params
- Reverb/mock search
- Ranking
- History
- Metrics
- Feedback, если есть
- Docker/Runbook, если есть
- Tests
- Docs

Статусы использовать только:

- `ready`
- `degraded`
- `pending`

Создать `docs/RELEASE_CHECKLIST.md`.

Чекбоксы:

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
- README не содержит placeholder.

### Файлы

- Создать: `docs/PROJECT_STATUS.md`
- Создать: `docs/RELEASE_CHECKLIST.md`

### Критерий приёмки

- статусы честные, не скрывают degraded/pending;
- checklist можно пройти перед PR/защитой;
- документы не зависят от незавершённых week-06/week-07 PR.

### Коммит

`docs: add project status and release checklist`

---

## Шаг 3 — README release patch + doc test

### Что делать

Создать `docs/README_RELEASE_PATCH.md`.

Документ должен содержать готовый текст для будущего обновления `README.md`, но не должен менять сам `README.md`.

Подготовить разделы:

1. `## Пример запроса и результата`
   - search пример;
   - consultation пример.

2. `## Вклад участников`
   - таблица 6 участников;
   - 1–2 строки вклада каждого.

3. `## Быстрый старт`
   - проверить, что команды актуальны;
   - добавить ссылку на `docs/RUNBOOK.md`, если он есть;
   - если runbook ещё не смержен — ссылку не добавлять.

Создать `tests/test_release_docs.py`.

Тест должен проверить:

- существуют `docs/DEMO_SCRIPT.md`;
- существуют `docs/PROJECT_STATUS.md`;
- существуют `docs/RELEASE_CHECKLIST.md`;
- существует `docs/README_RELEASE_PATCH.md`;
- `docs/README_RELEASE_PATCH.md` не содержит строку `"Будет добавлен после реализации MVP"`;
- `docs/README_RELEASE_PATCH.md` не содержит строку `"Будет дополнен по ходу разработки"`.

### Файлы

- Создать: `docs/README_RELEASE_PATCH.md`
- Создать: `tests/test_release_docs.py`

### Критерий приёмки

- README release patch больше не содержит placeholder-разделы;
- release docs существуют;
- `pytest tests/test_release_docs.py -v` проходит.

### Коммит

`docs: add README release patch and docs checks`
