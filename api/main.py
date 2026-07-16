from contextlib import asynccontextmanager

import json

import uuid

from fastapi import FastAPI, HTTPException

from fastapi . middleware . cors import CORSMiddleware

from pydantic import BaseModel, Field

from api . schemas import AnalysisRequest, AnalysisResponse, HealthResponse

from agents . graph import build_graph

from agents . llm_orchestrator import run_llm_orchestrator

from memory . redis_client import redis_client

from memory . conversation import save_conversation_turn

from core . config import config

from core . logger import get_logger, log_with_context

from core . metrics import get_recent_metrics



logger = get_logger ( "api" )

# ── App State Container ─────────────────────────────────
# Replaces bare module-level: graph = build_graph()
# Starts empty → lifespan fills it → endpoints read from it

app_state = {}

# LifeSpan

@asynccontextmanager
async def lifespan ( app : FastAPI ) :

    """
    
    Startup (before yield):
        → Verify Redis is reachable
        → Build LangGraph pipeline
        → Log that server is ready

    Shutdown (after yield):
        → Close Redis connection
        → Clear app state
    """

    # start up

    logger . info ( "server starting up..." )

    # Step 1 check redis
    try :

        redis_client . ping ()

        logger . info ( "Redis Connection verified" )

    except Exception as e :

        logger . warning ( f" Redis un reachable : { e } --- caching disabled " )
        # Dont crash, run without redis

    # Step 2 build graph once and store in app_state
    logger . info ( "Building LangGraph pipeline....." )

    app_state [ "graph" ] = build_graph()

    logger . info ( "LangGraph pipeline ready" )

    logger . info ( f" API ready -- version { config . APP_VERSION } " )

    yield
    # Server lives here accepting requests

    # Shutdown

    logger . info ( "Server shutting down....." )

    try :

        redis_client . close ()
        
        logger . info ( "REDIS connection closed.." )

    except Exception as e :

        logger . warning ( f" Error closing Redis : { e } " )

    app_state . clear ()
    
    logger . info ( "shutdown completed" )


# ── Create the FastAPI app ──────────────────────────────
app = FastAPI (
    title = "Multi-Agent Stock Analysis API",
    description = "AI-powered stock analysis using LangGraph multi-agent system",
    version = config . APP_VERSION,
    lifespan = lifespan
)
# These show up automatically in the Swagger UI docs page

# ── CORS Middleware ──────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Without this, a frontend running on a different domain/port
# would be BLOCKED by the browser from calling your API
app.add_middleware(
    CORSMiddleware,
    allow_origins = [ "*" ],
    # ["*"] = allow requests from ANY origin
    # In production you'd restrict this to your actual frontend domain
    allow_methods = [ "*" ],
    allow_headers = [ "*" ],
)



class ChatRequest ( BaseModel ) :

    query : str = Field (  ..., description = " Natural langurage query about any stock ", examples = [ "Is apply stock is too risky for retirement portfolios?" ] )

    session_id : str = Field ( default = "anonymous" )

class ChatResponse ( BaseModel ) :

    query : str

    response : str

    session_id : str


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint — confirms API is running"""
    return {
        "message": "Multi-Agent Stock Analysis API",
        "docs": "/docs"
        # Reminds users where to find interactive documentation
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Used by monitoring systems, load balancers, Docker healthchecks
    to verify the service is alive and dependencies are connected.
    """

    redis_ok = True
    try:
        redis_client.ping()
    except Exception:
        redis_ok = False
        # If Redis is down, we still respond (graceful degradation)
        # but report it in the health check

    return HealthResponse(
        status="healthy" if redis_ok else "degraded",
        redis_connected=redis_ok
    )


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_stock(request: AnalysisRequest):
    """
    Main endpoint — runs the full multi-agent stock analysis.

    Takes a ticker, runs it through Orchestrator → Price → News
    → Risk → Analyst → Report agents, returns structured analysis.
    """

    request_id = str ( uuid . uuid4 () )

    log_with_context ( logger, "info", "Analysis_req_received", ticker = request . ticker,query_type = request . query_type, request_id = request_id, session_id = request . session_id )

    graph = app_state . get ( "graph" )

    if graph is None :

        raise HTTPException ( status_code = 503, detail = "Analysis Pipeline not ready -- server starting up"  )

    # ── Build initial state from request ────────────────
    initial_state = {
        "ticker":                 request.ticker,
        "query_type":             request.query_type,
        "analysis_type":          None,
        "should_fetch_news":      None,
        "should_calculate_risk":  None,
        "current_price":          None,
        "price_change_pct":       None,
        "rsi":                    None,
        "news_headlines":         None,
        "sentiment_score":        None,
        "volatility":             None,
        "risk_level":             None,
        "recommendation":         None,
        "confidence":             None,
        "reasoning":              None,
        "final_report":           None,
        "error":                 [],
        "retry_count":            0,
        "request_id":             request_id 
    }

    # ── Run the graph ────────────────────────────────────
    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        # If the graph itself crashes unexpectedly
        # HTTPException is FastAPI's way of returning proper error responses

        log_with_context ( logger, "critical", f"Analysis pipline crashed : { str ( e ) }", ticker = request . ticker, request_id = request_id, error = str ( e ) )


        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(e)}"
        )

    # ── Parse the report ─────────────────────────────────
    try:
        
        report = json.loads(final_state.get("final_report") or "{}")

    except json.JSONDecodeError as e:

        log_with_context ( logger, "critical", f"Failed to parse : { str ( e ) }", ticker = request . ticker, request_id = request_id, error = str ( e ) )

        raise HTTPException(
            status_code=500,
            detail="Failed to parse analysis report"
        )

    # Check if orchestrator rejected the ticker
    if final_state.get("analysis_type") == "error":

        log_with_context ( logger, "critical", f"Invalid ticker -- ticker was not found ", ticker = request . ticker, request_id = request_id, error = "Invalid Ticker" )

        raise HTTPException(
            status_code=404,
            # 404 because the resource (valid ticker) wasn't found
            detail=final_state.get("error", ["Unknown error"])[0]
        )

    # ── Save to conversation memory ──────────────────────
    save_conversation_turn(request.session_id, request.ticker, report)

    log_with_context ( logger, "info", "Analysis Completed and saves the convo", ticker = request . ticker, request_id = request_id, recommendation = report . get ( "verdict", {} ) . get ( "recommendation" ), confidence = report . get ( "verdict", {} ) . get ( "confidence" ) )

    # ── Return the response ──────────────────────────────
    # FastAPI automatically validates this against AnalysisResponse
    # and converts to JSON
    return report


@app.get("/stocks/{ticker}/quick", tags=["Analysis"])
def quick_price_check(ticker: str):
    """
    Lightweight endpoint — just price data, skips news/risk/LLM calls.
    Much faster than /analyze for simple price checks.
    """

    graph = app_state . get ( "graph" )

    if graph is None :

        raise HTTPException ( status_code = 503, detail = "Analysis Pipeline not ready -- server starting up"  )


    initial_state = {
        "ticker": ticker.upper(), "query_type": "quick",
        "analysis_type": None, "should_fetch_news": None,
        "should_calculate_risk": None, "current_price": None,
        "price_change_pct": None, "rsi": None,
        "news_headlines": None, "sentiment_score": None,
        "volatility": None, "risk_level": None,
        "recommendation": None, "confidence": None,
        "reasoning": None, "final_report": None,
        "error": [], "retry_count": 0
    }

    final_state = graph . invoke(initial_state)
    # This is not async becuz one one agent will run...no need of parallel exe

    return {
        "ticker": ticker.upper(),
        "price": final_state.get("current_price"),
        "change_pct": final_state.get("price_change_pct"),
        "rsi": final_state.get("rsi")
    }


@app . post ( "/chat", response_model = ChatResponse, tags = [ "Chat" ] )
def chat ( request : ChatRequest ) :

    """
    Natural language interface — ask anything about any stock.
    The LLM decides which tools to call based on your question.

    Examples:
    - "What is Tesla's current price?"
    - "Is Apple too volatile for conservative investors?"
    - "Give me a full analysis of Microsoft"
    - "What's the latest news sentiment on NVDA?"
    """
    response = run_llm_orchestrator ( request . query, request . session_id )

    return ChatResponse ( query = request . query, response = response, session_id = request . session_id )


@app.get( "/metrics", tags = [ "Monitoring" ] )

def get_metrics ( count : int = 10 ) :

    """
    Returns metrics for the most recent N analyses.
    Shows per-agent duration, cache hits, success rates.
    Useful for monitoring system health and performance.
    """

    metrics = get_recent_metrics ( count )

    return { "count" : len ( metrics ), "metrics" : metrics }


