# TODO — Павлов Виктор

**Неделя 9:** 5–11 мая 2026  
**Ветка:** `feature/pavlov/agent-production-w9`

> Production hardening поведения агента по PRD.  
> Не дублировать week-08 LLM golden scenarios: использовать их как baseline и исправлять только реальные провалы.  
> Не трогать frontend source, ranking, search_reverb, Docker, README.

---

## Задача: довести agent behavior до полного покрытия PRD

Нужно проверить, что агент стабильно закрывает все пользовательские сценарии PRD и не нарушает ограничения:

- не выдумывает цены;
- не выдумывает ссылки;
- не проверяет продавцов;
- не обсуждает доставку/оплату как часть подбора;
- использует search только для search-запросов;
- отвечает консультационно без поиска, когда запрос консультационный.

---

## Шаг 1 — PRD behavior matrix

### Что делать

Создать или обновить документ `docs/PRD_BEHAVIOR_MATRIX.md`.

Матрица должна связать PRD-требования с текущими проверками:

| PRD пункт | Сценарий | Ожидаемый режим | Где проверяется | Статус |
|-----------|----------|-----------------|-----------------|--------|

Обязательные сценарии:

1. тёплый джазовый звук до 1000;
2. Telecaster до 800 долларов;
3. P90 vs humbucker;
4. beginner guitar;
5. metal high output;
6. vintage / 70-е;
7. бюджет в рублях;
8. противоречивый запрос;
9. слишком общий запрос;
10. off-topic.

Статусы использовать только:

- `ready`;
- `degraded`;
- `pending`.

### Файлы

- Создать или изменить: `docs/PRD_BEHAVIOR_MATRIX.md`
- Возможно изменить: `docs/LLM_RELEASE_BEHAVIOR.md`

### Критерий приёмки

- каждый PRD user flow имеет минимум один сценарий;
- каждый MVP-пункт имеет статус;
- не осталось требований PRD без владельца или проверки.

### Проверка

```bash
pytest tests/test_mode_detector.py tests/test_mode_detector_edge_cases.py tests/test_prompt_quality.py -v
```

### Коммит

`docs: map agent behavior to PRD`

---

## Шаг 2 — исправить реальные провалы режимов и промптов

### Что делать

Прогнать week-08 golden scenarios и существующие mode/prompt tests. Исправлять только реальные провалы:

- search-запрос ошибочно определяется как consultation/off-topic;
- consultation ошибочно запускает search;
- clarification не срабатывает на слишком общий запрос;
- off-topic получает гитарный ответ;
- противоречивый запрос не получает уточнение;
- рубли/доллары не попадают в нормализованные параметры.

Если поведение зависит от реального LLM, добавить deterministic fallback/mock path для проверки без `GROQ_API_KEY`.

### Файлы

- Изменить: `backend/agent/mode_detector.py`
- Изменить: `backend/agent/param_extractor.py`
- Изменить: `backend/agent/service.py`
- Возможно изменить: `docs/AGENT_PROMPT.md`
- Возможно изменить: `docs/CONSULTATION_PROMPT.md`
- Возможно изменить: `tests/test_mode_detector*.py`
- Возможно изменить: `tests/test_prompt_quality.py`
- Возможно изменить: `tests/test_llm_scenarios.py`

### Критерий приёмки

- search / consultation / clarification / off-topic разделяются стабильно;
- проверки работают без `GROQ_API_KEY`;
- антигаллюцинационные правила отражены в prompt/docs;
- изменения не ломают API-контракт.

### Проверка

```bash
pytest tests/test_mode_detector.py tests/test_mode_detector_edge_cases.py tests/test_prompt_quality.py tests/test_llm_scenarios.py -v
```

### Коммит

`fix: stabilize agent behavior for PRD flows`

---

## Шаг 3 — финальный anti-hallucination и degraded behavior pass

### Что делать

Проверить и задокументировать поведение без внешних ключей:

- без `GROQ_API_KEY`;
- с `USE_MOCK_REVERB=true`;
- когда LLM недоступен;
- когда запрос требует консультации;
- когда поиск вернул пусто.

Обновить `docs/LLM_RELEASE_BEHAVIOR.md` так, чтобы на защите было понятно:

- какие режимы есть;
- что агент не должен делать;
- как работает degraded mode;
- какие ограничения честно остаются.

### Файлы

- Изменить: `docs/LLM_RELEASE_BEHAVIOR.md`
- Возможно изменить: `tests/test_graceful_degradation.py`
- Возможно изменить: `tests/test_pipeline.py`

### Критерий приёмки

- без `GROQ_API_KEY` проект не падает на базовых сценариях;
- consultation не требует поиска;
- search в degraded/mock mode возвращает честный ответ или понятное пустое состояние;
- ограничения не скрыты.

### Проверка

```bash
pytest tests/test_graceful_degradation.py tests/test_pipeline.py -v
```

### Коммит

`docs: finalize agent production behavior`
