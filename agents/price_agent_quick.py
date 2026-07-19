import yfinance as yf

from core. state import StockAnalysisState

from memory. cache import set_cached, get_cached

from core . async_utils import run_sync_in_thread

import requests



def _fetch_price_quick_async_ ( ticker : str ) -> dict:

    session = requests . Session ()
    
    stock = yf. Ticker ( ticker, session = session )

    hist = stock. history ( period = "1d" )

    current_price = round ( float ( hist [ "Close" ]. iloc [ -1 ]), 2 )

    return { "current_price" : current_price }


def price_agent_quick_node ( state : StockAnalysisState ) -> dict:

    ticker = state [ "ticker" ]

    print ( f" Quick Price agent getting only price values for ticker : { ticker } " )

    # Check for cache

    cached_data = get_cached ( 'price', ticker )

    if cached_data:

        print ( f" Using cached data for { ticker } " )

        return { "current_price" : cached_data [ "current_price" ] }
    
    # If miss fetch

    try :

        current_price = _fetch_price_quick_async_ ( ticker )
        
        result = { "current_price" : current_price }
    
        set_cached ( "price", ticker, result )

        return { **result, "error" : [] }

    except Exception as e:

        print ( f"Price Agent: Error fetching price data for { ticker } : { e }" )

        return { "current_price" : None , "error" : [ str ( e ) ] }

