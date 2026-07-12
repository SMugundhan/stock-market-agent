# tests/test_price_agent.py

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function we're testing
from agents.price_agent import _fetch_price_sync, price_agent_node


class TestFetchPriceSync:
    """
    Unit tests for the _fetch_price_sync function.
    Uses mocking to avoid real yFinance calls.
    """

    def test_returns_correct_keys(self, mock_yfinance_data):
        """Verify the function returns all required fields"""

        with patch("agents.price_agent.yf.Ticker") as mock_ticker:
            # patch() temporarily replaces yf.Ticker with a mock
            # "agents.price_agent.yf.Ticker" = the yf.Ticker reference
            # inside price_agent.py specifically

            # Configure what the mock returns
            mock_ticker.return_value.history.return_value = mock_yfinance_data
            # mock_ticker() returns a mock object
            # that mock object's .history() returns our fake DataFrame

            result = _fetch_price_sync("AAPL")

            # Assert all required keys are present
            assert "current_price" in result
            assert "price_change_pct" in result
            assert "rsi" in result

    def test_price_is_float(self, mock_yfinance_data):
        """Price should always be a float, not a string or int"""
        with patch("agents.price_agent.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_yfinance_data
            result = _fetch_price_sync("AAPL")
            assert isinstance(result["current_price"], float)

    def test_rsi_within_valid_range(self, mock_yfinance_data):
        """RSI must always be between 0 and 100 — that's its definition"""
        with patch("agents.price_agent.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_yfinance_data
            result = _fetch_price_sync("AAPL")
            assert 0 <= result["rsi"] <= 100

    def test_empty_dataframe_raises_error(self):
        """If yFinance returns empty data, should raise ValueError"""
        with patch("agents.price_agent.yf.Ticker") as mock_ticker:
            # Return an EMPTY DataFrame — simulates invalid ticker
            mock_ticker.return_value.history.return_value = pd.DataFrame()

            with pytest.raises(ValueError) as exc_info:
                _fetch_price_sync("INVALIDXYZ")

            # exc_info.value contains the actual exception
            assert "No price data" in str(exc_info.value)

    def test_price_change_calculation(self):
        """Verify the price change % formula is correct"""
        # Create data where last price is exactly 10% higher than second-to-last
        closes = [100.0, 110.0]  # 10% increase from 100 to 110
        df = pd.DataFrame({"Close": closes})

        with patch("agents.price_agent.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = df

            result = _fetch_price_sync("TEST")
            # ((110 - 100) / 100) * 100 = 10.0%
            assert result["price_change_pct"] == pytest.approx(10.0, abs=0.01)
            # pytest.approx() allows tiny floating point differences
            # abs=0.01 means ±0.01 is acceptable


class TestPriceAgentNode:
    """
    Integration tests for the price_agent_node function.
    Tests the full node including cache checking logic.
    """

    @pytest.mark.asyncio
    async def test_cache_hit_skips_yfinance(self, base_state):
        """If cache has data, yFinance should never be called"""

        cached_price_data = {
            "current_price": 189.3,
            "price_change_pct": 1.2,
            "rsi": 58.4
        }

        with patch("agents.price_agent.get_cached") as mock_cache:
            with patch("agents.price_agent.yf.Ticker") as mock_yf:
                # Cache returns data
                mock_cache.return_value = cached_price_data

                result = await price_agent_node(base_state)

                # yFinance should NOT have been called
                mock_yf.assert_not_called()
                # assert_not_called() = verify this mock was never invoked

                # Result should match cached data
                assert result["current_price"] == 189.3

    @pytest.mark.asyncio
    async def test_cache_miss_calls_yfinance(self, base_state, mock_yfinance_data):
        """If cache is empty, should call yFinance"""

        with patch("agents.price_agent.get_cached") as mock_cache:
            with patch("agents.price_agent.yf.Ticker") as mock_yf:
                with patch("agents.price_agent.set_cached"):
                    # Cache returns None = cache miss
                    mock_cache.return_value = None
                    mock_yf.return_value.history.return_value = mock_yfinance_data

                    result = await price_agent_node(base_state)

                    # yFinance SHOULD have been called
                    mock_yf.assert_called_once_with("AAPL")
                    # assert_called_once_with() = verify called exactly
                    # once, with exactly these arguments

    @pytest.mark.asyncio
    async def test_yfinance_failure_returns_errors(self, base_state):
        """If yFinance crashes, node should return errors, not raise"""

        with patch("agents.price_agent.get_cached", return_value=None):
            with patch("agents.price_agent.yf.Ticker") as mock_yf:
                # Make yFinance raise an exception
                mock_yf.side_effect = Exception("Yahoo Finance is down")
                # side_effect = when this mock is called, raise this exception

                result = await price_agent_node(base_state)

                # Should NOT raise — should return gracefully
                assert result["current_price"] is None
                assert len(result["error"]) > 0
                assert "Yahoo Finance is down" in result["error"][0]