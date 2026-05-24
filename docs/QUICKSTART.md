# Быстрый старт

Пошаговая инструкция для запуска проекта с нуля.

## Вариант А — Docker (рекомендуется)

### Требования

- Docker
- Docker Compose

### Запуск

```bash
git clone https://github.com/algorithm-ssau/2026-6303-2-guitar-AGENT_TURBO.git
cd 2026-6303-2-guitar-AGENT_TURBO
cp .env.example .env
docker compose up --build
```

После запуска:

- Интерфейс (frontend): `http://localhost`
- Backend API: `http://localhost:8000`

### Настройка `.env` (опционально)

- `GROQ_API_KEY` — для полноценных LLM-ответов (получить на [console.groq.com](https://console.groq.com/)). Без него проект работает в degraded-режиме.
- `USE_MOCK_REVERB=true` — поиск использует локальный набор `tests/mock_reverb.json` (включено по умолчанию).
- `LLM_MODEL` — модель Groq, например `llama-3.3-70b-versatile` или `qwen/qwen3-32b`.

## Вариант Б — локальный запуск (без Docker)

### Требования

- Python 3.10+
- Node.js 18+
- npm

### 1. Клонирование

```bash
git clone https://github.com/algorithm-ssau/2026-6303-2-guitar-AGENT_TURBO.git
cd 2026-6303-2-guitar-AGENT_TURBO
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

### 3. Backend

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Сервер запустится на `http://localhost:8000`.

Проверка:
```bash
curl http://localhost:8000/
# → {"status": "ok"}
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Интерфейс откроется на `http://localhost:5173`.

## Проверка работы

### Health check

```bash
curl http://localhost:8000/api/health/
# → {"status":"ok","checks":{...},"version":"1.0.0"}
```

### Чат

Полный сценарий — через UI на `http://localhost` (Docker) или `http://localhost:5173` (локально):
зарегистрируйся → введи запрос (например "Найди Fender Stratocaster до 1000$").

> Чат-эндпоинты (`POST /api/chat`, `WebSocket /chat`) требуют авторизации.

### Тесты

```bash
pytest tests/ -v
```

## Ожидаемый результат

- На `http://localhost` (Docker) или `http://localhost:5173` (локально) — чат-интерфейс
- Вводите запрос → агент определяет режим (поиск/консультация) → возвращает результат
- Консультация: текстовый ответ о гитарах, звукоснимателях, древесине
- Поиск: список гитар с Reverb (ссылки, цены, изображения)
