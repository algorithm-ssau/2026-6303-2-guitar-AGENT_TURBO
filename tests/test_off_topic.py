"""Тесты фильтрации off-topic запросов."""

import unittest
from unittest.mock import patch, MagicMock

from backend.agent.mode_detector import detect_mode, OFF_TOPIC_ANSWER
from backend.agent.service import interpret_query


class TestOffTopicDetection(unittest.TestCase):
    """Тесты: off-topic запросы корректно определяются."""

    def test_programming_queries_are_off_topic(self):
        """Запросы про программирование → off_topic."""
        self.assertEqual(detect_mode("напиши сортировку пузырьком"), "off_topic")
        self.assertEqual(detect_mode("как написать функцию на python"), "off_topic")
        self.assertEqual(detect_mode("javascript массив filter"), "off_topic")

    def test_math_queries_are_off_topic(self):
        """Запросы про математику → off_topic."""
        self.assertEqual(detect_mode("реши уравнение x плюс 2 равно 5"), "off_topic")
        self.assertEqual(detect_mode("посчитай интеграл"), "off_topic")

    def test_everyday_queries_are_off_topic(self):
        """Бытовые запросы → off_topic."""
        self.assertEqual(detect_mode("какая погода завтра"), "off_topic")
        self.assertEqual(detect_mode("рецепт борща"), "off_topic")
        self.assertEqual(detect_mode("последние новости"), "off_topic")

    def test_off_topic_with_previous_search(self):
        """Off-topic срабатывает даже при has_previous_search=True."""
        self.assertEqual(
            detect_mode("напиши код", has_previous_search=True),
            "off_topic",
        )


class TestGuitarQueriesAreNotOffTopic(unittest.TestCase):
    """Тесты: гитарные запросы НЕ определяются как off_topic."""

    def test_search_queries_not_off_topic(self):
        """Поисковые запросы → НЕ off_topic."""
        self.assertEqual(detect_mode("найди стратокастер"), "search")
        self.assertEqual(detect_mode("подбери гитару до 500$"), "search")
        self.assertEqual(detect_mode("покажи варианты телекастеров"), "search")

    def test_consultation_queries_not_off_topic(self):
        """Консультационные запросы → НЕ off_topic."""
        self.assertEqual(detect_mode("что такое хамбакер"), "consultation")
        self.assertEqual(detect_mode("чем отличаются сингл и хамбакер"), "consultation")


class TestOffTopicInInterpretQuery(unittest.TestCase):
    """Тесты: interpret_query с off-topic возвращает ответ без вызова LLM."""

    def test_off_topic_returns_answer_without_llm(self):
        """Off-topic запрос → ответ без вызова LLM."""
        mock_llm = MagicMock()

        result = interpret_query(
            text="напиши сортировку пузырьком",
            llm_client=mock_llm,
        )

        self.assertEqual(result["mode"], "consultation")
        self.assertEqual(result["answer"], OFF_TOPIC_ANSWER)
        # LLM не должен был вызван
        mock_llm.ask.assert_not_called()
        mock_llm.extract_search_params.assert_not_called()

    def test_off_topic_with_session_id(self):
        """Off-topic с session_id → тоже без LLM."""
        mock_llm = MagicMock()

        result = interpret_query(
            text="какая погода",
            llm_client=mock_llm,
            session_id=1,
        )

        self.assertEqual(result["mode"], "consultation")
        self.assertIn("гитара", result["answer"].lower())
        mock_llm.ask.assert_not_called()


class TestOffTopicAnswerConstant(unittest.TestCase):
    """Тесты: константа OFF_TOPIC_ANSWER содержит полезное сообщение."""

    def test_answer_mentions_guitars(self):
        """Ответ упоминает гитары."""
        self.assertIn("гитар", OFF_TOPIC_ANSWER.lower())

    def test_answer_has_example(self):
        """Ответ содержит пример запроса."""
        self.assertIn("подбери", OFF_TOPIC_ANSWER.lower())


if __name__ == "__main__":
    unittest.main()
