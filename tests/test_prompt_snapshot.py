"""Snapshot-регрессия качества промптов.

Загружает 15 канонических запросов из fixtures/llm_snapshots.json,
мокает LLM и проверяет, что extract_params_from_llm_response корректно
парсит ожидаемые ответы. Работает без GROQ_API_KEY.

Порог: минимум 13 из 15 должны пройти.
"""

import json
import os
import pytest
from backend.agent.param_extractor import extract_params_from_llm_response

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "llm_snapshots.json")

def load_snapshots():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

SNAPSHOTS = load_snapshots()


def _check_snapshot(snapshot):
    """Проверяет один snapshot. Возвращает True если прошёл, False если нет."""
    llm_response = json.dumps(snapshot["llm_response"])
    result = extract_params_from_llm_response(llm_response)
    expect = snapshot["expect"]

    # Проверка min_queries
    if "min_queries" in expect:
        if len(result.get("search_queries", [])) < expect["min_queries"]:
            return False

    # Проверка price_max
    if "has_price_max" in expect:
        expected_price = expect["has_price_max"]
        actual_price = result.get("price_max")
        if expected_price is None:
            if actual_price is not None:
                return False
        else:
            if actual_price != expected_price:
                return False

    # Проверка type
    if "has_type" in expect:
        actual_type = result.get("type")
        if actual_type != expect["has_type"]:
            return False

    return True


@pytest.mark.parametrize("snapshot", SNAPSHOTS, ids=[s["query"] for s in SNAPSHOTS])
def test_snapshot_individual(snapshot):
    """Проверяет каждый snapshot индивидуально."""
    llm_response = json.dumps(snapshot["llm_response"])
    result = extract_params_from_llm_response(llm_response)
    expect = snapshot["expect"]

    if "min_queries" in expect:
        assert len(result.get("search_queries", [])) >= expect["min_queries"], \
            f"Ожидалось >= {expect['min_queries']} queries, получено {len(result.get('search_queries', []))}"

    if "has_price_max" in expect:
        expected_price = expect["has_price_max"]
        actual_price = result.get("price_max")
        if expected_price is None:
            assert actual_price is None, f"Ожидалось price_max=None, получено {actual_price}"
        else:
            assert actual_price == expected_price, \
                f"Ожидалось price_max={expected_price}, получено {actual_price}"

    if "has_type" in expect:
        assert result.get("type") == expect["has_type"], \
            f"Ожидалось type={expect['has_type']}, получено {result.get('type')}"


def test_snapshot_threshold():
    """Проверяет что минимум 13 из 15 snapshots проходят."""
    passed = sum(1 for s in SNAPSHOTS if _check_snapshot(s))
    total = len(SNAPSHOTS)
    assert passed >= 13, (
        f"Только {passed}/{total} snapshot-тестов прошло. "
        f"Минимальный порог: 13/{total}."
    )
