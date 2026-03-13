# TODO — Фокин Евгений
**Модуль:** Консультационный режим
**Неделя:** 15–22 марта 2026
**Ветка:** `feature/fokin/mode-detection`

---

## Из week-01 должно быть готово
- `docs/MODE_DETECTION.md` — правила переключения режимов с примерами
- `docs/CONSULTATION_PROMPT.md` — промпт для консультации + 5–7 примеров вопросов

---

## Задача: реализовать детектор режима и интеграцию

### Шаг 1 — Детектор режима и тесты на него
Реализовать `backend/agent/mode_detector.py`: функция `detect_mode(text) -> str` ("search" / "consultation") по ключевым словам и правилам из `docs/MODE_DETECTION.md`. Написать тесты в `tests/test_mode_detector.py`: все 7 примеров из week-01 возвращают правильный режим.
`feat: implement mode detector with tests`

### Шаг 2 — Интеграция с агентом и тесты веток
Интегрировать с агентом Павлова (`backend/agent/service.py`): `detect_mode` вызывается первым — "consultation" → LLM отвечает напрямую, "search" → идём в поиск. Написать тест на каждую ветку: мок LLM + мок search, проверить что при "consultation" поиск не вызывается, при "search" — вызывается.
`feat: integrate mode detection into agent with branch tests`

### Шаг 3 — Тесты на граничные случаи
Тесты на: смешанный запрос ("хочу купить и расскажи о датчиках"), пустая строка, очень короткий запрос ("гитара?"). Зафиксировать принятые решения по пограничным случаям в `docs/MODE_DETECTION.md`.
`test: add mode detection edge case tests`

---

> LLM: Groq. Согласуй интеграцию с Павловым. Подробнее — [STACK.md](../../STACK.md)
