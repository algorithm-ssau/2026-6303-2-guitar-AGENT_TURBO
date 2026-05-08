# Ranking acceptance

Документ фиксирует финальную acceptance-проверку модуля ранжирования перед защитой.

## Цель

Проверить, что `rank_results` стабильно выбирает наиболее релевантные объявления для типовых пользовательских сценариев и не ломает pipeline при пустых или неполных данных.

## Сценарии

Фикстура `tests/fixtures/ranking_acceptance.json` содержит 10 сценариев:

1. `jazz_warm` — тёплая semi-hollow гитара для джаза.
2. `metal_high_output` — high-output инструмент для металла.
3. `beginner_budget` — бюджетная гитара для начинающего.
4. `vintage_strat` — винтажный Stratocaster.
5. `acoustic_campfire` — акустика для простого аккомпанемента.
6. `bass_funk` — бас для фанка.
7. `blues_les_paul` — Les Paul/P90 для блюза.
8. `tele_country` — яркий Telecaster для country/twang.
9. `empty_results` — пустой вход.
10. `irrelevant_results` — релевантные результаты должны быть выше нерелевантных.

## Инварианты

Тесты намеренно не проверяют точные значения score, потому что веса и эвристики могут меняться без изменения пользовательского результата.

Проверяются устойчивые свойства:

- на выходе не больше 5 результатов;
- пустой вход возвращает пустой список;
- top-1 содержит ожидаемые ключевые слова;
- релевантный результат стоит выше явно нерелевантного;
- optional-поля вроде `id`, `image_url`, `listing_url` не обязательны для ранжирования;
- служебные поля `score` и `_score` не попадают в ответ.

## Запуск

```bash
pytest tests/test_ranking_acceptance.py -v
```

Для полной проверки backend перед защитой:

```bash
pytest tests/test_ranking.py tests/test_ranking_acceptance.py tests/test_ranking_pipeline.py -v
```
