# TODO — Сидоров Артемий

**Неделя 8:** 28 апреля – 4 мая 2026  
**Ветка:** `feature/sidorov/reproducible-launch-w8`

> Независимая release-задача по запуску проекта с нуля.
> Не трогать frontend source, ranking, LLM prompts, API docs Мергалиева.
> Скрипты должны работать без `GROQ_API_KEY`.

---

## Задача: воспроизводимый запуск проекта перед защитой

Нужно добавить скрипты и runbook, чтобы любой участник мог проверить окружение и запустить проект.

---

## Шаг 1 — environment check script

### Что делать

Создать `scripts/check_env.py`.

Скрипт должен проверять:

- версия Python >= 3.9;
- существует `requirements.txt`;
- существует `.env.example`;
- существует папка `backend`;
- можно импортировать `backend.main`;
- переменная `USE_MOCK_REVERB` либо задана, либо будет использоваться default;
- если `GROQ_API_KEY` не задан — вывести warning, но не падать.

Вывод должен быть человекочитаемый:

```text
[ok] Python version: ...
[ok] requirements.txt found
[warn] GROQ_API_KEY is not set, degraded mode expected
```

### Файлы

- Создать: `scripts/check_env.py`

### Критерий приёмки

- `python scripts/check_env.py` завершается с кодом 0 в обычном окружении;
- без `GROQ_API_KEY` не падает;
- если нет критичного файла, завершается с кодом 1.

### Коммит

`chore: add release environment check`

---

## Шаг 2 — backend smoke script

### Что делать

Создать `scripts/smoke_backend.sh`.

Скрипт должен:

- запускаться из корня проекта;
- проверять наличие `venv/bin/python`;
- если venv есть — запускать:
  ```bash
  venv/bin/python -m pytest tests/test_startup_smoke.py -v
  ```
- если venv нет — пробовать:
  ```bash
  python -m pytest tests/test_startup_smoke.py -v
  ```
- при отсутствии pytest выводить понятное сообщение;
- не требовать `GROQ_API_KEY`.

### Файлы

- Создать: `scripts/smoke_backend.sh`

### Критерий приёмки

- скрипт можно выполнить через `bash scripts/smoke_backend.sh`;
- он запускает startup smoke;
- ошибка окружения объясняется понятным текстом.

### Коммит

`test: add backend startup smoke script`

---

## Шаг 3 — release runbook

### Что делать

Создать `docs/RUNBOOK.md`.

Разделы:

1. `## Быстрый запуск`
   - clone;
   - venv;
   - pip install;
   - `.env`;
   - backend;
   - frontend.

2. `## Mock mode`
   - как включить `USE_MOCK_REVERB=true`;
   - что работает без Groq.

3. `## Проверка backend`
   - `/`;
   - `/api/chat`;
   - startup smoke.

4. `## Проверка frontend`
   - `npm install`;
   - `npm run dev`;
   - `npm run build`.

5. `## Частые ошибки`
   - нет pytest;
   - нет Groq key;
   - занят порт;
   - не установлен npm;
   - не активирован venv.

### Файлы

- Создать: `docs/RUNBOOK.md`

### Критерий приёмки

- по документу можно поднять проект с нуля;
- есть команды для backend и frontend;
- описан degraded/mock mode.

### Коммит

`docs: add release runbook`
