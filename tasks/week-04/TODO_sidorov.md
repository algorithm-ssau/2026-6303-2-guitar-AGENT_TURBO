# TODO — Сидоров Артемий

**Неделя 4:** 30 марта – 5 апреля 2026
**Ветка:** `feature/sidorov/reverb-real-api`

> **Независимая задача.** Можно работать параллельно с остальными. Мержить в любой момент.

---

## Задача 1 (Backend): подключение реального Reverb API с авторизацией

### Что делать

- Обновить `backend/search/search_reverb.py` — функция `_search_reverb_api()`:
  - Читать `REVERB_API_TOKEN` из env (Personal Access Token)
  - Добавить заголовки авторизации:
    ```python
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/hal+json",
        "Accept": "application/hal+json",
        "Accept-Version": "3.0",
    }
    ```
  - Обновить URL: `https://api.reverb.com/api/listings/all` (правильный endpoint для поиска)
  - Обработать пагинацию: если результатов мало — сделать до 3 запросов с разными query
  - Добавить дедупликацию по `id` — один и тот же лот не должен появляться дважды
  - **Fallback:** если `REVERB_API_TOKEN` не задан — использовать mock-данные (сохранить существующую логику)
- Обновить `_normalize_reverb_response()`:
  - Обработать реальный формат Reverb API: `_links.photo.href` для картинки, `_links.web.href` для URL
  - Обработать `price.amount` и `price.currency`

### Файлы

- Изменить: `backend/search/search_reverb.py`

### Критерий приёмки

- С `REVERB_API_TOKEN` → реальные результаты с Reverb
- Без `REVERB_API_TOKEN` → mock-данные (как раньше)
- Дубликаты отфильтрованы
- Нормализация: все результаты содержат id, title, price, currency, image_url, listing_url

### Тест: `tests/test_reverb_real.py`

- Mock requests.get → проверить что headers содержат Authorization
- Mock реальный ответ Reverb API → нормализация корректна
- Без токена → fallback на mock

### Коммит: `feat: add Reverb API auth and real search integration`

---

## Задача 2 (Frontend): улучшение GuitarCard — картинка и fallback

### Что делать

- Обновить `frontend/src/features/chat/components/GuitarCard.tsx`:
  - Если `imageUrl` отсутствует или загрузка не удалась — показать placeholder (текст "Нет фото" на сером фоне)
  - Обработка ошибки загрузки изображения: `onError` → показать placeholder
  - Сделать картинку кликабельной → открывает `listingUrl` в новой вкладке
  - Форматирование цены: "$499" вместо "499 USD"
  - Добавить hover-эффект на всю карточку

### Файлы

- Изменить: `frontend/src/features/chat/components/GuitarCard.tsx`

### Критерий приёмки

- Нет imageUrl → серый placeholder "Нет фото"
- Ошибка загрузки → placeholder
- Клик по картинке → открытие Reverb в новой вкладке
- Цена отображается как "$499" (не "499 USD")

### Тест: `frontend/src/features/chat/__tests__/GuitarCard.test.tsx`

- Обновить: без imageUrl → placeholder рендерится
- onError → placeholder рендерится
- Ссылка имеет target="_blank"

### Коммит: `feat: improve GuitarCard with image fallback and formatting`

---

## Задача 3 (Тестирование): тесты реального API Reverb с мок-ответами

### Что делать

- Написать `tests/test_reverb_api_format.py`:
  - Подготовить JSON-фикстуру с реальным форматом ответа Reverb API:
    ```json
    {
      "listings": [
        {
          "id": 123,
          "title": "Fender Stratocaster 2020",
          "price": {"amount": "499.00", "currency": "USD"},
          "_links": {
            "photo": {"href": "https://images.reverb.com/..."},
            "web": {"href": "https://reverb.com/item/123"}
          }
        }
      ]
    }
    ```
  - Мокнуть requests.get → вернуть фикстуру
  - Проверить нормализацию: price.amount "499.00" → число 499
  - Проверить дедупликацию: два одинаковых id → один результат
  - Проверить фильтрацию по цене после нормализации

### Файлы

- Создать: `tests/test_reverb_api_format.py`

### Критерий приёмки

- Тесты используют формат, максимально близкий к реальному Reverb API
- Нормализация корректна для всех полей

### Коммит: `test: add Reverb API response format tests`
