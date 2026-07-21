import yfinance as yf # unofficial API for Yahoo Finance, lets us fetch free stock data

from core.state import StockAnalysisState #import our shared state definition

from memory. cache import set_cached, get_cached

from core . async_utils import run_sync_in_thread

import uuid

from core . logger import get_logger, log_with_context

import requests


# Reusable session — created once, reused across all price fetches,
# with browser-like headers to reduce yfinance blocking on cloud IPs
_yf_session = requests.Session()

_yf_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
})

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

# In production this would be a database of all NYSE/NASDAQ tickers
KNOWN_TICKERS = [
    "AAPL", "TSLA", "GOOGL", "AMZN", "MSFT",
    "META", "NFLX", "NVDA", "AMD", "INTC",
    "JPM", "BAC", "GS", "MS", "WMT",
    "RELIANCE.NS", "INFY", "TCS.NS", "WIPRO.NS"
]

logger = get_logger ( "price_agent" )
# Creates "stock_agent.price_agent" logger
# Call this ONCE at module level — not inside the function




def _fetch_price_sync ( ticker : str ) -> dict:

    """
    This stays sync ( Regular function as Yfinance itself cant be async )
    """
    # Step 2 : Create a yfinance Ticker object to fetch data.

    session = session or _yf_session
    
    stock = yf. Ticker ( ticker, session = session ) # yf.Ticker ( "AAAPL" ) creates an obj connected to AAPL stock data

    # Step 3 : Fetch last 30 days of price data using .history() method

    # period = "1mo" means 1 month, interval = "1d" means daily data

    # This returns a dataframe with columns like Open, High, Low, Close, Volume for each day

    hist = stock.history ( period = "1mo" , interval = "1d" )

    if hist . empty or "Close" not in hist . columns :

        raise ValueError ( "No price data for ticker" )

    # Step 4 : Get the most recent closing price from the dataframe
    # [ "Close" ] -> gives us the Close column, .iloc [ -1 ] gives us the last row (most recent day)


    current_price = round ( float ( hist [ "Close" ] . iloc [ -1 ] ) , 2 ) # round to 2 decimal places

    # Step 5 : Calculate percentage change from previous close

    pre_price = float ( hist [ "Close" ] . iloc [ -2 ] ) # previous day's close

    price_change_pct = round ( ( current_price - pre_price ) / pre_price * 100 , 2 ) # formula : ( current - previous ) / previous * 100

    # Step 6 : Calculate RSI (Relative Strength Index) using the price data

    # RSI measures if a stock is overbought (>70) or oversold (<30)

    # 30 - 70 is the typical range for RSI

    closes = hist [ "Close" ]

    deltas = closes.diff ( ) # price changes day to day

    # Seperate the gains and losses

    gains = deltas . clip ( lower = 0 ) # gains are positive changes, clip negative to 0

    loss = - deltas . clip ( upper = 0 ) # losses are negative changes, clip positive to 0 and negate to make positive

    # 14 day avg gain and loss ( standard period for RSI )

    avg_gain = gains . rolling ( window = 14 ) . mean ( ) . iloc [ -1 ] # average gain over 14 days

    avg_loss = loss . rolling ( window = 14 ) . mean ( ) . iloc [ -1 ] # average loss over 14 days

    # RSI formula : RSI = 100 - ( 100 / ( 1 + RS ) ) where RS = avg_gain / avg_loss

    if avg_loss == 0 : # to avoid division by zero

        rsi = 100.0 # if no losses, RSI is 100 (overbought)

    else :

        rs = avg_gain / avg_loss

        rsi = round ( 100 - ( 100 / ( 1 + rs ) ) , 2 )

    print ( f"Price Agent: Current Price = ${ current_price } , Change = { price_change_pct }% , RSI = { rsi }" )

    return {
            "current_price" : current_price ,
            "price_change_pct" : price_change_pct ,
            "rsi" : rsi
            }
        


async def price_agent_node ( state: StockAnalysisState ) -> dict :

    """
    Price agent node.
    Reads : state [ 'ticker' ]
    Writes : current_price, price_change_pct, rsi
    """
    # step 1 : read the ticker from the state
    
    ticker = state [ 'ticker' ]

    request_id = state . get ( "request_id", str ( uuid . uuid4 () ) )
    # Req id flows through all agent via state
    # uuid4 gens a random uniq id like "a1b2c3n4o6...."
    
    log_with_context ( logger, "info", "Price_agent_started", ticker = ticker, request_id = request_id, agent = "price_agent" )

    # step 1 check cache first

    cached_data = get_cached ( "price", ticker )

    if cached_data :

        log_with_context ( logger, "info", "Cahce_Hit --returning cached price data", ticker = ticker, request_id = request_id,cache_hit = True, agent = "price_agent" )

        return { **cached_data, "error" : [] }
    
    # Step 2 if Miss then fetch fresh data

    import time

    start = time . time ()

    try :

        # Await the thread pool wrapped sync call
        result = await run_sync_in_thread ( _fetch_price_sync, ticker )
        # Await here means : while yfinance is doing its blocking network call in a seperate thread, This event loop is free to go on New agent or any

        duration_ms = round ( ( time . time () - start ) * 1000, 2 )

        log_with_context ( logger, "info", "Price data fetched successfully", ticker = ticker, request_id = request_id,price = result [ "current_price" ],rsi = result [ "rsi" ],duration_ms = duration_ms, cache_hit = False, agent = "price_agent" )

        # Saves to cache

        set_cached ( "price", ticker, result )

        # Step 7 : Write the results back to the state
        
        # LanGraph merges this dict with existing state, so we only need to return the new values

        return {
            **result,
            "error" : []
            }
    
    except Exception as e :

        log_with_context ( logger, "error", f"Price_agent_failed : { str ( e ) }", ticker = ticker, request_id = request_id,error = str ( e ), agent = "price_agent" )

        return { "current_price" : None , "price_change_pct" : None , "rsi" : None , "error" : [ str ( e ) ] }

