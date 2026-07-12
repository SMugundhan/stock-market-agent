import json

from memory.redis_client import redis_client

# Price changes every seconds, news changes every minutes

CACHE_TTL = {
    "price" : 60, # 60 seconds --- price moves fast
    "news" : 900, # 15 mins
    "risk" : 1800, # 30 mins --- risk metrics are stable
    "full_report" : 300, # 2 mins
}

def get_cached ( key_type : str, ticker : str ):

    """
    Try to get data from cache.

    Returns: parsed data if cache HIT, None if cache MISS
    """

    cache_key = f" cache : { key_type } : { ticker } " # Eg -> cache : price : AAPL

    cached_value = redis_client. get ( cache_key )

    if cached_value :

        print ( f" Cache Hit : { cache_key } " )

        return json. loads ( cached_value )
    # Json load converts JSON string to python dict

    print ( f" Cache Miss : { cache_key } " )

    return None

def set_cached ( key_type : str, ticker : str, data : dict ):

    """ Save data to catch with approppriate expiration """

    cache_key = f" cache : { key_type } : { ticker } "

    ttl = CACHE_TTL. get ( key_type, 300 )

    redis_client. set ( cache_key, json. dumps ( data ), ex = ttl )

    print ( f" Cached : { cache_key } ( expires in { ttl }s ) " )
