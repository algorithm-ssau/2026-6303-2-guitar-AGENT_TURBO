# TODO — Павлов Виктор

**Неделя 3:** 23–29 марта 2026
**Ветка:** `feature/pavlov/llm-client`

---

## Задача 1 (Backend): Groq LLM клиент

### Что делать

- Создать `backend/agent/llm_client.py` — класс `LLMClient`:
  - В конструкторе: читать `GROQ_API_KEY` из env, создавать `Groq` клиент, читать `LLM_MODEL` (дефолт `llama-3.3-70b-versatile`)
  - При отсутствии ключа — бросать `ValueError`
  - Метод `ask(user_message, system_prompt)` — отправляет запрос к Groq, возвращает текст ответа
  - Метод `extract_search_params(user_message)` — формирует промпт с маппингом из `docs/MAPPING.md`, просит LLM вернуть JSON, парсит результат через `param_extractor` (Мергалиева)
  - При ошибке LLM — не падает, возвращает fallback dict

### Файлы

- Создать: `backend/agent/llm_client.py`

### Критерий приёмки

- Без GROQ_API_KEY → ValueError
- `ask()` с замоканным groq.Client → строка
- `extract_search_params()` с замоканным ответом → dict с search_queries, price_min, price_max
- Невалидный JSON от LLM → fallback без падения

### Тест: `tests/test_llm_client.py`

- 4 теста: отсутствие ключа, ask(), extract с валидным JSON, extract с невалидным JSON

### Коммит: `feat: implement Groq LLM client with param extraction`

---

## Задача 2 (Frontend): компоненты отображения результатов

### Что делать

- Создать `GuitarCard.tsx` — карточка гитары:
  - Принимает: title, price, currency, imageUrl, listingUrl
  - Отображает: картинку, название, цену
  - Ссылка открывается в новой вкладке (`target="_blank"`)
- Создать `ResultsList.tsx` — список карточек:
  - Принимает массив GuitarResult[]
  - Рендерит GuitarCard для каждого элемента
  - Заголовок "Найдено N вариантов"
- Расширить тип `Message` в `types.ts` — добавить опциональное поле `results`
- Обновить `Message.tsx` — если есть results, рендерить ResultsList

### Файлы

- Создать: `frontend/src/features/chat/components/GuitarCard.tsx`
- Создать: `frontend/src/features/chat/components/ResultsList.tsx`
- Изменить: `types.ts`, `Message.tsx`, `index.ts`

### Критерий приёмки

- GuitarCard показывает картинку, название, цену
- Ссылка ведёт на listingUrl в новой вкладке
- Message с results → ResultsList, без results → текст

### Тест: `frontend/src/features/chat/__tests__/GuitarCard.test.tsx`

- Рендерит название и цену
- Ссылка имеет target="_blank"

### Коммит: `feat: add GuitarCard and ResultsList components`

---

## Задача 3 (Тестирование): сценарные тесты LLM

### Что делать

- Написать `tests/test_llm_scenarios.py`
- 7 параметризованных сценариев из `docs/test_scenarios.md`
- Каждый сценарий: вызов `interpret_query()` с mock LLM и mock search
- Проверка: правильный mode + корректная структура ответа

### Файлы

- Создать: `tests/test_llm_scenarios.py`

### Критерий приёмки

- 7 тестов проходят с `pytest.mark.parametrize`

### Коммит: `test: add parametrized LLM scenario tests`
