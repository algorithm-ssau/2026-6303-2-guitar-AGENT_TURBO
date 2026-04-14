"""Тесты retry с exponential backoff для Reverb API."""

import time
from unittest.mock import Mock, patch, call

import pytest
import requests

from backend.search.search_reverb import _search_reverb_api


def _make_mock_response(status_code: int, json_data: dict | None = None) -> Mock:
    """Создать мок-объект ответа requests."""
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status.return_value = None
    if 400 <= status_code < 500:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"HTTP {status_code}", response=resp,
        )
    return resp


class TestRetrySuccessAfterFailures:
    """Retry: 2 неудачи + 1 успех → успешный результат."""

    @patch("backend.search.search_reverb.time.sleep")
    def test_retry_after_two_timeouts_then_success(self, mock_sleep):
        """2 Timeout + 1 success → успех, 3 вызова requests.get."""
        success_resp = _make_mock_response(
            200,
            {
                "listings": [
                    {
                        "id": "1",
                        "title": "Fender Stratocaster",
                        "price": {"amount": "500", "currency": "USD"},
                        "image_url": "https://example.com/img.jpg",
                        "url": "https://reverb.com/item/1",
                    }
                ]
            },
        )

        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout(),
                requests.exceptions.Timeout(),
                success_resp,
            ]
            # Убираем token чтобы не fallback на mock
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 3
            assert mock_sleep.call_count == 2
            assert len(result) == 1

    @patch("backend.search.search_reverb.time.sleep")
    def test_retry_after_two_502_then_success(self, mock_sleep):
        """2 HTTP 502 + 1 success → успех."""
        error_resp1 = _make_mock_response(502)
        error_resp2 = _make_mock_response(503)
        success_resp = _make_mock_response(
            200,
            {
                "listings": [
                    {
                        "id": "2",
                        "title": "Gibson Les Paul",
                        "price": {"amount": "800", "currency": "USD"},
                        "image_url": "https://example.com/img.jpg",
                        "url": "https://reverb.com/item/2",
                    }
                ]
            },
        )

        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.side_effect = [error_resp1, error_resp2, success_resp]
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 3
            assert len(result) == 1


class TestRetryAllFailures:
    """Retry: 3 неудачи → пустой результат."""

    @patch("backend.search.search_reverb.time.sleep")
    def test_three_timeouts_returns_empty(self, mock_sleep):
        """3 Timeout → пустой список."""
        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout(),
                requests.exceptions.Timeout(),
                requests.exceptions.Timeout(),
            ]
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 3
            assert result == []

    @patch("backend.search.search_reverb.time.sleep")
    def test_three_503_returns_empty(self, mock_sleep):
        """3 HTTP 503 → пустой список."""
        error_resp = _make_mock_response(503)
        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.side_effect = [error_resp, error_resp, error_resp]
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 3
            assert result == []


class TestNoRetryOn4xx:
    """HTTP 4xx — ретрая нет, сразу []."""

    @patch("backend.search.search_reverb.time.sleep")
    def test_404_no_retry(self, mock_sleep):
        """HTTP 404 → 1 вызов requests.get, без ретрая."""
        error_resp = _make_mock_response(404)
        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.return_value = error_resp
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 1
            assert mock_sleep.call_count == 0
            assert result == []

    @patch("backend.search.search_reverb.time.sleep")
    def test_401_no_retry(self, mock_sleep):
        """HTTP 401 → 1 вызов requests.get, без ретрая."""
        error_resp = _make_mock_response(401)
        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.return_value = error_resp
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 1
            assert mock_sleep.call_count == 0
            assert result == []

    @patch("backend.search.search_reverb.time.sleep")
    def test_429_no_retry(self, mock_sleep):
        """HTTP 429 (rate limit) → 1 вызов requests.get, без ретрая."""
        error_resp = _make_mock_response(429)
        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.return_value = error_resp
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 1
            assert mock_sleep.call_count == 0
            assert result == []


class TestConnectionErrorRetry:
    """ConnectionError — ретраится."""

    @patch("backend.search.search_reverb.time.sleep")
    def test_connection_error_retries(self, mock_sleep):
        """ConnectionError → ретраится до 3 раз."""
        with patch("backend.search.search_reverb.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
            with patch.dict("os.environ", {"REVERB_API_TOKEN": "fake-token"}):
                result = _search_reverb_api(["test"])

            assert mock_get.call_count == 3
            assert result == []
