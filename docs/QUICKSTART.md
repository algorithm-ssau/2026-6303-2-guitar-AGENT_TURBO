# Быстрый старт

Пошаговая инструкция для запуска проекта с нуля.

## Требования

- Python 3.10+
- Node.js 18+
- npm

## 1. Клонирование

```bash
git clone <url-репозитория>
cd 2026-6303-2-guitar-AGENT_TURBO
```

## 2. Настройка окружения

```bash
cp .env.example .env
```

Откройте `.env` и заполните:
- `GROQ_API_KEY` — получить на [console.groq.com](https://console.groq.com/) (обязательно)
- `USE_MOCK_REVERB=true` — для работы без реального Reverb API

> Без `GROQ_API_KEY` проект запустится, но LLM-ответы будут в ограниченном режиме.

## 3. Backend

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

## 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Интерфейс откроется на `http://localhost:5173`.

## 5. Проверка работы

### REST API

```bash
# Консультация
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Что такое хамбакер?"}'

# Поиск
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Найди Fender Stratocaster до 1000$"}'
```

### Тесты

```bash
pytest tests/ -v
```

## Ожидаемый результат

- На `http://localhost:5173` — чат-интерфейс
- Вводите запрос → агент определяет режим (поиск/консультация) → возвращает результат
- Консультация: текстовый ответ о гитарах, звукоснимателях, древесине
- Поиск: список гитар с Reverb (ссылки, цены, изображения)
