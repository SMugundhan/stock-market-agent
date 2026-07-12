import pytest

import pandas as pd

import numpy as np

from unittest.mock import MagicMock, patch

# ── Shared Fixtures ─────────────────────────────────────

@pytest.fixture
def base_state():
    """
    Standard initial LangGraph state for testing.
    Every test that needs a state can use this fixture.
    """
    return {
        "ticker":                "AAPL",
        "query_type":            "full",
        "analysis_type":         None,
        "should_fetch_news":     None,
        "should_calculate_risk": None,
        "current_price":         None,
        "price_change_pct":      None,
        "rsi":                   None,
        "news_headlines":        None,
        "sentiment_score":       None,
        "volatility":            None,
        "risk_level":            None,
        "recommendation":        None,
        "confidence":            None,
        "reasoning":             None,
        "final_report":          None,
        "error":                [],
        "retry_count":           0,
        "request_id":            "test-request-001"
    }


@pytest.fixture
def partial_state():
    """
    State that's been partially filled — as if Price Agent already ran.
    Used for testing agents that depend on upstream data.
    """
    return {
        "ticker":                "AAPL",
        "query_type":            "full",
        "analysis_type":         "full",
        "should_fetch_news":     True,
        "should_calculate_risk": True,
        "current_price":         189.3,
        "price_change_pct":      1.2,
        "rsi":                   58.4,
        "news_headlines":        ["Apple hits record high", "Apple Q3 beats"],
        "sentiment_score":       0.68,
        "volatility":            22.4,
        "risk_level":            "MEDIUM",
        "recommendation":        None,
        "confidence":            None,
        "reasoning":             None,
        "final_report":          None,
        "error":                [],
        "retry_count":           0,
        "request_id":            "test-request-002"
    }


@pytest.fixture
def mock_yfinance_data():
    """
    Returns a mock pandas DataFrame that looks like what
    yfinance.Ticker.history() would return.
    Tests use this instead of calling real Yahoo Finance.
    """
    # Create 30 days of fake price data
    # np.linspace(185, 192, 30) = 30 evenly spaced values from 185 to 192
    closes = np.linspace(185.0, 192.0, 30)

    df = pd.DataFrame({
        "Close":  closes,
        "Open":   closes * 0.99,
        "High":   closes * 1.01,
        "Low":    closes * 0.98,
        "Volume": [50_000_000] * 30
    })
    return df