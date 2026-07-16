# tests/test_api.py

from unittest.mock import MagicMock, patch, AsyncMock

import pytest

import json

from fastapi.testclient import TestClient
# TestClient = FastAPI's built-in synchronous test client
# Lets you make HTTP requests to your FastAPI app in tests
# WITHOUT actually starting a server — no port, no network

from api . main import app, get_graph

from api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Health check tests — should always be fast and reliable"""

    def test_health_returns_200(self):
        """Health endpoint must return HTTP 200"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_has_status(self):
        """Response must have a 'status' field"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_status_is_string(self):
        """Status field must be a string ('healthy' or 'degraded')"""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["status"], str)
        assert data["status"] in ["healthy", "degraded"]


class TestAnalyzeEndpoint:
    """
    Tests for the main /analyze endpoint.
    Uses mocks to avoid real API calls during testing.
    """

    def get_mock_report(self):
        """Returns a fake but correctly structured final report"""
        return json.dumps({
            "ticker": "AAPL",
            "report_date": "2026-06-16 14:30",
            "analysis_type": "full",
            "market_data": {
                "current_price": 189.3,
                "price_change_pct": 1.2,
                "rsi": 58.4
            },
            "sentiment": {"score": 0.68, "headlines": []},
            "risk": {"volatility_annual": 22.4, "risk_level": "MEDIUM"},
            "verdict": {
                "recommendation": "BUY",
                "confidence": 0.78,
                "reasoning": "Strong fundamentals",
                "key_factors": ["momentum", "neutral RSI"]
            },
            "executive_summary": "Apple shows strong momentum...",
            "disclaimer": "For educational purposes only.",
            "generated_by": "Multi-Agent Stock Analysis System v1.0",
            "errors": []
        })

    def test_valid_ticker_returns_200(self):
        
        mock_graph = MagicMock()
        
        mock_graph.ainvoke = AsyncMock(return_value={...})  # analyze uses ainvoke — note async mock!

        app.dependency_overrides[get_graph] = lambda: mock_graph

        with TestClient(app) as client:
            
            response = client.post("/analyze", json={"ticker": "AAPL"})

        assert response.status_code == 200
        
        app.dependency_overrides.clear()

        
    def test_response_has_verdict(self):
        """Response must contain a verdict with recommendation"""
        with patch("api.main.graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock ( return_value = {
                "final_report": self.get_mock_report(),
                "analysis_type": "full",
                "errors": []
            } )
            with patch("api.main.save_conversation_turn"):
                response = client.post("/analyze", json={"ticker": "AAPL"})
                data = response.json()
                assert "verdict" in data
                assert "recommendation" in data["verdict"]

    def test_recommendation_is_valid_value(self):
        """Recommendation must be BUY, HOLD, or SELL"""
        with patch("api.main.graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock ( return_value = {
                "final_report": self.get_mock_report(),
                "analysis_type": "full",
                "errors": []
            } )
            with patch("api.main.save_conversation_turn"):
                response = client.post("/analyze", json={"ticker": "AAPL"})
                data = response.json()
                rec = data["verdict"]["recommendation"]
                assert rec in ["BUY", "HOLD", "SELL"]

    def test_missing_ticker_returns_422(self):
        """Request without ticker field should return 422 Unprocessable"""
        response = client.post("/analyze", json={
            "query_type": "full"
            # ticker is missing!
        })
        assert response.status_code == 422
        # FastAPI's Pydantic validation auto-returns 422 for missing
        # required fields — we don't need to write this logic ourselves

    def test_error_state_returns_404(self):
        """If orchestrator rejects the ticker, return 404"""
        with patch("api.main.graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock ( return_value = {
                "final_report": None,
                "analysis_type": "error",
                "errors": ["Invalid ticker: INVALIDXYZ"],
                "ticker": "INVALIDXYZ"
            } )
            response = client.post("/analyze", json={
                "ticker": "INVALIDXYZ"
            })
            assert response.status_code == 404