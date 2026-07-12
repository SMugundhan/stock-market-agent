# run_day9_benchmark.py

import asyncio
import time
from agents.graph import build_graph              # sequential (Day 6 version)
from agents.graph_parallel import build_parallel_graph   # NEW parallel version

def make_initial_state(ticker):
    return {
        "ticker": ticker, "query_type": "full",
        "analysis_type": None, "should_fetch_news": None,
        "should_calculate_risk": None, "current_price": None,
        "price_change_pct": None, "rsi": None,
        "news_headlines": None, "sentiment_score": None,
        "volatility": None, "risk_level": None,
        "recommendation": None, "confidence": None,
        "reasoning": None, "final_report": None,
        "error": [], "retry_count": 0
    }

async def benchmark():
    ticker = "AAPL"

    # ── Sequential version ────────────────────────────────
    seq_graph = build_graph()
    start = time.time()
    await seq_graph.ainvoke(make_initial_state(ticker))
    # .ainvoke() = async version of .invoke() — needed since
    # our nodes are now async functions
    seq_time = time.time() - start

    # ── Parallel version ──────────────────────────────────
    par_graph = build_parallel_graph()
    start = time.time()
    await par_graph.ainvoke(make_initial_state(ticker))
    par_time = time.time() - start

    print(f"\n{'='*50}")
    print(f"⏱️  BENCHMARK RESULTS for {ticker}")
    print(f"{'='*50}")
    print(f"Sequential pipeline: {seq_time:.2f}s")
    print(f"Parallel pipeline:   {par_time:.2f}s")
    print(f"Speedup:             {seq_time/par_time:.2f}x faster")

if __name__ == "__main__":
    asyncio.run(benchmark())
    # asyncio.run() is the entry point — starts the event loop
    # and runs our async benchmark() function to completion