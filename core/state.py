from typing import TypedDict, List, Optional

class StockAnalysisState ( TypedDict ):

    # This is shared patient file, where every agent reads from it
    
    # Input

    ticker : str    # The stock ticker user wants to analyze eg: "AAPL", "GOOG", "TSLA"

    query_type : Optional [ str ]

    request_id : Optional [ str ]

    # Orchestrator agent output

    analysis_type : Optional [ str ]    # full / risk_only / quick

    should_fetch_news : Optional [ bool ] # True -> news agent else skip

    should_calculate_risk : Optional [ bool ] # True -> risk agent else skip
    
    # Price agent output

    current_price : Optional [ float ]  # Current stock price, to be filled by Price Agent in USD

    price_change_pct : Optional [ float ]  # Percentage change in stock price from previous close e.g +1.2 means +1.2%

    rsi : Optional [ float ] # Above 70 = overbought, below 30 = oversold

    # News agent output

    news_headlines : Optional [ List [ str ] ]  # List of recent news headlines related to the stock

    sentiment_score : Optional [ float ]  # Sentiment score of the news, range -1 (negative) to +1 (positive)

    # Risk agent output

    volatility : Optional [ float ]  # Stock price volatility, higher means more risk

    risk_level : Optional [ str ]  # Risk level based on volatility, e.g "Low", "Medium", "High"

    # Analysis agent output

    recommendation : Optional [ str ]  # Final recommendation, e.g "Buy", "Hold", "Sell"

    confidence : Optional [ float ]  # Confidence level of the recommendation, range 0 to 1

    reasoning : Optional [ str ]  # Explanation of the recommendation based on the collected data

    # Report Agent output

    final_report : Optional [ str ]  # A comprehensive report summarizing the analysis and recommendation

    # Meta data

    error: Optional [ str ]  # To capture any errors that occur during the analysis process