# API Contract — Chat Endpoint

## POST /api/chat

Эндпоинт для отправки сообщения пользователя и получения ответа от ИИ-агента.

### Request

```json
{
  "message": "string"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `message` | string | Текст сообщения пользователя (не пустой) |

### Response (успех)

```json
{
  "reply": "string",
  "results": [
    {
      "title": "string",
      "url": "string",
      "price": "number"
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `reply` | string | Текстовый ответ агента |
| `results` | array | Опционально: результаты поиска гитар |
| `results[].title` | string | Название инструмента |
| `results[].url` | string | Ссылка на Reverb |
| `results[].price` | number | Цена (опционально) |

### Response (ошибка)

```json
{
  "detail": "string"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `detail` | string | Сообщение об ошибке |

### Примеры

**Запрос:**
```json
{
  "message": "Хочу гитару с тёплым звуком, бюджет до $500"
}
```

**Ответ:**
```json
{
  "reply": "Для тёплого звука рекомендую гитары с хамбакерами. Вот несколько вариантов:",
  "results": [
    {
      "title": "Epiphone Les Paul Standard",
      "url": "https://reverb.com/item/123456",
      "price": 450
    }
  ]
}
```
