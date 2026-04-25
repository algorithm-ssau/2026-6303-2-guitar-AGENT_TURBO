# Runbook

Этот документ нужен для воспроизводимого запуска проекта перед защитой. Все команды предполагают старт из корня репозитория.

## Быстрый запуск

### 1. Клонирование

```bash
git clone <url-репозитория>
cd 2026-6303-2-guitar-AGENT_TURBO
```

### 2. Проверка окружения

```bash
python3 scripts/check_env.py
```

Если `GROQ_API_KEY` не задан, это не блокирует запуск. Проект сможет работать в degraded/mock режиме.

### 3. Backend

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

Backend будет доступен на `http://localhost:8000`.

### 4. Frontend

Во втором терминале:

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:5173`.

## Mock mode

Для воспроизводимой демонстрации без внешних зависимостей можно использовать локальные мок-данные:

```bash
export USE_MOCK_REVERB=true
```

или через `.env`:

```env
USE_MOCK_REVERB=true
```

Что работает без `GROQ_API_KEY`:

- импорт backend и запуск FastAPI-приложения;
- root endpoint `GET /`;
- startup smoke-тесты;
- режимы, завязанные на mock-данные и локальную инфраструктуру;
- базовая проверка истории и WebSocket-сервера.

Что ухудшается без `GROQ_API_KEY`:

- LLM-ответы работают в degraded-режиме;
- консультационные и search-сценарии могут возвращать упрощённый результат или предупреждение о конфигурации.

## Проверка backend

### 1. Root endpoint

```bash
curl http://localhost:8000/
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

### 2. Chat endpoint

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Что такое хамбакер?"}'
```

Важно: без `GROQ_API_KEY` этот запрос не должен ломать запуск проекта, но содержимое ответа может быть degraded.

### 3. Startup smoke

```bash
bash scripts/smoke_backend.sh
```

Этот скрипт запускает:

```bash
pytest tests/test_startup_smoke.py -v
```

### 4. Дополнительная release-проверка

```bash
python3 scripts/check_env.py
```

## Проверка frontend

```bash
cd frontend
npm install
npm run dev
npm run build
```

Минимальный чек:

- dev-сервер стартует без ошибок;
- страница открывается в браузере;
- `npm run build` завершается успешно.

## Частые ошибки

### Нет pytest

Симптом:

```text
[error] pytest is not available ...
```

Решение:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Нет `GROQ_API_KEY`

Симптом:

```text
[warn] GROQ_API_KEY is not set, degraded mode expected
```

Решение:

- для локальной демонстрации можно продолжать работу;
- для полноценных LLM-ответов добавь ключ в `.env`.

### Занят порт

Симптом:

- backend не стартует на `8000`;
- frontend не стартует на `5173`.

Решение:

- остановить процесс, который уже слушает порт;
- или запустить сервер на другом порту.

### Не установлен npm

Симптом:

```text
npm: command not found
```

Решение:

- установить Node.js и npm;
- затем повторить `npm install` и `npm run dev`.

### Не активирован venv

Симптом:

- Python не видит `fastapi`, `pytest` или другие зависимости;
- `scripts/smoke_backend.sh` падает на проверке `pytest`.

Решение:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
