# TODO — Мергалиев Радмир

**Неделя 3:** 23–29 марта 2026
**Ветка:** `feature/mergaliev/param-extractor`

---

## Задача 1 (Backend): модуль извлечения параметров поиска

### Что делать

- Создать `backend/agent/param_extractor.py` с двумя функциями:
  - `extract_params_from_llm_response(llm_response: str) -> dict` — извлекает JSON с параметрами поиска из текстового ответа LLM. Должен обрабатывать:
    - Чистый JSON
    - JSON обёрнутый в \`\`\`json ... \`\`\`
    - JSON с лишним текстом вокруг
    - Невалидный текст → fallback `{"search_queries": [], "price_min": None, "price_max": None}`
    - Нормализация типов: строковые цены "1000" → int 1000
  - `build_search_prompt(user_query: str, mapping_table: str) -> str` — формирует промпт для LLM с инструкцией вернуть JSON, таблицей маппинга из `docs/MAPPING.md` и запросом пользователя

### Файлы

- Создать: `backend/agent/param_extractor.py`

### Критерий приёмки

- Чистый JSON → парсится
- JSON в markdown блоке → парсится
- JSON с текстом вокруг → парсится
- Невалидный текст → fallback без ошибки
- Пустая строка / None → fallback
- price_max строка "1000" → int 1000
- build_search_prompt включает запрос пользователя и маппинг

### Тест: `tests/test_param_extractor.py`

- Минимум 7 тестов: чистый JSON, markdown блок, текст вокруг, невалидный, пустой, конвертация типов, build_search_prompt

### Коммит: `feat: implement param extractor with JSON parsing`

---

## Задача 2 (Frontend): компоненты ошибок и пустого состояния

### Что делать

- Создать `ErrorMessage.tsx`:
  - Props: `message: string`, `onRetry?: () => void`
  - Показывает текст ошибки
  - Если передан onRetry — кнопка "Попробовать снова"
  - Если onRetry не передан — кнопка не рендерится
- Создать `EmptyResults.tsx`:
  - Сообщение "По вашему запросу ничего не найдено"
  - Совет: "Попробуйте расширить бюджет или изменить параметры"
- Интегрировать в `Chat.tsx`:
  - ErrorMessage при ошибке сети
  - EmptyResults при пустом results в search-режиме

### Файлы

- Создать: `frontend/src/features/chat/components/ErrorMessage.tsx`
- Создать: `frontend/src/features/chat/components/EmptyResults.tsx`
- Изменить: `Chat.tsx`, `index.ts`

### Критерий приёмки

- ErrorMessage показывает текст ошибки
- Кнопка retry есть только с onRetry
- EmptyResults показывается при пустых результатах

### Тест: `frontend/src/features/chat/__tests__/ErrorMessage.test.tsx`

- Рендерит текст ошибки
- Кнопка вызывает onRetry
- Без onRetry — кнопка отсутствует

### Коммит: `feat: add error and empty results components`

---

## Задача 3 (Тестирование): валидация извлечённых параметров

### Что делать

- Написать `tests/test_param_validation.py`
- Минимум 3 параметризованных кейса: бюджет, тип гитары, диапазон цен
- Каждый кейс: симуляция ответа LLM → проверка что параметры извлечены корректно

### Файлы

- Создать: `tests/test_param_validation.py`

### Критерий приёмки

- Тесты проходят, покрывают основные пользовательские сценарии

### Коммит: `test: add param extraction validation tests`
