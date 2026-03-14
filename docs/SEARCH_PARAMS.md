## 1. JSON-структура (Запрос от агента к скрипту)
Агент анализирует текст пользователя, подбирает конкретные модели, при необходимости переводит бюджет в доллары и передает параметры в виде следующего JSON-объекта:

```json
{
  "search_queries":[
    "Fender Stratocaster White under 1200",
    "Squier Classic Vibe Stratocaster"
  ],
  "price_min": 800,
  "price_max": 1200
}
```

### Описание полей запроса:
* `search_query`:  Массив строк, содержащих конкретные поисковые запросы (бренды, модели, серии, ценовые ограничения в долларах), которые скрипт напрямую введет в поисковый движок Reverb.
* `price_min`: (Опционально) Минимальная цена в долларах (USD). Заполняется, если пользователь указал нижний порог.
* `price_max`: (Опционально) Максимальная цена в долларах (USD). Заполняется, если пользователь указал верхний предел бюджета.


## 2. Формат ответа (Response от скрипта к агенту)
Скрипт возвращает список найденных объявлений в виде массива объектов:

```json
[
  {
    "id": "reverb_listing_id",
    "title": "Fender Player Stratocaster 2023",
    "price": 850,
    "currency": "USD",
    "image_url": "https://reverb.com/image.jpg",
    "listing_url": "https://reverb.com/item/123"
  }
]
```

### Описание полей ответа:
* `id`: уникальный номер объявления на Reverb.
* `title`: название гитары.
* `price`: цена лота.
* `currency`: валюта (всегда "USD").
* `image_url`: прямая ссылка на картинку.
* `listing_url`: ссылка на страницу товара.

## 3. Примеры сценариев (User -> Request -> Response)

### Сценарий 1: Поиск гитары для металла

**1. Запрос пользователя:**  
"Нужна гитара для металла до 45 тысяч рублей, чтобы звук был мощный"

**2. JSON уходит в скрипт:**
```json
{
  "search_queries":[
    "Jackson JS22 Dinky",
    "Ibanez RG Standard"
  ],
  "price_max": 450
}
```

**3. Ответ приходит из скрипта:**
```json
[
  {
    "id": "rev_001",
    "title": "Jackson JS22 Dinky Arch Top - Satin Black",
    "price": 199,
    "currency": "USD",
    "image_url": "https://reverb.com/js22.jpg",
    "listing_url": "https://reverb.com/p/jackson-js22"
  }
]
```
### Сценарий 2: Поиск яркого "стеклянного" звука

**1. Запрос пользователя:**  
"Ищу б/у Gibson Les Paul Studio, бюджет от 800 до 1200 баксов"

**2. JSON уходит в скрипт:**
```json
{
  "search_queries": [
    "Gibson Les Paul Studio",
    "Gibson Les Paul Tribute"
  ],
  "price_min": 800,
  "price_max": 1200
}
```

**3. Ответ приходит из скрипта:**

```json
[
  {
    "id": "rev_002",
    "title": "Gibson Les Paul Studio Faded Cherry 2012",
    "price": 950,
    "currency": "USD",
    "image_url": "https://reverb.com/gibson-lp.jpg",
    "listing_url": "https://reverb.com/p/gibson-les-paul-studio"
  }
]
```