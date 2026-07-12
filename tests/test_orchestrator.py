# tests/test_orchestrator.py

import pytest
from agents.orchestrator import validate_and_resolve_ticker


class TestTickerValidation:
    """
    Unit tests for ticker validation logic.
    No mocking needed for basic string operations.
    Real yFinance validation is mocked to avoid network calls.
    """

    def test_valid_ticker_passes(self):
        """Known valid tickers should pass validation"""
        with patch_yfinance_valid():
            resolved, error = validate_and_resolve_ticker("AAPL")
            assert error is None
            assert resolved == "AAPL"

    def test_lowercase_ticker_converted_to_uppercase(self):
        """'aapl' should automatically become 'AAPL'"""
        with patch_yfinance_valid():
            resolved, error = validate_and_resolve_ticker("aapl")
            assert resolved == "AAPL"

    def test_company_name_resolves_to_ticker(self):
        """'apple' should resolve to 'AAPL' via name mapping"""
        resolved, error = validate_and_resolve_ticker("apple")
        assert error is None
        assert resolved == "AAPL"

    def test_tesla_name_resolves_to_tsla(self):
        """'tesla' or 'TESLA' should resolve to 'TSLA'"""
        resolved, error = validate_and_resolve_ticker("TESLA")
        assert error is None
        assert resolved == "TSLA"

    def test_empty_ticker_returns_error(self):
        """Empty string should immediately return error"""
        resolved, error = validate_and_resolve_ticker("")
        assert error is not None
        assert resolved == ""

    def test_whitespace_only_returns_error(self):
        """Whitespace-only input should return error after stripping"""
        resolved, error = validate_and_resolve_ticker("   ")
        assert error is not None

    def test_spaces_around_ticker_are_stripped(self):
        """' AAPL ' with surrounding spaces should work"""
        with patch_yfinance_valid():
            resolved, error = validate_and_resolve_ticker(" AAPL ")
            assert error is None
            assert resolved == "AAPL"

    @pytest.mark.parametrize("company_name,expected_ticker", [
        ("apple",     "AAPL"),
        ("tesla",     "TSLA"),
        ("microsoft", "MSFT"),
        ("google",    "GOOGL"),
        ("amazon",    "AMZN"),
    ])
    def test_all_common_names_resolve(self, company_name, expected_ticker):
        """All names in COMMON_NAME_MAP should resolve correctly"""
        resolved, error = validate_and_resolve_ticker(company_name)
        assert error is None
        assert resolved == expected_ticker


# ── Helper context manager ──────────────────────────────
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def patch_yfinance_valid():
    """
    Context manager that makes yFinance validation always succeed.
    Used in tests where we want to test OTHER logic,
    not the yFinance validation itself.
    """
    with patch("agents.orchestrator.ysf.Ticker") as mock:
        mock.return_value.info = {
            "regularMarketPrice": 189.3,
            "longName": "Apple Inc."
        }
        yield mock