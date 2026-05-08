"""Acceptance-тесты финального ранжирования перед защитой."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.ranking.ranking import rank_results


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ranking_acceptance.json"


def _load_scenarios() -> list[dict]:
    """Загружает acceptance-сценарии из JSON-фикстуры."""
    with open(FIXTURE_PATH, "r", encoding="utf-8") as fixture:
        data = json.load(fixture)
    return data["scenarios"]


SCENARIOS = _load_scenarios()


def _title_index(results: list[dict], title: str) -> int:
    """Возвращает позицию результата по title."""
    titles = [item.get("title") for item in results]
    return titles.index(title)


def test_fixture_contains_exactly_10_scenarios():
    """Фикстура закрывает ровно 10 acceptance-сценариев из задания."""
    assert len(SCENARIOS) == 10


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[item["name"] for item in SCENARIOS])
def test_ranking_acceptance_scenario(scenario: dict):
    """Проверяет ranking-инварианты без привязки к точным score."""
    raw_results = scenario["results"]
    ranked = rank_results(raw_results, scenario["params"])

    assert len(ranked) <= 5

    if not raw_results:
        assert ranked == []
        return

    assert len(raw_results) >= 4
    assert ranked

    top_title = ranked[0].get("title", "").lower()
    expected_keywords = scenario["expected_top_keywords"]
    assert any(keyword.lower() in top_title for keyword in expected_keywords)

    relevant_title = scenario.get("relevant_title")
    irrelevant_title = scenario.get("irrelevant_title")
    if relevant_title and irrelevant_title:
        assert _title_index(ranked, relevant_title) < _title_index(ranked, irrelevant_title)

    for item in ranked:
        assert "score" not in item
        assert "_score" not in item


def test_missing_optional_fields_do_not_break_ranking():
    """Ranking не зависит от id, image_url, listing_url и других optional-полей."""
    scenario = next(item for item in SCENARIOS if item["name"] == "tele_country")
    minimal_results = [
        {"title": item["title"], "price": item["price"]}
        for item in scenario["results"]
    ]

    ranked = rank_results(minimal_results, scenario["params"])

    assert ranked[0]["title"] == scenario["relevant_title"]
    assert len(ranked) <= 5
