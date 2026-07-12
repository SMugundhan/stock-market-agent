# tests/test_state_flow.py

import pytest
from unittest.mock import patch, AsyncMock


class TestStateFlow:
    """
    Integration tests that verify State is correctly passed
    and updated as it flows through multiple agents.
    """

    @pytest.mark.asyncio
    async def test_ticker_preserved_through_pipeline(self, base_state):
        """
        The ticker set in initial_state must remain unchanged
        after Price Agent runs — agents should only ADD fields,
        never overwrite existing ones they don't own.
        """
        with patch("agents.price_agent.get_cached", return_value=None):
            with patch("agents.price_agent.yf.Ticker") as mock_yf:
                with patch("agents.price_agent.set_cached"):
                    mock_df = create_mock_dataframe()
                    mock_yf.return_value.history.return_value = mock_df

                    from agents.price_agent import price_agent_node
                    result = await price_agent_node(base_state)

                    # Ticker in base_state was "AAPL" — should not change
                    # Note: result only contains what price_agent WRITES
                    # The original state dict is NOT mutated by LangGraph
                    # when running outside the graph — test independently
                    assert base_state["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_price_agent_fills_correct_fields(self, base_state):
        """Price Agent should fill exactly these fields and no others"""
        with patch("agents.price_agent.get_cached", return_value=None):
            with patch("agents.price_agent.yf.Ticker") as mock_yf:
                with patch("agents.price_agent.set_cached"):
                    mock_yf.return_value.history.return_value = \
                        create_mock_dataframe()

                    from agents.price_agent import price_agent_node
                    result = await price_agent_node(base_state)

                    # Must fill these
                    assert "current_price" in result
                    assert "price_change_pct" in result
                    assert "rsi" in result
                    assert "error" in result

                    # Must NOT fill these (another agent's responsibility)
                    assert "news_headlines" not in result
                    assert "volatility" not in result
                    assert "recommendation" not in result

    @pytest.mark.asyncio
    async def test_errors_list_empty_on_success(self, base_state):
        """On success, errors field must be an empty list, not None"""
        with patch("agents.price_agent.get_cached", return_value=None):
            with patch("agents.price_agent.yf.Ticker") as mock_yf:
                with patch("agents.price_agent.set_cached"):
                    mock_yf.return_value.history.return_value = \
                        create_mock_dataframe()

                    from agents.price_agent import price_agent_node
                    result = await price_agent_node(base_state)

                    assert result["error"] == []
                    assert isinstance(result["error"], list)

    def test_state_fields_all_present(self, base_state):
        """
        Verify the base state fixture has all required fields.
        If we add a new field to StockAnalysisState, this test will
        catch that the fixture needs updating too.
        """
        from core.state import StockAnalysisState
        import typing

        required_keys = typing.get_type_hints(StockAnalysisState).keys()
        for key in required_keys:
            assert key in base_state, \
                f"base_state fixture is missing field: '{key}'"


# ── Helper ──────────────────────────────────────────────
import pandas as pd
import numpy as np

def create_mock_dataframe(num_days: int = 30):
    """Creates a minimal mock price DataFrame for testing"""
    closes = np.linspace(185.0, 192.0, num_days)
    return pd.DataFrame({"Close": closes, "Volume": [50_000_000] * num_days})