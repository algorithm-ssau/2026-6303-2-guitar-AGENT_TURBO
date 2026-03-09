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