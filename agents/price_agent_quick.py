import yfinance as yf

from core. state import StockAnalysisState

from memory. cache import set_cached, get_cached

from core . async_utils import run_sync_in_thread

import requests

import uuid

from core . logger import get_logger, log_with_context

# Reusable session — created once, reused across all price fetches,
# with browser-like headers to reduce yfinance blocking on cloud IPs
_yf_session = requests.Session()

_yf_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
})

logger = get_logger ( "price_agent_quick" )

def _fetch_price_quick_async_ ( ticker : str, session : requests . Session = None ) -> dict:

    session = session or _yf_session
    
    stock = yf. Ticker ( ticker, session = session )

    hist = stock. history ( period = "1d" )

    current_price = round ( float ( hist [ "Close" ]. iloc [ -1 ]), 2 )

    log_with_context ( logger, "info", "Quick_Price_agent_fetch_quick_sync", ticker = ticker, agent = "quick_price_agent" )


    return { "current_price" : current_price }


def price_agent_quick_node ( state : StockAnalysisState ) -> dict:

    ticker = state [ "ticker" ]

    request_id = state . get ( "request_id", str ( uuid . uuid4() ) )

    print ( f" Quick Price agent getting only price values for ticker : { ticker }, request_id : { request_id } " )

    log_with_context ( logger, "info", "Quick_Price_agent_started", ticker = ticker, request_id = request_id, agent = "quick_price_agent" )


    # Check for cache

    cached_data = get_cached ( 'price', ticker )

    if cached_data:

        log_with_context ( logger, "info", "CACHE HIT ---- RETURNING CACHED DATA", ticker = ticker, request_id = request_id, agent = "quick_price_agent" )

        return { "current_price" : cached_data [ "current_price" ] }
    
    # If miss fetch

    try :

        current_price = _fetch_price_quick_async_ ( ticker )
        
        result = { "current_price" : current_price }
    
        set_cached ( "price", ticker, result )

        return { **result, "error" : [] }

    except Exception as e:

        print ( f"Price Agent: Error fetching price data for { ticker } : { e }" )

        log_with_context ( logger, "info", "ERROR --- QUICK PRICE AGENT", ticker = ticker, request_id = request_id, agent = "quick_price_agent", error = str ( { e } ) )

        return { "current_price" : None , "error" : [ str ( e ) ] }

