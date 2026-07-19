<!-- README.md -->

# Multi-Agent Stock Market Analysis System

> An autonomous AI agent pipeline that delivers real-time BUY/HOLD/SELL
> stock recommendations by coordinating 5 specialized agents using
> LangGraph, LLaMA 3.1, and production-grade infrastructure.

![CI Status](https://github.com/SMugundhan/stock-market-agent/actions/workflows/ci.yml/badge.svg)

![CD Status](https://github.com/SMugundhan/stock-market-agent/actions/workflows/cd.yml/badge.svg)

![Python](https://img.shields.io/badge/python-3.11-blue?logo=python)

![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)

![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)

![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-7C3AED)

![License](https://img.shields.io/badge/license-MIT-green)

**Live Demo:** https://stock-market-agent.onrender.com/docs

---

## 🎯 What This Does

Ask any question about any stock in natural language:

```
"Is Apple too risky for a conservative portfolio?"
→ Fetches live price + RSI from Yahoo Finance
→ Searches today's news via Tavily, scores sentiment with LLaMA 3.1
→ Calculates annualised volatility, max drawdown, beta vs S&P 500
→ LLM reasons over all data → BUY/HOLD/SELL + confidence score
→ Report Agent compiles structured JSON report + executive summary
```

Or use the structured API for programmatic access:

```bash
curl -X POST https://stock-market-agent.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "query_type": "full"}'
```

---

## 🏗️ Architecture

```
User Request (FastAPI /analyze)
         │
         ▼
┌─────────────────────┐
│   ORCHESTRATOR      │  Validates ticker (3-layer: name map →
│   AGENT             │  yFinance → fuzzy match), sets analysis
└────────┬────────────┘  type, conditional routing
         │
    ┌────┴─────┐
    │ Full     │ Quick
    ▼          ▼
┌──────────┐  ┌─────────────┐
│  PRICE   │  │ PRICE QUICK │
│  AGENT   │  │    AGENT    │──────────────────┐
└────┬─────┘  └─────────────┘                  │
     │                                          │
     ▼                                          │
┌──────────┐                                    │
│  NEWS    │  Tavily search + LLM sentiment      │
│  AGENT   │                                    │
└────┬─────┘                                    │
     │                                          │
     ▼                                          │
┌──────────┐                                    │
│  RISK    │  Volatility + Drawdown + Beta       │
│  AGENT   │                                    │
└────┬─────┘                                    │
     │                                          │
     ▼                                          │
┌──────────┐                                    │
│ ANALYST  │  LLM reasoning over all data        │
│  AGENT   │                                    │
└────┬─────┘                                    │
     │                                          │
     ▼                                          ▼
┌─────────────────────────────────────────────────┐
│              REPORT AGENT                       │
│  Structured JSON + LLM executive summary        │
└─────────────────────────────────────────────────┘
         │
         ▼
    Final Response
    {recommendation, confidence, market_data,
     sentiment, risk, executive_summary}
```

**State flows as a shared TypedDict through every node. Each agent reads what it needs and writes only its own fields. LangGraph merges return dicts automatically.**

---

## ✨ Key Features

| Feature                        | Implementation                                            |
| ------------------------------ | --------------------------------------------------------- |
| **5-Agent LangGraph Pipeline** | Orchestrator → Price → News → Risk → Analyst → Report     |
| **LLM-Driven Tool Calling**    | Orchestrator autonomously selects tools via ReAct pattern |
| **Real-Time Data**             | yFinance (price/RSI) + Tavily (news)                      |
| **Risk Metrics**               | Annualised volatility, max drawdown, beta vs SPY          |
| **Redis Caching**              | Per-type TTL: price 60s, news 15min, risk 30min           |
| **Async Execution**            | Price/News/Risk agents run concurrently via thread pool   |
| **Structured Output**          | Pydantic-validated JSON report with executive summary     |
| **Request Tracing**            | Unique request_id flows through every agent log line      |
| **Natural Language Chat**      | /chat endpoint — LLM picks tools for any query            |
| **Docker Compose Stack**       | API + Redis with health checks, named volumes             |
| **CI/CD Pipeline**             | GitHub Actions → Docker Hub → Render auto-deploy          |

---

## 🛠️ Tech Stack

| Layer                | Technology                       | Purpose                                        |
| -------------------- | -------------------------------- | ---------------------------------------------- |
| **LLM**              | LLaMA 3.1 8B via Groq            | Sentiment, analysis, tool calling, reports     |
| **Agent Framework**  | LangGraph                        | Stateful multi-agent graph orchestration       |
| **Web Search**       | Tavily API                       | Real-time financial news retrieval             |
| **Market Data**      | yFinance                         | Live price, RSI, historical OHLCV              |
| **API**              | FastAPI + Pydantic               | REST endpoints, request validation, Swagger UI |
| **Memory**           | Redis                            | Caching, conversation history, request metrics |
| **Async**            | asyncio + ThreadPoolExecutor     | Concurrent I/O-bound agent execution           |
| **Containerisation** | Docker + Docker Compose          | Reproducible deployments                       |
| **CI/CD**            | GitHub Actions                   | Test → Build → Push → Deploy automation        |
| **Registry**         | Docker Hub                       | Versioned image storage                        |
| **Hosting**          | Render.com                       | Production deployment                          |
| **Testing**          | pytest + pytest-asyncio          | Unit, integration, API tests with mocking      |
| **Logging**          | Python logging (structured JSON) | Request tracing, per-agent metrics             |

---

## 🚀 Quick Start

### Prerequisites

```
Python 3.11+
Docker + Docker Compose
Git
```

### Option A — Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/SMugundhan/stock-market-agent.git
cd stock-market-agent

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   GROQ_API_KEY=gsk_...
#   TAVILY_API_KEY=tvly_...

# 3. Start the full stack (API + Redis)
docker compose up

# 4. Open Swagger UI
open http://localhost:8000/docs
```

### Option B — Local Development

```bash
# 1. Clone and create virtual environment
git clone https://github.com/SMugundhan/stock-market-agent.git
cd stock-market-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Add your API keys to .env

# 4. Start Redis (via Docker)
docker run -d -p 6379:6379 redis:7-alpine

# 5. Start the API server
uvicorn api.main:app --reload

# 6. Open Swagger UI
open http://localhost:8000/docs
```

### Getting API Keys (Both Free)

```
Groq API  → https://console.groq.com    (LLaMA 3.1 inference)
Tavily    → https://tavily.com           (web search, 1000/month free)
```

---

## 📡 API Reference

### Core Endpoints

#### `POST /analyze` — Full Multi-Agent Analysis

Runs the complete 5-agent pipeline for a given stock ticker.

**Request:**

```json
{
  "ticker": "AAPL",
  "query_type": "full",
  "session_id": "user_123"
}
```

**`query_type` options:**
| Value | Agents Called | Use When |
|---|---|---|
| `full` | All 5 agents | Complete analysis needed |
| `quick` | Price Agent only | Just need current price fast |
| `risk_only` | Price + Risk | Risk assessment only |

**Response:**

```json
{
  "ticker": "AAPL",
  "report_date": "2026-07-13 18:57",
  "market_data": {
    "current_price": 189.3,
    "price_change_pct": 1.2,
    "rsi": 58.4
  },
  "sentiment": {
    "score": 0.68,
    "headlines": [
      "Apple hits 52-week high amid AI buzz",
      "Apple Q3 earnings beat expectations"
    ]
  },
  "risk": {
    "volatility_annual": 22.4,
    "risk_level": "MEDIUM"
  },
  "verdict": {
    "recommendation": "BUY",
    "confidence": 0.81,
    "reasoning": "RSI at 58.4 indicates neutral-bullish momentum...",
    "key_factors": [
      "Strong upward momentum (+1.2%)",
      "RSI in neutral zone (58.4)",
      "Strong positive news sentiment (0.68)",
      "MEDIUM risk profile (volatility: 22.4%)"
    ]
  },
  "executive_summary": "Apple Inc demonstrates strong near-term momentum...",
  "disclaimer": "For educational purposes only. Not financial advice."
}
```

---

#### `POST /chat` — Natural Language Interface

LLM autonomously selects which tools to call based on your query.

**Request:**

```json
{
  "query": "Is Tesla too volatile for a retirement portfolio?",
  "session_id": "user_123"
}
```

**Response:**

```json
{
  "query": "Is Tesla too volatile for a retirement portfolio?",
  "response": "Tesla (TSLA) carries a HIGH risk profile with 58.7% annual volatility and a maximum drawdown of -34.2% over the past 6 months...",
  "session_id": "user_123"
}
```

---

#### `GET /stocks/{ticker}/quick` — Fast Price Check

Returns price, change %, and RSI without running News or Risk agents.

```bash
curl https://stock-market-agent.onrender.com/stocks/AAPL/quick
```

```json
{
  "ticker": "AAPL",
  "price": 189.3,
  "change_pct": 1.2,
  "rsi": 58.4
}
```

---

#### `GET /health` — Health Check

Used by monitoring systems and Docker health checks.

```json
{
  "status": "healthy",
  "redis_connected": true,
  "version": "1.0.0"
}
```

---

#### `GET /metrics` — Recent Request Metrics

Returns timing data for the most recent analyses.

```json
{
  "count": 5,
  "metrics": [
    {
      "request_id": "a1b2c3d4",
      "ticker": "AAPL",
      "total_duration_ms": 4218,
      "agent_timings": {
        "price_agent": { "duration_ms": 342, "success": true },
        "news_agent": { "duration_ms": 2100, "success": true },
        "risk_agent": { "duration_ms": 1410, "success": true }
      },
      "final_recommendation": "BUY"
    }
  ]
}
```

---

## 📁 Project Structure

```
stock-market-agent/
├── agents/                      # All LangGraph agent nodes
│   ├── orchestrator.py          # Entry point — validates + routes
│   ├── price_agent.py           # Live price + RSI (yFinance)
│   ├── price_agent_quick.py     # Fast price-only variant
│   ├── news_agent.py            # Headlines + sentiment (Tavily + LLM)
│   ├── risk_agent.py            # Volatility + drawdown + beta
│   ├── analyst_agent.py         # BUY/HOLD/SELL recommendation (LLM)
│   ├── report_agent.py          # Structured JSON report compiler
│   ├── error_handler.py         # Graceful error responses
│   ├── routing.py               # Conditional routing functions
│   ├── tools.py                 # LangChain tool definitions
│   ├── llm_orchestrator.py      # LLM-driven tool calling (ReAct)
│   ├── graph.py                 # Sequential LangGraph pipeline
│   └── graph_parallel.py        # Parallel fan-out/fan-in variant
│
├── api/                         # FastAPI application layer
│   ├── main.py                  # App + all endpoints
│   └── schemas.py               # Pydantic request/response models
│
├── core/                        # Shared utilities
│   ├── config.py                # Environment variables + settings
│   ├── state.py                 # LangGraph TypedDict state schema
│   ├── logger.py                # Structured JSON logging
│   ├── metrics.py               # Per-request agent timing
│   └── async_utils.py           # Thread pool wrapper for sync libs
│
├── memory/                      # Redis integration
│   ├── redis_client.py          # Redis connection
│   ├── cache.py                 # get_cached / set_cached with TTL
│   └── conversation.py          # Session history management
│
├── tests/                       # Test suite
│   ├── conftest.py              # Shared fixtures
│   ├── test_price_agent.py      # Unit + async node tests
│   ├── test_risk_agent.py       # Math validation tests
│   ├── test_orchestrator.py     # Ticker validation + parametrize
│   ├── test_state_flow.py       # State integrity tests
│   └── test_api.py              # FastAPI endpoint tests
│
├── .github/
│   └── workflows/
│       ├── ci.yml               # Test → Lint → Docker verify
│       └── cd.yml               # Build → Push → Deploy → Health check
│
├── notes/                       # Daily study notes (HTML)
├── Dockerfile                   # Production container definition
├── docker-compose.yml           # Full stack: API + Redis
├── .dockerignore                # Excludes .env, cache, venv
├── .env.example                 # Template for required secrets
├── requirements.txt             # Python dependencies
├── VERSION                      # Semantic version (read by CI/CD)
├── Makefile                     # Shorthand dev commands
├── pytest.ini                   # Test configuration
└── README.md                    # This file
```

---

## 🧠 Key Technical Decisions

**Why LangGraph over CrewAI or AutoGen?**
LangGraph gives explicit control over agent graph topology — nodes, edges, conditional routing, and shared State. CrewAI abstracts too much for a portfolio project that needs to demonstrate architectural thinking. AutoGen is better for conversational research agents, not production API-served pipelines.

**Why thread pool wrapping instead of native async libraries?**
yFinance has no async version — the only way to achieve concurrency is wrapping sync calls in `run_in_executor`. This offloads the blocking network wait to a background thread while freeing the main event loop for other requests. For LLM calls, LangChain's `.ainvoke()` provides true async — queued as a refinement.

**Why Redis TTL differs per data type?**
Price data changes every second (60s TTL). News sentiment changes every few hours (15min TTL). Risk metrics (volatility, beta) are computed from 6-month history and barely change intraday (30min TTL). Tuning TTL per type balances data freshness against API cost and latency.

**Why Pydantic for both State and API schemas?**
TypedDict for LangGraph State gives type hints without runtime validation overhead — agents read/write frequently and speed matters. Pydantic for API schemas gives runtime validation with clear error messages — user-facing boundaries need strict enforcement. Different tools for different trust boundaries.

---

## 🧪 Running Tests

```bash
# All unit tests (fast, no external deps)
make test-unit

# Integration tests (needs Redis running)
make test-integration

# Full suite with coverage
make coverage

# Specific test file
pytest tests/test_price_agent.py -v
```

---

## 🔮 Roadmap

- [ ] Dynamic versioning via VERSION file pipeline integration
- [ ] FastAPI lifespan context manager for controlled startup
- [ ] True async LLM calls via `llm.ainvoke()`
- [ ] OpenTelemetry distributed tracing
- [ ] Grafana dashboards — cache hit rate, agent latency, error rates
- [ ] Rate limiting per session to prevent LLM quota abuse
- [ ] Price target calculation via technical analysis models
- [ ] Historical recommendation accuracy tracking
- [ ] Peer/sector comparison in reports
- [ ] Earnings calendar integration
- [ ] Portfolio fit analysis

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Mugundhan S**
[

![GitHub](https://img.shields.io/badge/GitHub-SMugundhan-181717?logo=github)

](https://github.com/SMugundhan)
[

![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin)

](https://www.linkedin.com/in/mugundhan-s-3b18b8286/)

> _Built as a portfolio project demonstrating production LLM engineering,
> multi-agent system design, and end-to-end MLOps practices._
