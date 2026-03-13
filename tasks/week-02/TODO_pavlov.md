# TODO — Павлов Виктор
**Модуль:** LLM-интерпретация запроса
**Неделя:** 15–22 марта 2026
**Ветка:** `feature/pavlov/llm-agent`

---

## Из week-01 должно быть готово
- `docs/AGENT_PROMPT.md` — системный промпт агента
- `docs/MAPPING.md` — таблица маппинга абстракций (тёплый → HH/P90, яркий → single coil и т.д.)
- `docs/test_scenarios.md` — 5–7 тестовых сценариев

---

## Задача: реализовать LLM-агента

### Шаг 1 — Groq-клиент и тесты на него
Создать `backend/agent/llm_client.py`: Groq-клиент, читает `GROQ_API_KEY` и `LLM_MODEL` из `.env`. Написать тест в `tests/test_llm_client.py`: клиент создаётся корректно, бросает ошибку если ключ не задан.
`feat: add groq llm client with tests`

### Шаг 2 — Функция интерпретации запроса и тесты на неё
Реализовать `backend/agent/service.py`: функция `interpret_query(text)` — системный промпт + запрос пользователя → JSON с полями `mode` ("search"/"consultation") и `params` или `answer`. Написать тесты на мок-ответах LLM: правильная структура ответа, обработка невалидного JSON от модели.
`feat: implement llm query interpreter with tests`

### Шаг 3 — Сценарные тесты
Расширить тесты в `tests/test_agent.py`: прогнать 5–7 сценариев из `docs/test_scenarios.md` на мок-LLM — каждый сценарий проверяет что вернулся правильный `mode` и нужные поля.
`test: add agent scenario tests`

---

> LLM: Groq (`llama-3.3-70b-versatile` по умолчанию, модель задаётся через `LLM_MODEL` в `.env`). Подробнее — [STACK.md](../../STACK.md)
