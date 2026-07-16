# api/schemas.py

from pydantic import BaseModel, Field

from typing import Optional, List

from core . config import config

# ── REQUEST MODELS ──────────────────────────────────────

class AnalysisRequest(BaseModel):
    """What the user sends us to request an analysis"""

    ticker: str = Field(
        ...,
        # ... means this field is REQUIRED (no default value)
        description="Stock ticker symbol e.g. AAPL, TSLA",
        examples=["AAPL"]
        # examples shows up in Swagger UI as a sample
    )

    query_type: str = Field(
        default="full",
        description="Type of analysis: full, quick, or risk_only"
    )

    session_id: Optional[str] = Field(
        default="anonymous",
        description="Session ID for conversation memory"
    )


# ── RESPONSE MODELS ─────────────────────────────────────

class MarketData(BaseModel):
    current_price:    Optional[float] = None
    price_change_pct: Optional[float] = None
    rsi:               Optional[float] = None

class SentimentData(BaseModel):
    score:     Optional[float] = None
    headlines: List[str] = []

class RiskData(BaseModel):
    volatility_annual: Optional[float] = None
    risk_level:        Optional[str] = None

class Verdict(BaseModel):
    recommendation: Optional[str] = None
    confidence:      Optional[float] = None
    reasoning:        Optional[str] = None
    key_factors:      List[str] = []

class AnalysisResponse(BaseModel):
    """What we send back to the user"""

    ticker:             str
    report_date:        str
    market_data:        MarketData
    sentiment:           SentimentData
    risk:                RiskData
    verdict:             Verdict
    executive_summary:   str
    disclaimer:           str


class HealthResponse(BaseModel):
    status: str
    redis_connected: bool
    version: str = config . APP_VERSION


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None