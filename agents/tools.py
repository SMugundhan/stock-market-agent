from langchain_core . tools import tool

# @tool decorator converts a regular Py function into a Langchain tool obj that the LLM can tell

@tool
def get_stock_price ( ticker : str ) -> str :

    """
    Fetches current stock price, daily change percentage, and RSI
    for the given ticker symbol from Yahoo Finance.

    Use this tool when the user asks about:
    - Current stock price or today's movement
    - RSI or momentum indicators
    - Whether a stock is overbought or oversold

    Do NOT use this for: news sentiment, volatility, or risk scoring.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'TSLA', 'GOOGL')

    Returns:
        JSON string with price, change_pct, and rsi
    """

    from agents . price_agent import _fetch_price_sync

    from memory . cache import get_cached, set_cached

    cached  = get_cached ( "price", ticker )

    if cached :

        return str ( cached )
    
    result = _fetch_price_sync ( ticker )

    set_cached ( "price", ticker, result )

    return str ( result )

@tool
def get_stock_news ( ticker : str ) -> str:

    """
    Fetches latest stock news headlines and sentiment score
    for the given ticker symbol from Tavily.

    Use this tool when the user asks about:
    - Recent news articles or headlines
    - Overall sentiment of news coverage
    - Whether the news is positive, negative, or neutral

    Do NOT use this for: price, RSI, volatility, or risk scoring.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'TSLA', 'GOOGL')
    
    Returns:
        JSON string with news_headlines and sentiment_score ( -1 to +1 )

        """
    from tavily import TavilyClient

    from langchain_groq import ChatGroq

    from core . config import config

    tavily = TavilyClient ( api_key = config . TAVILY_API_KEY )

    results = tavily . search ( query = f" { ticker } stock news today ", max_results = 5 )

    articles = results . get ( "results", [] )

    headlines = [ a . get ( "title" ) for a in articles if a . get ( "title" ) ]

    llm = ChatGroq ( api_key = config . GROQ_API_KEY, model_name = config . MODEL_NAME )

    news_text = "\n" . join ( [ f" { a . get ( 'title', '' ) } : { a . get ( 'content', '' )  [ :150 ] }"  for a in articles ] )

    prompt = f" Sentiment score for { ticker } news ( -1 to 1 ) respond only with the number : \n { news_text } "

    score_str = llm . invoke ( prompt ) . content . strip()

    try :

        score = float ( score_str )

    except:

        score = 0.3

    return str ( { "headlines" : headlines[ :3 ], "sentiment_score" : score } )


@tool

def calculate_risk ( ticker : str ) -> str:

    """
    Calculates volatility, maximum drawdown, beta, and overall risk level
    for a given stock over the past 6 months.

    Use this tool when the user asks about:
    - How risky a stock is
    - Volatility or price stability
    - Whether a stock is suitable for conservative/aggressive investors
    - Beta or market sensitivity

    Do NOT use this for: current price, news, or recommendations.

    Args:
        ticker: Stock ticker symbol

    Returns:
        JSON string with volatility, risk_level (LOW/MEDIUM/HIGH)
    """

    from agents . risk_agent import _calculate_risk_sync

    from memory . cache import set_cached, get_cached

    cached = get_cached ( "risk", ticker )

    if cached :

        return str ( cached )
    
    result = _calculate_risk_sync ( ticker )

    set_cached ( "risk", ticker, result )

    return str ( result )


@tool
def get_full_analysis ( ticker : str ) -> str:

    """
    Runs a COMPLETE multi-agent analysis including price, news sentiment,
    risk metrics, and a BUY/HOLD/SELL recommendation.

    Use this tool when the user asks for:
    - A complete or full analysis
    - A recommendation on whether to buy, hold, or sell
    - A comprehensive overview of a stock

    This is the most expensive tool — only use when the user explicitly
    wants a full analysis, not for simple price checks or news queries.

    Args:
        ticker: Stock ticker symbol

    Returns:
        JSON string with complete analysis including recommendation
    """

    import json

    from agents . graph import build_graph

    graph = build_graph ()

    state = {
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

    final_state = graph . invoke ( state )

    report = json . loads ( final_state . get ( "final_report", "{}" ) )

    return str ( report . get ( "verdict", {} ) )


