# Adding 3 layers of ticker validation to avaoid below things
    # Typos → APL instead of AAPL
    #Full names → "TESLA" instead of "TSLA"
    #Wrong exchange tickers → "RELIANCE" (Indian stock) in a US system
    #Delisted stocks → ticker exists but no data

import yfinance as ysf

from langchain_groq import ChatGroq

from core.state import StockAnalysisState

from core.config import config

from difflib import get_close_matches
# difflib is python's inbuild fuzzy matching library
# get_close_matches fins strings similar to a given string

llm = ChatGroq ( api_key = config.GROQ_API_KEY, model_name = config.MODEL_NAME )

# Common name -> Ticker mappping for popular stocks

COMMON_MAP_NAME = {
    "tesla":     "TSLA",
    "apple":     "AAPL",
    "microsoft": "MSFT",
    "google":    "GOOGL",
    "alphabet":  "GOOGL",
    "amazon":    "AMZN",
    "meta":      "META",
    "facebook":  "META",
    "netflix":   "NFLX",
    "nvidia":    "NVDA",
    "reliance":  "RELIANCE.NS",  # Indian stocks need .NS suffix
    "infosys":   "INFY",
}

# known valid tickker for fuzzy matching suggestions

# In production this would be a database of all NYSE/NASDAQ tickers
KNOWN_TICKERS = [
    "AAPL", "TSLA", "GOOGL", "AMZN", "MSFT",
    "META", "NFLX", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "GS", "MS", "WMT",
    "RELIANCE.NS", "INFY", "TCS.NS", "WIPRO.NS"
]

def validate_and_resolve_ticker ( ticker : str ) -> tuple [ str, str | None ] : 

    """
    Validates ticker and attempts to resolve it if wrong.

    Returns:
        (resolved_ticker, error_message)
        If valid: ("AAPL", None)
        If resolved: ("TSLA", None)  ← user typed "TESLA"
        If invalid: ("", "error message with suggestion")
    """

    # Layer 1 basic cleanup

    ticker = ticker. strip (). upper ()

    if not ticker:

        return '', " Ticker cannot be empty "
    
    # Layer 2 -> company name -> ticker mapping

    ticker_lower = ticker. lower ()

    if ticker_lower in COMMON_MAP_NAME:

        resolved = COMMON_MAP_NAME [ ticker_lower ]

        print ( f" Resolved Company name '{ ticker }' -> '{resolved}' " )

        return resolved, None
    
    # layer 3 Real time validation via yFinance
    # This is a reliable way to know if a ticker is valid or not

    try :

        test = ysf. Ticker ( ticker )

        info = test.info
        # info - fetched the onfo of the company from yahoo finance
        # if ticker dont exist it will be {}

        # Check if we got meaningful data back
        # "regularMarketPlace" exists for valid, active tickers
        # "longname" exists for most valid tickers

        has_price = info. get ( "regularMarketPrice" )is not None

        has_name = info. get ( "longName" )is not None
        
        if not has_name and not has_price:

            # Yfinance returns empty / minimal data -> invalid ticker
            # Try suggest closest vaid ticker

            suggestions = get_close_matches ( ticker, KNOWN_TICKERS, n = 3, cutoff = 0.5 )
            # return upto 3 suggestions and minimum 50% similairy

            if suggestions:

                suggestion_str = ','.join ( suggestions )

                return "", f" Ticker { ticker } not found. Do you mean : { suggestion_str } ? "
            
            else:

                return "", f" Ticker { ticker } not found. Please check the symbol "
            
        # Valid ticker ---- return it

        company_name = info. get ( "longName", ticker )

        print ( f" Validated : { ticker } = { company_name } " )

        return ticker, None

    except Exception as e:

        return "", f" Could not validate ticker { ticker } : { str ( e ) } "

def orchestrator_node ( state : StockAnalysisState ) -> dict:

    """
    Orchestrator Node — the entry point of the system.

    Reads:  state["ticker"], state["query_type"] (optional)
    Does:   Validates the request
            Determines analysis type
            Sets routing flags for downstream agents
    Writes: analysis_type, should_fetch_news, should_calculate_risk
    """

    ticker = state.get ( 'ticker', '' )

    print ( f" Orchestrator : Starting analysis for { ticker } " )

    # Validate ticker

    resolved_ticker, error = validate_and_resolve_ticker ( ticker )

    if error:

        # Tickers alwasy short -> AAPL, TSLA, GOOGL, etc..,
        
        print ( "Invalid ticker" )

        return {
            "error" : [ f" Invalid ticker : { ticker } " ],
            "analysis_type" : "error"
        }
    
    if resolved_ticker != ticker.strip().upper ():

        print ( f" Using resolved ticker : { resolved_ticker } " )
    
    # Determine what kindof analysis to run
    # Based on ticker type - this is simpliefied logic
    # In production, the LLM woul make this decision
    query = state. get ( "query_type", "full" ).lower ()
    # query type can be full, risk_only, quick
    # Default is full - all agents

    if query == "quick":

        # Quick mode - only price, skip news and risk

        print ( " Quick analysis mode --- ksipping news and risk " )

        return { "ticker" : resolved_ticker , "analysis_type" : "quick", "should_fetch_news": False, "should calculate risk" : False, "error" : [] }
    
    elif query == "risk_only":

        # Skip news

        print ( " Risk only mode " )

        return { "ticker" : resolved_ticker ,"analysis_type" : "risk_only", "should_fetch_news": False, "should calculate risk" : True, "error" : [] }
    
    else:

        # Full analysis

        print ( " Full analysis mode ---- running all agents " )

        return { "ticker" : resolved_ticker ,"analysis_type" : "Full", "should_fetch_news": True, "should calculate risk" : True, "error" : [] }




