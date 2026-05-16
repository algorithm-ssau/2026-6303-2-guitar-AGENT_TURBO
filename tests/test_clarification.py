"""Тесты шаблонов clarification без backend NLP inference."""

from backend.agent.clarification import CLARIFICATION_QUESTIONS
from backend.agent.service import _question_from_missing_fields


def test_question_from_router_missing_budget():
    assert _question_from_missing_fields(["budget"]) == CLARIFICATION_QUESTIONS["budget"]


def test_question_from_router_missing_type():
    assert _question_from_missing_fields(["type"]) == CLARIFICATION_QUESTIONS["type"]


def test_question_from_router_missing_both():
    assert _question_from_missing_fields(["budget", "type"]) == CLARIFICATION_QUESTIONS["both"]
