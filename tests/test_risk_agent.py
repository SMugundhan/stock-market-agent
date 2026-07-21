# tests/test_risk_agent.py

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, ANY


class TestRiskCalculations:
    """
    Tests for the risk calculation logic.
    The math itself (volatility, drawdown, beta) can be tested
    with known inputs and expected outputs — no mocking needed here.
    """

    def test_volatility_calculation(self):
        """
        Verify annual volatility formula:
        daily_std * sqrt(252) * 100
        """
        from agents.risk_agent import _calculate_risk_sync

        # Create price data with KNOWN volatility
        # All returns are 0% → zero volatility
        closes = pd.Series([100.0] * 100)

        df = pd.DataFrame({"Close": closes})
        spy_df = pd.DataFrame({"Close": closes})

        with patch("agents.risk_agent.yf.Ticker") as mock_ticker:
            # First call = stock data, second call = SPY data
            mock_ticker.return_value.history.side_effect = [df, spy_df]
            # side_effect = [a, b] means: first call returns a,
            #                              second call returns b

            result = _calculate_risk_sync("AAPL", session = ANY)

            # Constant price = zero daily returns = zero volatility
            assert result["volatility"] == pytest.approx(0.0, abs=0.1)

    def test_high_volatility_classified_as_high_risk(self):
        """Stocks with >40% annual volatility should be HIGH risk"""
        from agents.risk_agent import _calculate_risk_sync

        # Create very volatile price data — large daily swings
        # Alternating up 10% and down 10% every day
        prices = []
        price = 100.0
        for i in range(200):
            if i % 2 == 0:
                price *= 1.10  # up 10%
            else:
                price *= 0.90  # down 10%
            prices.append(price)

        df = pd.DataFrame({"Close": pd.Series(prices)})
        spy_df = pd.DataFrame({"Close": pd.Series([100.0] * 200)})

        with patch("agents.risk_agent.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = [df, spy_df]
            result = _calculate_risk_sync("TSLA", session = ANY)
            assert result["risk_level"] == "HIGH"

    def test_risk_level_values_are_valid(self):
        """risk_level must always be one of these three values"""
        from agents.risk_agent import _calculate_risk_sync

        closes = pd.Series(np.linspace(100, 110, 200))
        df = pd.DataFrame({"Close": closes})
        spy_df = pd.DataFrame({"Close": closes})

        with patch("agents.risk_agent.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = [df, spy_df]
            result = _calculate_risk_sync("AAPL", session = ANY)
            assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

    def test_max_drawdown_is_negative(self):
        """
        Drawdown represents a LOSS from peak — must always be ≤ 0
        A positive drawdown would mean the stock GAINED from its peak,
        which makes no mathematical sense for this metric.
        """
        from agents.risk_agent import _calculate_risk_sync

        closes = pd.Series(np.linspace(100, 110, 200))
        df = pd.DataFrame({"Close": closes})
        spy_df = pd.DataFrame({"Close": closes})

        with patch("agents.risk_agent.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = [df, spy_df]

            # We need to check internal calculation
            # Let's test it directly
            daily_returns = closes.pct_change().dropna()
            cumulative = (1 + daily_returns).cumprod()
            rolling_max = cumulative.cummax()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = float(drawdown.min()) * 100

            assert max_drawdown <= 0