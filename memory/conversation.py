import json

from datetime import datetime

from memory. redis_client import redis_client

import redis

CONVERSATION_TTL = 3600 # 1 hr of inactivity = conversation expires

def save_conversation_turn ( session_id : str, ticker : str, report : dict ) : 

    """
    Saves a single conversation turn so follow-up questions work.

    Example: User asks "What was the RSI?" after analyzing AAPL
    We need to remember the AAPL analysis to answer this.
    """

    conversation_key = f" conversation : { session_id } "

    # Get existing convo id or start a fresh one

    try :

        existing = redis_client. get ( conversation_key )

        history = json. loads ( existing ) if existing else []

        history. append ( { "timestamp" : datetime.now ().isoformat(), # isoformat -> "2026-06-16T14:30:00"  --- standard format
                        "ticker" : ticker,
                        "report_summary" : {
                                            "recommendation" : report. get ( "verdict", {} ). get ( "recommendation" ),
                                            "confidence" : report. get ( "verdict", {} ). get ( "confidence" ),
                                            "price" : report . get ( "market_data", {} ). get ( "current_price" ),
                                            "rsi" : report. get ( "market_data", {} ) . get ( "rsi" )
                                            }
                        } )
    

        # keep only last 10 turns --- prevent unlimited growth
        history = history [ -10 : ]

        # Save back to redis, refresh expiration

        redis_client. set ( conversation_key, json.dumps ( history ), ex = CONVERSATION_TTL )

        print ( f" Saved convos turn for session { session_id } " )

    except redis . exception . RedisError as e :

        print ( f"Could not save the conversation turn  -- redis unavailable" )


def get_conversation_history ( session_id : str ) -> list:

    """ Retrives conversation history for follow up question handling """

    conversation_key = f" conversation : { session_id } "

    try :

        existing = redis_client. get ( conversation_key )

    except redis . exceptions . RedisError as e:

        print ( f"Could not fetch the convo  --- redis unavailable ( {e} )" )

        return []

    if existing :

        return json. loads ( existing )
    
    return []


def get_last_ticker ( session_id : str ) -> str | None:

    """
    Useful for follow-up questions like "what was the RSI?"
    without re-specifying the ticker.
    """

    history = get_conversation_history ( session_id )

    if history:

        return history [ -1 ][ 'ticker' ]

        # [ -1 ] = most recent entry in the list

    return None