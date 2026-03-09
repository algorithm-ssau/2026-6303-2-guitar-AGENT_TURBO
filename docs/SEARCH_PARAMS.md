## 1. JSON-структура (Запрос от агента к скрипту)
Агент анализирует текст пользователя и передает параметры в виде следующего JSON-объекта:

```json
{
  "instrument_type": "electric_guitar",
  "budget_min": 0,
  "budget_max": 50000,
  "tonality_keywords": ["bright", "stratocaster"],
  "pickup_config": ["single-coil"]
}
```

### Описание полей запроса:
* `instrument_type`: тип гитары (например, "electric_guitar", "acoustic_guitar").
* `budget_min` / `budget_max`: диапазон цен для поиска.
* `tonality_keywords`: массив слов, описывающих характер звука (используется для ранжирования).
* `pickup_config`: технические параметры звукоснимателей (извлекаются из запроса).


## 2. Формат ответа (Response от скрипта к агенту)
Скрипт возвращает список найденных объявлений в виде массива объектов:

```json
[
  {
    "id": "reverb_listing_id",
    "title": "Fender Stratocaster Player Series 2023",
    "price": 45000,
    "currency": "RUB",
    "image_url": "https://reverb.com/image.jpg",
    "listing_url": "https://reverb.com/item/123"
  }
]
```

### Описание полей ответа:
* `id`: уникальный номер объявления на Reverb.
* `title`: название гитары.
* `price`: цена лота.
* `currency`: валюта.
* `image_url`: прямая ссылка на картинку.
* `listing_url`: ссылка на страницу товара.

## 3. Примеры сценариев (User -> Request -> Response)

### Сценарий 1: Поиск гитары для металла

**1. Запрос пользователя:**  
"Нужна гитара для металла до 45 тысяч рублей, чтобы звук был мощный"

**2. JSON уходит в скрипт:**
```json
{
  "instrument_type": "electric_guitar",
  "budget_max": 45000,
  "tonality_keywords": ["metal", "heavy", "high-gain"],
  "pickup_config": ["humbucker"]
}
```

**3. Ответ приходит из скрипта:**
```json
[
  {
    "id": "rev_001",
    "title": "Jackson JS22 Dinky - Satin Black",
    "price": 32000,
    "currency": "RUB",
    "image_url": "https://reverb.com/js22.jpg",
    "listing_url": "https://reverb.com/p/jackson-js22"
  }
]
```
### Сценарий 2: Поиск яркого "стеклянного" звука

**1. Запрос пользователя:**  
"Нужен классический яркий звук стратокастера, бюджет 70к"

**2. JSON уходит в скрипт:**
```json
{
  "instrument_type": "electric_guitar",
  "budget_max": 70000,
  "tonality_keywords": ["bright", "twang", "stratocaster"],
  "pickup_config": ["single-coil"]
}
```

**3. Ответ приходит из скрипта:**

```json
[
  {
    "id": "rev_002",
    "title": "Fender Player Stratocaster 2022",
    "price": 68500,
    "currency": "RUB",
    "image_url": "https://reverb.com/fender-strat.jpg",
    "listing_url": "https://reverb.com/p/fender-strat-player"
  }
]
```