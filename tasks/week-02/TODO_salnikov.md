# TODO — Сальников Илья
**Модуль:** Chat UI
**Неделя:** 15–22 марта 2026
**Ветка:** `feature/salnikov/chat-ui-connect`

---

## Из week-01 должно быть готово
- `docs/UI_DESIGN.md` — описание интерфейса
- Статичный скелет чата: поле ввода, кнопка, область вывода
- `frontend/README.md`

---

## Задача: подключить Chat UI к бэкенду

### Шаг 1 — Zod-схемы и тесты на валидацию
Добавь Zod-схемы в `frontend/src/features/chat/types.ts` по контракту из `docs/API_CONTRACT.md`: схема запроса и схема ответа. Написать тесты в `frontend/src/features/chat/__tests__/types.test.ts` (Vitest): валидный объект проходит схему, невалидный — бросает ошибку.
`feat: add chat api zod schemas with validation tests`

### Шаг 2 — Функция отправки запроса и тесты на неё
Реализовать `frontend/src/features/chat/api.ts` — функция `sendMessage(text)` с `fetch` на `/api/chat`, ответ валидируется через Zod-схему из шага 1. Написать тесты с мок-fetch: правильный URL, метод, тело запроса, обработка ошибок сети, невалидный ответ от сервера.
`feat: add chat api call with tests`

### Шаг 3 — Подключить в компонент и тесты компонента
Подключить в компонент: отправка → "загрузка..." → ответ или ошибка. Написать тесты компонента (React Testing Library): рендер, ввод текста, клик, отображение каждого состояния.
`feat: connect chat ui to backend with component tests`

---

> Стек: Vite + React + TypeScript, Zod, Vitest, React Testing Library. Подробнее — [STACK.md](../../STACK.md)
