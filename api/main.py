# api/main.py

from contextlib import asynccontextmanager
import json
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from agents.graph import build_graph
from agents.llm_orchestrator import run_llm_orchestrator
from memory.redis_client import redis_client
from memory.conversation import save_conversation_turn
from core.config import config          # ← instance, not class
from core.logger import get_logger, log_with_context
from core.metrics import get_recent_metrics

logger = get_logger("api")

# ── App State Container ─────────────────────────────────
# Replaces bare module-level: graph = build_graph()
# Starts empty → lifespan fills it → endpoints read from it
app_state = {}


# ── Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup (before yield):
      → Verify Redis is reachable
      → Build LangGraph pipeline
      → Log that server is ready

    Shutdown (after yield):
      → Close Redis connection
      → Clear app state
    """

    # ── STARTUP ────────────────────────────────────────
    logger.info("🚀 Server starting up...")

    # Step 1: Check Redis before accepting any requests
    try:
        redis_client.ping()
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.warning(f"⚠️  Redis unreachable: {e} — caching disabled")
        # Don't crash — app still works without Redis, just slower

    # Step 2: Build the graph ONCE, store in app_state
    logger.info("🔧 Building LangGraph pipeline...")
    app_state["graph"] = build_graph()
    logger.info("✅ LangGraph pipeline ready")

    logger.info(f"✅ API ready — version {config.APP_VERSION}")

    yield
    # ← Server lives here, accepting requests

    # ── SHUTDOWN ───────────────────────────────────────
    logger.info("🛑 Server shutting down...")
    try:
        redis_client.close()
        logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis: {e}")

    app_state.clear()
    logger.info("✅ Shutdown complete")


# ── Create FastAPI App ──────────────────────────────────
app = FastAPI(
    title="Multi-Agent Stock Analysis API",
    description="AI-powered stock analysis using LangGraph multi-agent system",
    version=config.APP_VERSION,     # ← reads from VERSION file
    lifespan=lifespan               # ← wires our lifecycle in
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models (Chat) ──────────────────────
class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language query about any stock",
        examples=["Is Apple stock too risky for retirement portfolios?"]
    )
    session_id: str = Field(default="anonymous")


class ChatResponse(BaseModel):
    query: str
    response: str
    session_id: str


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint — confirms API is running"""
    return {
        "message": "Multi-Agent Stock Analysis API",
        "version": config.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Used by monitoring systems, load balancers, Docker health checks.
    """
    redis_ok = True
    try:
        redis_client.ping()
    except Exception:
        redis_ok = False

    return HealthResponse(
        status="healthy" if redis_ok else "degraded",
        redis_connected=redis_ok
    )


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_stock(request: AnalysisRequest):
    """
    Full multi-agent stock analysis.
    Orchestrator → Price → News → Risk → Analyst → Report
    """

    request_id = str(uuid.uuid4())

    log_with_context(
        logger, "info", "Analysis request received",
        ticker=request.ticker,
        query_type=request.query_type,
        request_id=request_id,
        session_id=request.session_id
    )

    # ── Read graph from app_state (set during lifespan startup) ──
    graph = app_state.get("graph")
    if graph is None:
        raise HTTPException(
            status_code=503,
            detail="Analysis pipeline not ready — server is starting up"
        )

    initial_state = {
        "ticker":                request.ticker,
        "query_type":            request.query_type,
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
        "error":                [],    # ← plural, fixed
        "retry_count":           0,
        "request_id":            request_id
    }

    # ── Run the graph ────────────────────────────────────
    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        log_with_context(
            logger, "critical",
            f"Analysis pipeline crashed: {str(e)}",
            ticker=request.ticker,
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(e)}"
        )

    # ── Parse the report ─────────────────────────────────
    try:
        report = json.loads(final_state.get("final_report") or "{}")
    except json.JSONDecodeError as e:
        log_with_context(
            logger, "critical",
            f"Failed to parse report: {str(e)}",
            ticker=request.ticker,
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to parse analysis report"
        )

    # ── Check if orchestrator rejected the ticker ────────
    if final_state.get("analysis_type") == "error":
        log_with_context(
            logger, "warning",
            "Invalid ticker rejected by orchestrator",
            ticker=request.ticker,
            request_id=request_id
        )
        raise HTTPException(
            status_code=404,
            detail=final_state.get("error", ["Unknown error"])[0]
            
        )

    # ── Save to conversation memory ──────────────────────
    save_conversation_turn(request.session_id, request.ticker, report)

    log_with_context(
        logger, "info",
        "Analysis completed",
        ticker=request.ticker,
        request_id=request_id,
        recommendation=report.get("verdict", {}).get("recommendation"),
        confidence=report.get("verdict", {}).get("confidence")
    )

    return report


@app.get("/stocks/{ticker}/quick", tags=["Analysis"])
def quick_price_check(ticker: str):
    """
    Lightweight endpoint — price data only.
    Skips News, Risk, Analyst agents entirely.
    """

    graph = app_state.get("graph")
    if graph is None:
        raise HTTPException(status_code=503, detail="Server starting up")

    initial_state = {
        "ticker":                ticker.upper(),
        "query_type":            "quick",
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
        "error":                [],   # ← plural, fixed
        "retry_count":           0
    }

    final_state = graph.invoke(initial_state)
    # ← sync .invoke() here because this endpoint is def (not async def)
    # If you change this to async def, use await graph.ainvoke()

    return {
        "ticker":     ticker.upper(),
        "price":      final_state.get("current_price"),
        "change_pct": final_state.get("price_change_pct"),
        "rsi":        final_state.get("rsi")
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Natural language interface — LLM picks tools autonomously.
    Examples:
      - "What is Tesla's current price?"
      - "Is Apple too volatile for conservative investors?"
      - "Give me a full analysis of Microsoft"
    """
    response = run_llm_orchestrator(request.query, request.session_id)
    return ChatResponse(
        query=request.query,
        response=response,
        session_id=request.session_id
    )


@app.get("/metrics", tags=["Monitoring"])
def get_metrics(count: int = 10):
    """
    Returns metrics for the most recent N analyses.
    Shows per-agent duration, cache hits, success rates.
    """
    metrics = get_recent_metrics(count)
    return {"count": len(metrics), "metrics": metrics}