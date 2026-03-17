# Changelog

## Неделя 0 — 3–8 марта 2026

- Инициализация репозитория, настройка Git Flow и веток (`main`, `feature/*`)
- Составлен PRD: описание продукта, сценарии использования, функциональные и нефункциональные требования ([prd/prd.md](prd/prd.md))
- Составлен PROJECT_PLAN.md: архитектура, этапы разработки, требования по коммитам, распределение модулей по участникам
- Планирование работы на следующую неделю: подготовка TODO-файлов для каждого участника, создание STACK.md

---

## Неделя 1 — 9–15 марта 2026

- **Сальников** — описан дизайн Chat UI ([docs/UI_DESIGN.md](docs/UI_DESIGN.md)), добавлен скелет интерфейса (поле ввода, кнопка, область вывода), написан README фронтенда
- **Павлов** — написан черновик системного промпта агента ([docs/AGENT_PROMPT.md](docs/AGENT_PROMPT.md)), составлена таблица маппинга абстракций в параметры ([docs/MAPPING.md](docs/MAPPING.md)), добавлены тестовые сценарии ([docs/test_scenarios.md](docs/test_scenarios.md))
- **Мергалиев** — описан формат search params и контракт API ([docs/SEARCH_PARAMS.md](docs/SEARCH_PARAMS.md)), добавлены примеры запрос → JSON → ответ
- **Сидоров** — проведено исследование Reverb ([docs/REVERB_RESEARCH.md](docs/REVERB_RESEARCH.md)), добавлена заглушка `search_reverb()` ([backend/search/search_reverb.py](backend/search/search_reverb.py)), подготовлены мок-данные ([tests/mock_reverb.json](tests/mock_reverb.json))
- **Хасанов** — описан алгоритм ранжирования с критериями и весами ([docs/RANKING.md](docs/RANKING.md)), добавлена заглушка `rank_results()` ([backend/ranking/ranking.py](backend/ranking/ranking.py))
- **Фокин** — описаны правила переключения режимов поиск/консультация, написан черновик промпта консультационного режима с примерами вопросов
