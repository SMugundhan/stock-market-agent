# run_day10.py

from agents.llm_orchestrator import run_llm_orchestrator

test_queries = [
    # Should only call get_stock_price
    "Cuál es el precio actual de las acciones de Apple y el RSI?",

    # Should only call calculate_risk
    "Es Tesla demasiado arriesgada para una cartera de jubilación conservadora?",

    # Should call get_stock_news
    "What's the latest news sentiment on NVIDIA?",

    # Should call get_full_analysis
    "Give me a complete analysis of Microsoft with a recommendation",

    # Tricky — LLM needs to figure out which tools to combine
    "Compare the risk and sentiment of Apple vs Tesla",
]

def main():
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"❓ Query: {query}")
        print('='*60)
        result = run_llm_orchestrator(query)
        print(f"\n💬 Answer:\n{result}")
        print()

if __name__ == "__main__":
    main()