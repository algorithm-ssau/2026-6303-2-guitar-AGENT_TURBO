# Frontend Release QA Checklist

Чеклист для ручной проверки интерфейса перед защитой.

## Таблица состояний

| # | Состояние | Что проверить | Desktop 1440 | Tablet 768 | Mobile 375 |
|---|-----------|---------------|:------------:|:----------:|:----------:|
| 1 | Пустой чат | Welcome-экран с 🎸, заголовок «Добро пожаловать в Guitar Agent!», описание, пример запроса | ✅ | ✅ | ✅ |
| 2 | Welcome / начальное состояние | Заголовок «REVERB AGENT» виден, placeholder читается, кнопка «Отправить» активна | ✅ | ✅ | ✅ |
| 3 | Search-ответ с карточками | Грид карточек, фото (или PHOTO), title, цена, ссылка, номер позиции, бейдж релевантности | ✅ | ✅ | ✅ |
| 4 | Consultation-ответ | Markdown (заголовки, списки, **жирный**), ModeBadge, кнопка «Копировать» | ✅ | ✅ | ✅ |
| 5 | Empty results | Блок «По вашему запросу ничего не найдено» с предложением изменить параметры | ✅ | ✅ | ✅ |
| 6 | Error state | ⚠️, текст ошибки, кнопка «Попробовать снова» | ✅ | ✅ | ✅ |
| 7 | Loading state | Спиннер анимируется, текст «Загрузка чата» и описание | ✅ | ✅ | ✅ |
| 8 | Длинный ответ | `overflow-wrap: break-word` — текст не вылезает, скролл работает, переносы корректны | ✅ | ✅ | ✅ |
| 9 | Длинный title карточки | `WebkitLineClamp: 2`, ellipsis, layout не ломается | ✅ | ✅ | ✅ |
| 10 | Светлая/тёмная тема | Переключение работает, элементы читаемы, нет контрастных багов | 🟡 | 🟡 | 🟡 |
| 11 | Сайдбар | Открытие/закрытие по ☰, скролл сессий, на mobile — оверлей | ✅ | ✅ | ✅ |
| 12 | Мобильный input | Textarea на 375px доступна, кнопка отправки видна, placeholder не обрезан | ✅ | ✅ | ✅ |

**Легенда:** ✅ — готово, 🟡 — требуется проверка в рантайме (зависит от backend-данных)

## Закрытые frontend blockers (Week 9)

| Блокер | Файл | Исправление |
|--------|------|-------------|
| Syntax Error в тесте — невалидный CSS-селектор | `StatusIndicator.test.tsx:34` | Исправлен `querySelector` — убрано некорректное экранирование кавычек |
| Timeout всех тестов useChat — `vi.useFakeTimers()` блокировал `waitFor` | `useChat.test.ts` | Убран `vi.useFakeTimers()` из `beforeEach`; reconnect-тест использует fakeTimers локально |
| `parseQuery` не замокан → ошибка "No parseQuery export" | `useChat.test.ts` | Добавлен `parseQuery: () => Promise.resolve({})` в `vi.mock('../api')` |
| Гонка: `ws.onopen` сбрасывал `setError(null)` после установки ошибки 404 сессии | `useChat.ts:onopen` | Убран `setError(null)` из `ws.onopen` — ошибка уже чистится в `sendMessage` и `selectSession` |
| Длинный текст мог вылезать из бабла сообщения | `Message.tsx` | Добавлен `overflow-wrap: break-word; word-break: break-word` |

## Оставшиеся ограничения

1. **API/Zod контракты** — `api.test.ts` и `types.test.ts` не трогались (contract freeze Мергалиева)
2. **Промежуточный статус consultation** — `StatusIndicator` не используется в production `Chat.tsx` (статус показывается через transient thinking-сообщение)
3. **ChatDemoScenarios** — изолированный QA-инструмент, не подключён к production сборке (импортируется вручную для проверки)
4. **Светлая/тёмная тема** — переключение реализовано, но требуется проверка с реальными цветовыми переменными в рантайме (зависит от `useTheme`)

## Команды проверки

```bash
cd frontend

# Тесты
npm run test -- --run

# Production сборка
npm run build

# Локальный сервер для ручной QA
npm run dev
```

Ручная проверка размеров (DevTools → Device Toolbar):
- Desktop: 1440px
- Tablet: 768px
- Mobile: 375px

Для проверки сценариев импортируйте `ChatDemoScenarios` временно в `App.tsx`.
